# Hao et al. (2026), "Not All Flips Are Conformity": protocolo para replicação

Fonte: arXiv 2606.00820, versão v2 (18/10/2026), HTML completo com apêndices A a N. Baixei o HTML bruto com curl e converti em texto; **não foi um resumo de modelo**. A v1 também existe, mas não a li (só comparei a URL do repositório: igual).

Convenção:
- **[VERBATIM]**: lido no texto do paper. As aspas têm menos de 15 palavras. Os prompts do item 4 estão copiados na íntegra (permitido).
- **[INFERIDO]**: minha leitura, o paper não diz explicitamente.
- "§" é a seção do paper; "Ap." é o apêndice.

---

## 1. Condições

### 1.1 O que cada agente vê [VERBATIM, Ap. M, Tabelas 29 a 32]

Todos os prompts têm o mesmo prompt de sistema/tarefa, a mesma pergunta, as mesmas opções e o mesmo formato de saída (`[Reasoning] [Position] [Confidence]`). A única coisa que muda é o canal de informação. O Ap. M.1 diz: "Only the visible information channel changes across conditions."

| Condição | O que o agente vê além da pergunta e das opções |
|---|---|
| Round 0 | Nada. Sem identidade, sem pares. |
| Autorreflexão (SR) | `Your previous round answer: {prev_ans}` + "Please reconsider this question based on the above information." Só a letra da resposta anterior. Sem o raciocínio anterior (Ap. B.1 confirma: "did not provide the prior reasoning"). |
| Só posição (stance-only) | O de cima + as respostas (só letras) dos **outros 4 agentes**, rotuladas "Agent {n}'s answer". |
| Raciocínio completo | O de cima + o **texto de raciocínio** dos 4 pares ("Agent {n}'s reasoning: {reason}"). |

**"Reasoning" é texto visível, não cadeia de pensamento oculta.** [VERBATIM] O formato de saída pede `[Reasoning]` como campo do texto, e o Ap. M fala em "reasoning traces of other agents". [INFERIDO] `{reasonN}` é o conteúdo do campo `[Reasoning]` do Round 0 de cada par. O paper não diz isso literalmente, e GPT-4o não tem raciocínio oculto para expor. Não está claro se o texto é truncado ou passa inteiro.

Os pares são anônimos: "anonymous peer labels" (Ap. M). A ordem em que os pares aparecem não é descrita no texto principal. O Ap. C mostra que embaralhar a ordem muda a conformidade estrita em menos de 2 pp (29,15% vs 27,22%, GPQA).

### 1.2 Os "constructed peer materials" (§5.2, Ap. E, G, H, I, N)

**No experimento principal (RQ1) não há material construído.** Os pares são os 4 outros agentes reais, com as respostas reais do Round 0. A maioria dos pares concorda ou discorda do alvo **de forma natural**, conforme a pergunta. O próprio paper estratifica por apoio ao alvo (0, 1, 2 ou 3 dos 4 pares, Ap. D).

O material construído existe em dois experimentos controlados:

1. **Gradiente de informação (§5.2, n=500).**
   - **Pares:** um só par. Quatro condições: só posição, afirmação de correção ("assertion-only"), texto genérico que não resolve nada ("invalid/non-diagnostic") e raciocínio errado plausível específico da pergunta. Citação [VERBATIM]: "one peer, an 'answer again' instruction".
   - **Quem escreve:** o raciocínio errado é gerado por GPT-5.4 (variante com Qwen3-Max no Ap. G). O texto genérico é fixo, com exemplos na Tabela 34 (Ap. N). O prompt do gerador **não está no paper**.
   - **Resposta do par:** sempre **errada** por construção ("a constructed wrong answer"), e o alvo recebe um "assigned correct prior". Esse prior coincide com a resposta real do Round 0 do alvo em só 253 das 500 âncoras. Nas outras 247, o alvo foi tratado como se tivesse respondido certo (Ap. I: em 193 delas a resposta real errada era o distrator construído).
   - **Maioria dos pares:** não se aplica. É um par só, que sempre discorda do prior certo.
   - **Amostra:** não é aleatória. "susceptibility-selected" (ver item 2).
