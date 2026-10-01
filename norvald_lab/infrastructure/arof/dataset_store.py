from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Sequence

from norvald_lab.application.arof.dataset import (
    DatasetFileIntegrity,
    ExperimentCompletion,
    ExperimentManifest,
    ExperimentResultView,
    ReplayFilter,
    ReplayIssue,
    ReplayRecord,
    ReplayResult,
)
from norvald_lab.application.arof.raw_observation import AROF_RAW_SCHEMA_VERSION

if TYPE_CHECKING:
    from norvald_lab.application.arof.capacity import CapacityReport

_SAFE_COMPONENT = re.compile(r"[^A-Za-z0-9._-]+")


def arof_data_root() -> Path:
    configured = os.environ.get("NORVALD_LAB_DATA_DIR")
    root = Path(configured).expanduser() if configured else Path.home() / ".norvald" / "lab"
    return root


def safe_component(value: str, fallback: str) -> str:
    cleaned = _SAFE_COMPONENT.sub("_", (value or "").strip()).strip("._")
    return cleaned[:160] or fallback


def experiment_dir(experiment_id: str, *, root: str | os.PathLike[str] | None = None) -> Path:
    base = Path(root) if root is not None else arof_data_root()
    return base / "experiments" / safe_component(experiment_id, "experiment")


def session_dir(session_id: str, *, root: str | os.PathLike[str] | None = None) -> Path:
    base = Path(root) if root is not None else arof_data_root()
    return base / "sessions" / safe_component(session_id, "unscoped")


def write_manifest(
    manifest: ExperimentManifest,
    *,
    root: str | os.PathLike[str] | None = None,
) -> Path:
    """Grava a especificação uma única vez.

    open("x") é intencional: uma condição já declarada não pode ser
    sobrescrita depois de ver resultados.
    """

    directory = experiment_dir(manifest.experiment_id, root=root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "manifest.json"
    payload = json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)
        handle.write("\n")
    return path


def load_manifest(
    experiment_id: str,
    *,
    root: str | os.PathLike[str] | None = None,
) -> dict:
    path = experiment_dir(experiment_id, root=root) / "manifest.json"
    return json.loads(path.read_text(encoding="utf-8"))


def replay_jsonl(
    paths: Sequence[str | os.PathLike[str]],
    *,
    filters: ReplayFilter | None = None,
    accepted_schema_versions: Iterable[str] = (AROF_RAW_SCHEMA_VERSION,),
) -> ReplayResult:
    """Lê RAW offline. Não importa orchestrator e não pode chamar provider."""

    accepted = set(accepted_schema_versions)
    records: list[ReplayRecord] = []
    issues: list[ReplayIssue] = []

    for raw_path in paths:
        path = Path(raw_path)
        try:
            handle = path.open("r", encoding="utf-8")
        except OSError as exc:
            issues.append(
                ReplayIssue(str(path), 0, "file_unreadable", str(exc))
            )
            continue

        with handle:
            for line_number, line in enumerate(handle, start=1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError as exc:
                    issues.append(
                        ReplayIssue(
                            str(path),
                            line_number,
                            "invalid_json",
                            f"{exc.msg} at column {exc.colno}",
                        )
                    )
                    continue

                if not isinstance(payload, dict):
                    issues.append(
                        ReplayIssue(
                            str(path),
                            line_number,
                            "invalid_record",
                            "registro RAW deve ser objeto JSON",
                        )
                    )
                    continue

                version = str(payload.get("schema_version") or "")
                if version not in accepted:
                    issues.append(
                        ReplayIssue(
                            str(path),
                            line_number,
                            "unsupported_schema",
                            version or "(ausente)",
                        )
                    )
                    continue

                if not payload.get("observation_id") or not payload.get("logical_execution_id"):
                    issues.append(
                        ReplayIssue(
                            str(path),
                            line_number,
                            "missing_identity",
                            "observation_id/logical_execution_id ausente",
                        )
                    )
                    continue

                if filters is not None and not filters.matches(payload):
                    continue

                records.append(ReplayRecord(str(path), line_number, payload))

    return ReplayResult(tuple(records), tuple(issues))


def file_integrity(
    path: str | os.PathLike[str],
    *,
    accepted_schema_versions: Iterable[str] = (AROF_RAW_SCHEMA_VERSION,),
) -> DatasetFileIntegrity:
    file_path = Path(path)
    digest = hashlib.sha256()
    lines = 0
    with file_path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)

    with file_path.open("r", encoding="utf-8") as handle:
        lines = sum(1 for line in handle if line.strip())

    replay = replay_jsonl(
        [file_path],
        accepted_schema_versions=accepted_schema_versions,
    )
    return DatasetFileIntegrity(
        path=str(file_path),
        sha256=digest.hexdigest(),
        bytes=file_path.stat().st_size,
        lines=lines,
        valid_records=len(replay.records),
        invalid_records=len(replay.issues),
    )


