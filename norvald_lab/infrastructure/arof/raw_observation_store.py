from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from norvald_lab.application.arof.raw_observation import (
    NullRawObservationSink,
    RawObservationRecord,
)
from norvald_lab.infrastructure.arof.dataset_store import (
    arof_data_root,
    experiment_dir,
    safe_component,
    session_dir,
)

_TRUE = {"1", "true", "yes", "on"}


def arof_capture_enabled() -> bool:
    """Captura RAW é opt-in enquanto o AROF está em fase experimental."""

    return os.environ.get("NORVALD_LAB_CAPTURE", "").strip().lower() in _TRUE


class JsonlRawObservationStore:
    """Append-only L0 fora do banco operacional do Studio.

    Cada sessão recebe um arquivo próprio para reduzir contenção e manter o
    corpus navegável. O lock protege escritas concorrentes das tasks da leva.
    Não há fsync por registro: fechar o arquivo entrega o buffer ao SO sem
    transformar telemetria científica em gargalo do turno.
    """

    def __init__(self, root: str | os.PathLike[str] | None = None) -> None:
        # root agora representa a raiz AROF inteira. Isso permite manter
        # manifesto, RAW e fechamento do experimento sob o mesmo namespace.
        self.root = Path(root) if root is not None else arof_data_root()
        self._mirror_to_drive = root is None
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return True

    def path_for(self, observation: RawObservationRecord) -> Path:
        if observation.experiment_id:
            run_component = safe_component(
                observation.run_id or observation.session_id,
                "run",
            )
            return (
                experiment_dir(observation.experiment_id, root=self.root)
                / "raw"
                / run_component
                / "observations.jsonl"
            )
        return session_dir(observation.session_id, root=self.root) / "raw" / "observations.jsonl"

    def record(self, observation: RawObservationRecord) -> None:
        path = self.path_for(observation)
        payload = json.dumps(
            observation.to_dict(),
            ensure_ascii=False,
            separators=(",", ":"),
        )
        with self._lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(payload)
                handle.write("\n")


_store: JsonlRawObservationStore | None = None
_store_lock = threading.Lock()
_null = NullRawObservationSink()


def build_arof_observation_sink():
    """Retorna Null por padrão e store persistente somente com opt-in.

    O gate por ambiente é avaliado em cada chamada para que testes e processos
    de desenvolvimento possam ligar/desligar a captura sem alterar código.
    """

    if not arof_capture_enabled():
        return _null

    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = JsonlRawObservationStore()
    return _store

