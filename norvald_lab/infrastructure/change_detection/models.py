from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Change:
    """One sanitized structural change."""

    kind: str
    path: str
    old_value: Any = None
    new_value: Any = None


@dataclass(frozen=True)
class ChangeSet:
    """Small, vendor-neutral representation of structural differences."""

    added: tuple[Change, ...] = field(default_factory=tuple)
    removed: tuple[Change, ...] = field(default_factory=tuple)
    changed: tuple[Change, ...] = field(default_factory=tuple)

    @property
    def is_empty(self) -> bool:
        return not (self.added or self.removed or self.changed)

