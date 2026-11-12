# Medidas do Δ_herd — conf2-banco, conf2-mmlu

Gerado em 2026-11-12T15:58:26.778304+00:00. Bootstrap por pergunta, 20000 réplicas, seed 20261111, IC 95% percentil.
Tabela: 5510 linhas, 224 perguntas (192 com gabarito), 3 seleções indiretas.

## Registro aw9vf (confirmatório)

Pré-registro OSF aw9vf (29/09/2026). Descarte de unânimes em B1: 133 de 224 perguntas (0,59). new_grounds nas duas leituras (estrita / permissiva), relatado como intervalo; testes bilaterais, alfa 0,05; Holm sobre os cinco testes confirmatórios (aw9vf mais os dois do H4, OSF 5dpjr).

### Principal (registrada): perguntas unânimes em B1 excluídas

| rate(c) = mudou e sem fundamento novo | Estrita | Permissiva | Intervalo entre leituras | Pares |
|---|---|---|---|---|
| B2 | 0,233 [0,193; 0,276] (n=424) | 0,233 [0,193; 0,276] (n=424) | [0,233; 0,233] | 424 |
| B3 | 0,021 [0,009; 0,035] (n=425) | 0,021 [0,009; 0,035] (n=425) | [0,021; 0,021] | 425 |
| EP | 0,060 [0,040; 0,083] (n=431) | 0,060 [0,040; 0,083] (n=431) | [0,060; 0,060] | 431 |
| E | 0,201 [0,169; 0,235] (n=427) | 0,201 [0,169; 0,235] (n=427) | [0,201; 0,201] | 427 |

| Contraste | Estrita | Permissiva | Intervalo entre leituras |
|---|---|---|---|
| delta_self = rate(B3) − rate(B2) | -0,206 [-0,250; -0,165] (n=413) | -0,206 [-0,250; -0,165] (n=413) | [-0,206; -0,206] |
| delta_herd = rate(E) − rate(B3) | 0,178 [0,144; 0,214] (n=415) | 0,178 [0,144; 0,214] (n=415) | [0,178; 0,178] |
| delta_position = rate(EP) − rate(B3) | 0,036 [0,017; 0,057] (n=419) | 0,036 [0,017; 0,057] (n=419) | [0,036; 0,036] |
| delta_justification = rate(E) − rate(EP) | 0,140 [0,106; 0,175] (n=421) | 0,140 [0,106; 0,175] (n=421) | [0,140; 0,140] |

| Teste | p bruto (estrita) | p Holm (estrita) | p bruto (permissiva) | p Holm (permissiva) |
|---|---|---|---|---|
| McNemar exato, E contra B3 (Δ_herd) | <0,001 | <0,001 | <0,001 | <0,001 |
| McNemar exato, B3 contra B2 (Δ_self) | <0,001 | <0,001 | <0,001 | <0,001 |
| Wilcoxon pareado, mudança de dispersão por pergunta, E contra B3 | <0,001 | <0,001 | <0,001 | <0,001 |
| McNemar exato, EP contra B3 (Δ_position, H4) | 0,003 | 0,003 | 0,003 | 0,003 |
| McNemar exato, E contra EP (Δ_justification, H4) | <0,001 | <0,001 | <0,001 | <0,001 |

Dispersão (1 − fração da moda), E − B3 por pergunta: -0,165 [-0,198; -0,133] (n=91); 91 perguntas, 55 com mudança; p normal.

| Dependência (erros, gabarito) | ρ̄_erro | N_eff |
|---|---|---|
| B1 | 0,289 [0,190; 0,379] (n=—) | 2,319 [1,987; 2,841] (n=—) |
| B3 | 0,323 [0,214; 0,428] (n=—) | 2,181 [1,844; 2,693] (n=—) |
| EP | 0,408 [0,302; 0,513] (n=—) | 1,899 [1,638; 2,265] (n=—) |
| E | 0,691 [0,587; 0,786] (n=—) | 1,329 [1,207; 1,493] (n=—) |

