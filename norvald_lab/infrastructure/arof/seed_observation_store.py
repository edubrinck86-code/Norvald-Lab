"""Persistência do que a semeadura da condição exposta fez com a leva cega.

Irmão do `JsonlRawObservationStore`, e separado dele de propósito: o RAW
é por execução, a semeadura é por leva. Misturar os dois num arquivo só
obrigaria quem analisa a filtrar por esquema antes de contar qualquer
coisa, e uma linha por leva se perderia entre centenas de linhas por
execução.

    <root>/experiments/<experiment_id>/seed/observations.jsonl

Fora do banco operacional do Studio, como todo o acervo do experimento.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path

from norvald_lab.application.arof.seed_observation import SeedObservation
from norvald_lab.infrastructure.arof.dataset_store import arof_data_root, experiment_dir


class JsonlSeedObservationStore:
    """Append-only, uma linha por leva semeada."""

    def __init__(self, root: str | os.PathLike[str] | None = None) -> None:
        self.root = Path(root) if root is not None else arof_data_root()
        self._mirror_to_drive = root is None
        self._lock = threading.Lock()

    def path_for(self, experiment_id: str) -> Path:
        return experiment_dir(experiment_id, root=self.root) / "seed" / "observations.jsonl"

    def record(self, experiment_id: str, observation: SeedObservation) -> Path:
        path = self.path_for(experiment_id)
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
        return path


def load_seed_observations(
    experiment_id: str,
    *,
    root: str | os.PathLike[str] | None = None,
) -> list[dict]:
    """As levas semeadas de um experimento, na ordem em que foram gravadas."""

    path = JsonlSeedObservationStore(root).path_for(experiment_id)
    if not path.exists():
        return []
    linhas = []
    with path.open(encoding="utf-8") as handle:
        for linha in handle:
            linha = linha.strip()
            if linha:
                linhas.append(json.loads(linha))
    return linhas

