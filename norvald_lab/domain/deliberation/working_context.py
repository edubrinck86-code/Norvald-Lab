from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from norvald_lab.domain.deliberation.context_item import CONTEXT_ITEM_TYPES, ContextItem
from norvald_lab.domain.deliberation.context_relation import ContextRelation
from norvald_lab.domain.deliberation.working_context_graph import WorkingContextGraph


@dataclass
class WorkingContext:
    """Fonte de verdade do conhecimento deliberativo.

    O WC impõe as invariantes estruturais do Framework sem transformar
    metadados auxiliares em conhecimento semântico.

    Regra arquitetural: execução é efêmera; conhecimento declarado é
    persistente. Ferramentas, resultados brutos, raciocínio intermediário,
    histórico operacional e documentos completos pertencem à auditoria da
    execução e nunca atravessam a fronteira para o grafo sem uma declaração
    explícita do especialista validada pelo Studio.
    """

    question: str = ""
    graph: WorkingContextGraph = field(default_factory=WorkingContextGraph)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def items(self) -> List[ContextItem]:
        return list(self.graph.items.values())

    @property
    def relations(self) -> List[ContextRelation]:
        return list(self.graph.relations)

    @property
    def protocol_instructions(self) -> Dict[str, Any]:
        """Contrato de recuperação que acompanha o WC em todas as rodadas.

        As instruções são estado operacional do protocolo, não conhecimento
        semântico e não viram ContextItem.
        """
        return {
            "always_start_with_working_context": True,
            "round_policy": {
                "every_round": [
                    "Consultar primeiro o Working Context e tratá-lo como a fonte de verdade do conhecimento já deliberado.",
                    "Usar o WC para verificar o que já foi estabelecido antes de decidir qualquer recuperação.",
                    "Não transformar uma consulta, resultado de ferramenta ou documento em conhecimento do WC automaticamente.",
                ],
                "round_1": [
                    "Receber o WC inicial e toda a Evidence anexada na aba Contexto como base da rodada.",
                    "Estruturar a deliberação a partir do objetivo, das instruções e das evidências recebidas.",
                    "Pesquisar somente se isso for estritamente necessário para produzir a contribuição e o conhecimento declarado desta rodada.",
                ],
                "round_2_plus": [
                    "Receber o WC acumulado com o conhecimento declarado e validado das rodadas anteriores.",
                    "Debater esse conhecimento antes de buscar material novo.",
                    "Quando existir uma lacuna que exija conhecimento adicional, consultar primeiro o Knowledge Graph por busca semântica.",
                    "Usar o Knowledge Graph para complementar, relacionar ou aprofundar o argumento; não despejar o grafo inteiro no contexto.",
                    "Consultar a Library somente quando houver necessidade de evidência documental, fonte primária ou conteúdo que o Knowledge Graph não forneça adequadamente.",
                    "A busca na Library deve servir à composição da contribuição e das citações, não à incorporação do documento inteiro no WC.",
                ],
            },
            "wc_boundary": {
                "persistent": True,
                "entry_rule": "Somente conhecimento semanticamente declarável pelo especialista, validado pelo Studio, pode criar ou alterar ContextItems e relações.",
                "allowed": [
                    "conhecimento declarado no bloco CONTRIBUTION",
                    "relações declaradas no bloco CONTRIBUTION",
                    "Evidence como referência/proveniência/citação associada ao conhecimento",
                ],
                "never_promote_automatically": [
                    "tool calls",
                    "tool outputs",
                    "web search results",
                    "Knowledge Graph search results",
                    "Library search results",
                    "documentos completos",
                    "raciocínio interno ou intermediário da LLM",
                    "histórico operacional da execução",
                    "telemetria",
                ],
                "audit_location": "Timeline e estruturas de auditoria da execução preservam os eventos e resultados operacionais sem contaminarem o Working Context.",
            },
            "evidence_policy": {
                "all_attached_context_evidence_is_input": True,
                "library_is_evidence": True,
                "repository_is_evidence": True,
                "specialist_declared_evidence_is_evidence": True,
                "do_not_embed_full_documents": True,
                "store_only_relevant_evidence": True,
                "preserve_citation_marker": True,
                "preserve_source_link_or_id": True,
                "instruction": "Evidence pode vir da aba Contexto, Library, Repository ou de fonte declarada pelo especialista. No WC, preserve a referência/citação e a proveniência necessária para sustentar o conhecimento; não incorporar o documento completo.",
            },
            "tool_policy": {
                "max_calls_per_round": 6,
                "count_includes_working_context_preflight": True,
                "tool_results_are_ephemeral": True,
                "instruction": "Ferramentas são meios de investigação. O resultado fica disponível para o debate e para a auditoria da rodada; somente o conhecimento explicitamente declarado e validado atravessa a fronteira para o WC.",
            },
            "termination_policy": [
                "Uma ausência de resultado não autoriza repetir indefinidamente a mesma busca.",
                "Não repetir uma consulta sem uma razão nova e explícita.",
                "Se o conhecimento e as evidências disponíveis forem suficientes para compor a contribuição, encerrar a recuperação e responder.",
                "Se a evidência continuar insuficiente depois do limite de ferramentas, compor a resposta com o que existe e declarar a insuficiência em vez de entrar em ciclo.",
            ],
            "semantic_roles": {
                "working_context": "fonte de verdade e memória do conhecimento deliberativo declarado",
                "knowledge_graph": "conhecimento relacionado usado sob demanda para complementar e aprofundar o raciocínio",
                "library": "evidência documental e fonte citável, usada sob demanda",
                "timeline": "auditoria da execução, incluindo ferramentas e resultados intermediários",
            },
        }

    def add(self, item: ContextItem) -> ContextItem:
        self._validate_item(item)
        return self.graph.add_item(item)

    def extend(self, items: Iterable[ContextItem]) -> None:
        for item in items:
            self.add(item)

    def get(self, item_id: str) -> Optional[ContextItem]:
        return self.graph.get_item(item_id)

    def relate(
        self,
        source_id: str,
        relation_type: str,
        target_id: str,
        *,
        author_id: str | None = None,
        round_number: int | None = None,
    ) -> ContextRelation:
        return self.graph.relate(
            source_id, relation_type, target_id,
            author_id=author_id, round_number=round_number,
        )

    def remove(self, item_id: str) -> bool:
        return self.set_status(item_id, "rejected")

    def set_status(self, item_id: str, status: str) -> bool:
        item = self.get(item_id)
        if item is None:
            return False
        item.status = status
        return True

    def supersede(self, item_id: str, replacement_id: str) -> bool:
        """Registra substituição preservando o lifecycle próprio de gaps."""
        item = self.get(item_id)
        replacement = self.get(replacement_id)
        if item is None or replacement is None:
            return False
        self.graph.validate_relation(replacement_id, "supersedes", item_id)

        # Gaps mantêm o ContextItem original intacto: a substituição é
        # estado derivado da aresta e pode ser revertida automaticamente
        # se o gap substituto deixar de estar ativo.
        if item.type == "gap" and replacement.type == "gap":
            self.graph.relate(replacement_id, "supersedes", item_id)
            return True

        item.status = "superseded"
        self.graph.relate(replacement_id, "supersedes", item_id)
        return True

    def by_type(self, item_type: str, active_only: bool = False) -> List[ContextItem]:
        return self.graph.by_type(item_type, active_only=active_only)

    def active_items(self) -> List[ContextItem]:
        return self.graph.active_items()

    def deliberative_items(self) -> List[ContextItem]:
        """Itens correntes apresentados à deliberação.

        Difere de active_items apenas para gaps cujo lifecycle derivado já
        está resolvido ou substituído. O histórico continua no grafo.
        """
        return self.graph.deliberative_items()

    def gap_registry(self) -> List[Dict[str, object]]:
        """Registro auditável de todas as lacunas e seu estado derivado."""
        return self.graph.gap_registry()

    def open_gaps(self) -> List[ContextItem]:
        return self.graph.open_gaps()

    def contested_items(self) -> List[ContextItem]:
        """Itens ativos que outro especialista contesta e ninguém resolveu."""
        return self.graph.contested_items()

    def disputes(self, item_id: str) -> List[ContextItem]:
        return self.graph.disputes(item_id)

    def validate_integrity(self) -> None:
        """Revalida o estado completo do WC sem alterar seu conteúdo.

        A pergunta é exigida a partir do momento em que existe
        conhecimento: todo item é declarado *em resposta a* algo, e um
        grafo sem pergunta não teria como ser interpretado depois.

        Um WC vazio é outro caso — é uma deliberação que ainda não foi
        definida. O objetivo é escrito no ambiente Configuração, e até lá
        não há nada a interpretar. Quem impede executar sem objetivo é o
        `DeliberationRoundExecutor`, antes de qualquer item existir.
        """
        if self.items and not self.question.strip():
            raise ValueError(
                "Working Context com conhecimento exige uma pergunta/objetivo."
            )
        for item in self.items:
            self._validate_item(item)
        for relation in self.relations:
            self.graph.validate_relation(
                relation.source_id, relation.relation_type, relation.target_id
            )

    @staticmethod
    def _validate_item(item: ContextItem) -> None:
        if item.type not in CONTEXT_ITEM_TYPES:
            raise ValueError(f"Primitive não reconhecido no Working Context: {item.type}")
        if not item.id.strip():
            raise ValueError("ContextItem exige id.")
        if not item.content.strip():
            raise ValueError(f"ContextItem {item.id} exige conteúdo não vazio.")

    def to_dict(self) -> Dict[str, Any]:
        graph = self.graph.to_dict()
        return {
            "question": self.question,
            "items": graph["items"],
            "relations": graph["relations"],
            "metadata": dict(self.metadata),
            "protocol_instructions": self.protocol_instructions,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkingContext":
        graph = WorkingContextGraph.from_dict(data)
        context = cls(
            question=data.get("question", ""),
            graph=graph,
            metadata=dict(data.get("metadata", {})),
        )
        context.validate_integrity()
        return context

