from __future__ import annotations

from typing import Any, Mapping, Sequence

from .models import Change, ChangeSet

# Coleções do Working Context cujos elementos têm identidade própria.
# Só estas entram no caminho rápido: comparar por id exige que o id
# exista e seja estável, e fora daqui isso não é garantido.
_KEYED_COLLECTIONS = ("items", "relations")


def _is_keyed_collection(value: Any) -> bool:
    """A coleção é uma lista de dicts com `id` único?

    Sem unicidade a comparação por chave perderia elementos em silêncio,
    o que é pior que ser lenta. A verificação custa O(n) e evita entregar
    um diff errado.
    """
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False
    ids = []
    for element in value:
        if not isinstance(element, Mapping) or "id" not in element:
            return False
        ids.append(element["id"])
    return len(ids) == len(set(ids))


def is_keyed_structure(payload: Any) -> bool:
    """Reconhece o formato do Working Context serializado."""
    if not isinstance(payload, Mapping):
        return False
    present = [key for key in _KEYED_COLLECTIONS if key in payload]
    if not present:
        return False
    return all(_is_keyed_collection(payload[key]) for key in present)


def diff_keyed(before: Mapping[str, Any], after: Mapping[str, Any]) -> ChangeSet:
    """Compara duas versões do Working Context por identidade.

    O DeepDiff é genérico: não sabe que `items` é um conjunto com chave,
    então compara posicionalmente e faz hashing profundo de cada
    elemento. Num WC de mil itens isso custava ~350 ms para detectar um
    único item novo — trabalho proporcional ao contexto inteiro a cada
    contribuição.

    Aqui a comparação é por `id`, em O(n): presente só depois é
    adicionado, só antes é removido, nos dois com conteúdo diferente é
    alterado. Os caminhos seguem o formato do DeepDiff
    (`root['items'][i]`) porque `contribution_impact` os interpreta.
    """
    added: list[Change] = []
    removed: list[Change] = []
    changed: list[Change] = []

    for collection in _KEYED_COLLECTIONS:
        old_elements = {e["id"]: e for e in before.get(collection, []) or []}
        new_elements = {e["id"]: e for e in after.get(collection, []) or []}

        for index, (element_id, element) in enumerate(new_elements.items()):
            previous = old_elements.get(element_id)
            if previous is None:
                added.append(Change(kind="added", path=f"root['{collection}'][{index}]",
                                    old_value=None, new_value=element_id))
            elif previous != element:
                changed.append(Change(kind="changed", path=f"root['{collection}'][{index}]",
                                      old_value=element_id, new_value=element_id))

        for index, element_id in enumerate(old_elements):
            if element_id not in new_elements:
                removed.append(Change(kind="removed", path=f"root['{collection}'][{index}]",
                                      old_value=element_id, new_value=None))

    # Campos escalares fora das coleções (question, id, versão) também
    # mudam e precisam aparecer — ignorá-los tornaria o diff incompleto.
    scalar_keys = set(before) | set(after)
    for key in sorted(scalar_keys - set(_KEYED_COLLECTIONS)):
        old_value = before.get(key)
        new_value = after.get(key)
        if old_value == new_value:
            continue
        if key not in before:
            added.append(Change(kind="added", path=f"root['{key}']", old_value=None, new_value=_scalar(new_value)))
        elif key not in after:
            removed.append(Change(kind="removed", path=f"root['{key}']", old_value=_scalar(old_value), new_value=None))
        else:
            changed.append(Change(kind="changed", path=f"root['{key}']",
                                  old_value=_scalar(old_value), new_value=_scalar(new_value)))

    return ChangeSet(added=tuple(added), removed=tuple(removed), changed=tuple(changed))


def _scalar(value: Any) -> Any:
    return value if value is None or isinstance(value, (str, int, float, bool)) else None

