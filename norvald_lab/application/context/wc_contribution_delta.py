from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from norvald_lab.domain.deliberation.contribution_validation import ValidatedContribution
from norvald_lab.domain.deliberation.working_context import WorkingContext
from norvald_lab.infrastructure.change_detection import ChangeSet, diff_structures

from .wc_snapshot import WCSnapshot


@dataclass(frozen=True)
class WCContributionDelta:
    """Read-only evidence of the structural effect of one contribution."""

    change_set: ChangeSet
    contribution_id: str | None
    participant_id: str | None
    round_number: int | None
    # Tamanho e composição antes/depois. Contagens, não conteúdo: ver
    # WCSnapshot para o porquê de não guardar o WC inteiro.
    snapshot_before: WCSnapshot | None = None
    snapshot_after: WCSnapshot | None = None


def capture_contribution_delta(
    before: WorkingContext,
    after: WorkingContext,
    validated: ValidatedContribution,
) -> WCContributionDelta:
    """Compare WC states and preserve attribution already carried by the contribution.

    No attribution is inferred from the diff. Contribution identity comes only
    from validated item metadata, and participant/round only from the validated
    items' domain fields.
    """
    contribution_id: str | None = None
    participant_id: str | None = None
    round_number: int | None = None

    for item in validated.items:
        candidate = item.metadata.get("contribution_id") if item.metadata else None
        if candidate is not None:
            contribution_id = str(candidate)
        if participant_id is None and item.author_id:
            participant_id = str(item.author_id)
        if round_number is None:
            round_number = item.round_number
        if contribution_id and participant_id is not None and round_number is not None:
            break

    return WCContributionDelta(
        change_set=diff_structures(before.to_dict(), after.to_dict()),
        contribution_id=contribution_id,
        participant_id=participant_id,
        round_number=round_number,
        snapshot_before=WCSnapshot.capture(before),
        snapshot_after=WCSnapshot.capture(after),
    )

