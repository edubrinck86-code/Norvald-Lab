# Custo por chamada: B3T (texto corrido) × B3R (formato estruturado)

Cálculo feito em 16/11/2026 (Opus do Huginn, pedido do Eduardo) sobre a coleta deste estudo,
`~/.norvald/lab/experiments/f-*-{b3t,b3r}/raw/*/observations.jsonl`, campo `result.metadata.raw_usage`
(custo e tokens informados pelo provedor). Exploratório, não pré-registrado.

| Condição | Chamadas | Custo médio por chamada (US$) | Tokens de entrada | Tokens de saída |
|---|---|---|---|---|
| B3T (texto corrido) | 455 | 0,001004 | 2.385 | 1.078 |
| B3R (formato da engine) | 458 | 0,000938 | 2.598 | 1.036 |
| Diferença | | −6,6% | +9% | −4% |

Leitura: o formato estruturado envia um pouco mais de contexto, mas o modelo escreve menos ao revisar;
como a saída custa mais que a entrada, a chamada sai mais barata. Mesmas perguntas e mesmos cinco modelos.
Usado no README da engine documental e na divulgação como "6,6% menos por chamada" / "uns 7%".
