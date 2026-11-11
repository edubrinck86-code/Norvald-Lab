"""Indicadores de erro em B1 por participante, nas perguntas com gabarito (F e E)."""

from __future__ import annotations

from norvald_lab.measures.observation_table import ObservationTable


def b1_errors(table: ObservationTable, unit: tuple[str, str, str]) -> dict[str, float]:
    """agente → 1.0 se errou em B1, 0.0 se acertou; só quem tem posição válida."""
    rows = table.by_question_unit.get(unit, {}).get("B1", {})
    return {row.agent: float(not row.correct) for row in rows.values() if row.correct is not None}
