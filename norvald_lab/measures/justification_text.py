"""O texto da justificativa de uma contribuição: o que o participante escreveu para os outros lerem.

Entra a prosa fora do bloco e o conteúdo de todas as unidades declaradas
(a decisão e as demais). Não entra o raciocínio interno do provider
(`result.reasoning`): os pares em E nunca o veem, e a pergunta do Eduardo é
sobre as razões que circulam, não sobre o pensamento oculto.
"""

from __future__ import annotations

from norvald_lab.domain.deliberation.contribution import Contribution, strip_contribution_block


def justification_from_content(content: str, *, author_id: str = "") -> str:
    contribution = Contribution.parse(content or "", author_id=author_id, round_number=1)
    parts = [strip_contribution_block(content or "")]
    parts += [str(item.content) for item in contribution.knowledge if str(item.content).strip()]
    return "\n".join(part for part in parts if part.strip())