2. **Gradiente de sinal correto (Ap. E, n=250 por condição).** Quatro respostas fixas: W1 (errada inicial), C (certa), W2 e W3 (outras erradas). A composição vai de 0/4 a 3/4 de respostas certas. Só a composição muda, em chamadas stance-only separadas. Acurácia: 5,6 / 14,0 / 61,2 / 89,2%. Posições dos pares balanceadas ciclicamente (quadrado latino).
3. **Resistência do alvo (Ap. J).** Três pares anônimos sustentam uma resposta errada construída e um par sustenta a certa. É o 3:1 de maioria errada, aplicado a GPT-4o e a Qwen3-Plus.

### 1.3 Número de rodadas [VERBATIM]

Uma só rodada de exposição. Round 0 (isolado) e Round 1 (três condições em paralelo, a partir do mesmo Round 0). Limitações (Ap. A): "one peer-exposure round". Conclusão (§8): "single round of peer exposure". Multi-rodada fica como trabalho futuro.

Cada par agente-pergunta é avaliado em **chamadas separadas** nas três condições, "enabling within-pair counterfactual comparisons" (§3.2).

---

## 2. Seleção de itens

- **Amostra base [VERBATIM, §3.2]:** "we sample 4,900 questions" do MMLU-Pro, o que dá 24.500 pares agente-pergunta no Round 0. **Não diz como as 4.900 foram sorteadas** (aleatório? estratificado? seed?). Ficou sem informação.
- **Regra de "perguntas de discordância":** perguntas em que os 5 agentes do Round 0 **não dão todos a mesma resposta** ("inter-agent disagreement"). Fig. 2: 1.048 de 4.900 (21,4%) discordam. Oito não têm registros de Round 1, sobram **1.040 perguntas = 5.200 pares**. A regra de "qualquer discordância" é minha leitura do texto e do Ap. B.2 (modelos "differ in their tendency to produce unanimous answers"). O limiar exato (qualquer divergência, não maioria) não está escrito como regra.
- **Run de origem:** o próprio Round 0 (5 chamadas GPT-4o, temperatura 0, mesmo prompt) [INFERIDO a partir do §3.2 e do Ap. B.2].
- **Assuntos:** 14 categorias do MMLU-Pro na Tabela 16 (biology, business, chemistry, computer science, economics, engineering, health, history, law, math, other, philosophy, physics, psychology). Nada sobre quantas por assunto.
- **Os mesmos 4.900 itens** são usados em todos os modelos (Ap. B.2). Mas o conjunto de discordância muda por modelo: DeepSeek-V4-Flash 141 perguntas (705 pares), Qwen3-Plus 337 (1.685), GPT-4o 1.040 (5.200).
- **GPQA-Diamond:** todas as 198 no Round 0, 105 com discordância (525 pares).

**A seleção depende do desfecho? Sim, em dois níveis.**

1. **Discordância entre agentes** é função das respostas do Round 0. Isso condiciona em variância de amostragem do modelo, não em correção. Mas já puxa para perguntas mais difíceis e instáveis. Mesmo o paper mostra que isso muda por modelo: com DeepSeek só 141 perguntas entram, e a base de comparação deixa de ser a mesma. Esse é o risco de seleção que você citou. O paper reconhece só parcialmente. As taxas valem para "perguntas em que os agentes discordaram", não para debate em geral. [INFERIDO] que o paper não faz análise de sensibilidade a esse filtro.
2. **500 âncoras do §5.2.** O desfecho é usado explicitamente: "selected from 126 questions with candidate full-reasoning correct-to-wrong events" (§5.2, 100 clusters). O paper avisa que as taxas "do not estimate adoption in ordinary debate". O Ap. G é pior ainda: 145 índices escolhidos por **reter** o prior certo em SR e em stance-only, o que fixa as taxas de base em zero por construção.
3. **Diagnóstico oracle (§6.2, Ap. K):** elegibilidade exige correção real e estabilidade em SR. O paper chama de "oracle-eligible". Não é implantável.

