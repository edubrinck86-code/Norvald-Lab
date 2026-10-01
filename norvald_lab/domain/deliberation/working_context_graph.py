"""Grafo semântico do Working Context.

As relações deste módulo são SEMÂNTICAS: ligam afirmações de uma
deliberação, com autor e proveniência, e descrevem o movimento do
argumento — um contra-argumento contesta, uma evidência sustenta.

Não confundir com as 16 relações do Framework (UDF §13), que são
ESTRUTURAIS: ligam documentos e descrevem a organização do corpo
documental, sem autor e sem rodada. Os dois vocabulários coexistem de
propósito e não devem ser unificados — ver ADR-UX-008. `supersedes`
aparece nos dois por coincidência de nome, não como ponte entre eles.
"""

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from norvald_lab.domain.deliberation.context_item import ContextItem
from norvald_lab.domain.deliberation.context_relation import ContextRelation


_ALLOWED_RELATIONS = {
    ("reference", "documents", "evidence"),
    ("evidence", "supports", "claim"),
    ("claim", "supports", "argument"),
    ("claim", "supports", "decision"),
    ("argument", "supports", "decision"),
    ("counterargument", "challenges", "argument"),
    ("counterargument", "challenges", "claim"),
    ("counterargument", "challenges", "option"),
    ("counterargument", "challenges", "decision"),
    ("response", "addresses", "counterargument"),
    # Incompatibilidade entre asserções, distinta de `challenges`.
    # `challenges` é o movimento de um contra-argumento contra o alvo;
    # `contradicts` é a constatação de que duas asserções do mesmo peso
    # não podem valer juntas. Por isso os pares são simétricos em tipo,
    # e não partem de `counterargument`.
    #
    # A aresta permanece dirigida: quem declara aponta para o que está
    # sendo contrariado, e é essa direção que identifica o autor a ser
    # convocado na leva seguinte.
    ("claim", "contradicts", "claim"),
    ("argument", "contradicts", "argument"),
    ("evidence", "contradicts", "claim"),
    ("inference", "derived_from", "evidence"),
    ("inference", "derived_from", "claim"),
    ("inference", "derived_from", "argument"),
    ("option", "evaluated_by", "criterion"),
    ("comparison", "compares", "option"),
    ("decision", "selects", "option"),
    ("decision", "produces", "consequence"),
    ("condition", "constrains", "decision"),
    ("consequence", "derived_from", "decision"),
    ("claim", "supersedes", "claim"),
    ("decision", "supersedes", "decision"),
    # Uma lacuna pode ser reformulada sem apagar a anterior. O novo gap
    # referencia o UUID antigo; o lifecycle derivado decide qual fica
    # aberto, preservando ambos para auditoria.
    ("gap", "supersedes", "gap"),
    # As três abaixo estavam em RELATION_TYPES sem nenhum par permitido:
    # declaráveis pelo especialista e descartadas em silêncio no commit.
    # Mesmo caso já corrigido para `contradicts`.
    #
    # `answers` fecha uma pergunta em aberto. O que responde é uma
    # asserção — não uma decisão: decidir apesar da pergunta é outro
    # movimento, e colapsar os dois apagaria a distinção entre responder
    # e seguir sem resposta.
    ("claim", "answers", "open_question"),
    ("argument", "answers", "open_question"),
    ("inference", "answers", "open_question"),
    ("evidence", "answers", "open_question"),
    # `resolves` retira o que impedia avançar. Uma incerteza cai por
    # evidência ou inferência; uma lacuna, por conteúdo que a preencha.
    # `gap` e `uncertainty` continuam distintos: são alvos separados, e
    # nenhuma relação converte um no outro.
    ("evidence", "resolves", "uncertainty"),
    ("inference", "resolves", "uncertainty"),
    ("evidence", "resolves", "gap"),
    ("claim", "resolves", "gap"),
    ("decision", "resolves", "open_question"),
    # `motivates` é a direção oposta de `derived_from`: registra o que
    # deu origem a um movimento, e não o que dele decorre. O que motiva
    # é sempre uma falta — pergunta, lacuna, incerteza — ou uma
    # restrição; por isso nenhuma asserção aparece como origem.
    ("open_question", "motivates", "option"),
    ("open_question", "motivates", "decision"),
    ("gap", "motivates", "option"),
    ("gap", "motivates", "criterion"),
    ("uncertainty", "motivates", "criterion"),
    ("condition", "motivates", "criterion"),
}