def write_capacity_report(
    experiment_id: str,
    report: "CapacityReport",
    *,
    root: str | os.PathLike[str] | None = None,
) -> Path:
    """Persiste a medição operacional sem misturá-la ao manifesto científico."""

    directory = experiment_dir(experiment_id, root=root)
    if not (directory / "manifest.json").exists():
        raise FileNotFoundError(
            f"manifesto ausente para o experimento {experiment_id}"
        )
    path = directory / "capacity.json"
    payload = json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)
        handle.write("\n")
    return path


def close_experiment(
    experiment_id: str,
    raw_files: Sequence[str | os.PathLike[str]],
    *,
    status: str,
    root: str | os.PathLike[str] | None = None,
    notes: Sequence[str] = (),
) -> Path:
    """Fecha a coleta sem modificar manifest.json.

    O fechamento também é write-once. Se a coleta precisar ser repetida,
    ela recebe outro experiment_id.
    """

    directory = experiment_dir(experiment_id, root=root)
    manifest_path = directory / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"manifesto ausente para o experimento {experiment_id}"
        )

    if status == "complete" and not raw_files:
        raise ValueError("experimento complete exige ao menos um arquivo RAW")

    base_root = Path(root) if root is not None else arof_data_root()
    files_list: list[DatasetFileIntegrity] = []
    seen_logical: set[str] = set()
    attempts = 0
    integrity_errors: list[str] = []

    for raw_path in raw_files:
        path = Path(raw_path)
        integrity = file_integrity(path)
        replay = replay_jsonl([path])

        if integrity.invalid_records:
            integrity_errors.append(
                f"{path}: {integrity.invalid_records} registro(s) inválido(s)"
            )

        mismatched = [
            record
            for record in replay.records
            if record.payload.get("experiment_id") != experiment_id
        ]
        if mismatched:
            integrity_errors.append(
                f"{path}: {len(mismatched)} registro(s) de outro experiment_id"
            )

        for record in replay.records:
            if record.payload.get("experiment_id") != experiment_id:
                continue
            attempts += 1
            seen_logical.add(str(record.payload["logical_execution_id"]))

        try:
            portable_path = str(path.resolve().relative_to(base_root.resolve()))
        except ValueError:
            portable_path = str(path)

        files_list.append(
            DatasetFileIntegrity(
                path=portable_path,
                sha256=integrity.sha256,
                bytes=integrity.bytes,
                lines=integrity.lines,
                valid_records=integrity.valid_records,
                invalid_records=integrity.invalid_records,
            )
        )

    if status == "complete" and integrity_errors:
        raise ValueError(
            "experimento não pode ser fechado como complete: "
            + "; ".join(integrity_errors)
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    planned = int(
        (manifest.get("budget") or {}).get(
            "planned_logical_executions",
            (manifest.get("budget") or {}).get(
                "max_logical_executions", 0
            ),
        )
        or 0
    )
    if (
        status == "complete"
        and planned
        and len(seen_logical) != planned
    ):
        raise ValueError(
            "experimento não pode ser fechado como complete: "
            f"esperava {planned} execuções lógicas e encontrou "
            f"{len(seen_logical)}"
        )

    files = tuple(files_list)
    completion = ExperimentCompletion(
        experiment_id=experiment_id,
        status=status,
        files=files,
        logical_executions=len(seen_logical),
        attempts=attempts,
        notes=tuple(notes),
    )
    path = directory / "completion.json"
    payload = json.dumps(completion.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)
        handle.write("\n")
    return path



def write_experiment_result(
    result: ExperimentResultView,
    *,
    root: str | os.PathLike[str] | None = None,
) -> Path:
    """Materializa a view de UI uma única vez, depois do fechamento."""

    directory = experiment_dir(result.experiment_id, root=root)
    if not (directory / "completion.json").exists():
        raise FileNotFoundError(
            f"completion ausente para o experimento {result.experiment_id}"
        )
    path = directory / "result.json"
    payload = json.dumps(
        result.to_dict(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)
        handle.write("\n")
    return path


def load_experiment_result(
    experiment_id: str,
    *,
    root: str | os.PathLike[str] | None = None,
) -> dict:
    path = experiment_dir(experiment_id, root=root) / "result.json"
    return json.loads(path.read_text(encoding="utf-8"))


def latest_experiment_result_for_source(
    source_session_id: str,
    *,
    root: str | os.PathLike[str] | None = None,
) -> dict | None:
    base = Path(root) if root is not None else arof_data_root()
    experiments = base / "experiments"
    if not experiments.exists():
        return None

    candidates: list[dict] = []
    for path in experiments.glob("*/result.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("source_session_id") != source_session_id:
            continue
        candidates.append(payload)

    if not candidates:
        return None
    candidates.sort(
        key=lambda item: str(item.get("completed_at") or ""),
        reverse=True,
    )
    return candidates[0]



def _experiment_raw_files(
    experiment_id: str,
    *,
    root: str | os.PathLike[str] | None = None,
) -> list[Path]:
    """Resolve RAW pela certificação do fechamento quando ela existe.

    completion.json é a autoridade para um experimento fechado: foi criado
    somente depois de validar os próprios arquivos RAW. O glob permanece
    apenas como compatibilidade para coletas ainda não fechadas/legadas.
    """

    base_root = Path(root) if root is not None else arof_data_root()
    directory = experiment_dir(experiment_id, root=root)
    completion_path = directory / "completion.json"

    if completion_path.exists():
        completion = json.loads(
            completion_path.read_text(encoding="utf-8")
        )
        resolved: list[Path] = []
        for item in completion.get("files") or ():
            stored_path = str((item or {}).get("path") or "").strip()
            if not stored_path:
                continue
            candidate = Path(stored_path)
            if not candidate.is_absolute():
                candidate = base_root / candidate
            resolved.append(candidate)
        if resolved:
            return resolved

    return sorted((directory / "raw").glob("*/observations.jsonl"))


def load_experiment_raw_view(
    experiment_id: str,
    *,
    root: str | os.PathLike[str] | None = None,
) -> dict:
    """Projeta o RAW para inspeção humana sem reescrever seu conteúdo.

    Cada item devolve o payload JSONL integral, acompanhado apenas da
    localização física (arquivo/linha). Replans permanecem registros
    separados; nenhuma tentativa é fundida ou descartada.
    """

    raw_files = _experiment_raw_files(experiment_id, root=root)
    if not raw_files:
        raise FileNotFoundError(
            f"RAW ausente para o experimento {experiment_id}"
        )

    replay = replay_jsonl(
        raw_files,
        filters=ReplayFilter(experiment_id=experiment_id),
    )
    return {
        "experiment_id": experiment_id,
        "records": [
            {
                "path": record.path,
                "line_number": record.line_number,
                "payload": record.payload,
            }
            for record in replay.records
        ],
        "issues": [
            {
                "path": issue.path,
                "line_number": issue.line_number,
                "code": issue.code,
                "message": issue.message,
            }
            for issue in replay.issues
        ],
    }