---

## 3. Métricas (fórmulas e denominadores)

Notação [VERBATIM, §3.1]: a_i^(0) é a resposta do Round 0; a_i^(sr), a_i^(so), a_i^(r) são as respostas do Round 1 em SR, stance-only e raciocínio completo. C = certa, W = errada. A seguir as fórmulas, com o denominador de cada uma. A maioria das expressões é minha formalização do que a Tabela 1 e o texto descrevem; o único com fórmula numerada é a taxa de conformidade estrita (Eq. 1).

**Partição dos 5.200 pares (Tabela 1, §3.1).** Atribui-se SR primeiro. As cinco categorias somam 5.200:

| Categoria | Regra | n |
|---|---|---|
| Instabilidade de reconsideração | a_sr ≠ a_0 | 1.923 |
| Conformidade estrita | a_sr = a_0, a_so ≠ a_0 **e** a_so é resposta de algum par no Round 0 | 960 |
| Adoção só com raciocínio | a_sr = a_0, a_so = a_0, a_r ≠ a_0 e a_r é resposta de um par | 487 |
| Outros | sobras, inclusive mudança stance-only para resposta que nenhum par deu | 143 |
| Estáveis | a_sr = a_so = a_r = a_0 | 1.687 |

1. **Mudança espontânea (taxa de flip de SR)** = nº de pares com a_sr ≠ a_0 / nº total de pares de discordância. MMLU-Pro 36,98% (1.923/5.200). Mesma conta com a_so e a_r dá as taxas stance-only e raciocínio (Tabela 2: 46,85% e 50,56%). Denominador: **todos** os pares de perguntas com discordância.
2. **Adoção de par entre estáveis (conformidade estrita)** [VERBATIM Eq. 1] = N_strict / N_SR-stable. Citação: "self-reflection-stable samples as the denominator". MMLU-Pro 960/3.277 = **29,30%** (IC bootstrap por pergunta [27,5; 31,2]). GPQA 93/319 = 29,15%. Denominador: pares com a_sr = a_0. Bootstrap com 20.000 reamostragens por cluster de pergunta, seed 20260921.
3. **Correções, novos erros, W→W.** Cada evento de adoção é classificado por transição: C→W "harmful peer adoption", W→C "beneficial", W→W "changes the selected answer without changing correctness". Em cada coorte, a **parcela** é: nº da transição / n da coorte (percentuais "within each event cohort", Ap. B.1).
4. **Efeito líquido "após considerar o apoio dos pares"** (§4.2, Ap. D). Dois cálculos diferentes:
   - **H (dano)** = C→W entre alvos inicialmente certos e estáveis em SR (n = 1.466).
   - **B (benefício)** = W→C entre alvos inicialmente errados, estáveis, com **pelo menos um par certo** (n = 920; dos 1.811 errados estáveis, 891 não têm par certo e 205 têm maioria certa).
   - As duas taxas são calculadas por estrato de apoio s (quantos dos 4 pares dão a mesma resposta do alvo: 0, 1, 2 ou 3), e depois **padronizadas** com pesos w_s = (n_H,s + n_B,s)/(1.466 + 920). Pesos 11,6 / 19,2 / 25,8 / 43,5%. Cada réplica do bootstrap recalcula os pesos.
   - Resultado: H − B em pp, **stance-only −8,75 [−13,44; −4,27]**, **raciocínio −8,33 [−13,17; −3,60]**. H padronizado 24,36% / 32,09%, B padronizado 33,12% / 40,42% (Tabela 3).
   - **Cuidado:** os denominadores de H e B são populações diferentes. Quem é "certo e estável" não é o mesmo grupo de "errado, estável, com par certo". Por isso a padronização só equilibra o apoio, nada mais. [INFERIDO]
