"""Confiança declarada → posto (344-75: ordinal, analisada por posto).

baixa = 1, média = 2, alta = 3. O extrator já normaliza high/medium/low para
alta/média/baixa. Qualquer outro texto, ou vazio, é ausência: nunca vira zero
(344-81) e a análise é pareada só onde há confiança declarada nos dois lados.
"""

from __future__ import annotations

import unicodedata

RANKS = {"baixa": 1, "media": 2, "alta": 3}


class ConfidenceScale:
    def rank(self, confidence: str) -> int | None:
        text = unicodedata.normalize("NFKD", str(confidence or "")).encode("ascii", "ignore").decode().strip().lower()
        return RANKS.get(text)
