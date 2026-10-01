"""Leitura do corpo de uma resposta de streaming que falhou.

Acessar `.text` num stream ainda não lido levanta "Attempted to access
streaming response content, without having called read()" — e esse erro
**substitui** o do provider. O que chega ao usuário é um detalhe de
transporte no lugar do motivo real da falha, que era justamente o que a
mensagem existia para mostrar.

Vive em módulo próprio porque os três providers repetiam o mesmo acesso
e o mesmo defeito: corrigir em um deixava os outros dois quebrados do
mesmo jeito.
"""

from __future__ import annotations


async def read_stream_body(response) -> str:
    """O corpo da resposta, ou uma descrição de por que não deu.

    Nunca levanta. O corpo é contexto de uma mensagem de erro, e falhar
    ao obtê-lo não pode piorar um erro que já aconteceu — foi
    exatamente esse encadeamento que escondeu a falha do Gemini.
    """
    # `aread` primeiro: é o que funciona num stream de verdade, em que
    # o corpo ainda não chegou.
    try:
        body = await response.aread()
        if body:
            return body.decode(
                getattr(response, "encoding", None) or "utf-8", errors="replace"
            )
    except Exception:  # noqa: BLE001
        pass

    # `text` depois, e não só quando `aread` levanta: ele pode devolver
    # vazio num transporte que já carregou o corpo por outro caminho, e
    # aí o motivo do provider está aqui. Cair para "(corpo
    # indisponível)" nesse caso perderia a única informação útil.
    try:
        texto = response.text
        if texto:
            return str(texto)
    except Exception:  # noqa: BLE001
        return "(corpo indisponível)"
    return "(corpo vazio)"

