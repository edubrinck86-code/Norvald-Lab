"""Indicadores de erro por participante, nas perguntas com gabarito (F, E e o registro aw9vf)."""

from __future__ import annotations

from norvald_lab.measures.observation_table import ObservationTable


def condition_errors(table: ObservationTable, unit: tuple[str, str, str], condition: str) -> dict[str, float]:
    """agente → 1.0 se errou na condição, 0.0 se acertou; só quem tem posição válida."""
    rows = table.by_question_unit.get(unit, {}).get(condition, {})
    return {row.agent: float(not row.correct) for row in rows.values() if row.correct is not None}


def b1_errors(table: ObservationTable, unit: tuple[str, str, str]) -> dict[str, float]:
    """agente → 1.0 se errou em B1, 0.0 se acertou; só quem tem posição válida."""
    return condition_errors(table, unit, "B1")
