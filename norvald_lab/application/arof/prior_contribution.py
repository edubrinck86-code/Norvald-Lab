from dataclasses import dataclass


@dataclass(frozen=True)
class PriorContribution:
    """Uma resposta de condição cega, para semear a condição exposta.

    Deliberadamente pobre: autor e texto bruto. O parsing acontece do
    outro lado, com o mesmo parser do turno normal — se a condição
    exposta recebesse conhecimento já estruturado, ela estaria vendo
    algo diferente do que um participante de rodada 2 vê.

    Aceita tanto o resultado direto de uma leva quanto uma releitura do
    RAW: o que importa é (quem falou, o que respondeu).
    """

    author_id: str
    response: str

