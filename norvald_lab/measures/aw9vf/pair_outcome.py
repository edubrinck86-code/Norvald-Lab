"""Um par participante-pergunta numa condição, contra a própria B1 (344-62)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PairOutcome:
    unit: tuple[str, str, str]
    participant_id: str
    agent: str
    condition: str
    b1_option: str
    option: str
    changed: bool  # changed_position: opção da condição ≠ opção da própria B1
    new_strict: bool  # new_grounds, leitura estrita
    new_permissive: bool  # new_grounds, leitura permissiva

    def event(self, reading: str) -> bool:
        """changed_position AND NOT new_grounds, na leitura dada (344-66, item 1)."""
        return self.changed and not (self.new_strict if reading == "estrita" else self.new_permissive)