@dataclass
class WorkingContextGraph:
    """Grafo incremental do conhecimento deliberativo.

    O grafo conhece unidades do WC e relações semânticas permitidas. Ele não
    interpreta texto, executa LLM ou acessa fontes externas.
    """

    items: Dict[str, ContextItem] = field(default_factory=dict)
    relations: List[ContextRelation] = field(default_factory=list)

    def add_item(self, item: ContextItem) -> ContextItem:
        if item.id in self.items and self.items[item.id] is not item:
            raise ValueError(f"ID de ContextItem já existente no Working Context: {item.id}")
        self.items[item.id] = item
        return item

    def add_items(self, items: Iterable[ContextItem]) -> None:
        for item in items:
            self.add_item(item)

    def get_item(self, item_id: str) -> ContextItem | None:
        return self.items.get(item_id)

    def by_type(self, item_type: str, active_only: bool = False) -> List[ContextItem]:
        items = self.items.values()
        if active_only:
            return [item for item in items if item.type == item_type and item.status == "active"]
        return [item for item in items if item.type == item_type]

    @staticmethod
    def relation_is_allowed(source_type: str, relation_type: str, target_type: str) -> bool:
        return (source_type, relation_type, target_type) in _ALLOWED_RELATIONS

    def validate_relation(self, source_id: str, relation_type: str, target_id: str) -> None:
        source = self._require_item(source_id)
        target = self._require_item(target_id)
        if not self.relation_is_allowed(source.type, relation_type, target.type):
            raise ValueError(
                f"Relação inválida para o grafo: {source.type} -{relation_type}-> {target.type}"
            )

    def relate(
        self,
        source_id: str,
        relation_type: str,
        target_id: str,
        *,
        author_id: str | None = None,
        round_number: int | None = None,
    ) -> ContextRelation:
        self.validate_relation(source_id, relation_type, target_id)
        relation = ContextRelation(
            source_id, relation_type, target_id,
            author_id=author_id, round_number=round_number,
        )
        # A deduplicação é pela tripla semântica: dois autores declarando
        # a mesma relação não criam duas arestas. A proveniência gravada
        # é a do primeiro — a segunda declaração é redundante, não um
        # fato novo do grafo.
        if not any(
            existing.source_id == source_id
            and existing.relation_type == relation_type
            and existing.target_id == target_id
            for existing in self.relations
        ):
            self.relations.append(relation)
        return relation

    def related_to(self, item_id: str, relation_type: str | None = None) -> List[ContextItem]:
        target_ids = {
            relation.target_id
            for relation in self.relations
            if relation.source_id == item_id
            and (relation_type is None or relation.relation_type == relation_type)
        }
        return [self.items[item_id] for item_id in target_ids if item_id in self.items]

    def supporting_evidence(self, item_id: str) -> List[ContextItem]:
        return [
            item for relation in self.relations
            if relation.target_id == item_id and relation.relation_type == "supports"
            for item in [self.items.get(relation.source_id)] if item is not None
        ]

    def contradictions(self, item_id: str) -> List[ContextItem]:
        return [
            item for relation in self.relations
            if relation.target_id == item_id and relation.relation_type in {"contradicts", "challenges"}
            for item in [self.items.get(relation.source_id)] if item is not None
        ]

    def disputes(self, item_id: str) -> List[ContextItem]:
        """Quem contesta este item e ainda vale.

        Diferente de `contradictions`, considera só contestadores ativos.
        Um contra-argumento superado ou rejeitado deixou de sustentar a
        disputa: mantê-lo aqui faria um ponto já resolvido continuar
        aparecendo como aberto.

        A disputa é **derivada**, não gravada. `contested` existe em
        `ITEM_STATUSES` e nunca foi usado — se passasse a ser escrito, a
        contestação viveria em dois lugares (o status e as arestas) e
        eles divergiriam na primeira vez que um contestador fosse
        superado sem alguém lembrar de reavaliar o alvo. Lendo do grafo,
        a disputa some sozinha quando deixa de existir.
        """
        return [item for item in self.contradictions(item_id) if item.status == "active"]

    def is_contested(self, item_id: str) -> bool:
        return bool(self.disputes(item_id))

    def unanswered_disputes(self, item_id: str) -> List[ContextItem]:
        """Contestações ativas que ninguém endereçou ainda.

        `addresses` não encerra a disputa: decidir que uma resposta
        bastou é julgamento semântico, e o Studio não julga — quem
        responde não pode declarar sozinho que venceu o debate. Mas
        tratar "contestado e respondido" igual a "contestado e ignorado"
        apaga a diferença que move a deliberação: uma pede réplica, a
        outra pede resposta.

        A distinção é estrutural e derivada, como `disputes`: existe uma
        aresta `addresses` apontando para o contestador, ou não existe.
        Nada aqui muda status nem grava veredito.
        """
        answered = {
            relation.target_id
            for relation in self.relations
            if relation.relation_type == "addresses"
        }
        return [item for item in self.disputes(item_id) if item.id not in answered]

    def contested_items(self) -> List[ContextItem]:
        """Itens ativos sob contestação ativa, na ordem do grafo."""
        return [item for item in self.active_items() if self.is_contested(item.id)]

    def relations_by_item(self) -> Dict[str, List[ContextRelation]]:
        """Índice de adjacência das relações, por item participante.

        Calculado a cada chamada, sem cache. O grafo é mutável e um
        índice guardado divergiria na primeira relação acrescentada sem
        alguém lembrar de invalidá-lo — o mesmo motivo pelo qual a
        disputa é derivada em vez de gravada.

        Existe porque projetar o CDD varria todas as relações uma vez
        para cada item: com mil itens e cinco mil relações são cinco
        milhões de comparações, e a projeção roda a cada leitura do
        documento. Uma passada monta o índice e as buscas passam a ser
        diretas.
        """
        indice: Dict[str, List[ContextRelation]] = {}
        for relation in self.relations:
            indice.setdefault(relation.source_id, []).append(relation)
            if relation.target_id != relation.source_id:
                indice.setdefault(relation.target_id, []).append(relation)
        return indice

    def active_items(self) -> List[ContextItem]:
        return [item for item in self.items.values() if item.status == "active"]

    def _gap_lifecycle_index(self) -> Dict[str, Dict[str, object]]:
        """Calcula todos os lifecycles em uma passada pelas relações."""
        gaps = {
            item.id: item
            for item in self.items.values()
            if item.type == "gap"
        }
        incoming: Dict[str, Dict[str, List[ContextRelation]]] = {
            gap_id: {"resolves": [], "supersedes": []}
            for gap_id in gaps
        }

        for relation in self.relations:
            if relation.target_id not in gaps:
                continue
            if relation.relation_type not in {"resolves", "supersedes"}:
                continue
            source = self.items.get(relation.source_id)
            if source is None or source.status != "active":
                continue
            if relation.relation_type == "supersedes" and source.type != "gap":
                continue
            incoming[relation.target_id][relation.relation_type].append(relation)

        result: Dict[str, Dict[str, object]] = {}
        for gap_id, gap in gaps.items():
            active_resolvers = incoming[gap_id]["resolves"]
            active_superseders = incoming[gap_id]["supersedes"]
            if gap.status != "active":
                state = gap.status
                basis = "item_status"
            elif active_superseders:
                state = "superseded"
                basis = "relation"
            elif active_resolvers:
                state = "resolved"
                basis = "relation"
            else:
                state = "open"
                basis = "derived"

            result[gap_id] = {
                "gap_id": gap.id,
                "content": gap.content,
                "item_status": gap.status,
                "state": state,
                "basis": basis,
                "round_number": gap.round_number,
                "author_id": gap.author_id,
                "dimension_id": gap.dimension_id,
                "resolved_by": [relation.source_id for relation in active_resolvers],
                "superseded_by": [relation.source_id for relation in active_superseders],
                "resolution_relations": [relation.to_dict() for relation in active_resolvers],
                "supersession_relations": [relation.to_dict() for relation in active_superseders],
            }
        return result

    def gap_lifecycle(self, gap_id: str) -> Dict[str, object]:
        """Estado auditável de uma lacuna, derivado do grafo."""
        gap = self._require_item(gap_id)
        if gap.type != "gap":
            raise ValueError(f"ContextItem {gap_id} não é uma lacuna.")
        return self._gap_lifecycle_index()[gap_id]

    def gap_registry(self) -> List[Dict[str, object]]:
        """Registro separado de todas as lacunas, inclusive as fechadas."""
        index = self._gap_lifecycle_index()
        gaps = sorted(
            self.by_type("gap"),
            key=lambda item: (
                item.round_number if item.round_number is not None else 0,
                item.id,
            ),
        )
        return [index[item.id] for item in gaps]

    def open_gaps(self) -> List[ContextItem]:
        """Lacunas fisicamente ativas cujo lifecycle derivado segue aberto."""
        index = self._gap_lifecycle_index()
        return [
            item
            for item in self.by_type("gap", active_only=True)
            if index[item.id]["state"] == "open"
        ]

    def deliberative_items(self) -> List[ContextItem]:
        """Visão corrente para LLM/CDD, sem apagar o histórico auditável.

        Itens ativos comuns continuam iguais. Gaps resolvidos ou substituídos
        saem da superfície deliberativa, mas permanecem no grafo e no
        gap_registry com suas relações.
        """
        index = self._gap_lifecycle_index()
        return [
            item
            for item in self.active_items()
            if item.type != "gap" or index[item.id]["state"] == "open"
        ]

    def to_dict(self) -> Dict[str, object]:
        return {
            "items": [item.to_dict() for item in self.items.values()],
            "relations": [relation.to_dict() for relation in self.relations],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "WorkingContextGraph":
        graph = cls()
        raw_items = data.get("items", [])
        raw_relations = data.get("relations", [])
        graph.add_items(ContextItem.from_dict(item) for item in raw_items)
        for relation in raw_relations:
            relation_obj = ContextRelation.from_dict(relation)
            graph.validate_relation(
                relation_obj.source_id, relation_obj.relation_type, relation_obj.target_id
            )
            graph.relations.append(relation_obj)
        return graph

    def _require_item(self, item_id: str) -> ContextItem:
        item = self.get_item(item_id)
        if item is None:
            raise ValueError(f"Item de contexto não encontrado: {item_id}")
        return item

