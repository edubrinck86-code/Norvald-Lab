"""Um fundamento declarado por uma contribuição (relação de fundamento → alvo)."""

from __future__ import annotations

from dataclasses import dataclass

# base:  alvo é item do contexto sem autor (opção, evidência da pergunta); a chave é o id.
# local: alvo é outra unidade da própria contribuição (que não a decisão); a chave é o conteúdo normalizado.
# own:   alvo é contribuição anterior do próprio participante; nunca é novo.
# peer:  alvo é contribuição de outro participante; só é novo na leitura permissiva.
SCOPES = ("base", "local", "own", "peer")


@dataclass(frozen=True)
class Ground:
    scope: str
    key: str
