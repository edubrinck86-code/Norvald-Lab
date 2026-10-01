from typing import Any, Iterable, List, Mapping, Optional

from norvald_lab.domain.deliberation.contribution_validation import RejectedContributionPart

from norvald_lab.domain.deliberation.context_item import ContextItem
from norvald_lab.domain.deliberation.working_context import WorkingContext


class WorkingContextUpdater:
    """Aplica Contributions validadas ao Working Context de forma determinística."""

    def update(
        self,
        current_context: WorkingContext,
        items: Iterable[ContextItem],
        relations: Iterable[Mapping[str, Any]] = (),
        rejected: Optional[List[Any]] = None,
    ) -> WorkingContext:
        """Aplica a contribuição, tolerando a parte inválida.

        Antes, uma relação com par não permitido levantava `ValueError` e
        derrubava a contribuição inteira — nem os itens válidos entravam.
        Isso contradizia a validação da Contribution, que descarta a
        parte inválida em `rejected` e nunca lança: duas filosofias no
        mesmo caminho, e a mais severa era acidente de implementação.

        Agora a relação inválida é descartada e registrada em `rejected`,
        do mesmo jeito. O especialista recebe o motivo na rodada
        seguinte e corrige; o que ele acertou não é perdido junto.

        A atomicidade que importa continua: itens só entram depois de
        todas as relações terem sido examinadas, então não fica metade
        do grafo dentro e metade fora.
        """
        incoming = list(items)
        incoming_relations = [dict(relation) for relation in relations]
        canonical_items: List[ContextItem] = []
        id_map = {}

        # Resolve duplicates first, without mutating the WC with new items yet.
        for item in incoming:
            duplicate = self._find_duplicate(current_context, item)
            if duplicate is not None:
                id_map[item.id] = duplicate.id
                canonical_items.append(duplicate)
            else:
                id_map[item.id] = item.id
                canonical_items.append(item)

        # Examina todas as relações antes de gravar qualquer coisa, e
        # separa as que não podem entrar em vez de abortar.
        aceitas: List[Mapping[str, Any]] = []
        for relation in incoming_relations:
            source_id = id_map.get(str(relation.get("source_id") or ""), str(relation.get("source_id") or ""))
            target_id = id_map.get(str(relation.get("target_id") or ""), str(relation.get("target_id") or ""))
            try:
                self._validate_relation(
                    current_context, canonical_items, source_id,
                    str(relation.get("relation_type") or ""), target_id,
                )
            except ValueError as motivo:
                if rejected is not None:
                    rejected.append(
                        RejectedContributionPart(
                            "relation",
                            f"{relation.get('source_id')} -{relation.get('relation_type')}-> {relation.get('target_id')}",
                            str(motivo),
                        )
                    )
                continue
            aceitas.append(relation)
        incoming_relations = aceitas

        # Grava os itens. `duplicates` reaproveita a resolução da
        # primeira passada: recalcular percorria os itens ativos de novo,
        # e a resposta já estava em `id_map`.
        for item in incoming:
            destino = id_map.get(item.id)
            if destino is not None and destino != item.id:
                existente = current_context.get(destino)
                if existente is not None:
                    self._merge_provenance(existente, item)
                    continue
            current_context.add(item)

        for relation in incoming_relations:
            source_id = id_map.get(str(relation.get("source_id") or ""), str(relation.get("source_id") or ""))
            target_id = id_map.get(str(relation.get("target_id") or ""), str(relation.get("target_id") or ""))
            round_number = relation.get("round_number")
            current_context.relate(
                source_id,
                str(relation.get("relation_type") or ""),
                target_id,
                author_id=str(relation.get("author_id") or "") or None,
                round_number=int(round_number) if round_number is not None else None,
            )

        return current_context

    def has_update(self, items: Iterable[ContextItem]) -> bool:
        return any(True for _ in items)

    @staticmethod
    def _find_duplicate(
        context: WorkingContext,
        item: ContextItem,
    ) -> Optional[ContextItem]:
        normalized = item.content.strip().casefold()
        for existing in context.active_items():
            if (
                existing.type == item.type
                and existing.content.strip().casefold() == normalized
                and existing.source_id == item.source_id
                and WorkingContextUpdater._structurally_compatible(existing, item)
            ):
                return existing
        return None

    @staticmethod
    def _structurally_compatible(existing: ContextItem, incoming: ContextItem) -> bool:
        """Só funde declarações cujo enriquecimento não cria contradição.

        A deduplicação é literal, mas dimension_id e confidence fazem
        parte da estrutura que o Documental Engine mede. Se a unidade
        antiga não tinha o campo e a nova o declara, é enriquecimento da
        mesma unidade. Se ambas declaram valores diferentes, preservar as
        duas é mais seguro do que apagar silenciosamente uma revisão.
        """
        for field_name in ("dimension_id", "confidence"):
            old = getattr(existing, field_name)
            new = getattr(incoming, field_name)
            if old and new and old != new:
                return False
        return True

    @staticmethod
    def _merge_provenance(existing: ContextItem, incoming: ContextItem) -> None:
        incoming_provenance = incoming.metadata.get("provenance", [])
        if not isinstance(incoming_provenance, list):
            incoming_provenance = [incoming_provenance]

        if incoming_provenance:
            provenance = existing.metadata.setdefault("provenance", [])
            if not isinstance(provenance, list):
                provenance = [provenance]
                existing.metadata["provenance"] = provenance
            for value in incoming_provenance:
                if value and value not in provenance:
                    provenance.append(value)

        # Uma redeclaração literal pode ser justamente a correção de uma
        # lacuna estrutural. Antes, a deduplicação mantinha o texto e
        # descartava dimension_id/confidence, então o Documental Engine
        # continuava vendo a mesma lacuna apesar da rodada corretiva.
        if incoming.dimension_id and not existing.dimension_id:
            existing.dimension_id = incoming.dimension_id
        if incoming.confidence and not existing.confidence:
            existing.confidence = incoming.confidence

        if incoming.author_id and not existing.author_id:
            existing.author_id = incoming.author_id
        if incoming.source_type and not existing.source_type:
            existing.source_type = incoming.source_type
        if incoming.source_location and not existing.source_location:
            existing.source_location = incoming.source_location
        if incoming.origin and not existing.origin:
            existing.origin = incoming.origin

    @staticmethod
    def _validate_relation(
        context: WorkingContext,
        incoming_items: List[ContextItem],
        source_id: str,
        relation_type: str,
        target_id: str,
    ) -> None:
        if not source_id or not relation_type or not target_id:
            raise ValueError("Relação inválida: source_id, relation_type e target_id são obrigatórios.")
        if source_id == target_id:
            raise ValueError("Uma relação não pode apontar para o próprio item.")

        source = context.get(source_id) or next((item for item in incoming_items if item.id == source_id), None)
        target = context.get(target_id) or next((item for item in incoming_items if item.id == target_id), None)
        if source is None or target is None:
            raise ValueError("Relação referencia item inexistente no Working Context.")
        if not context.graph.relation_is_allowed(source.type, relation_type, target.type):
            raise ValueError(
                f"Relação incompatível: {source.type} -{relation_type}-> {target.type}"
            )

