"""Dispersão do painel numa pergunta: 1 − fração do painel na opção modal.

344-71 não fixa o índice. Escolhida a fração da moda porque é o que "o painel
convergiu" quer dizer: 0 com unanimidade; com 5 participantes, 0,2 se há
4 na mesma opção e 0,4 se a maior é 3. É diferente da dispersão do critério B
(pares discordantes): aqui só a opção mais votada pesa.
"""

from __future__ import annotations

from collections import Counter
from typing import Sequence


class ModalDispersion:
    def of(self, options: Sequence[str]) -> float | None:
        if len(options) < 2:
            return None
        return 1.0 - Counter(options).most_common(1)[0][1] / len(options)
