from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid

from norvald_lab.domain.deliberation.context_item import ContextItem
from norvald_lab.domain.deliberation.context_relation import RELATION_TYPES
from norvald_lab.domain.deliberation.contribution import Contribution, DECLARABLE_KNOWLEDGE_TYPES
from norvald_lab.domain.execution.execution_usage import ExecutionUsage
from norvald_lab.domain.deliberation.dimension_registry import DimensionRegistry
from norvald_lab.domain.deliberation.working_context import WorkingContext
from norvald_lab.domain.deliberation.working_context_graph import WorkingContextGraph

@dataclass(frozen=True)
class RejectedContributionPart:
    kind: str
    identifier: str
    reason: str

@dataclass(frozen=True)
class ValidatedContribution:
    items: List[ContextItem] = field(default_factory=list)
    relations: List[Dict[str, Any]] = field(default_factory=list)
    rejected: List[RejectedContributionPart] = field(default_factory=list)
    raw_text: str = ""
    reasoning: str = ""
    usage: Optional[ExecutionUsage] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    # Proveniência operacional do turno. Não faz parte do conteúdo cognitivo
    # da Contribution; acompanha a contribuição para auditoria e citações.
    provenance: List[Dict[str, Any]] = field(default_factory=list)

def validate_and_convert(contribution: Contribution, context: WorkingContext, *, dimension_registry: DimensionRegistry | None = None) -> ValidatedContribution:
    rejected: List[RejectedContributionPart] = []
    items: List[ContextItem] = []
    local_to_id: Dict[str, str] = {}
    for knowledge in contribution.knowledge:
        if not knowledge.local_id:
            rejected.append(RejectedContributionPart("knowledge", "", "local_id obrigatório")); continue
        if knowledge.local_id in local_to_id:
            rejected.append(RejectedContributionPart("knowledge", knowledge.local_id, "local_id duplicado")); continue
        if knowledge.type not in DECLARABLE_KNOWLEDGE_TYPES:
            rejected.append(RejectedContributionPart("knowledge", knowledge.local_id, "tipo semântico não declarável")); continue
        if not knowledge.content.strip():
            rejected.append(RejectedContributionPart("knowledge", knowledge.local_id, "conteúdo vazio")); continue
        if knowledge.dimension_id and dimension_registry is not None:
            try:
                dimension_registry.validate(knowledge.dimension_id)
            except ValueError as exc:
                rejected.append(RejectedContributionPart("knowledge", knowledge.local_id, str(exc))); continue
        item_id = str(uuid.uuid4()); local_to_id[knowledge.local_id] = item_id
        metadata = dict(knowledge.metadata)
        metadata.setdefault("contribution_id", contribution.id)
        metadata.setdefault("provenance", [contribution.id])
        # `source_id` identifica a ORIGEM do item, e é o que impede o
        # `_find_duplicate` de fundir afirmações idênticas de autores
        # diferentes. Sem ele a guarda compara None com None, sempre casa,
        # e dois participantes que declararem o mesmo texto viram uma
        # unidade só — apagando o sinal de maioria justo onde a
        # concordância é maior. O caminho da deliberação já preenchia;
        # este não, e era por aqui que a condição exposta do experimento
        # perdia repetição.
        items.append(ContextItem(id=item_id, type=knowledge.type, content=knowledge.content, dimension_id=knowledge.dimension_id, layer=knowledge.layer, origin="specialist", source_type="specialist", source_id=contribution.author_id, author_id=contribution.author_id, round_number=contribution.round_number, confidence=knowledge.confidence, metadata=metadata))
    item_types = {item.id: item.type for item in context.items}; item_types.update({item.id: item.type for item in items})
    validated_relations: List[Dict[str, Any]] = []
    for relation in contribution.relations:
        if relation.relation_type not in RELATION_TYPES:
            rejected.append(RejectedContributionPart("relation", relation.id, "relação semântica desconhecida")); continue
        source_id = local_to_id.get(relation.source, relation.source); target_id = local_to_id.get(relation.target, relation.target)
        if source_id == target_id:
            rejected.append(RejectedContributionPart("relation", relation.id, "relação reflexiva não permitida")); continue
        if source_id not in item_types or target_id not in item_types:
            rejected.append(RejectedContributionPart("relation", relation.id, "source ou target inexistente")); continue
        if not WorkingContextGraph.relation_is_allowed(item_types[source_id], relation.relation_type, item_types[target_id]):
            rejected.append(RejectedContributionPart("relation", relation.id, f"relação incompatível: {item_types[source_id]} -{relation.relation_type}-> {item_types[target_id]}")); continue
        validated_relations.append({"source_id": source_id, "relation_type": relation.relation_type, "target_id": target_id, "author_id": contribution.author_id, "round_number": contribution.round_number})
    return ValidatedContribution(items=items, relations=validated_relations, rejected=rejected)

