# Medidas do Δ_herd — conf2-mmlu

Gerado em 2026-11-12T17:57:47.317044+00:00. Bootstrap por pergunta, 20000 réplicas, seed 20261111, IC 95% percentil.
Tabela: 3422 linhas, 140 perguntas (140 com gabarito), 3 seleções indiretas.

## Registro aw9vf (confirmatório)

Pré-registro OSF aw9vf (29/09/2026). Descarte de unânimes em B1: 79 de 140 perguntas (0,56). new_grounds nas duas leituras (estrita / permissiva), relatado como intervalo; testes bilaterais, alfa 0,05; Holm sobre os cinco testes confirmatórios (aw9vf mais os dois do H4, OSF 5dpjr).

### Principal (registrada): perguntas unânimes em B1 excluídas

| rate(c) = mudou e sem fundamento novo | Estrita | Permissiva | Intervalo entre leituras | Pares |
|---|---|---|---|---|
| B2 | 0,245 [0,194; 0,299] (n=278) | 0,245 [0,194; 0,299] (n=278) | [0,245; 0,245] | 278 |
| B3 | 0,029 [0,011; 0,048] (n=280) | 0,029 [0,011; 0,048] (n=280) | [0,029; 0,029] | 280 |
| EP | 0,062 [0,038; 0,090] (n=288) | 0,062 [0,038; 0,090] (n=288) | [0,062; 0,062] | 288 |
| E | 0,216 [0,175; 0,258] (n=283) | 0,216 [0,175; 0,258] (n=283) | [0,216; 0,216] | 283 |

| Contraste | Estrita | Permissiva | Intervalo entre leituras |
|---|---|---|---|
| delta_self = rate(B3) − rate(B2) | -0,211 [-0,268; -0,156] (n=270) | -0,211 [-0,268; -0,156] (n=270) | [-0,211; -0,211] |
| delta_herd = rate(E) − rate(B3) | 0,186 [0,142; 0,232] (n=274) | 0,186 [0,142; 0,232] (n=274) | [0,186; 0,186] |
| delta_position = rate(EP) − rate(B3) | 0,032 [0,007; 0,059] (n=279) | 0,032 [0,007; 0,059] (n=279) | [0,032; 0,032] |
| delta_justification = rate(E) − rate(EP) | 0,149 [0,106; 0,193] (n=282) | 0,149 [0,106; 0,193] (n=282) | [0,149; 0,149] |

| Teste | p bruto (estrita) | p Holm (estrita) | p bruto (permissiva) | p Holm (permissiva) |
|---|---|---|---|---|
| McNemar exato, E contra B3 (Δ_herd) | <0,001 | <0,001 | <0,001 | <0,001 |
| McNemar exato, B3 contra B2 (Δ_self) | <0,001 | <0,001 | <0,001 | <0,001 |
| Wilcoxon pareado, mudança de dispersão por pergunta, E contra B3 | <0,001 | <0,001 | <0,001 | <0,001 |
| McNemar exato, EP contra B3 (Δ_position, H4) | 0,049 | 0,049 | 0,049 | 0,049 |
| McNemar exato, E contra EP (Δ_justification, H4) | <0,001 | <0,001 | <0,001 | <0,001 |

Dispersão (1 − fração da moda), E − B3 por pergunta: -0,180 [-0,222; -0,140] (n=61); 61 perguntas, 39 com mudança; p exato.

| Dependência (erros, gabarito) | ρ̄_erro | N_eff |
|---|---|---|
| B1 | 0,635 [0,541; 0,721] (n=—) | 1,413 [1,287; 1,580] (n=—) |
| B3 | 0,642 [0,547; 0,729] (n=—) | 1,401 [1,277; 1,568] (n=—) |
| EP | 0,689 [0,600; 0,770] (n=—) | 1,332 [1,226; 1,471] (n=—) |
| E | 0,826 [0,751; 0,894] (n=—) | 1,162 [1,093; 1,249] (n=—) |

