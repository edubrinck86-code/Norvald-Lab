---
id: TESE-003
type: Posicionamento
status: Vigente
version: 2.0.0
references:
  - docs/tese/01_Protocolo_Experimental.md
  - docs/tese/02_Mapa_de_Teste.md
  - docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
  - docs/analise/Analise_Critica_da_Tese.md
---

# Posicionamento da contribuição e procedência do CC

Duas coisas que faltavam para a tese ser defensável: onde ela se encaixa na literatura que existe hoje, e de onde veio a fórmula que ela examina.

## 1. Onde `N_eff` se aplica — e onde não

Delimitação necessária, porque a confusão inverte a conclusão.

`N_eff` só entra quando **N execuções respondem à mesma pergunta e o resultado vira uma conclusão**. É desconto sobre observação redundante agregada, não sobre trabalho paralelo.

**Não se aplica:** frota de agentes executando tarefas distintas em paralelo. Ali o número é vazão. Cortar pela metade corta o trabalho feito, não a redundância.

**Aplica-se, e em escala de produção:**

| Técnica | Estrutura |
|---|---|
| Self-consistency | k amostras do mesmo modelo, voto na maioria |
| LLM-as-judge em painel | vários modelos avaliando a mesma saída |
| Best-of-n / rejection sampling | n amostras pontuadas, uma escolhida |

Nas três, amostras correlacionadas viram uma conclusão. A literatura descreve retorno decrescente em self-consistency como "acurácia satura"; `N_eff` diz **quanto** vale, não só que satura. É a diferença entre observação descritiva e quantidade acionável — e incide sobre linha de custo de inferência.

## 2. A conclusão econômica não é "use menos"

É **"use diferentes"**.

Se `N_eff` é baixo porque os modelos são correlacionados, reduzir o painel não recupera informação — só economiza em observação que já não valia. Aumentar diversidade de família e provider é a intervenção candidata a elevar `N_eff`.

    8 modelos da mesma família  <  3 de famílias diferentes

Recomendação de composição, não de tamanho. Vale para o Studio e para qualquer ensemble.

**O teto não depende do tamanho.** `N_eff → 1/ρ̄` quando *n* cresce: com ρ̄ = 0,5, nenhum painel supera duas observações efetivas, e ir de 8 para 16 modelos move `N_eff` de 1,78 para 1,88. É aqui que a recomendação deixa de ser preferência e vira aritmética — o gasto marginal em painel maior compra uma fração decrescente de observação, e o limite é fixado pela dependência, não pelo orçamento.

### 2.1 Medido aqui, não herdado

A desigualdade acima vinha da teoria e de Kim (§3). O desenho original usava uma única composição de painel e portanto **não testava a própria recomendação central**.

`TESE-002` §2.2 acrescenta o painel de contraste — quatro modelos da mesma família, mesma classe, apenas em condição cega — e com ele a comparação vira resultado:

```
ρ̄_erro(heterogêneo)  vs  ρ̄_erro(homogêneo)   →  N_eff(4) nos dois
```

Custo marginal de meio dólar. Sem esse braço, a seção continuaria sendo citação com aparência de achado; com ele, a conclusão econômica passa a ter medida e magnitude próprias.

Resultado negativo também decide algo: se `ρ̄` mal se mover entre os dois painéis, diversidade de família não compra o que se supõe, e a intervenção teria de ser buscada fora do eixo de família — em prompt, em decomposição de tarefa, ou em fonte de evidência.

## 3. Quem estrutura confiança composta hoje

Levantamento de 27/09/2026. Resumos lidos das versões HTML; conferir autores, venue e números na fonte antes de citar.

