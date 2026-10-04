---
id: DESK-02
tema: Erro correlacionado e co-falha entre LLMs — a premissa
data: 2026-10-04
---

# Erro correlacionado entre LLMs

A premissa de que modelos diferentes não erram de forma independente. Todas as entradas
conferidas na fonte, salvo marcação.

## Evidência central

### Kim, E. M.; Garg, A.; Peng, K.; Garg, N. (2025) — Correlated Errors in LLMs — ICML 2025
- [PMLR v267, pp. 30038–30066](https://proceedings.mlr.press/v267/kim25e.html) ·
  [arXiv:2506.07962](https://arxiv.org/abs/2506.07962) · conferido nas duas fontes
- 350+ LLMs, dois leaderboards, tarefa de triagem de currículos
- **Concordam 60% das vezes quando ambos erram.** Arquitetura e provedor compartilhados
  explicam parte; **modelos maiores e mais acurados têm erros altamente correlacionados
  mesmo com arquiteturas e provedores distintos**
- **Apoia premissa; e ameaça o desenho** — a classe de tamanho alta, que o painel fixa, é
  onde a correlação é *maior*. Isso precisa ser declarado como trade-off assumido

### Goel et al. (2025) — Great Models Think Alike — ICML 2025
- [PMLR v267, pp. 19621–19678](https://proceedings.mlr.press/v267/goel25b.html) ·
  [arXiv:2502.04313](https://arxiv.org/abs/2502.04313) · conferido
- Propõe **CAPA**, similaridade por sobreposição de **erros**, ajustada por acaso
- Juízes favorecem modelos similares a si; **erros ficam mais similares conforme a
  capacidade aumenta**; weak-to-strong depende de conhecimento complementar
- **Apoia + ameaça novidade** — CAPA é métrica de correlação de erro entre especialistas
  com ajuste por acaso; qualquer métrica nova precisa se posicionar contra ela

### Zhou, Xiong, Savarese & Wu (2024) — Shared Imagination: LLMs Hallucinate Alike
- [arXiv:2407.16604](https://arxiv.org/abs/2407.16604) · conferido · preprint
- *Imaginary Question Answering*: um modelo gera perguntas sobre conceitos inteiramente
  fictícios, outro responde
- **Todos os modelos respondem às perguntas uns dos outros com sucesso notável**
- **Apoia premissa, no ponto mais nítido** — a co-falha não é artefato de dificuldade do
  item: existe onde não há resposta certa alguma

### Usama & Chang (2026) — Convergence Without Understanding
- [arXiv:2605.23315](https://arxiv.org/abs/2605.23315) · conferido · preprint
- 16 modelos, 8 famílias, 1,5B–72B, 800 problemas estratificados
- **Inversão de dificuldade: convergem mais nos problemas que coletivamente erram
  (CKA = 0,897) do que nos que acertam (CKA = 0,830).** Pré-decisão alinha (0,875),
  pós-decisão diverge (0,274); informação compartilhada decodificável entre modelos (66%)
  mas com influência causal mínima (flip 1,5–5,5%)
- **Apoia no ponto mais forte possível** — e qualifica: convergência representacional
  reflete restrições de processamento de input, não estratégia compartilhada

## Mecanismo: por que os erros se correlacionam

### Huh, Cheung, Wang & Isola (2024) — The Platonic Representation Hypothesis — ICML 2024
- [arXiv:2405.07987](https://arxiv.org/abs/2405.07987) · conferido (arXiv; venue não
  reconferido em proceedings)
- **Conforme modelos crescem, medem distância entre pontos de dado de forma cada vez mais
  parecida** — convergência para um modelo estatístico compartilhado da realidade
- **Vizinho** — é o mecanismo mais citado para *por que* escala aumenta correlação

### Li, Z. M.; Vu, H. A.; Awofisayo, D.; Wenger, E. (2025) — Causes and Consequences of Representational Similarity
- [arXiv:2505.13899](https://arxiv.org/abs/2505.13899) · conferido · preprint
- Isola **sobreposição de dataset** e **sobreposição de tarefa** experimentalmente
- Ambos causam maior similaridade; combinados, efeito mais forte; maior similaridade
  aumenta vulnerabilidade a ataques transferíveis
- **Apoia** — responde causalmente ao "o que explica a correlação"

### Bommasani, Creel, Kumar, Jurafsky & Liang (2022) — Picking on the Same Person — NeurIPS 2022
- [arXiv:2211.13972](https://arxiv.org/abs/2211.13972) · conferido
- Introduz **outcome homogenization**; testa a component-sharing hypothesis
- **Compartilhar dados de treino agrava homogeneização de forma confiável**; compartilhar o
  foundation model dá resultado **misto** — o método de adaptação importa
- **Apoia, com a ressalva mais fina contra a versão forte da premissa**

### Sun, Yin, Xu, Kolter & Liu (2025) — Idiosyncrasies in LLMs — ICML 2025
- [arXiv:2502.12150](https://arxiv.org/abs/2502.12150) · conferido
- **97,1% de acurácia na classificação de 5 vias** entre ChatGPT, Claude, Grok, Gemini e
  DeepSeek, a partir do texto gerado; persiste a reescrita, tradução e sumarização
- **Ameaça parcial** — modelos são altamente distinguíveis em *estilo*. Distinguibilidade e
  independência de erro são compatíveis, mas um leitor cético usará isto contra a tese

## Consequências medidas

### Bommasani, Bana, Creel, Jurafsky & Liang (2026) — Algorithmic Monocultures in Hiring — FAccT 2026
- [arXiv:2605.27371](https://arxiv.org/abs/2605.27371) · conferido
- 3 milhões de candidatos, 4 milhões de candidaturas, mesmo fornecedor
- **4% dos candidatos que se inscrevem em 10 posições são recomendados para rejeição em
  todas — acima do esperado por acaso.** 14,74% das candidaturas de asiáticos e 25,87% das
  de negros vão para posições com impacto adverso
- **Apoia** — evidência de campo, não de benchmark

### Li, H. & Hai, M. (2026) — State-dependent error correlations shape voting thresholds
- [arXiv:2607.23931](https://arxiv.org/abs/2607.23931) · conferido · preprint
- Screening de Sah–Stiglitz com dependência que difere entre casos bons e ruins;
  **174.384 votos de 28 modelos** em 4 benchmarks binários
- Erros compartilhados criam **piso assintótico de erro** para voto majoritário. R² sobe de
  0,840 (independência) para **0,967** (matriz completa). Perda: 60,25 → 52,50 → 50,77;
  redução total 15,73% (IC bootstrap 95% [13,41–16,75])
- **Apoia + ameaça novidade** — é o mais próximo de "modelar a dependência muda a regra de
  agregação", com estimação empírica

### Bugaud, Z. (2026) — Hidden Clones: Family Bias in VLM Ensembles
- [arXiv:2603.17111](https://arxiv.org/abs/2603.17111) · conferido · **preprint de autor
  único, sem revisão aparente — tratar com cautela**
- 17 VLMs, 8 famílias
- Erros por família reduzem a **dimensionalidade efetiva a 2,5–3,6 votantes independentes**;
  "misleading tier" (1,5–6,5% das perguntas) onde o erro majoritário derruba a acurácia a 0%
  apesar de o melhor modelo estar certo; voto hierárquico recupera +18–26 p.p.
- **Apoia** — quantifica "N especialistas ≠ N vozes". Domínio VLM, não LLM puro

### Zou, Wang, Carlini, Nasr, Kolter & Fredrikson (2023) — Universal and Transferable Adversarial Attacks
- [arXiv:2307.15043](https://arxiv.org/abs/2307.15043) · conferido
- Sufixos treinados em Vicuna transferem para ChatGPT, Bard, Claude, LLaMA-2-Chat, Pythia, Falcon
- **Apoia por outra via** — co-falha sob entrada adversarial é superfície de vulnerabilidade
  compartilhada entre provedores distintos

### Zöller, N. et al. (2024) — Human-AI collectives produce the most accurate differential diagnoses
- [arXiv:2406.14981](https://arxiv.org/abs/2406.14981) · conferido
- 40.762 diagnósticos de médicos + 5 LLMs, 2.133 casos
- Coletivos híbridos superam médicos isolados, coletivos de médicos, LLMs isolados **e
  ensembles de LLMs** — atribuído a humanos e LLMs cometerem *tipos diferentes* de erro
- **Vizinho** — a complementaridade que falta entre LLMs existe entre LLM e humano

### Li, Liu & Yuen (2026) — Measuring Collapse and Correction in Homogeneous-Panel LLM Debate
- [arXiv:2609.35279](https://arxiv.org/abs/2609.35279) · conferido · NeurIPS 2026 D&B
- 6.925 debates MMLU-Pro, 253 colapsos (maioria correta destruída pela discussão)
- **Apoia** — co-falha induzida por homogeneidade de painel em deliberação

### Turkmen, Buyukates & Bastopcu (2026) — Information Theoretic View of LLM Ensemble Selection
- [arXiv:2602.08003](https://arxiv.org/abs/2602.08003) · conferido
- Piso de erro informação-teórico; cópula gaussiana para erros correlacionados
- **Apoia** — formaliza o custo da correlação

### Aitchison, Jeen, Shevlane & Day (2026) — Diversity is the Strength of the AI Crowd — ICML 2026 Workshop
- [arXiv:2606.29661](https://arxiv.org/abs/2606.29661) · conferido
- Previsões binárias no Metaculus AI Benchmark
- **Acurácia individual não basta** — muitos LLMs de fronteira fazem previsões altamente
  correlacionadas; os ensembles mais fortes combinam acurácia *e* diversidade
- **Apoia** — em domínio de previsão, fora de QA

### Dung, L. & Mai, F. (2025) — AI Alignment Strategies from a Risk Perspective
- [arXiv:2510.11235](https://arxiv.org/abs/2510.11235) · conferido · preprint under review
- 7 técnicas de alinhamento × 7 modos de falha, para medir sobreposição
- **Vizinho** — transpõe o argumento para segurança: defense-in-depth só vale o que vale a
  descorrelação dos modos de falha

## Contestações à premissa

Não localizei nenhum trabalho que meça erro entre LLMs e conclua que é aproximadamente
independente. As contestações reais são de outro tipo:

### Kleinberg, J. & Raghavan, M. (2021) — Algorithmic Monoculture and Social Welfare — PNAS
- [arXiv:2101.05853](https://arxiv.org/abs/2101.05853) · PNAS 118(22):e2018340118 · conferido
- Convergência monocultural **reduz a qualidade agregada das decisões, mesmo quando o
  algoritmo é mais acurado para qualquer decisor isolado**
- **Apoia** a premissa teoricamente — é a base de "swarm controlado não degenerar em monocultura"

### Hedden, B. & Raghavan, M. (2026) — Algorithmic Monoculture and its Critics
- [arXiv:2604.06047](https://arxiv.org/abs/2604.06047) · conferido · preprint v3
- Avaliação formal das objeções à monocultura
- **Concluem que monocultura é menos problemática do que seus críticos supõem**
- **Ameaça a premissa normativa** — é o contraponto publicado mais forte, escrito por um dos
  autores do próprio arcabouço. A tese deve citá-lo explicitamente

### Peng, K. & Garg, N. (2023) — Monoculture in Matching Markets
- [arXiv:2312.09841](https://arxiv.org/abs/2312.09841) · conferido · preprint
- Monocultura seleciona candidatos menos preferidos, mas **casa mais candidatos com a
  primeira escolha** e é mais robusta a disparidades no número de candidaturas
- **Ameaça normativa** — mesmos autores do Kim et al.

### Ballestero, Hosseini, Khanna & Shorrer (2026) — Strategic Algorithmic Monoculture
- [arXiv:2604.09502](https://arxiv.org/abs/2604.09502) · conferido · preprint
- Distingue monocultura primária de estratégica. LLMs têm alta similaridade baseline e a
  regulam conforme incentivos, mas **ficam atrás de humanos em sustentar heterogeneidade
  quando a divergência é recompensada**
- **Apoia, com ângulo próprio** — a correlação persiste sob incentivo explícito para divergir

### Baek, J.; Bastani, H.; Chen, S. (2025) — Strategic Hiring under Algorithmic Monoculture
- [arXiv:2502.20063](https://arxiv.org/abs/2502.20063) · conferido · preprint
- Equilíbrios de Nash quando firmas competem por um pool avaliado por algoritmo comum
- **Vizinho**, lado de mercado
