---
id: DESK-05
tema: Observabilidade e estrutura do raciocínio — fundamentação do AROF
data: 2026-10-04
---

# Raciocínio como observável estrutural

A hipótese do AROF: observáveis **estruturais** do traço contêm informação sobre
**dependência de erro entre modelos**, e poderiam estimá-la sem gabarito.

**Resposta curta à pergunta "alguém já prediz co-falha entre modelos a partir de
observáveis de raciocínio?": não.** As duas metades existem separadas. O cruzamento é a
lacuna do AROF — e o fato de as duas metades estarem construídas por terceiros é bom:
a ponte tem pés, falta o vão.

## Os dois pés da ponte, no mesmo paper

### Lee, Queen & Zou (2026) — ReasonOps: Operator Segmentation for LLM Reasoning Traces
- [arXiv:2605.29192](https://arxiv.org/abs/2605.29192) · conferido (abs + HTML completo)
- Segmenta CoT em **7 operadores recorrentes** (backtracking, inferring, hypothesizing…)
  descobertos por clustering não-supervisionado. 44.662 traços, 12 LLMs, 6 famílias, 8 benchmarks
- **(a) Assinatura de modelo:** classificador sobre distribuições de operadores identifica o
  modelo-fonte com **macro-AUC 0,987** (acurácia 79,9%, acaso 8,3%); AUCs one-vs-rest
  0,967–0,997, **com os piores casos concentrados em pares intra-família** — a confusão
  residual é exatamente linhagem
- **(b) Predição de correção pelo processo:** WP-AUC **0,701 cross-dataset**, **0,801 em AIME**
- **(c) Baselines superficiais são quase acaso:** comprimento 0,551, contagem de "backtrack"
  0,594, contagem de "wait" 0,603
- **(d) SelfCheck (o modelo lendo o próprio traço) = WP-AUC 0,512, acaso.** Null result explícito
- **(e)** Predição precoce: 0,664 com 50% do traço; AIME 0,645 (10%) → 0,740 (50%) → 0,801 (100%)
- **(f)** O "committal-reflective gap" prediz correção com AUC 0,76 em problemas fáceis mas
  **cai para 0,48 em difíceis** — o sinal estrutural não é uniforme
- **Apoia, e é o paper base do AROF.** Prova as duas premissas separadamente e já usa o
  protocolo cross-dataset vs in-dataset. **O que não faz: cruzar as duas.** Nunca pergunta se
  a similaridade estrutural entre traços de modelos diferentes prediz erro *no mesmo item*

## O mais próximo conceitualmente

### Wawer & Chudziak (2026) — When AI Agents Disagree Like Humans
- [arXiv:2604.03796](https://arxiv.org/abs/2604.03796) · conferido
- Embeda traços de 5 agentes e classifica o par (similaridade de raciocínio × concordância de
  conclusão) numa **taxonomia de 4 estados**. Corpus Measuring Hate Speech
- *"raw reasoning divergence weakly predicts human annotator conflict, but the structure of
  agent discord carries additional signal"* — effect sizes grandes (d > 0,8) sobrevivendo a
  correção para múltiplas comparações
- **Meio apoio, meio ameaça.** Apoio: similaridade estrutural carrega informação além da
  concordância de resposta, e o *estado conjunto* é mais informativo que a magnitude. Ameaça:
  **a magnitude bruta da divergência prediz fraco** — se o AROF usar uma métrica escalar de
  similaridade de traço, provavelmente será fraca. Ressalva: o alvo é desacordo humano em
  tarefa normativa, não co-erro com gabarito

### Wawer & Chudziak (2026) — Consensus is Strategically Insufficient
- [arXiv:2606.04223](https://arxiv.org/abs/2606.04223) · conferido
- Formaliza a taxonomia numa camada simbólica de KR com roteamento derrotável. Sem resultado
  empírico novo
- **Vizinho forte** — é quase a arquitetura do Studio/CDD descrita por outros. Útil para
  ancorar vocabulário e não reinventar a taxonomia

## O concorrente mais sério

### Liu (2026) — LLMs as a Jury: Cross-Model Consensus Can Outperform Process Reward Models
- [arXiv:2607.10139](https://arxiv.org/abs/2607.10139) · conferido
- Consenso cross-model como sinal de verificação **sem gabarito**, contra self-consistency e
  4 verificadores treinados. 7 benchmarks
- Mecanismo explicitamente de **descorrelação de erro**. Deriva uma **lei em forma fechada,
  sem parâmetros**, que prediz a acurácia do consenso a partir de **três estatísticas
  mensuráveis do painel**, com erro absoluto médio de **0,03**. Expõe um **shared-error
  floor**: onde os modelos compartilham a mesma concepção errada, não funciona — piso quase
  zero em matemática, **não-trivial em ciências**
- **Apoia e é o concorrente direto.** Faz com respostas finais, barato, com teoria fechada.
  **O AROF precisa mostrar que observáveis estruturais ACRESCENTAM poder preditivo sobre esta
  baseline** — especialmente no regime onde a lei falha (o shared-error floor em ciências),
  que é onde um sinal de processo deveria valer mais. Tratar como baseline obrigatória, não
  como trabalho relacionado

## Estrutura do traço prediz erro — bem estabelecido

### Grünefeld et al. (2026) — Tracing Uncertainty in Language Model "Reasoning"
- [arXiv:2605.07776](https://arxiv.org/abs/2605.07776) · conferido
- **"uncertainty trace profile"**: poucas features descrevendo a *forma* do sinal de incerteza
  ao longo do traço. 5 LMs, GSM8K e ProntoQA
- **AUROC até 0,807**; **0,801 usando só as primeiras centenas de tokens**. Traços corretos
  mostram declínio de incerteza mais íngreme e menos linear
- **Apoia, e é o melhor molde metodológico** — conjunto pequeno e interpretável de features de
  forma, não conteúdo semântico. A extensão não feita: comparar perfis entre modelos

### Fang et al. (2026) — Playing Psychic: Thought Trees to Predict Reasoning Models Accuracy
- [arXiv:2604.16931](https://arxiv.org/abs/2604.16931) · conferido
- *"the structure of a reasoning trace, not just its contents, is a strong predictor of
  correctness"*. Ganhos consistentes **só em complexidade mais baixa** — ecoa o colapso do
  sinal em problemas difíceis do ReasonOps
- **Apoia quase literalmente**

### Tan, Tan, Lee & Kok (2025) — The Shape of Reasoning: Topological Analysis
- [arXiv:2510.20665](https://arxiv.org/abs/2510.20665) · conferido
- Topological data analysis vs. proxies baseadas em grafo
- Features topológicas rendem poder preditivo **substancialmente maior** que métricas de
  grafo; conjunto compacto e estável
- **Apoia, com advertência de desenho** — **grafos de raciocínio são explicitamente
  insuficientes.** Se o AROF planeja representar traços como grafos de passos, esta
  abstração perde informação

### Zhao et al. (2025) — Verifying CoT Reasoning via Its Computational Graph (CRV)
- [arXiv:2510.09312](https://arxiv.org/abs/2510.09312) · conferido
- Attribution graphs de passos de CoT como traços de execução de circuitos latentes
- (1) *"structural signatures of error are highly predictive"*; (2) as assinaturas são
  **altamente específicas de domínio**; (3) **não são meramente correlacionais** —
  intervenções dirigidas corrigem o raciocínio
- **Apoia no mecanismo, ameaça na transferência.** O (3) é evidência *causal*, e contorna a
  objeção de circularidade. O (2) é a ameaça: predição fora da amostra precisa ser
  **fora de domínio**, não só fora de item. Exige white-box — inviável em modelo fechado

### Zhou et al. (2025) — Landscape of Thoughts
- [arXiv:2503.22165](https://arxiv.org/abs/2503.22165) · conferido
- Estados textuais como features numéricas de distância a cada alternativa; t-SNE
- Distingue modelos fortes de fracos **e** corretos de incorretos; adaptável a verificador leve
- **Apoia, e é a única referência que mostra a mesma representação separando simultaneamente
  modelo e correção** — as duas dimensões que o AROF precisa cruzar. Código público

### Chen et al. (2025) — Do LLMs Signal When They're Right? Neuron Agreement
- [arXiv:2510.26277](https://arxiv.org/abs/2510.26277) · conferido
- Sinais externos são **projeções de baixa dimensão** de dinâmicas internas; respostas
  corretas ativam **substancialmente menos neurônios únicos**; **ativações de respostas
  corretas exibem concordância cross-sample mais forte, as incorretas divergem**. Predição nos
  primeiros 32 tokens, −99% de tokens
- **Apoia por caminho independente, com achado estruturalmente análogo** — concordância entre
  trajetórias prediz correção, só que entre amostras do mesmo modelo

### Wang et al. (2024) — Chain-of-Probe
- [arXiv:2406.16144](https://arxiv.org/abs/2406.16144) · conferido
- **Muitas respostas corretas contêm erros no processo de raciocínio**
- **Apoia no ponto que justifica o AROF** — se resultado correto não implica processo correto,
  avaliar pelo resultado é insuficiente

### Yu et al. (2025) — Explainable CoT: State-Aware Reasoning Dynamics
- [arXiv:2509.00190](https://arxiv.org/abs/2509.00190) · conferido
- Trajetórias como cadeia de Markov sobre estados latentes via análise espectral
- **Vizinho** — formalização útil, sem validação preditiva

## Fidelidade do CoT — a ameaça estrutural

**Este bloco pertence à seção de ameaças à validade do AROF, não a uma nota de rodapé.**

### Turpin, Michael, Perez & Bowman (2023) — Language Models Don't Always Say What They Think
- [arXiv:2305.04388](https://arxiv.org/abs/2305.04388) · conferido
- Explicações de CoT podem **sistematicamente deturpar** a razão real; modelos falham em
  mencionar o viés injetado e **racionalizam respostas incorretas**. Queda de acurácia de
  **até 36%** em 13 tarefas do BIG-Bench Hard
- **Ameaça.** Se o traço racionaliza em vez de computar, o observável pode medir *estilo de
  racionalização* em vez de estrutura de cálculo. Não mata o AROF — racionalização
  compartilhada também pode predizer co-falha — mas obriga a enunciar qual das duas está
  medindo, e a não alegar acesso ao cálculo real

### Lanham et al. (2023) — Measuring Faithfulness in Chain-of-Thought Reasoning
- [arXiv:2307.13702](https://arxiv.org/abs/2307.13702) · conferido
- Intervenção no CoT (erros, paráfrase, truncamento) para testar dependência causal
- **Grande variação entre tarefas**; **modelos maiores e mais capazes produzem raciocínio
  menos fiel na maioria das tarefas**
- **Ameaça, e define o escopo de validade.** O AROF pode funcionar onde o traço é fiel e
  degradar exatamente nos modelos de fronteira. **Recomendação: medir fidelidade por
  truncamento/corrupção como covariável e reportar estratificado.** Transforma a ameaça em
  eixo de análise

### Chen et al. (2025) — Reasoning Models Don't Always Say What They Think
- [arXiv:2505.05410](https://arxiv.org/abs/2505.05410) · conferido
- **Taxa de revelação de dica frequentemente abaixo de 20%**; RL de outcome melhora fidelidade
  mas **estabiliza sem saturar**; quando RL aumenta reward hacking, a propensão a verbalizar
  **não aumenta**
- **Ameaça, versão 2025.** E mecanismo plausível de **co-falha invisível no traço**: dois
  modelos podem ser puxados pela mesma dica implícita sem que nenhum traço registre. Nesse
  caso observáveis de traço **subestimam sistematicamente** a dependência

### Arcuschin et al. (2025) — CoT Reasoning In The Wild Is Not Always Faithful
- [arXiv:2503.08679](https://arxiv.org/abs/2503.08679) · conferido
- Infidelidade em prompts **naturais**, sem viés artificial. **Implicit Post-Hoc
  Rationalization** em até 13% em modelos de produção; fronteira muito melhor —
  DeepSeek R1 **0,37%**, Sonnet 3.7 with thinking **0,04%**
- **Ameaça com números que a delimitam favoravelmente** — nos modelos relevantes é sub-1%.
  O risco sério são os **Unfaithful Illogical Shortcuts**: traços **estruturalmente
  bem-formados** e substantivamente errados — o caso de falso negativo de uma métrica estrutural

### Young (2026) — Measuring Faithfulness Depends on How You Measure
- [arXiv:2603.20172](https://arxiv.org/abs/2603.20172) · conferido
- Três classificadores de fidelidade sobre os **mesmos** 10.276 traços, 12 modelos, 9 famílias
- Taxas de **74,4% / 82,6% / 69,7%** nos dados idênticos. Gaps por modelo de 2,6 a 30,6 p.p.;
  McNemar todos significativos (p < 0,001); kappa de Cohen de **0,06** a **0,42**.
  **A escolha do classificador inverte rankings** — Qwen3.5-27B é 1º sob um pipeline e 7º sob outro
- **Ameaça metodológica, a mais fácil de levar ao AROF em revisão e a mais barata de
  neutralizar.** Exigência concreta: **medir qualquer observável por pelo menos duas
  operacionalizações independentes e reportar a faixa de sensibilidade**, nunca um número único

## Supervisão de processo — predizer erro pelo processo, com rótulos

### Lightman et al. (2023) — Let's Verify Step by Step
- [arXiv:2305.20050](https://arxiv.org/abs/2305.20050) · conferido
- Supervisão de processo **supera significativamente** a de outcome; resolve **78%** de um
  subconjunto do MATH. Liberam **PRM800K**, 800.000 rótulos em nível de passo
- **Apoia** — evidência canônica de que sinal em nível de passo carrega informação que o
  resultado não carrega. PRM800K é o dataset com-gabarito em nível de processo disponível

### Uesato et al. (2022) — Solving math word problems with process- and outcome-based feedback
- [arXiv:2211.14275](https://arxiv.org/abs/2211.14275) · conferido
- Erro de resposta final 16,8% → 12,7%; **erro de raciocínio 14,0% → 3,4% entre soluções com
  resposta final correta**
- **Apoia e quantifica a dissociação central** — resultado e processo são variáveis distintas
  com erro mensurável independente

### Wang et al. (2023) — Math-Shepherd
- [arXiv:2312.08935](https://arxiv.org/abs/2312.08935) · conferido
- PRM treinado com supervisão por passo **construída automaticamente**. Mistral-7B 77,9% →
  84,1% em GSM8K; 28,6% → 33,0% em MATH; com verificação, 89,1% e 43,5%
- **Vizinho com valor metodológico** — rótulos de processo sem anotação humana é meio caminho
  para o regime sem-gabarito

### Chen et al. (2026) — The Paradox of Outcome Optimization
- [arXiv:2606.00674](https://arxiv.org/abs/2606.00674) · conferido · teórico
- **Reward-Induced Manifold Collapse**; bound de generalização por **Semantic Coverage
  Measure (η)** em vez de tamanho de amostra; PRMs como filtros topológicos
- **Apoia no plano teórico** — e o bound por cobertura semântica é o argumento de que a
  validação fora da amostra precisa ser fora de *distribuição*

## Traço como assinatura de linhagem

### Sun et al. (2025) — Idiosyncrasies in LLMs
- [arXiv:2502.12150](https://arxiv.org/abs/2502.12150) · conferido
- **97,1%** de acurácia em classificação de 5 vias; raízes em **distribuições em nível de
  palavra**; persiste a reescrita, tradução e sumarização
- **Apoia parcialmente, e é o confound crítico.** Se traços são 97% identificáveis por
  distribuição de palavras, uma métrica de "similaridade estrutural" pode estar medindo estilo
  lexical. **O AROF precisa de um controle mostrando que o sinal sobrevive à remoção de
  features lexicais** — o ReasonOps faz isso parcialmente ao separar operadores de anchor-phrases

### Kikteva et al. (2026) — Show Me How You Reason and I'll Tell You Who You Are
- [arXiv:2607.14905](https://arxiv.org/abs/2607.14905) · conferido
- Atribuição de autoria por **reasoning graphs** + GNN, além da superfície linguística
- Supera a baseline em **até 27 p.p. sob ataques de ofuscação** e **19 p.p. em textos de
  versões não-vistas do modelo**
- **Apoia, e é a resposta ao confound acima** — a estrutura é sinal de identidade **mais
  robusto** que o estilo, sobrevive a paráfrase e a mudança de versão. A generalização para
  versões não-vistas é precisamente a predição fora da amostra exigida

## Avaliação sem gabarito

### Chen, Yin & Tsang (2025) — Evaluating LLMs Without Oracle Feedback
- [arXiv:2509.08809](https://arxiv.org/abs/2509.08809) · conferido
- **CAI Ratio** (Consistent and Inconsistent), 10 datasets, 4 LLMs
- Correlação positiva forte com a acurácia do LLM
- **Vizinho, com a mesma estrutura de validação do AROF** — métrica de consistência sem
  gabarito, validada por correlação com acurácia medida com gabarito. É o template de
  evidência mínima, um nível abaixo (correlação, não predição fora da amostra)

### Chen et al. (2024) — On the Overthinking of o1-Like LLMs
- [arXiv:2412.21187](https://arxiv.org/abs/2412.21187) · conferido
- Métricas de eficiência de **outcome** e de **process**
- **Vizinho** — referência canônica de redundância intra-trajetória. **Atenção:** o ReasonOps
  mostra que o observável mais óbvio (comprimento do traço) é quase acaso (WP-AUC 0,551).
  Redundância bruta provavelmente não é a feature certa

## Ameaça metodológica transversal

### Sun & Yang (2026) — RouteGuard: Certifying Routing Gain When Complementarity Is Not Enough
- [arXiv:2608.07583](https://arxiv.org/abs/2608.07583) · conferido
- Decompõe ganho como G = π·Δ_E; o ganho alcançável é governado por um funcional de regret
  condicional Φ, **não pela AUC do gate**. Bracket de certificação + lower bound de Le Cam
- Em RouterBench **o veredito depende da unidade de amostragem** — certifica ganho sob
  amostragem por prompt e **recusa certificar sob reamostragem por cluster de workload**,
  porque o ganho repousa em 3 de 86 células. Em OpenRCA recusa certificar em todas as 221 pools
- **Ameaça metodológica séria, e a mais útil do conjunto.** Para o AROF: validar fora da
  amostra **por item não basta** — é preciso reamostrar por cluster de tarefa/domínio, senão
  há risco de certificar um efeito que vive em poucas células. Oferece também o vocabulário
  (certificação, lower bound, pré-registro) que blinda contra a acusação de circularidade

## Síntese: o que o AROF precisa entregar

```
1. baseline obrigatória    a lei fechada de Liu 2026, só com respostas finais
2. controle lexical        mostrar que o sinal sobrevive à remoção de features de palavra
3. fidelidade              medir por truncamento como covariável, reportar estratificado
4. duas operacionalizações  por exigência de Young 2026; reportar faixa, não número
5. fora da amostra         por cluster de domínio, não só por item (RouteGuard)
6. alvo                    CAPA (Goel et al.) é o candidato defensável a variável dependente
```