n do painel: 5. Δ_N_eff = N_eff(B1) − N_eff(E): 0,251 [0,153; 0,385] (n=—). ρ̄_comportamento (Fleiss): não se aplica (0 perguntas contestáveis).
Painel homogêneo de contraste (conf3-contraste-mmlu), B1: ρ̄_erro 0,848 [0,759; 0,924] (n=—); N_eff 1,138 [1,065; 1,239] (n=—) (n=5).

Canal da confiança (exploratório, sem correção), mudança média de posto E − B3: maioria_concorda 0,102 [0,051; 0,158] (n=128), p <0,001; maioria_discorda 0,111 [0,016; 0,211] (n=63), p 0,092.

### Alternativa (desvio aprovado em 11/11/2026): unânimes mantidas

| rate(c) = mudou e sem fundamento novo | Estrita | Permissiva | Intervalo entre leituras | Pares |
|---|---|---|---|---|
| B2 | 0,124 [0,095; 0,155] (n=652) | 0,124 [0,095; 0,155] (n=652) | [0,124; 0,124] | 652 |
| B3 | 0,014 [0,006; 0,023] (n=655) | 0,014 [0,006; 0,023] (n=655) | [0,014; 0,014] | 655 |
| EP | 0,027 [0,015; 0,040] (n=664) | 0,027 [0,015; 0,040] (n=664) | [0,027; 0,027] | 664 |
| E | 0,092 [0,068; 0,118] (n=664) | 0,092 [0,068; 0,118] (n=664) | [0,092; 0,092] | 664 |

| Contraste | Estrita | Permissiva | Intervalo entre leituras |
|---|---|---|---|
| delta_self = rate(B3) − rate(B2) | -0,109 [-0,139; -0,080] (n=635) | -0,109 [-0,139; -0,080] (n=635) | [-0,109; -0,109] |
| delta_herd = rate(E) − rate(B3) | 0,077 [0,054; 0,103] (n=646) | 0,077 [0,054; 0,103] (n=646) | [0,077; 0,077] |
| delta_position = rate(EP) − rate(B3) | 0,012 [0,000; 0,025] (n=648) | 0,012 [0,000; 0,025] (n=648) | [0,012; 0,012] |
| delta_justification = rate(E) − rate(EP) | 0,064 [0,043; 0,087] (n=655) | 0,064 [0,043; 0,087] (n=655) | [0,064; 0,064] |

| Teste | p bruto (estrita) | p Holm (estrita) | p bruto (permissiva) | p Holm (permissiva) |
|---|---|---|---|---|
| McNemar exato, E contra B3 (Δ_herd) | <0,001 | <0,001 | <0,001 | <0,001 |
| McNemar exato, B3 contra B2 (Δ_self) | <0,001 | <0,001 | <0,001 | <0,001 |
| Wilcoxon pareado, mudança de dispersão por pergunta, E contra B3 | <0,001 | <0,001 | <0,001 | <0,001 |
| McNemar exato, EP contra B3 (Δ_position, H4) | 0,096 | 0,096 | 0,096 | 0,096 |
| McNemar exato, E contra EP (Δ_justification, H4) | <0,001 | <0,001 | <0,001 | <0,001 |

Dispersão (1 − fração da moda), E − B3 por pergunta: -0,080 [-0,104; -0,058] (n=140); 140 perguntas, 40 com mudança; p exato.

| Dependência (erros, gabarito) | ρ̄_erro | N_eff |
|---|---|---|
| B1 | 0,635 [0,541; 0,721] (n=—) | 1,413 [1,287; 1,580] (n=—) |
| B3 | 0,642 [0,547; 0,729] (n=—) | 1,401 [1,277; 1,568] (n=—) |
| EP | 0,689 [0,600; 0,770] (n=—) | 1,332 [1,226; 1,471] (n=—) |
| E | 0,826 [0,751; 0,894] (n=—) | 1,162 [1,093; 1,249] (n=—) |

