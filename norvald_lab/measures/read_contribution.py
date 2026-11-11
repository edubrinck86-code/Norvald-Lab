"""O que se lê da contribuição de uma execução para o registro aw9vf."""

from __future__ import annotations

from dataclasses import dataclass

from norvald_lab.measures.ground import Ground


@dataclass(frozen=True)
class ReadContribution:
    structured: bool
    grounds: tuple[Ground, ...]
    claims: tuple[tuple[str, str], ...]
