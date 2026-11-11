# Medidas do Δ_herd — piloto-mmlu-2

Gerado em 2026-11-11T19:35:01.192860+00:00. Bootstrap por pergunta, 20000 réplicas, seed 20261111, IC 95% percentil.
Tabela: 700 linhas, 28 perguntas (28 com gabarito), 0 seleções indiretas.

## Tentativas e custo
Custo total: US$ 0,7306.

| Modelo | Observações | Falha na tentativa 1 | Sem posição no fim |
|---|---|---|---|
| google/gemma-4-31b-it | 140 | 0 (0,00) | 0 |
| meta/muse-glimmer-30b | 140 | 0 (0,00) | 0 |
| mistralai/mistral-small-2603 | 140 | 9 (0,06) | 1 |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | 140 | 10 (0,07) | 0 |
| qwen/qwen3.8-27b | 140 | 1 (0,01) | 1 |

## Critérios do bloco 1.2

| | Medida | Com indiretas | Veredito | Sem indiretas | Veredito |
|---|---|---|---|---|---|
| A | Δ_pares(ida à maioria) | 0,417 [0,111; 0,692] (n=12) | compatível | 0,417 [0,111; 0,692] (n=12) | compatível |
| B | Δ_pares(unanimidade) | 0,179 [0,036; 0,321] (n=28) | compatível | 0,179 [0,036; 0,321] (n=28) | compatível |
| C | alteração em E: divididas − unânimes | 0,233 [0,125; 0,354] (n=—) | compatível | 0,233 [0,125; 0,354] (n=—) | compatível |
| D | entre modelos − dentro do modelo | 0,098 [0,004; 0,195] (n=28) | compatível | 0,098 [0,004; 0,195] (n=28) | compatível |
| F | N_eff (erros em B1) | 1,641 [1,330; 2,188] (n=—) | compatível | 1,641 [1,330; 2,188] (n=—) | compatível |
| G | P(todos erram) ÷ Π taxas | 67,545 [0,000; 731,733] (n=28) | não compatível | 67,545 [0,000; 731,733] (n=28) | não compatível |
| H | Δ_pares(acerto) | 0,007 [-0,044; 0,057] (n=139) | compatível | 0,007 [-0,044; 0,057] (n=139) | compatível |
| I | Δ_pares(C→W) | 0,030 [-0,019; 0,101] (n=101) | não compatível | 0,030 [-0,019; 0,101] (n=101) | não compatível |
| E | N_eff posições − N_eff erros | — [—; —] (n=—) | a definir | — [—; —] (n=—) | a definir |

J (exploratória): 14 mudanças em E; excesso do 1º par da lista sobre o acaso: 0,036 [-0,212; 0,250] (n=14).

## Hao et al. (a_0=B1, a_sr=B3, a_so=EP, a_r=E)

| Subconjunto | Pares | Flip SR | Conformidade estrita | H−B só posição | H−B raciocínio |
|---|---|---|---|---|---|
| todas | 139 | 0,029 [0,007; 0,058] (n=139) | 0,022 [0,000; 0,046] (n=135) | -0,110 [-0,200; 0,000] (n=—) | 0,065 [-0,147; 0,640] (n=—) |
| discordancia | 59 | 0,051 [0,000; 0,102] (n=59) | 0,054 [0,000; 0,105] (n=56) | -0,110 [-0,200; 0,000] (n=—) | 0,065 [-0,140; 0,594] (n=—) |

## Conferência algébrica
Δ_pares(acerto | estáveis em SR) = (W→C − C→W)/N: todas confere, discordância confere.

## Mesma resposta, razões diferentes (exploratória)
Similaridade lexical (tfidf-cosseno-v1) entre concordantes, E − B1: 0,045 [0,007; 0,085] (n=28). Limiar provisório 0,20.