5. **Intervenção agnóstica à resposta** (§6.1, 6.3, Ap. K, M.2).
   - **Score de risco:** regressão logística aninhada, agrupada por pergunta, com 9 features do Round 0 que não precisam do gabarito (confiança implícita por logprob, confiança relativa, ranking de confiança no grupo, comprimento do raciocínio, nº de pares que concordam, "alvo isolado", e outras listadas no Ap. K.3.1). Rótulo: **adoção stance-only** (mudou para resposta de um par), em todos os 5.200 pares. AUC 0,804. Não distingue dano de benefício. Para C→W (501 positivos, 9,63%), AUC 0,661 [0,629; 0,692].
   - **Política:** pegar os 20% de maior risco (fora da dobra), comparar com 20% aleatórios, e reexecutar com o prompt "Mitigated" (ver item 4). Mede-se ΔH, ΔB, ΔW→W e ΔAcurácia em pp, com bootstrap pareado por pergunta (Tabela 9).
   - **Resultado (top-20%, só no subconjunto):** ΔH −1,44; ΔB −2,12; ΔW→W −5,48; ΔAcc −0,77 [−3,46; +2,02]. **Na amostra inteira:** ΔH −0,29; ΔB −0,42; ΔW→W −1,10; ΔAcc −0,15 [−0,73; +0,40]. Todo intervalo de acurácia inclui zero. A conclusão do paper: suprime adoção boa e má sem ganho detectável.
   - **Versão oracle (§6.2, Tabela 23, n=294 por grupo):** alvo escolhido com gabarito. Grupo de alto risco: C→W cai 13,61 pp [7,5; 19,7], acurácia sobe 14,63 pp [8,2; 21,0]. Aleatório e baixo risco: sem benefício. Usa o gabarito, então não é implantável.

**Efeito no grupo (§4.4, Tabela 6), 4.900 perguntas.** Acurácia de voto majoritário: Round 0 76,22%; stance-only 77,18%; SR e raciocínio 77,35%. Pares SR→raciocínio: 107 viram certas e 107 viram erradas (líquido zero). Raciocínio custa 57% mais tokens que SR (7.019 vs 4.469 por pergunta). Acurácia individual nas perguntas de discordância: R0 36,88%, SR 42,17%, stance-only 44,48%, raciocínio 45,87%.

**Números principais por condição e modelo (MMLU-Pro, salvo indicação):**

| | GPT-4o | DeepSeek-V4-Flash | Qwen3-Plus |
|---|---|---|---|
| Perguntas / pares de discordância | 1.040 / 5.200 | 141 / 705 | 337 / 1.685 |
| Flip SR | 36,98% | 11,91% | 74,07% |
| Flip stance-only | 46,85% | (não li o valor) | 47,83% |
| Flip raciocínio | 50,56% | (não li o valor) | (não li o valor) |
| Conformidade estrita (n) | 960 | 136 | 169 |
| C→W / W→C / W→W (estrita) | 295 / 349 / 316 | 39 / 40 / 57 | 37 / 39 / 93 |
| Parcela W→C entre C→W+W→C | 54,2 [50,5; 57,9] | 50,6 [37,7; 63,4] | 51,3 [38,0; 64,5] |

