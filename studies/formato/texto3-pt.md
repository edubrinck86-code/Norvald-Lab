# O formato da própria resposta anterior ancora a reconsideração? Itens estruturados × texto corrido num painel de LLMs

Eduardo Guedes · Pesquisador independente · ORCID 0009-0003-9960-3337

> Rascunho de 12/11/2026. Leitura pendente — proprietário. Números de `studies/formato/resultados.md` (saída de `medidas.py`, sem edição). Pré-registro: OSF gzvk5, registro 46erj. Desvios em `studies/formato/desvios.md`.

## Resumo

No estudo Δ_herd (OSF gbx5m), modelos que reveem a própria resposta anterior quase não mudam de opção (B3: 2,1%), enquanto modelos que veem só a letra escolhida mudam bem mais (B3L: 16,3%). As duas condições diferem em duas coisas: no conteúdo (o B3 mostra o raciocínio declarado) e no formato (o B3 o mostra como itens e relações estruturados). Para separar as duas, criamos uma condição nova, B3T, com o mesmo conteúdo do B3 apresentado em texto corrido, e uma réplica do B3 coletada no mesmo dia (B3R) como controle de deriva. O painel e as perguntas são os mesmos do Δ_herd: cinco modelos de cinco empresas e as 91 perguntas não unânimes (30 de um banco novo e 61 do MMLU-Pro).

A hipótese confirmatória se sustentou. Os modelos mudaram de opção em 10,3% [7,5; 13,3] das vezes no B3T e em 3,9% [2,3; 5,8] no B3R: diferença de 6,5 pontos [3,7; 9,3], McNemar pareado p = 6,2 × 10⁻⁵, com 431 pares. O efeito vem do MMLU-Pro (13,6% × 4,5%, p = 6,9 × 10⁻⁵). No banco novo, mais fácil, não houve diferença detectável (4,1% × 2,7%, p = 0,69). A ordem descritiva esperada se confirmou: B3R ≤ B3T ≤ B3L. As mudanças a mais do B3T foram, na maior parte, troca de um erro por outro erro (20, contra 4 no B3R). O saldo de correção foi parecido (+6 no B3T, +5 no B3R). Em reconsideração, o formato estruturado deixou os modelos mais estáveis sem reduzir a correção.

## 1. Introdução

O texto 1 mediu quanto os modelos mudam de resposta quando veem os pares, e usou como linha de base a reconsideração da própria resposta (B3). Essa linha de base saiu baixa: cerca de 2%. Quando o modelo via só a letra que tinha escolhido (B3L, exploratório), a taxa subia para 16%. Hao et al. (2026) relatam 37% num desenho com outros modelos e texto livre.

A diferença entre B3 e B3L tem duas explicações possíveis. Ou o que segura o modelo é ver o próprio raciocínio (conteúdo), ou é o modo como ele aparece, em itens com confiança declarada e relações explícitas (formato). Se for o formato, a escolha de como guardar e devolver a resposta de um modelo muda o comportamento dele. Isso importa para qualquer sistema que faz o modelo revisar o próprio trabalho em etapas.

## 2. Método

**Condições.** Todas derivam das respostas B1 já coletadas em 11/11/2026 (rodadas conf2-banco e conf2-mmlu). Nenhum B1 foi coletado de novo. A instrução de reconsideração e o formato de resposta pedido são idênticos. Muda só a apresentação da resposta anterior.

| Condição | O participante vê | Coleta |
|---|---|---|
| B3 | a própria contribuição B1, em itens e relações estruturados | 11/11 (conf2) |
| B3L | só a opção escolhida em B1 | 11/11 (exploratório do Δ_herd) |
| B3T | o mesmo conteúdo do B3, em texto corrido: cada item vira um parágrafo com a confiança declarada, cada relação uma frase | 12/11 |
| B3R | o mesmo que o B3, coletado de novo | 12/11 |

