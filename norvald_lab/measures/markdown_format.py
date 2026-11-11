"""Formatação de números e intervalos nos resumos .md (vírgula decimal)."""

from __future__ import annotations

from typing import Any


def number(value: Any, digits: int = 3) -> str:
    if value is None:
        return "—"
    return f"{value:.{digits}f}".replace(".", ",")


def interval(data: dict | None) -> str:
    if not data:
        return "—"
    low, high = data.get("ic", [None, None])
    return f"{number(data.get('estimativa'))} [{number(low)}; {number(high)}] (n={data.get('n') if data.get('n') is not None else '—'})"