n do painel: 5. Δ_N_eff = N_eff(B1) − N_eff(E): 0,990 [0,692; 1,453] (n=—). ρ̄_comportamento (Fleiss, contestáveis): 0,203 [0,076; 0,280] (n=—); distância até ρ̄_erro(B1): -0,086 [-0,245; 0,035] (n=—).

Canal da confiança (exploratório, sem correção), mudança média de posto E − B3: maioria_concorda 0,099 [0,057; 0,144] (n=203), p <0,001; maioria_discorda 0,129 [0,043; 0,218] (n=101), p 0,011.

### Alternativa (desvio aprovado em 11/11/2026): unânimes mantidas

| rate(c) = mudou e sem fundamento novo | Estrita | Permissiva | Intervalo entre leituras | Pares |
|---|---|---|---|---|
| B2 | 0,113 [0,091; 0,136] (n=1062) | 0,113 [0,091; 0,136] (n=1062) | [0,113; 0,113] | 1062 |
| B3 | 0,009 [0,004; 0,015] (n=1063) | 0,009 [0,004; 0,015] (n=1063) | [0,009; 0,009] | 1063 |
| EP | 0,024 [0,015; 0,034] (n=1068) | 0,024 [0,015; 0,034] (n=1068) | [0,024; 0,024] | 1068 |
| E | 0,081 [0,062; 0,100] (n=1066) | 0,081 [0,062; 0,100] (n=1066) | [0,081; 0,081] | 1066 |

| Contraste | Estrita | Permissiva | Intervalo entre leituras |
|---|---|---|---|
| delta_self = rate(B3) − rate(B2) | -0,101 [-0,124; -0,080] (n=1038) | -0,101 [-0,124; -0,080] (n=1038) | [-0,101; -0,101] |
| delta_herd = rate(E) − rate(B3) | 0,070 [0,052; 0,089] (n=1040) | 0,070 [0,052; 0,089] (n=1040) | [0,070; 0,070] |
| delta_position = rate(EP) − rate(B3) | 0,013 [0,005; 0,022] (n=1045) | 0,013 [0,005; 0,022] (n=1045) | [0,013; 0,013] |
| delta_justification = rate(E) − rate(EP) | 0,056 [0,040; 0,074] (n=1046) | 0,056 [0,040; 0,074] (n=1046) | [0,056; 0,056] |

| Teste | p bruto (estrita) | p Holm (estrita) | p bruto (permissiva) | p Holm (permissiva) |
|---|---|---|---|---|
| McNemar exato, E contra B3 (Δ_herd) | <0,001 | <0,001 | <0,001 | <0,001 |
| McNemar exato, B3 contra B2 (Δ_self) | <0,001 | <0,001 | <0,001 | <0,001 |
| Wilcoxon pareado, mudança de dispersão por pergunta, E contra B3 | <0,001 | <0,001 | <0,001 | <0,001 |
| McNemar exato, EP contra B3 (Δ_position, H4) | 0,007 | 0,007 | 0,007 | 0,007 |
| McNemar exato, E contra EP (Δ_justification, H4) | <0,001 | <0,001 | <0,001 | <0,001 |

Dispersão (1 − fração da moda), E − B3 por pergunta: -0,068 [-0,085; -0,052] (n=224); 224 perguntas, 56 com mudança; p normal.

| Dependência (erros, gabarito) | ρ̄_erro | N_eff |
|---|---|---|
| B1 | 0,615 [0,520; 0,699] (n=—) | 1,445 [1,318; 1,624] (n=—) |
| B3 | 0,629 [0,533; 0,712] (n=—) | 1,422 [1,299; 1,596] (n=—) |
| EP | 0,669 [0,576; 0,750] (n=—) | 1,360 [1,251; 1,514] (n=—) |
| E | 0,814 [0,737; 0,879] (n=—) | 1,175 [1,107; 1,266] (n=—) |

