from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from norvald_lab.infrastructure.arof.dataset_store import (
    arof_data_root,
    experiment_dir,
    load_experiment_raw_view,
)

AROF_L1_REFERENCE_SCHEMA_VERSION = "arof.l1.reference.v0"
AROF_REFERENCE_NORMALIZER_VERSION = "reference-manual-v0"
AROF_REFERENCE_SEGMENTATION_METHOD = "paragraph-block-v0"

REASONING_FUNCTIONS = (
    "FRAME",
    "DECOMPOSE",
    "GENERATE",
    "EVALUATE",
    "CHALLENGE",
    "REVISE",
    "INTEGRATE",
    "CONCLUDE",
    "UNCERTAINTY",
)

REASONING_SCOPES = (
    "problem_reasoning",
    "response_construction",
    "tool_reasoning",
    "unknown",
)

_BLOCK_RE = re.compile(
    r"(?ms)^[ \t]*(?P<body>\S(?:.*?\S)?)[ \t]*(?=\r?\n[ \t]*\r?\n|\Z)"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _reference_path(
    experiment_id: str,
    *,
    root: str | Path | None = None,
) -> Path:
    return (
        experiment_dir(experiment_id, root=root)
        / "normalized"
        / "reference-v0.json"
    )


def segment_reasoning_blocks(reasoning: str) -> list[dict[str, Any]]:
    """Segmenta somente por estrutura textual observável.

    Não classifica macrofunção nem scope. A segmentação é deliberadamente
    reproduzível e substituível; L0 permanece a autoridade.
    """

    events: list[dict[str, Any]] = []
    for index, match in enumerate(_BLOCK_RE.finditer(reasoning), start=1):
        raw_span = match.group("body")
        start = match.start("body")
        end = match.end("body")
        events.append(
            {
                "event_id": f"e{index:04d}",
                "span_index": index,
                "start_char": start,
                "end_char": end,
                "raw_span": raw_span,
                "macro_function": None,
                "scope": "unknown",
                "ambiguous": True,
                "annotation_note": None,
                "alternative_function": None,
                "annotation_origin": None,
                "reference_tier": "unreviewed",
                "assistant_assignment": None,
                # Reservado para a próxima etapa de provenance/suporte.
                # O vocabulário ainda não está congelado e este campo não
                # participa da macrofunção nem de futuras transições.
                "support_status": None,
                "dimensions": {},
                "orientation": None,
                "relations": [],
            }
        )
    return events


def _with_observability_semantics(document: dict[str, Any]) -> dict[str, Any]:
    """Completa metadados L1 aditivos sem reinterpretar o trace.

    Compatibilidade: documentos reference-v0 já anotados continuam válidos.
    Os campos abaixo descrevem a superfície observada; não inferem como o
    provider implementa internamente a exposição de reasoning.
    """

    for trace in document.get("traces") or ():
        reasoning_observed = bool(trace.get("reasoning_observed"))
        declared_mode = str(
            trace.get("reasoning_exposure_mode")
            or trace.get("reasoning_exposure_mode_declared")
            or "unknown"
        )
        trace["reasoning_exposure_mode"] = declared_mode
        trace.setdefault("reasoning_exposure_mode_declared", declared_mode)
        trace.setdefault(
            "reasoning_observation_status",
            "observed" if reasoning_observed else "not_exposed",
        )
        trace.setdefault(
            "reasoning_exposure_character_observed",
            "unknown" if reasoning_observed else "not_observed",
        )
        trace.setdefault(
            "process_trajectory_status",
            (
                "available_for_annotation"
                if reasoning_observed
                else "unavailable_reasoning_not_exposed"
            ),
        )
        for event in trace.get("events") or ():
            event.setdefault("annotation_note", None)
            event.setdefault("alternative_function", None)
            if "annotation_origin" not in event:
                legacy_material_annotation = bool(
                    event.get("macro_function") is not None
                    or str(event.get("scope") or "unknown") != "unknown"
                    or event.get("ambiguous") is False
                    or event.get("annotation_note")
                )
                event["annotation_origin"] = (
                    "human" if legacy_material_annotation else None
                )
            event.setdefault(
                "reference_tier",
                "human_reviewed"
                if event.get("annotation_origin") == "human"
                else (
                    "assisted_reference"
                    if event.get("annotation_origin") == "assistant"
                    else "unreviewed"
                ),
            )
            event.setdefault("assistant_assignment", None)
            event.setdefault("support_status", None)
    document.setdefault("assistant_annotation", None)
    return document


def prepare_reference_normalization(
    experiment_id: str,
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Cria o scaffold L1 uma única vez sem inferir classes.

    Se já existir, devolve a anotação atual e nunca sobrescreve trabalho
    humano anterior.
    """

    path = _reference_path(experiment_id, root=root)
    if path.exists():
        return load_reference_normalization(experiment_id, root=root)

    raw = load_experiment_raw_view(experiment_id, root=root)
    traces: list[dict[str, Any]] = []
    for record in raw["records"]:
        payload = record["payload"]
        result = payload.get("result") or {}
        reasoning = result.get("reasoning")
        reasoning = reasoning if isinstance(reasoning, str) else ""
        reasoning_observed = bool(reasoning.strip())
        declared_exposure_mode = str(
            payload.get("reasoning_exposure_mode") or "unknown"
        )
        traces.append(
            {
                "observation_id": str(payload.get("observation_id") or ""),
                "logical_execution_id": str(
                    payload.get("logical_execution_id") or ""
                ),
                "attempt_index": int(payload.get("attempt_index") or 1),
                "participant_id": str(payload.get("participant_id") or ""),
                "participant_name": str(payload.get("participant_name") or ""),
                "provider": str(
                    result.get("provider")
                    or payload.get("requested_provider_kind")
                    or ""
                ),
                "model": str(
                    result.get("model")
                    or payload.get("requested_model")
                    or ""
                ),
                # Mantém o nome histórico e adiciona semântica explícita:
                # modo declarado/conhecido != característica inferida da
                # superfície observada.
                "reasoning_exposure_mode": declared_exposure_mode,
                "reasoning_exposure_mode_declared": declared_exposure_mode,
                "reasoning_observation_status": (
                    "observed" if reasoning_observed else "not_exposed"
                ),
                "reasoning_exposure_character_observed": (
                    "unknown" if reasoning_observed else "not_observed"
                ),
                "process_trajectory_status": (
                    "available_for_annotation"
                    if reasoning_observed
                    else "unavailable_reasoning_not_exposed"
                ),
                "reasoning_observed": reasoning_observed,
                "raw_reasoning_chars": len(reasoning),
                "events": segment_reasoning_blocks(reasoning),
            }
        )

    created_at = _now()
    document = {
        "schema_version": AROF_L1_REFERENCE_SCHEMA_VERSION,
        "normalizer_version": AROF_REFERENCE_NORMALIZER_VERSION,
        "segmentation_method": AROF_REFERENCE_SEGMENTATION_METHOD,
        "experiment_id": experiment_id,
        "created_at": created_at,
        "updated_at": created_at,
        "classification_policy": "manual_reference",
        "traces": traces,
    }
    save_reference_normalization(
        experiment_id,
        document,
        root=root,
    )
    return document


def save_reference_normalization(
    experiment_id: str,
    document: dict[str, Any],
    *,
    root: str | Path | None = None,
) -> None:
    """Persiste L1 de forma atômica sem tocar no L0."""

    path = _reference_path(experiment_id, root=root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)


def load_reference_normalization(
    experiment_id: str,
    *,
    root: str | Path | None = None,
) -> dict[str, Any]:
    path = _reference_path(experiment_id, root=root)
    if not path.exists():
        raise FileNotFoundError(
            f"L1 referência ausente para o experimento {experiment_id}"
        )
    return _with_observability_semantics(
        json.loads(path.read_text(encoding="utf-8"))
    )


def update_reference_event(
    experiment_id: str,
    *,
    observation_id: str,
    event_id: str,
    macro_function: str | None,
    scope: str,
    ambiguous: bool,
    annotation_note: str | None = None,
    root: str | Path | None = None,
) -> dict[str, Any]:
    if macro_function is not None and macro_function not in REASONING_FUNCTIONS:
        raise ValueError(f"macro_function inválida: {macro_function}")
    if scope not in REASONING_SCOPES:
        raise ValueError(f"scope inválido: {scope}")

    path = _reference_path(experiment_id, root=root)
    document = load_reference_normalization(experiment_id, root=root)

    target: dict[str, Any] | None = None
    for trace in document.get("traces") or ():
        if trace.get("observation_id") != observation_id:
            continue
        for event in trace.get("events") or ():
            if event.get("event_id") == event_id:
                target = event
                break
        if target is not None:
            break

    if target is None:
        raise KeyError(f"{observation_id}:{event_id}")

    target["macro_function"] = macro_function
    target["scope"] = scope
    target["ambiguous"] = bool(ambiguous)
    target["alternative_function"] = None
    target["annotation_origin"] = "human"
    target["reference_tier"] = "human_reviewed"
    target["reviewed_at"] = _now()
    target["annotation_note"] = (
        annotation_note.strip()
        if isinstance(annotation_note, str) and annotation_note.strip()
        else None
    )
    document["updated_at"] = _now()
    save_reference_normalization(
        experiment_id,
        document,
        root=root,
    )
    return document

