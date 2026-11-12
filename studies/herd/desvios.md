# Desvios do registro — coleta confirmatória do Δ_herd

Registro: OSF aw9vf (plano, 29/09/2026) e 5dpjr (registro da coleta, 11/11/2026 17:14, Brasília).
Declarados em 12/11/2026, depois da coleta e antes de qualquer texto de resultado.
Cada desvio traz a data, o motivo e o efeito sobre a análise.

Horários em Brasília (UTC−3). O registro completo das rodadas, com início, fim, chamadas e custo, está em [`coletas/README.md`](coletas/README.md).

## D1. Empresa fixa por modelo atrás do OpenRouter (11/11/2026)

**O que o registro previa:** cada modelo chamado pelo OpenRouter, sem dizer qual empresa serve o modelo.

**O que aconteceu:** na primeira tentativa (rodadas `conf-*`), o OpenRouter distribuiu as chamadas por 13 empresas diferentes. A mesma "versão" de um modelo pode vir com precisão numérica, quantização ou configuração diferentes, e isso entraria como ruído entre condições.

**O que mudou:** cada modelo passou a ser servido por uma única empresa, sem plano B (`provider.order` com `allow_fallbacks: false`). Resposta servida por outra empresa é recusada (Lab PR #17).

| Modelo | Empresa |
|---|---|
| google/gemma-4-31b-it | Crusoe (bf16) |
| qwen/qwen3.8-27b | DeepInfra (bf16) |
| meta/muse-glimmer-30b | DeepInfra (bf16) |
| mistralai/mistral-small-2603 | Mistral |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | Nvidia |

**Efeito:** as rodadas `conf-*` foram interrompidas e não entram na análise. Os modelos e as condições não mudaram.

## D2. Rodadas interrompidas e refeitas (11/11/2026)

- `conf-banco`, `conf-mmlu`, `conf-contraste-banco`, `conf-contraste-mmlu`: interrompidas por causa de D1.
- `conf2-contraste-banco`, `conf2-contraste-mmlu`: interrompidas porque a Crusoe recusou por limite de taxa entre 17 e 24% das respostas do Gemma. O contraste foi refeito como `conf3-contraste-*`, com concorrência de 2 por empresa.
- Quatro experimentos parciais de `conf2-*` foram movidos para fora da pasta de dados antes de serem refeitos: `conf2-banco-g02-b2`, `conf2-mmlu-m03713-b1`, `conf2-banco-g10-b1` e `conf2-mmlu-m04145-b2`. Ficam guardados, não são apagados e não entram na análise.

**Efeito:** só `conf2-banco`, `conf2-mmlu` e `conf3-contraste-*` entram na análise. Os registros interrompidos ficam guardados e listados em `coletas/`.

## D3. Coleta dividida em processos paralelos (11/11/2026, 23:00)

**Motivo:** o Muse servido pela DeepInfra levou cerca de 104 s por resposta. Uma pergunta por vez teria dado cerca de 40 horas de coleta.

**O que mudou:** as perguntas foram divididas em seis grupos, rodando em paralelo com a mesma configuração e o mesmo `run_id`. A ordem do protocolo dentro de cada pergunta (B1, depois B2, depois B3, EP e E) não mudou.

**Efeito:** nenhum sobre o desenho. Cada experimento é independente dos outros.

## D4. Exclusão por participante, e não por pergunta (12/11/2026)

**O registro (344-79, item 2):** o participante que não declarou contribuição estruturada em B1 não entra no WC, ninguém o vê, e ele sai da análise de exposição daquela pergunta. A exclusão é registrada pergunta a pergunta.

**O que o Lab fazia:** recusava B3, EP e E da pergunta inteira quando qualquer participante ficava sem contribuição em B1, mesmo depois da segunda tentativa. Assim se perderam 28 perguntas, 4 do banco e 24 do MMLU-Pro. Isso era mais rígido que o registro.

**O que mudou:** o Lab passou a seguir o registro (Lab PR #18). As derivadas dessas 28 perguntas rodaram em 12/11, entre 10:00 e 10:22. As respostas de B1 não foram tocadas e ninguém ganhou nova tentativa. A exclusão de cada pergunta fica gravada em `excluded_from_exposure`.

**Exclusões gravadas: 30 participante-pergunta em 28 perguntas.**

| Causa | Modelo | Quantas |
|---|---|---|
| Limite de taxa da empresa | Gemma (Crusoe) | 15 |
| Limite de taxa da empresa | Muse (DeepInfra) | 3 |
| Resposta vazia | Gemma 4, Qwen 4, Muse 2 | 10 |
| Sem o bloco CONTRIBUTION | Mistral | 2 |

**Efeito:** 26 dessas perguntas têm mesa de 4 e 2 têm mesa de 3. Nenhuma pergunta ficou sem derivadas.

## D5. Limite de taxa da empresa do Gemma (efeito do fornecedor)

**O que aconteceu:** a Crusoe é a única empresa permitida para o Gemma (D1) e limitou a taxa de pedidos. A falha na primeira tentativa foi de 19% das chamadas do Gemma no banco e de 21% no MMLU-Pro. Com a segunda tentativa permitida pelo registro (item 4), ainda ficaram sem posição no fim 25 respostas no banco e 64 no MMLU-Pro.

**Efeito:**
- O Gemma é o modelo mais excluído.
- O desequilíbrio vem do fornecedor e não deve ser lido como característica do modelo.
- No contraste homogêneo (5 × Gemma), a perda reduz a amostra, e o ρ̄ do contraste é lido com essa ressalva.

## Pendências declaradas

- **Contraste do banco:** as medidas do painel de contraste no banco próprio saíram vazias ("—"). A causa está em investigação. Nenhuma conclusão sobre o contraste do banco será tirada antes disso.
- **Concordância de Fleiss:** a leitura principal do MMLU-Pro saiu vazia ("—"). Está em investigação, junto com o item anterior.