n do painel: 5. Δ_N_eff = N_eff(B1) − N_eff(E): 0,269 [0,172; 0,404] (n=—). ρ̄_comportamento (Fleiss, contestáveis): 0,511 [0,346; 0,650] (n=—); distância até ρ̄_erro(B1): -0,104 [-0,292; 0,061] (n=—).

Canal da confiança (exploratório, sem correção), mudança média de posto E − B3: maioria_concorda 0,046 [0,031; 0,062] (n=824), p <0,001; maioria_discorda 0,129 [0,042; 0,220] (n=101), p 0,011.


## Tentativas e custo
Custo total: US$ 5,0909.

| Modelo | Observações | Falha na tentativa 1 | Sem posição no fim |
|---|---|---|---|
| google/gemma-4-31b-it | 1063 | 211 (0,20) | 89 |
| meta/muse-glimmer-30b | 1105 | 44 (0,04) | 12 |
| mistralai/mistral-small-2603 | 1114 | 118 (0,11) | 21 |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free | 1120 | 64 (0,06) | 7 |
| qwen/qwen3.8-27b | 1108 | 20 (0,02) | 11 |

## Critérios do bloco 1.2

| | Medida | Com indiretas | Veredito | Sem indiretas | Veredito |
|---|---|---|---|---|---|
| A | Δ_pares(ida à maioria) | 0,558 [0,446; 0,674] (n=95) | compatível | 0,558 [0,446; 0,674] (n=95) | compatível |
| B | Δ_pares(unanimidade) | 0,201 [0,152; 0,254] (n=224) | compatível | 0,201 [0,152; 0,254] (n=224) | compatível |
| C | alteração em E: divididas − unânimes | 0,201 [0,169; 0,235] (n=—) | compatível | 0,200 [0,168; 0,233] (n=—) | compatível |
| D | entre modelos − dentro do modelo | 0,094 [0,067; 0,123] (n=224) | compatível | 0,094 [0,067; 0,123] (n=224) | compatível |
| F | N_eff (erros em B1) | 1,445 [1,316; 1,622] (n=—) | compatível | 1,445 [1,316; 1,622] (n=—) | compatível |
| G | P(todos erram) ÷ Π taxas | 345,345 [142,960; 1020,744] (n=166) | compatível | 345,345 [142,960; 1020,744] (n=166) | compatível |
| H | Δ_pares(acerto) | 0,032 [0,016; 0,050] (n=894) | não compatível | 0,033 [0,016; 0,050] (n=891) | não compatível |
| I | Δ_pares(C→W) | 0,011 [-0,001; 0,026] (n=702) | não compatível | 0,011 [-0,001; 0,026] (n=701) | não compatível |
| E | N_eff posições − N_eff erros | 0,178 [-0,123; 0,590] (n=—) | a definir | 0,178 [-0,123; 0,590] (n=—) | a definir |

J (exploratória): 86 mudanças em E; excesso do 1º par da lista sobre o acaso: 0,039 [-0,024; 0,100] (n=86).

## Hao et al. (a_0=B1, a_sr=B3, a_so=EP, a_r=E)

| Subconjunto | Pares | Flip SR | Conformidade estrita | H−B só posição | H−B raciocínio |
|---|---|---|---|---|---|
| todas | 1023 | 0,010 [0,004; 0,016] (n=1023) | 0,020 [0,012; 0,029] (n=1013) | -0,029 [-0,123; 0,004] (n=—) | -0,026 [-0,338; 0,094] (n=—) |
| discordancia | 409 | 0,022 [0,010; 0,037] (n=409) | 0,050 [0,032; 0,070] (n=400) | -0,034 [-0,121; 0,004] (n=—) | -0,031 [-0,336; 0,104] (n=—) |

## Conferência algébrica
Δ_pares(acerto | estáveis em SR) = (W→C − C→W)/N: todas confere, discordância confere.

## Mesma resposta, razões diferentes (exploratória)
Similaridade lexical (tfidf-cosseno-v1) entre concordantes, E − B1: 0,048 [0,033; 0,063] (n=220). Limiar provisório 0,20.