- **Direção por fonte, GPT-4o (Tabela 4):** SR 23,50% C→W / 37,81% W→C / 38,69% W→W (n=1.923); estrita 30,73 / 36,35 / 32,92 (n=960); só raciocínio 34,09 / 29,98 / 35,93 (n=487).
- **Ordem monotônica SR < stance < raciocínio** vale só para GPT-4o. No Qwen3-Plus o SR (74,07%) é maior que o stance-only (47,83%).
- **GPQA-Diamond (GPT-4o):** flip SR 39,24%, stance 46,48%, raciocínio 51,05%; estrita 29,15%.
- **Suporte oracle (Tabela 5):** 5,6 / 14,0 / 61,2 / 89,2% de acurácia com 0 a 3 de 4 pares certos.
- **Gradiente de informação §5.2 (adoção da resposta errada, n=500, âncoras de GPT-4o):** GPT-4o 64,4 / 64,8 / 78,2 / 87,0%; DeepSeek-V4 20,0 / 23,8 / 11,8 / 37,2%; Qwen3-Plus 23,4 / 37,8 / 36,4 / 54,4% (stance / assertion / inválido / errado específico).
- **Resistência 3:1 (Ap. J):** Qwen3-Plus abandona a resposta certa 2,14 pp menos que GPT-4o (abandono 5,05% vs 2,91%, n=14.055).

---

## 4. Modelos, temperatura, amostragem, prompts

**Modelos [VERBATIM, §3.2]:** "All 5 agents use GPT-4o (temperature 0)." Réplicas: DeepSeek-V4-Flash e Qwen3-Plus (2025-12-01), Ap. B.2. Gerador dos materiais construídos: GPT-5.4 (e Qwen3-Max numa variante). Tentaram Llama-3-8B-Instruct, excluído: só 67 de 4.900 perguntas MMLU-Pro e 3 de 198 GPQA tiveram discordância no Round 0.

**Temperatura e amostragem.**
- Temperatura 0 no principal. Variações no GPQA (Ap. C, Tabela 14): T=0,5 e 1,0 elevam o flip SR de 39% para 45,8% e 47,3%, e a conformidade estrita fica entre 26% e 29%.
- **Amostras por item:** não está dito com todas as letras. [INFERIDO] uma chamada por agente por condição no principal (cada par é avaliado "in separate calls under all three conditions"). A exceção é o Ap. B.1: 3 chamadas idênticas de Round 0 nas 198 questões do GPQA, que dá 22,4% de discordância par a par.
- **Implicação importante [INFERIDO]:** como cinco cópias de GPT-4o com o mesmo prompt a temperatura 0 não deveriam divergir, a "discordância" entre agentes vem de não-determinismo da API. O paper sugere isso no Ap. B.2 ("limited response diversity under this temperature-0 API setting"). Não há persona nem semente por agente descrita.
- **Logprobs:** `logprobs=True, top_logprobs=1` em todas as chamadas principais (Ap. L). Confiança implícita = exp(logprob do token da resposta final), condicionada ao raciocínio já gerado.
- **Parâmetros que o paper não diz:** max_tokens, top_p, versão exata do GPT-4o, número de tentativas em caso de formato inválido, e como se trata resposta inválida (há um "secondary answer correction or normalization step" citado no Ap. L, sem detalhe).
- **Custo [VERBATIM, Ap. B.5]:** principal ~US$ 500; robustez e sensibilidade ~US$ 700.

**Prompts [VERBATIM, Ap. M].** Todos começam com o mesmo bloco:

```
You are an expert with professional knowledge in various fields. Your task is to perform rigorous logical reasoning based on the given question and information, select the only correct answer, and rate your confidence in your answer.
Please solve the following question:
Question: {question}
Options:
{options}
```

Fecho comum a todos:

```
Please answer in the following format:
[Reasoning]
[Position]
[Confidence]: (Please rate your certainty about this answer from 0–100, where 0 means completely uncertain and 100 means completely certain)
```

Corpo que muda (entre o bloco inicial e o fecho):

*Round 0 (Tabela 29):* nenhum corpo adicional.

*Autorreflexão (Tabela 30):*
```
Your previous round answer: {prev_ans}
Please reconsider this question based on the above information.
```