**Elahi & Di Eugenio (UIC) — "Confidence Composition for Multiagent Language Model Systems"** · [arXiv 2606.13591](https://arxiv.org/html/2606.13591)

Três protocolos agregando confiança entre agentes e estágios: voto ponderado por stream, gating com fusão bayesiana `c₁c₂/[c₁c₂+(1−c₁)(1−c₂)]`, e roteamento por acordo/limiar. **Assume independência condicional e registra que a suposição é violada nos próprios resultados**, seguindo adiante mesmo assim. Não usa tamanho amostral efetivo nem design effect.

É o alvo direto desta tese: composição de confiança que sabe da dependência e não tem mecanismo para descontá-la.

**Donghwan Kim (Aidentyx) — "Are Diversity Metrics Measuring Diversity?"** · [arXiv 2607.20768](https://arxiv.org/html/2607.20768v1) · jul/2026

Auditoria controlada por capacidade sobre 31.900 subconjuntos de 30 LLMs em MMLU-Pro, replicada em TruthfulQA. Achados:

- voto majoritário supera o melhor membro em apenas **9,98%** dos ensembles de tamanho 3;
- "strict diversity" tem correlação **0,991** com o inverso da acurácia média — as métricas de diversidade são emaranhadas com capacidade;
- cita que erros de LLM são fortemente correlacionados e que modelos mais acertivos tendem a ser **mais** correlacionados.

Dupla relevância: é evidência publicada de que a premissa desta tese se sustenta, e é a justificativa citável para manter os quatro modelos do painel na mesma classe de tamanho. Sem controlar capacidade, mede-se capacidade acreditando medir diversidade.

**Bo Jiang (Temple) — DiscoUQ** · [arXiv 2603.20975](https://arxiv.org/html/2603.20975) · mar/2026

Quantificação de incerteza a partir da estrutura da discordância em ensembles de agentes: features linguísticas extraídas por LLM e geometria de embeddings, AUROC ~0,80. Não modela dependência entre agentes nem usa `N_eff`.

É o vizinho mais próximo em espírito e o oposto em método — usa juiz semântico, que é o que o desenho desta tese evita. Diferenciar explicitamente no texto.

**Huang, Wu & Wang — "How Many Human Survey Respondents is a Large Language Model Worth?"** · [arXiv 2502.17773](https://arxiv.org/html/2502.17773v4) · atualizado ago/2026

Calcula tamanho amostral humano efetivo para simulação por LLM. O enquadramento existe — mas para substituição LLM↔humano, e **sem tratar correlação entre respostas de LLM**.

Precedente do enquadramento; delimita a novidade.

**Guneet Kohli — "Nine Judges, Two Effective Votes: Correlated Errors Undermine LLM Evaluation Panels"** · [arXiv 2605.29800](https://arxiv.org/abs/2605.29800) · mai/2026

Nove LLMs de sete famílias em NLI sobre ChaosNLI. Constrói vetor binário de erro por juiz (`e_j,i = 1` se discorda do rótulo majoritário), tira φ̄ sobre os 36 pares e aplica **Kish effective sample size**: nove juízes valem ≈ 2,18 votos independentes. Reporta n_eff por condição para variação de prompt, ordenação de rótulo, **temperatura** (1,94 a 2,18) e **chain-of-thought** (φ̄ = 0,456, n_eff = 1,94 — CoT *aumenta* a correlação).

**Os nove juízes não se veem.** Temperatura 0.0, prompt padronizado, sem comunicação nem refinamento iterativo. Não há condição de exposição.

É o precedente direto, e o trabalho contra o qual esta tese precisa ser lida.

### A lacuna, com precisão

```
erro correlacionado entre LLMs documentado       sim, com dado em escala
composição de confiança multiagente              sim, assumindo independência violada
tamanho amostral efetivo envolvendo LLM          sim, LLM↔humano, sem correlação
ESS para painel de LLM correlacionado            sim — Kohli 2026, em painel ISOLADO
ESS sob exposição entre participantes            não encontrado
```

A contribuição não é aplicar tamanho amostral efetivo a painel de LLM: Kohli já faz isso, com número. Também não é medir efeito manada, que tem literatura própria — Hao et al. decompõem conformidade por condições contrafactuais controladas, ainda que sem calcular ESS.

O que está aberto é a interseção: **o que a exposição entre participantes faz com o tamanho amostral efetivo**. Kohli mede uma propriedade estática de um painel que nunca interage; esta tese mede o efeito de um tratamento sobre essa propriedade.

    Kohli estabelece o piso em painéis isolados.
    Esta tese mede o que a exposição faz a esse piso.

O enquadramento inverso — "mais abrangente que Kohli" — é insustentável e não deve ser usado. Painel isolado é o caso dominante da prática (self-consistency, best-of-n, LLM-as-judge, ensemble); exposição é subconjunto, e menor. A tese é mais estreita, e é isso que a torna defensável.

## 4. Procedência do CC

`CC = 0.30·E + 0.25·R + 0.20·C_adj + 0.15·I + 0.10·H`

Três camadas com origens diferentes, e é preciso declarar as três.

**A forma é genérica.** Índice composto linear ponderado, componentes normalizados, pesos somando 1. É o formato padrão de índice composto — escore de crédito, índice de risco, rubrica, indicador de desenvolvimento. Não é específico de confiança em LLM nem é interpretação de algum modelo de CC da área.

**A decomposição é própria.** `E`, `R`, `C_adj`, `I`, `H` como cinco componentes não foi encontrado em literatura. O trabalho mais próximo (Elahi & Di Eugenio) tem estrutura completamente diferente.

**Os pesos vieram de elicitação, não de calibração.** O CC foi formulado em CDD-017 — deliberação com 12 especialistas LLM no próprio Studio. Nunca foram ajustados contra dado.

### Isso é um problema? Não, se for declarado

Peso elicitado por especialista é método padrão em índice composto: IDH, índices de sustentabilidade, escores clínicos de risco. O que a prática exige não é que o peso seja derivado — é que a elicitação seja **descrita** e que haja **análise de sensibilidade** sobre os pesos.

A elicitação aqui está documentada com precisão incomum: painel identificado, rodadas registradas, tudo auditável. A sensibilidade usa o mesmo instrumento já previsto para `ρ̄`.

Feito isso, o CC deixa de ser fórmula indefensável e vira **índice composto com pesos elicitados, elicitação declarada e sensibilidade reportada** — objeto padrão.

### A ironia, que entra no texto

O CC é um espécime do fenômeno que esta tese mede.

Doze especialistas LLM, treinados sobre literatura que contém milhares de índices compostos ponderados, convergiram para um índice composto ponderado com escada de pesos arredondada. A concordância entre eles provavelmente não representou doze julgamentos independentes.

> A própria fórmula que este trabalho examina foi produzida por um painel cuja independência este trabalho questiona.

Não é fraqueza do trabalho — é a melhor ilustração dele, e é raro ter o instrumento e o objeto coincidindo com registro completo dos dois.

### O que fazer no texto

| Situação | Ação |
|---|---|
| Apresentar o CC | Como hipótese elicitada, com a procedência declarada — nunca como fórmula estabelecida |
| Os pesos | Declarar provisórios, reportar sensibilidade |
| A forma aditiva | Registrar a objeção da §47 e a alternativa multiplicativa |
| A contribuição | Desacoplada: o desconto por `N_eff` vale para qualquer agregação de observações correlacionadas, e sobrevive ao CC inteiro cair |

## 5. Como posicionar a contribuição em uma frase

> Trabalhos recentes compõem confiança em sistemas multiagente assumindo independência condicional que eles próprios reportam violada, e auditorias em escala mostram que erros de LLM são fortemente correlacionados. Este trabalho mede a dependência manifesta num sistema deliberativo real, por definições estruturais que dispensam juiz semântico, e a converte em desconto sobre o tamanho amostral efetivo do painel.
