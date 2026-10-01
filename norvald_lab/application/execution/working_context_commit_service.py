from __future__ import annotations

from norvald_lab.application.context.wc_contribution_delta import WCContributionDelta, capture_contribution_delta
from norvald_lab.domain.telemetry.telemetry_event import (
    PHASE_WC_DIFF,
    PHASE_WC_UPDATE,
    PhaseTimer,
)
from norvald_lab.application.deliberation.working_context_updater import WorkingContextUpdater
from norvald_lab.domain.deliberation.contribution_validation import ValidatedContribution
from norvald_lab.domain.deliberation.working_context import WorkingContext


class WorkingContextCommitService:
    """Aplica uma Contribution validada e pode expor sua mudança observável.

    A validação e a construção do conhecimento acontecem antes desta
    fronteira. O serviço continua delegando a mutação ao updater; a captura
    do delta é somente leitura e não altera o fluxo de commit.
    """

    def __init__(self, updater: WorkingContextUpdater):
        self._updater = updater

    def apply(
        self,
        working_context: WorkingContext,
        validated: ValidatedContribution,
    ) -> WorkingContext:
        result, _ = self.apply_with_delta(working_context, validated)
        return result

    def apply_with_delta(
        self,
        working_context: WorkingContext,
        validated: ValidatedContribution,
        timer: PhaseTimer | None = None,
    ) -> tuple[WorkingContext, WCContributionDelta]:
        """Aplica e mede.

        O timer é opcional para que a fronteira continue utilizável sem
        telemetria: medir não pode ser condição para commitar.
        """
        if validated.rejected and not validated.items and not validated.relations:
            empty = capture_contribution_delta(working_context, working_context, validated)
            return working_context, empty

        # Cópia real, não a mesma referência.
        #
        # `update()` muta o Working Context no lugar, então `before` e
        # `after` eram o mesmo objeto: `diff_structures` comparava um
        # dicionário consigo mesmo e os dois snapshots relatavam o
        # estado final. Medido: com 1 item antes e 2 depois, ambos
        # diziam 2 — a telemetria de impacto de contribuição media a
        # mesma coisa duas vezes.
        before = WorkingContext.from_dict(working_context.to_dict())

        # Recusado na escrita, e não só na validação da Contribution.
        #
        # A relação com par não permitido só é detectável aqui, contra o
        # grafo real. Sem juntar as duas listas, o especialista corrigia
        # o que a validação apontou e continuava redeclarando a relação
        # que o grafo recusa — sem nunca saber por quê.
        rejeitado_na_escrita: list = []
        if timer is not None:
            with timer.measure(PHASE_WC_UPDATE, items=len(validated.items)):
                result = self._updater.update(
                    working_context, validated.items, validated.relations, rejected=rejeitado_na_escrita
                )
            with timer.measure(PHASE_WC_DIFF):
                delta = capture_contribution_delta(before, result, validated)
            validated.rejected.extend(rejeitado_na_escrita)
            return result, delta

        result = self._updater.update(
            working_context,
            validated.items,
            validated.relations,
            rejected=rejeitado_na_escrita,
        )
        delta = capture_contribution_delta(before, result, validated)
        # O que o grafo recusou volta junto do que a validação recusou:
        # para o especialista é a mesma pergunta — o que não entrou e por
        # quê.
        validated.rejected.extend(rejeitado_na_escrita)
        return result, delta