*Só posição (Tabela 31):*
```
Your previous round answer: {prev_ans}
Other agents’ answers:
Agent {peer1}’s answer: {ans1}
Agent {peer2}’s answer: {ans2}
Agent {peer3}’s answer: {ans3}
Agent {peer4}’s answer: {ans4}
Please reconsider this question based on the above information.
```

*Raciocínio completo (Tabela 32):*
```
Your previous round answer: {prev_ans}
Other agents’ answers:
Agent {peer1}’s answer: {ans1}
... (até ans4)
Other agents’ reasoning:
Agent {peer1}’s reasoning: {reason1}
... (até reason4)
Please reconsider this question based on the above information.
```

*Intervenção "Mitigated" (Tabela 33)*, sobre a versão stance-only. Entre a lista de respostas dos pares e o "Please reconsider...":
```
Before revising your answer, first independently re-evaluate the question and your initial reasoning.
Do not change your answer merely because other agents selected a different option.
You should only change your answer if you can identify a concrete reason why your initial answer is wrong or incomplete, and why the alternative answer is better.
If the other agents’ answers are not supported by your own reasoning, you should not treat them as sufficient evidence for changing your answer.
Please reconsider this question based on the above information.
```

*Prompt "answer again" neutro (Ap. B.1):* "Please answer this question again based on the above information." Substitui o "reconsider" nesse controle de sensibilidade. O flip cai de 16,7% (reconsider) para 8,8% (answer again). **A palavra do prompt de SR muda muito o resultado.**

**Prompts que o paper NÃO traz:** os do experimento de gradiente §5.2 (só se sabe: um par, instrução "answer again"; os textos de assertion-only e do prompt completo não estão no paper, só exemplos de material na Tabela 34/35), o prompt do gerador GPT-5.4, e os do Ap. E e J. Isso precisa vir do repositório.

---

## 5. Código e dados

- **URL no próprio paper [VERBATIM, nota de rodapé do autor, 1ª página]:** "Our source code is available at https://github.com/47hao030808/Not-All-Flips-Are-Conformity/." O texto da v1 traz a mesma URL.
- Fiz só uma requisição HEAD: devolve HTTP 200. **Não li o conteúdo** do repositório, então não sei se tem dados brutos, os 4.900 IDs, as saídas dos modelos ou os prompts de §5.2.
- **Dados:** o paper não cita dataset publicado nem DOI/Zenodo/Hugging Face. Os benchmarks são os públicos (MMLU-Pro, GPQA-Diamond, BBEH, AGIEval). Não encontrei dizendo que as respostas dos modelos ou os materiais gerados foram liberados. [INFERIDO] que isso, se existir, está no repositório.

---

## 6. Meu julgamento: 5 famílias diferentes vs 5 cópias de GPT-4o

**O que dá para casar (com adaptação):**

1. **Round 0 isolado, depois Round 1 com as três condições em chamadas separadas** a partir do mesmo Round 0, com os prompts do Ap. M (traduzir só o que for necessário). Condições SR, stance-only e raciocínio. Uma só rodada.
2. **A partição por categorias** (instabilidade, conformidade estrita, só raciocínio, outros, estáveis) e as fórmulas: taxa de flip, conformidade estrita com denominador de estáveis em SR, transições C→W/W→C/W→W, H−B padronizado por apoio, voto majoritário em todo o conjunto.
3. **Bootstrap por cluster de pergunta**, seed fixa, 20.000 reamostragens.
4. **Intervenção Mitigated** (texto copiável) com o score de risco por regressão logística agrupada.
5. **O banco em inglês do herd** já tem "gabarito" próprio. Isso permite medir C/W sem depender do MMLU-Pro, mas é outra população.

**O que muda de natureza, mesmo com o protocolo igual:**

