from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from norvald_lab.vendor.documental_engine.framework.dimension import Dimension


@dataclass
class DimensionRegistry:
    """Registry hierárquico e extensível das dimensões do Framework."""

    dimensions: Dict[str, Dimension] = field(default_factory=dict)

    def register(self, dimension: Dimension) -> Dimension:
        if dimension.id in self.dimensions and self.dimensions[dimension.id] != dimension:
            raise ValueError(f"Dimensão já registrada: {dimension.id}")
        if dimension.parent_id is not None and dimension.parent_id not in self.dimensions:
            raise ValueError(f"Dimensão pai não encontrada: {dimension.parent_id}")
        self.dimensions[dimension.id] = dimension
        return dimension

    def register_many(self, dimensions: Iterable[Dimension]) -> None:
        for dimension in dimensions:
            self.register(dimension)

    def get(self, dimension_id: str) -> Dimension | None:
        return self.dimensions.get(dimension_id)

    def children_of(self, parent_id: str) -> List[Dimension]:
        return [d for d in self.dimensions.values() if d.parent_id == parent_id]

    def descendants_of(self, dimension_id: str, *, include_self: bool = False) -> List[Dimension]:
        """Todos os descendentes de uma dimensão, em qualquer profundidade.

        `children_of` só pega um nível — insuficiente para checar
        obrigatoriedade numa árvore funda de verdade (o caso real, tipo
        Segurança→Autenticação→Rotação→Frequência, que o Universal
        Document Framework descreve mas o Registry hoje nunca populou).

        Sem risco de ciclo: `register()` já exige que o pai exista antes
        do filho ser aceito, e `Dimension` é `frozen=True` — não dá para
        criar um ciclo depois do fato, então esta função não precisa de
        guarda de profundidade defensiva contra loop infinito.
        """
        resultado: List[Dimension] = []
        if include_self:
            raiz = self.get(dimension_id)
            if raiz is not None:
                resultado.append(raiz)
        fila = list(self.children_of(dimension_id))
        while fila:
            atual = fila.pop()
            resultado.append(atual)
            fila.extend(self.children_of(atual.id))
        return resultado

    def validate(self, dimension_id: str) -> Dimension:
        dimension = self.get(dimension_id)
        if dimension is None:
            raise ValueError(f"Dimensão não registrada: {dimension_id}")
        if dimension.state == "DEPRECATED":
            raise ValueError(f"Dimensão obsoleta: {dimension_id}")
        return dimension

