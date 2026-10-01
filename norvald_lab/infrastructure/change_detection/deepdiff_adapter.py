from __future__ import annotations

from typing import Any, Mapping

from .keyed_diff import diff_keyed, is_keyed_structure
from .models import Change, ChangeSet


_ADDED = ("dictionary_item_added", "iterable_item_added", "set_item_added", "attribute_added")
_REMOVED = ("dictionary_item_removed", "iterable_item_removed", "set_item_removed", "attribute_removed")
_CHANGED = ("values_changed", "type_changes")


def diff_structures(before: Any, after: Any) -> ChangeSet:
    """Mudanças estruturais entre duas versões.

    Estruturas com identidade — o Working Context — usam comparação por
    chave, que é O(n). O DeepDiff continua sendo o caminho geral para
    tudo que não tem `id` estável, porque ali não há chave pela qual
    comparar.

    O import do DeepDiff é adiado de propósito: ele arrasta pandas e
    custava 789 ms no startup do backend, mesmo quando o caminho rápido
    atende a todas as chamadas da sessão.
    """
    if is_keyed_structure(before) and is_keyed_structure(after):
        return diff_keyed(before, after)

    from deepdiff import DeepDiff

    diff = DeepDiff(before, after, ignore_order=False, verbose_level=2)
    return ChangeSet(
        added=_changes(diff, *_ADDED),
        removed=_changes(diff, *_REMOVED),
        changed=_changes(diff, *_CHANGED),
    )


def _changes(diff: Mapping[str, Any], *categories: str) -> tuple[Change, ...]:
    result: list[Change] = []
    for category in categories:
        entries = diff.get(category, {})
        if isinstance(entries, Mapping):
            iterable = entries.items()
        elif isinstance(entries, (set, frozenset, list, tuple)):
            iterable = ((path, None) for path in entries)
        else:
            continue
        for path, detail in iterable:
            old_value = None
            new_value = None
            if isinstance(detail, Mapping):
                old_value = detail.get("old_value")
                new_value = detail.get("new_value")
            result.append(Change(
                kind=_kind(category),
                path=str(path),
                old_value=_sanitize_value(old_value),
                new_value=_sanitize_value(new_value),
            ))
    return tuple(result)


def _kind(category: str) -> str:
    if category in _ADDED:
        return "added"
    if category in _REMOVED:
        return "removed"
    return "changed"


def _sanitize_value(value: Any) -> Any:
    """Return only simple serializable values; never expose DeepDiff objects."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _sanitize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return [_sanitize_value(item) for item in sorted(value, key=repr)]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return repr(value)

