from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict

from norvald_lab.infrastructure.arof.dataset_store import arof_data_root, safe_component

_TRUE = {"1", "true", "yes", "on"}


def outcome_capture_enabled() -> bool:
    """Captura do desfecho é opt-in, como a do RAW.

    Sob a mesma chave do AROF: os dois compõem o mesmo corpus e separar
    os interruptores produziria corpus meio gravado, pior que nenhum.
    """
    return os.environ.get("NORVALD_LAB_CAPTURE", "").strip().lower() in _TRUE


class JsonlOutcomeObservationStore:
    """Append-only, fora do banco operacional — como o L0 do AROF.

    Um arquivo por workspace: o desfecho é lido por acervo, não por
    sessão, porque é entre deliberações que a convergência aparece.
    """

    def __init__(self, root: str | os.PathLike[str] | None = None) -> None:
        self.root = Path(root) if root is not None else arof_data_root()
        self._lock = threading.Lock()

    def path_for(self, observation: Dict[str, Any]) -> Path:
        workspace = safe_component(str(observation.get("workspace_id") or ""), "sem_workspace")
        return self.root / "outcomes" / f"{workspace}.jsonl"

    def record(self, observation: Dict[str, Any]) -> None:
        destino = self.path_for(observation)
        with self._lock:
            destino.parent.mkdir(parents=True, exist_ok=True)
            with destino.open("a", encoding="utf-8") as arquivo:
                arquivo.write(json.dumps(observation, ensure_ascii=False) + "\n")


class NullOutcomeSink:
    def record(self, observation: Dict[str, Any]) -> None:
        return None


_store: JsonlOutcomeObservationStore | None = None
_store_lock = threading.Lock()
_null = NullOutcomeSink()


def build_outcome_observation_sink():
    if not outcome_capture_enabled():
        return _null

    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = JsonlOutcomeObservationStore()
    return _store