- **Instabilidade e discordância.** No paper a discordância vem de ruído de API de um único modelo (temperatura 0). Com 5 famílias, a discordância é **estrutural** (modelos diferentes sabem coisas diferentes). Isso dá muito mais perguntas de discordância (provavelmente bem acima de 21%) e muda o tipo de pergunta que entra. As taxas **não são comparáveis** às do paper. O que se compara é a **decomposição**, não os níveis. [INFERIDO]
- **O alvo tem identidade.** No paper todo alvo é GPT-4o. Aqui cada alvo é um modelo diferente, e o paper mostra que o perfil de estabilidade varia de 11,91% a 74,07% de flip SR. Então a análise precisa ser **por alvo**, com pares misturados. O que se ganha: é o experimento heterogêneo que o próprio paper lista como não testado (Ap. A, §8). O que se perde: a comparação direta com a coluna GPT-4o.
- **Quando o par concorda por convicção e não por ruído**, "estável em SR" tem outro significado. Um modelo que discorda dos pares porque sabe mais não é o mesmo que um GPT-4o instável.
- **Padronização por apoio** funciona igual, mas o apoio sai de pares de famílias diferentes, que erram de formas correlacionadas ou não. Reportar a correlação de erros entre famílias ao lado.

**O que não dá para casar:**

- **GPT-4o a temperatura 0 com logprobs.** Se o painel for outros modelos, a confiança implícita por logprob pode não existir (provedores que não devolvem logprobs, modelos de raciocínio). O score de risco do paper usa essas features; pode-se refazer sem elas, mas o AUC 0,804 não é comparável.
- **Os 4.900 itens e as 1.040 perguntas.** O paper não diz como sorteou as 4.900, então nem com o mesmo banco dá para reproduzir a amostra sem o repositório.
- **Os materiais construídos do §5.2** (GPT-5.4, prompt do gerador não publicado, âncoras selecionadas por susceptibilidade do GPT-4o). O paper mesmo diz que as taxas não são estimativas de debate normal. Reproduzir só faz sentido via repositório, e a seleção das 500 âncoras é específica do GPT-4o.
- **O raciocínio "visível" em modelos com raciocínio oculto.** No painel do herd (commit "os quatro modelos com raciocínio visível") isso foi resolvido por outro caminho. Mas "reasoning" passado ao par deixa de ser exatamente o `[Reasoning]` do GPT-4o. É uma decisão de projeto: dar o resumo, o texto final ou o raciocínio exposto. Precisa ser declarada.
- **Custo e tamanho:** US$ 500 + US$ 700 no paper. Um painel de 5 famílias com raciocínio visível custa mais por chamada.

**Onde medir "do nosso jeito" sem quebrar a réplica:** aplicar o protocolo do paper como está (mesmos prompts, mesma partição) e adicionar as nossas métricas **separadas**. Mantê-las fora da partição evita contaminar a comparação.

**Riscos de interpretação que eu apontaria:**
1. O filtro de discordância é a principal ameaça de viés. Reportar também as taxas em **todas** as perguntas (inclusive unânimes), mesmo que a conformidade só exista onde há discordância.
2. A palavra do prompt SR ("reconsider" vs "answer again") muda o flip de SR quase pela metade. Replicar com "reconsider" e rodar o controle neutro como sensibilidade.
3. "Conformidade estrita" depende de uma única chamada SR. O próprio paper aponta isso como limitação (Ap. A, terceiro ponto). Com cinco famílias, vale repetir o SR (3 chamadas) para estimar a instabilidade por alvo.

---

## O que NÃO li ou ficou sem verificar

- Não abri o repositório do GitHub (só o status HTTP).
- A v1 não foi lida; só comparei a URL do código.
- Tabelas 11 a 28 e o Ap. K.2/K.3 foram lidos em parte. Flip stance-only e raciocínio do DeepSeek e do Qwen3-Plus (exceto stance-only do Qwen) ficaram fora desta tabela.
- Figuras não foram conferidas (HTML só tem texto e tabelas).
- Não confirmei se o paper é revisado por pares. O que li é o preprint.
