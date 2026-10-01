"""Remove sintaxe de chamada de ferramenta que vazou para o texto.

Um modelo pode emitir a chamada nativa e, na mesma mensagem, escrever a
mesma chamada em prosa — visto em deliberação real:

    <invoke name="search_context"><parameter name="limit">5</parameter>
    <parameter name="query">Constitution template</parameter>

As ferramentas rodaram de verdade; este texto é ruído do protocolo
vazando para o campo de conteúdo. Renderizado, vira `5 Constitution
template deliberação efeito` — que se lê como se fosse a resposta do
especialista.

Isto **não julga o conteúdo**. Remove uma forma sintática conhecida, do
mesmo modo que `strip_contribution_block` remove o bloco declarado: o
Studio não decide se a análise é boa, decide que marcação de protocolo
não é prosa.

Importa mais depois da recuperação de texto da fase de ferramentas: sem
limpar, o que se recupera quando a síntese vem vazia é justamente este
lixo.
"""

from __future__ import annotations

import re

# Blocos completos, em qualquer das formas que os providers usam.
_BLOCOS = [
    re.compile(r"<invoke\b.*?</invoke>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<invoke\b.*?</invoke>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<function_calls>.*?</function_calls>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<function_calls>.*?</function_calls>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<tool_call>.*?</tool_call>", re.DOTALL | re.IGNORECASE),
]

# Tags soltas: o modelo costuma truncar no meio, e o que sobra não fecha.
# Sem isto restariam fragmentos como `<parameter name="query"` no texto.
_SOLTAS = [
    re.compile(r"</?antml:(?:invoke|parameter|function_calls)\b[^>]*>?", re.IGNORECASE),
    re.compile(r"</?(?:invoke|parameter|function_calls|tool_call)\b[^>]*>?", re.IGNORECASE),
]

# Um `<parameter name="query">valor` sem fechamento deixa o valor solto
# no texto depois que a tag sai. Casar a tag junto do que vem até o fim
# da linha resolve: o que sobrava era a query aparecendo como se fosse a
# resposta — `5 Constitution template deliberação efeito`.
_PARAMETRO_TRUNCADO = re.compile(
    r"</?(?:antml:)?parameter\b[^>]*>?[^\n]*", re.IGNORECASE
)

_ESPACOS = re.compile(r"\n{3,}")


def strip_tool_syntax(text: str) -> str:
    """O texto sem marcação de chamada de ferramenta."""
    limpo = text or ""
    for padrao in _BLOCOS:
        limpo = padrao.sub("", limpo)
    limpo = _PARAMETRO_TRUNCADO.sub("", limpo)
    for padrao in _SOLTAS:
        limpo = padrao.sub("", limpo)
    return _ESPACOS.sub("\n\n", limpo).strip()


def is_only_tool_syntax(text: str) -> bool:
    """O texto era só marcação, sem prosa por baixo.

    Distingue "o modelo escreveu a chamada junto da análise" de "o
    modelo só escreveu a chamada": no segundo caso não há o que
    recuperar, e tratar o resto como resposta seria pior que declarar
    que não houve.
    """
    original = (text or "").strip()
    return bool(original) and not strip_tool_syntax(original)