n do painel: 5. Δ_N_eff = N_eff(B1) − N_eff(E): 0,251 [0,153; 0,385] (n=—). ρ̄_comportamento (Fleiss): não se aplica (0 perguntas contestáveis).
Painel homogêneo de contraste (conf3-contraste-mmlu), B1: ρ̄_erro 0,848 [0,759; 0,924] (n=—); N_eff 1,138 [1,065; 1,239] (n=—) (n=5).

Canal da confiança (exploratório, sem correção), mudança média de posto E − B3: maioria_concorda 0,052 [0,031; 0,075] (n=496), p <0,001; maioria_discorda 0,111 [0,016; 0,212] (n=63), p 0,092.


## Tentativas e custo
Custo total: US$ 3,7568.

| Modelo | Observações | Falha na tentativa 1 | Sem posição no fim |
|---|---|---|---|
| google/gemma-4-31b-it | 652 | 134 (0,21) | 64 |
| meta/muse-glimmer-30b | 685 | 33 (0,05) | 10 |
| mistralai/mistral-small-2603 | 697 | 65 (0,09) | 9 |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | 700 | 41 (0,06) | 2 |
| qwen/qwen3.8-27b | 688 | 18 (0,03) | 11 |

## Critérios do bloco 1.2

| | Medida | Com indiretas | Veredito | Sem indiretas | Veredito |
|---|---|---|---|---|---|
| A | Δ_pares(ida à maioria) | 0,561 [0,414; 0,707] (n=57) | compatível | 0,561 [0,414; 0,707] (n=57) | compatível |
| B | Δ_pares(unanimidade) | 0,214 [0,150; 0,286] (n=140) | compatível | 0,214 [0,150; 0,286] (n=140) | compatível |
| C | alteração em E: divididas − unânimes | 0,216 [0,175; 0,258] (n=—) | compatível | 0,214 [0,174; 0,255] (n=—) | compatível |
| D | entre modelos − dentro do modelo | 0,108 [0,071; 0,145] (n=140) | compatível | 0,108 [0,071; 0,145] (n=140) | compatível |
| F | N_eff (erros em B1) | 1,413 [1,287; 1,580] (n=—) | compatível | 1,413 [1,287; 1,580] (n=—) | compatível |
| G | P(todos erram) ÷ Π taxas | 113,928 [48,237; 345,321] (n=116) | compatível | 113,928 [48,237; 345,321] (n=116) | compatível |
| H | Δ_pares(acerto) | 0,036 [0,014; 0,057] (n=647) | não compatível | 0,036 [0,014; 0,058] (n=644) | não compatível |
| I | Δ_pares(C→W) | 0,013 [-0,004; 0,034] (n=467) | não compatível | 0,013 [-0,004; 0,034] (n=466) | não compatível |
| E | N_eff posições − N_eff erros | — [—; —] (n=—) | a definir | — [—; —] (n=—) | a definir |

J (exploratória): 61 mudanças em E; excesso do 1º par da lista sobre o acaso: 0,022 [-0,054; 0,095] (n=61).

## Hao et al. (a_0=B1, a_sr=B3, a_so=EP, a_r=E)

| Subconjunto | Pares | Flip SR | Conformidade estrita | H−B só posição | H−B raciocínio |
|---|---|---|---|---|---|
| todas | 639 | 0,014 [0,006; 0,023] (n=639) | 0,022 [0,012; 0,034] (n=630) | -0,035 [-0,131; 0,005] (n=—) | -0,018 [-0,300; 0,118] (n=—) |
| discordancia | 273 | 0,029 [0,011; 0,049] (n=273) | 0,053 [0,030; 0,078] (n=265) | -0,042 [-0,128; 0,006] (n=—) | -0,022 [-0,298; 0,131] (n=—) |

## Conferência algébrica
Δ_pares(acerto | estáveis em SR) = (W→C − C→W)/N: todas confere, discordância confere.

## Mesma resposta, razões diferentes (exploratória)
Similaridade lexical (tfidf-cosseno-v1) entre concordantes, E − B1: 0,034 [0,015; 0,052] (n=136). Limiar provisório 0,20.
