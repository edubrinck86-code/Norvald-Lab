from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from norvald_lab.application.arof.raw_observation import json_safe


@dataclass(frozen=True)
class LibraryCorpusFingerprint:
    """Identidade observável do corpus global que alimenta o KG.

    O fingerprint não restringe nem replica a Library. Ele apenas permite
    provar se duas repetições viram exatamente o mesmo estado persistido.
    """

    scope: str
    algorithm: str
    fingerprint: str
    item_count: int
    active_count: int
    captured_at: str

    def to_dict(self) -> dict[str, Any]:
        return json_safe(asdict(self))


def fingerprint_library(items: Iterable[Any]) -> LibraryCorpusFingerprint:
    normalized: list[dict[str, Any]] = []
    active = 0

    for item in items:
        to_dict = getattr(item, "to_dict", None)
        payload = to_dict() if callable(to_dict) else item
        safe = json_safe(payload)
        if not isinstance(safe, dict):
            safe = {"value": safe}
        normalized.append(safe)
        if str(safe.get("status") or "active") == "active":
            active += 1

    normalized.sort(
        key=lambda item: (
            str(item.get("id") or ""),
            str(item.get("identifier") or ""),
            str(item.get("reference") or ""),
        )
    )
    canonical = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return LibraryCorpusFingerprint(
        scope="studio_library_global",
        algorithm="sha256-canonical-json-v1",
        fingerprint=digest,
        item_count=len(normalized),
        active_count=active,
        captured_at=datetime.now(timezone.utc).isoformat(),
    )


def same_library_corpus(
    expected: LibraryCorpusFingerprint | dict[str, Any],
    current: LibraryCorpusFingerprint | dict[str, Any],
) -> bool:
    left = (
        expected.to_dict()
        if isinstance(expected, LibraryCorpusFingerprint)
        else expected
    )
    right = (
        current.to_dict()
        if isinstance(current, LibraryCorpusFingerprint)
        else current
    )
    return (
        str(left.get("algorithm") or "")
        == str(right.get("algorithm") or "")
        and str(left.get("fingerprint") or "")
        == str(right.get("fingerprint") or "")
        and int(left.get("item_count") or 0)
        == int(right.get("item_count") or 0)
    )


class FrozenEvidenceLibrary:
    """Snapshot read-only da Library usado por uma condição experimental."""

    def __init__(self, items: Iterable[Any]) -> None:
        from norvald_lab.domain.evidence import Evidence

        frozen = []
        for item in items:
            payload = item.to_dict() if hasattr(item, "to_dict") else item
            frozen.append(Evidence.from_dict(json_safe(payload)))
        self._items = tuple(frozen)
        self._by_id = {item.id: item for item in self._items}

    def list(self, kind: str | None = None) -> list[Any]:
        items = list(self._items)
        if kind is not None:
            items = [item for item in items if item.kind == kind]
        return items

    def get(self, evidence_id: str) -> Any:
        item = self._by_id.get(str(evidence_id))
        if item is None:
            raise ValueError(
                f"Evidência '{evidence_id}' não encontrada no snapshot da Library."
            )
        return item


def fingerprint_payload(payload: Any) -> str:
    """Hash determinístico de um contrato experimental JSON-safe."""
    canonical = json.dumps(
        json_safe(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

