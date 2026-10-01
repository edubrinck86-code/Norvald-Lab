from __future__ import annotations

import asyncio
import shutil
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import psutil
except ModuleNotFoundError:  # capacidade opcional; não derruba o Studio
    psutil = None

from norvald_lab.application.arof.raw_observation import json_safe


PSUTIL_AVAILABLE = psutil is not None


def require_capacity_dependencies() -> None:
    if psutil is None:
        raise RuntimeError(
            "CapacityMonitor indisponível: instale as dependências do backend "
            "com 'python -m pip install -r backend/requirements.txt' "
            "(psutil>=6.0)."
        )


@dataclass(frozen=True)
class CapacitySample:
    captured_at: str
    elapsed_seconds: float
    system_cpu_percent: float
    process_cpu_percent: float
    system_memory_percent: float
    system_available_bytes: int
    process_rss_bytes: int
    disk_free_bytes: int

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


@dataclass(frozen=True)
class CapacityReport:
    started_at: str
    finished_at: str
    elapsed_seconds: float
    sample_count: int

    process_rss_start_bytes: int
    process_rss_end_bytes: int
    process_rss_peak_bytes: int

    system_cpu_peak_percent: float
    process_cpu_peak_percent: float
    system_memory_peak_percent: float

    disk_free_start_bytes: int
    disk_free_end_bytes: int
    disk_free_min_bytes: int

    dataset_bytes_start: int
    dataset_bytes_end: int
    dataset_growth_bytes: int

    logical_executions: int
    attempts: int
    failures: int

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


def _directory_size(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            continue
    return total


class CapacityMonitor:
    """Amostrador leve da máquina durante um experimento.

    Não decide se o notebook "aguenta" nem define threshold científico.
    Apenas registra uso observado para que a decisão seja feita com dados.

    O monitor não roda como serviço do Studio. Existe somente enquanto o
    Experiment Runner explicitamente o inicia.
    """

    def __init__(
        self,
        *,
        disk_path: str | Path,
        dataset_path: str | Path | None = None,
        sample_interval_seconds: float = 1.0,
    ) -> None:
        if sample_interval_seconds <= 0:
            raise ValueError("sample_interval_seconds deve ser > 0")
        require_capacity_dependencies()
        self.disk_path = Path(disk_path)
        self.dataset_path = Path(dataset_path) if dataset_path is not None else None
        self.sample_interval_seconds = float(sample_interval_seconds)
        try:
            self._process = psutil.Process()
        except psutil.NoSuchProcess:
            # Alguns executores isolam os PIDs, mas montam /proc do host.
            # /proc/self continua apontando para este processo; nunca medir
            # um PID arbitrário nem inventar valores para preencher o relatório.
            proc_self = Path("/proc/self/stat")
            if not proc_self.exists():
                raise
            self._process = psutil.Process(int(proc_self.read_text().split()[0]))
        self._samples: list[CapacitySample] = []
        self._task: asyncio.Task | None = None
        self._running = False
        self._started_monotonic = 0.0
        self._started_at = ""
        self._dataset_bytes_start = 0

    @property
    def samples(self) -> tuple[CapacitySample, ...]:
        return tuple(self._samples)

    async def start(self) -> None:
        if self._running:
            raise RuntimeError("CapacityMonitor já iniciado")
        self._running = True
        self._samples = []
        self._started_monotonic = time.monotonic()
        self._started_at = datetime.now(timezone.utc).isoformat()
        self._dataset_bytes_start = _directory_size(self.dataset_path)

        # Primeira leitura inicializa os contadores percentuais do psutil.
        psutil.cpu_percent(interval=None)
        self._process.cpu_percent(interval=None)
        self._samples.append(self._sample())
        self._task = asyncio.create_task(self._loop())

    async def stop(
        self,
        *,
        logical_executions: int = 0,
        attempts: int = 0,
        failures: int = 0,
    ) -> CapacityReport:
        if not self._running:
            raise RuntimeError("CapacityMonitor não iniciado")
        self._running = False

        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        self._samples.append(self._sample())
        finished_at = datetime.now(timezone.utc).isoformat()
        elapsed = max(0.0, time.monotonic() - self._started_monotonic)
        dataset_bytes_end = _directory_size(self.dataset_path)

        first = self._samples[0]
        last = self._samples[-1]
        return CapacityReport(
            started_at=self._started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed,
            sample_count=len(self._samples),
            process_rss_start_bytes=first.process_rss_bytes,
            process_rss_end_bytes=last.process_rss_bytes,
            process_rss_peak_bytes=max(s.process_rss_bytes for s in self._samples),
            system_cpu_peak_percent=max(s.system_cpu_percent for s in self._samples),
            process_cpu_peak_percent=max(s.process_cpu_percent for s in self._samples),
            system_memory_peak_percent=max(s.system_memory_percent for s in self._samples),
            disk_free_start_bytes=first.disk_free_bytes,
            disk_free_end_bytes=last.disk_free_bytes,
            disk_free_min_bytes=min(s.disk_free_bytes for s in self._samples),
            dataset_bytes_start=self._dataset_bytes_start,
            dataset_bytes_end=dataset_bytes_end,
            dataset_growth_bytes=dataset_bytes_end - self._dataset_bytes_start,
            logical_executions=max(0, int(logical_executions)),
            attempts=max(0, int(attempts)),
            failures=max(0, int(failures)),
        )

    async def _loop(self) -> None:
        while self._running:
            await asyncio.sleep(self.sample_interval_seconds)
            if self._running:
                self._samples.append(self._sample())

    def _sample(self) -> CapacitySample:
        memory = psutil.virtual_memory()
        disk = shutil.disk_usage(self.disk_path)
        return CapacitySample(
            captured_at=datetime.now(timezone.utc).isoformat(),
            elapsed_seconds=max(0.0, time.monotonic() - self._started_monotonic),
            system_cpu_percent=float(psutil.cpu_percent(interval=None)),
            process_cpu_percent=float(self._process.cpu_percent(interval=None)),
            system_memory_percent=float(memory.percent),
            system_available_bytes=int(memory.available),
            process_rss_bytes=int(self._process.memory_info().rss),
            disk_free_bytes=int(disk.free),
        )
