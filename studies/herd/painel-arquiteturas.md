# Arquitetura dos modelos do painel (para declarar no OSF)

Registrado em 11/11/2026, a pedido do Eduardo. Fica aqui, e não no `panel.json`, porque mudar o painel no meio da rodada `piloto-mmlu-2` impediria retomá-la: `freeze_plan` recusa um painel diferente no mesmo run_id.

Por que importa: se os erros em comum vierem de arquitetura parecida, o dado precisa estar declarado antes da análise. "30B" no nome não diz quantos parâmetros trabalham em cada palavra gerada.

| Modelo (OpenRouter) | Arquitetura | Fonte |
|---|---|---|
| google/gemma-4-31b-it | densa | descrição do modelo no OpenRouter, 11/11/2026 |
| qwen/qwen3.8-27b | densa | descrição do modelo no OpenRouter, 11/11/2026 |
| meta/muse-glimmer-30b | densa (destilada do Muse Spark) | descrição do modelo no OpenRouter, 11/11/2026 |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | MoE: 30B no total, 3B ativos por token ("A3B") | nome do modelo; a descrição não diz |
| mistralai/mistral-small-2603 | não declarada | a descrição não diz; conferir na ficha do fabricante |
| deepseek/deepseek-v4-pro-0813 (candidato do teste EF, estacionado) | MoE grande | descrição do modelo no OpenRouter, 11/11/2026 |

No piloto-mmlu-1 (B1, 28 perguntas), o Nemotron foi o que menos acertou (13 de 28).
