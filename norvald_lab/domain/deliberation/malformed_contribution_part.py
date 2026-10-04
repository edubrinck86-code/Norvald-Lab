from dataclasses import dataclass


@dataclass(frozen=True)
class MalformedContributionPart:
    """Parte do bloco CONTRIBUTION que o parser não conseguiu ler.

    Divergência intencional do Studio (docs/MIGRACAO.md, 2026-10-04).

    No parser de origem, uma única unidade sem `local_id` ou uma única
    relação sem `target` descartava o bloco inteiro: zero unidades, o
    participante não era semeado e a derivação de B3/E era recusada por
    causa de um campo. Aqui a parte defeituosa é registrada e as demais
    seguem para o validador.

    Nada é reparado: o campo ausente não é preenchido nem inferido. A
    parte é recusada, com posição e motivo, e aparece entre as recusas do
    validador.

    `kind` é "knowledge" ou "relation". `index` é a posição da parte na
    lista declarada, contada a partir de zero. `identifier` é o
    `local_id` quando existe, ou vazio.
    """

    kind: str
    index: int
    identifier: str
    reason: str
