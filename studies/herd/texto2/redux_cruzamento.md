# Cruzamento com o MMLU-Redux 2.0 (exploratório, 12/11/2026)

Leitura pendente — proprietário.

Fonte: `edinburgh-dawg/mmlu-redux-2.0`, split test, 13 matérias, baixado pela API de linhas do Hugging Face (autorização do Eduardo em 12/11). A chave registrada não foi editada (344-79 item 3).

**Escopo:** das perguntas contestadas no texto 2 (§4.1 e §4.1b) que vieram do MMLU original, 14 estão no Redux. Outras 5 não estão: m06785, m01935, m01566, m02530 e m02085. Entram aqui só as 14 em que 3 ou mais modelos escolheram a mesma opção errada em B1.

**Resultado:**
- O Redux marca as 14 como `ok`: a chave da versão original, com 4 opções, está certa.
- Em 11 das 14, a opção em que os modelos convergiram é um distrator acrescentado pelo MMLU-Pro, que não existia no MMLU. O Redux não revisou essas opções.
- Em 3 das 14, a escolha é uma das opções originais, e o Redux diz que a chave está certa: m01086, m05302 e m05787. Nessas, o erro é dos modelos.

| Pergunta | Chave | Escolha (de 5) | Escolha é | Redux |
|---|---|---|---|---|
| m01086 | C | H (4) | original | ok |
| m03165 | B | D (4) | acrescentada pelo Pro | ok |
| m04683 | D | F (4) | acrescentada pelo Pro | ok |
| m04776 | H | C (5) | acrescentada pelo Pro | ok |
| m05018 | F | G (4) | acrescentada pelo Pro | ok |
| m05022 | B | H (3) | acrescentada pelo Pro | ok |
| m05049 | G | J (5) | acrescentada pelo Pro | ok |
| m05198 | B | I (4) | acrescentada pelo Pro | ok |
| m05220 | G | B (3) | acrescentada pelo Pro | ok |
| m05302 | I | H (3) | original | ok |
| m05787 | G | D (4) | original | ok |
| m07045 | E | C (5) | acrescentada pelo Pro | ok |
| m07114 | G | F (5) | acrescentada pelo Pro | ok |
| m09169 | F | A (3) | acrescentada pelo Pro | ok |

**Leitura:** a maior parte do erro em comum nas perguntas herdadas do MMLU acontece num distrator que o MMLU-Pro acrescentou. O Redux não diz se esses distratores também estão corretos. A leitura das sessões sugere que vários estão, mas ninguém conferiu em fonte. Os dados não separam duas explicações: os modelos podem ter acertado uma opção que também está correta, ou os cinco podem ter caído no mesmo distrator plausível. Nos dois casos, a origem é o conjunto de perguntas, e não uma dependência entre os modelos que se possa ver fora dele.