O texto do B3T é gerado no idioma da rodada (Lab PR #27). Um teste automático confere que cada item, cada confiança e a opção escolhida do B3 aparecem no texto, sem estrutura e sem nada dos pares.

**Painel.** Os mesmos cinco modelos do Δ_herd, cada um com o mesmo provedor fixo: Gemma 4 31B (Google), Nemotron 3 Nano 30B (NVIDIA), Mistral Small 2603, Qwen 3.8 27B (Alibaba) e Muse Glimmer 30B (Meta). Temperatura 0,7, top_p 1,0, esforço de raciocínio médio, max_tokens 4096.

**Perguntas.** As não unânimes em B1, as mesmas do B3L: 30 do banco novo e 61 do MMLU-Pro.

**Medida.** A opção escolhida na condição difere da opção do B1. É a mesma regra do B3 e do B3L.

**Hipóteses (pré-registradas).**
- H1, confirmatória: a mudança de opção é mais frequente no B3T do que no B3R. McNemar exato pareado por participante × pergunta, bilateral, α = 0,05. A análise principal junta os dois bancos.
- H2, descritiva: ordem esperada B3R ≤ B3T ≤ B3L, com IC bootstrap.
- H3, descritiva: nas perguntas com gabarito, cada mudança classificada como errado → certo, certo → errado ou errado → outro errado.

**Estatística.** Bootstrap por pergunta, 20.000 réplicas, seed 20261112, IC 95% percentil.

**Coleta.** Em 12/11/2026, das 19:42 às 21:02 (horário de Brasília): 182 experimentos, todos completos, a um custo de US$ 0,886. Respostas sem posição válida ficaram fora, sem imputação: 20 no B3T e 22 no B3R, de 455 esperadas em cada.

## 3. Resultados

### 3.1 H1: texto corrido × estruturado

| | B3R (estruturado) | B3T (texto corrido) | Diferença B3T − B3R | McNemar p |
|---|---|---|---|---|
| Combinado (H1) | 3,9% [2,3; 5,8] | 10,3% [7,5; 13,3] | 6,5 [3,7; 9,3] | 6,2 × 10⁻⁵ |
| MMLU-Pro | 4,5% [2,4; 7,1] | 13,6% [9,9; 17,4] | 9,2 [5,5; 12,9] | 6,9 × 10⁻⁵ |
| Banco novo | 2,7% [0,7; 5,5] | 4,1% [1,3; 8,1] | 1,4 [−2,0; 4,7] | 0,69 |

A H1 se confirma. Com o mesmo conteúdo, os modelos mudaram de opção cerca de 2,6 vezes mais quando a resposta anterior veio em texto corrido. A leitura "estrita" (mudou sem fundamento novo) dá números iguais ou quase iguais (`resultados.md`).

### 3.2 H2: a ordem das quatro condições

| Condição | Mudou de opção |
|---|---|
| B3 (11/11) | 2,1% [0,9; 3,5] |
| B3R (12/11) | 3,9% [2,3; 5,8] |
| B3T | 10,3% [7,5; 13,3] |
| B3L (só a letra) | 16,3% [12,8; 19,9] |

A ordem esperada (B3R ≤ B3T ≤ B3L) se confirmou. O texto corrido fica entre o estruturado e a letra sozinha. O B3R ficou um pouco acima do B3 original, com os ICs sobrepostos. Pode ser deriva de um dia para o outro, e é por isso que a comparação confirmatória usa o B3R.

### 3.3 H3: o que as mudanças fizeram

Nas perguntas com gabarito, os dois bancos juntos:

| Condição | Errado → certo | Certo → errado | Errado → outro errado | Pares |
|---|---|---|---|---|
| B3 | 5 | 3 | 1 | 333 |
| B3R | 9 | 4 | 4 | 339 |
| B3T | 14 | 8 | 20 | 341 |
| B3L | 26 | 13 | 19 | 314 |

O B3T mudou mais, mas a maior parte do excesso foi troca de um erro por outro (20, contra 4 no B3R). O saldo de correção (errado → certo menos certo → errado) foi +6 no B3T e +5 no B3R. O formato estruturado não reduziu a correção: reduziu as trocas sem ganho.

### 3.4 Acerto final (exploratório, pós-hoc)

Esta análise não estava no registro; ela foi feita depois de ver os dados (`desvios.md`). Nas perguntas com gabarito, o acerto final foi 53,8% no B3T (184/342) e 53,3% no B3R (180/338). Em pares: 12 vezes o B3T acertou e o B3R errou, 11 vezes o contrário (McNemar p = 1,0). Nenhuma diferença de acerto entre os formatos.

## 4. Ressalvas

- **O texto corrido vem de uma resposta estruturada.** O B1 foi produzido sob a instrução do formato estruturado. O B3T é a mesma resposta sem a estrutura, não uma resposta escrita livremente desde o início. Um B1 em texto livre seria uma segunda etapa, com registro próprio.
- **O efeito está no MMLU-Pro.** No banco novo quase ninguém muda em nenhuma condição, e o estudo não tem poder para ver diferença ali.
- **O B3L é de outro dia e é exploratório.** Entra só como referência descritiva.
- **O MMLU-Pro tem perguntas com chave discutível** (texto 2, seção 4.1). Isso afeta a H3 (o que conta como certo), não a H1, que mede mudança e não acerto.
- **Coleta antes da aprovação do registro.** O registro foi enviado às 17:08 de 12/11. A coleta começou às 19:42, enquanto o OSF ainda aguardava a aprovação automática. O conteúdo registrado não muda com ela.
- **Um painel, dois bancos, um dia.** Os resultados valem para este painel.

## 5. Discussão

A ancoragem quase total do B3 não vem só de o modelo ver o próprio raciocínio. Uma parte importante vem do formato: com o mesmo conteúdo, a apresentação em itens e relações estruturados reduziu a mudança de opção de 10,3% para 3,9%. O formato responde por quase metade da distância entre o B3 e o B3L (6,4 de 14,2 pontos).

A H3 mostra que essa estabilidade não teve custo de correção. O que o formato estruturado cortou foi, em grande parte, a troca de um erro por outro, uma mudança que não melhora a resposta. Para sistemas em que um modelo revisa o próprio trabalho em várias etapas, isso sugere que a forma de guardar e devolver a resposta anterior é uma escolha de projeto com efeito medido, e não só uma questão de apresentação.

O resultado não diz que o formato estruturado torna o modelo mais correto. O acerto final foi igual nos dois formatos (seção 3.4). O ganho é de consistência.

## Declaração de interesse

O formato estruturado usado nas condições B3 e B3R foi desenvolvido pelo autor em software próprio. O código que gera as condições (B3, B3T e B3R) está público no repositório indicado abaixo, e a descrição da seção 2 basta para reproduzi-las.

## Referências

- Guedes, E. (2026). Δ_herd: efeito manada num painel heterogêneo de LLMs (texto 1). OSF gbx5m; registros aw9vf e 5dpjr.
- Guedes, E. (2026). Quantos modelos valem cinco? (texto 2). OSF gbx5m.
- Hao et al. (2026). arXiv 2606.00820.

## Código e dados

- Pré-registro: `studies/formato/preregistration-en.md` (OSF gzvk5, registro 46erj).
- Coleta: `studies/formato/coleta.py`. Medidas: `studies/formato/medidas.py`, escrito antes da coleta.
- Exposição `self_text`: Lab PR #26 e #27. Repositório: https://github.com/edubrinck86-code/Norvald-Lab
