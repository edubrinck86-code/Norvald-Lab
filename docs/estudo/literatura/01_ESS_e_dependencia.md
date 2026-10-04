---
id: DESK-01
tema: Tamanho amostral efetivo, design effect e dependência em painéis de LLM
data: 2026-10-04
---

# N_eff, design effect e dependência

Todas as entradas conferidas na fonte, salvo marcação explícita.

## Fundação clássica

### Kish, L. (1965) — Survey Sampling
- Livro, John Wiley & Sons, ISBN 0-471-10949-5
- **Verificação: NÃO CONFERIDO na fonte primária.** Fórmula, autoria e ano confirmados em
  fonte secundária e citados consistentemente por Kohli 2026, Xin 2026 e Bay & Yearick 2026.
- Fórmula: `Deff = 1 + (n* − 1)·ρ`, `n_eff = n/Deff`
- **Ressalva de rigor:** a formulação original pressupõe clusters de tamanho igual e ρ
  constante. Transpor para painel de LLM com ρ heterogêneo exige justificar a média — e é
  exatamente aí que um revisor estatístico bate.

### Fleiss, J. L. & Cohen, J. (1973) — The Equivalence of Weighted Kappa and the Intraclass Correlation Coefficient
- *Educational and Psychological Measurement*, 33(3), 613–619
- [SAGE](https://journals.sagepub.com/doi/10.1177/001316447303300309)
- **Verificação: parcial** — título, autores, periódico, volume, páginas e DOI conferidos na
  página do editor; **corpo atrás de paywall, não lido**
- É o elo canônico kappa ↔ ICC, necessário para converter concordância em ρ de Kish
- **Obter o PDF antes de invocar as condições de validade.** A equivalência vale para pesos
  quadráticos e um desenho de efeitos específico, não genericamente.

## Precedentes diretos em painel de LLM

### Kohli, G. (2026) — Nine Judges, Two Effective Votes
- [arXiv:2605.29800](https://arxiv.org/abs/2605.29800) · conferido (abs + HTML)
- Kish ESS sobre 9 juízes LLM de 7 famílias, votando **cegamente, sem comunicação**
- φ̄ = **0,391** (σ = 0,111; faixa [0,161–0,603]); **n_eff = 2,18** de 9 (IC bootstrap 95%
  [2,07–2,31]); acurácia 8–22 p.p. abaixo do voto independente; agregação ótima fecha no
  máximo 11% da lacuna. Robusto a prompt, temperatura, CoT e RewardBench.
- Datasets: ChaosNLI-MNLI (1.000 de 1.599 itens), replicado em SNLI, AlphaNLI
- **Apoia premissa** — é o baseline sem exposição

### Acharya, Pan & Verkhovsky (2026) — ROPOLL: Robust Panel of LLM Judges
- [arXiv:2606.30931](https://arxiv.org/abs/2606.30931) · conferido no HTML completo
- Corollary 1, §3.5: *"Defining the effective jury size N_eff ≜ N/(1+(N−1)γ), the MSE rate
  is tr(Σ)/N_eff."*
- γ̄ ∈ [0,49–0,71] em HelpSteer-2 e UltraFeedback; γ̄_W ∈ [0,45–0,53]. Sob γ ∈ [0,3–0,5],
  N_eff satura em 2–3 — justificativa dos comitês de três juízes
- Não citam Kish; derivam do próprio modelo equicorrelacionado
- **Ameaça novidade, a mais séria sobre a fórmula.** Ver `07_ALERTAS.md` §1

### Xin (2026) — Are Verifier Errors Independent Within a GRPO Group?
- [arXiv:2609.06386](https://arxiv.org/abs/2609.06386) · conferido
- ICC one-way, `DEFF = 1 + (k̄−1)·ρ_cat`, `n_eff = k̄/DEFF` sobre erros de verificador
- Pooled **ρ_cat = 0,530** (IC 95% [0,500–0,560]), 24.998 grupos Qwen2.5-1.5B;
  **n_eff = 1,70 de k = 8**
- Heterogeneidade: categorias de formatação −0,001 a 0,093; estruturalmente complexas
  (frações, radicais, intervalos) 0,38–0,69
- **Apoia + ameaça na transferência.** O achado de heterogeneidade de ρ é metodologicamente
  importante: ρ̄ agregado esconde estrutura

### Bay & Yearick (2026) — When More Sampling Hurts
- [arXiv:2606.28661](https://arxiv.org/abs/2606.28661) · conferido no HTML
- Reenquadra test-time sampling como **cluster sampling**: tentativas repetidas são draws
  correlacionados de um cluster, não ensaios independentes
- **Teto de correlação: o número efetivo tende a 1/ρ quando n cresce.** Com ρ = 0,1,
  ~10 amostras efetivas qualquer que seja o orçamento
- Separa coverage (sobe), selection (satura no teto modal) e benchmark estimation
- **Apoia + ameaça na origem do framing** — o limite 1/ρ̄ já está explicitado e nomeado

### Yu et al. (2026) — Diversity Combining for Multi-Path LLM Reasoning — NeurIPS 2026
- [arXiv:2609.38829](https://arxiv.org/abs/2609.38829) · conferido via API arXiv (abs
  completo; **corpo não aberto** — HTML deu 429)
- Formaliza multi-path reasoning como diversity combining de comunicações sem fio
- "the pairwise correlation of path correctness **caps the design-effect effective sample
  size** of the vote at a finite ceiling". Diversidade de prompt-template reduz correlação
  em **55 de 57 células**. Regra Adaptive-K com piloto de 4 caminhos retém 96–103% da
  acurácia de MV@K=32
- **Vizinho forte, com selo de conferência** — materializa o K* e o teto de ESS

### Yang, Y. et al. (2026) — Understanding Agent Scaling in LLM-Based MAS via Diversity — ICLR 2026
- [arXiv:2602.03794](https://arxiv.org/abs/2602.03794) · conferido (abs + página ICLR)
- Introduz **K\***, contagem efetiva de canais estimável **sem rótulos**
- **2 agentes diversos igualam ou superam 16 homogêneos.** Desempenho limitado pela
  incerteza intrínseca da tarefa, não pela contagem de agentes
- **Vizinho + ameaça novidade** — K* é uma métrica de "número efetivo" sem rótulo

## Exposição e colapso de independência

### Shu (2026) — Unanimity Without Persuasion
- [arXiv:2609.26145](https://arxiv.org/abs/2609.26145) · conferido (API + HTML + checagem
  independente)
- 7 juízes, 7 provedores, 1 rodada cega + 3 de debate, 600 candidatos com gabarito executável
- Unanimidade **39,5% → 95,2% na rodada 1** (93,1% do colapso total), 98,6%, 99,3%;
  acurácia move < 1 ponto; **96,3% das inversões seguem a maioria exibida**
- Controles: reconsideração sem pares reproduz 79,6% do colapso; rótulos sem raciocínio
  91,5%; debate completo acrescenta 4,3 p.p. (IC 95% [0,7–8,1])
- Cédula de verificação por execução corrige 8 de 2.037 pré-debate e **zero** depois
- **Não usa ESS, Kish, design effect nem ICC** (verificado por grep)
- **Ameaça novidade do fenômeno, não da métrica.** Ver `07_ALERTAS.md` §2

### Liu, Xiong, Zhang & Tang (2026) — Social Networks of LLM Agents
- [arXiv:2607.03695](https://arxiv.org/abs/2607.03695) · conferido no HTML
- Distingue **exposição visível** de **influência realizada**; atenção limitada (β) como
  variável de controle
- *"Narrow attention causes herding, where the effective sample size stays bounded
  regardless of population size"*; atenção larga recupera wisdom-of-crowds.
  `Var(θ̂_T) = s²‖q_T‖₂²`, minimizada em s²/n
- **Vizinho forte** — é o mais próximo de "exposição estruturada vs. ESS limitado", mas em
  populações grandes com topologia, usando variância do estimador e não Kish

### Bertalanič & Fortuna (2026) — The Cost of Consensus
- [arXiv:2605.00914](https://arxiv.org/abs/2605.00914) · conferido no HTML
- Três condições, times de 10 agentes homogêneos × 3 rodadas: debate, auto-correção isolada,
  injeção de ruído (controle)
- Debate **pior** que auto-correção consumindo 2,1–3,4× mais tokens. GSM-Hard/Qwen2.5-7B:
  58,8% vs 61,0% (p<0,001), 18.240 vs 5.396 tokens. Sicofancia modal até 85,5%. Debate infla
  consenso para **90,1% vs 81,7%**. **Oracle gap de até 32,3%**
- **Apoia premissa, e é o desenho a copiar** — tem o controle de ruído

### Li, Liu & Yuen (2026) — Measuring Collapse and Correction in Homogeneous-Panel LLM Debate
- [arXiv:2609.35279](https://arxiv.org/abs/2609.35279) · conferido no HTML · NeurIPS 2026 D&B
- Ledger 2×2 por debate; 253 colapsos em 6.925 debates MMLU-Pro; taxa condicional 8,46% vs
  2,15%; **58,9% dos colapsos na rodada 1**; Spearman ρ = 0,893 entre probe e colapso por família
- Freeze com gate previne 29 colapsos mas **perde 108 correções**
- **Não computam ESS** (verificado) — replicam o front-loading de Shu por outro caminho

## Dependência no eixo dos itens

### Llewellyn, Thornton, Bishop & Gray (2026) — Correcting Prompt Dependence in LLM Benchmarks
- [arXiv:2510.05709](https://arxiv.org/abs/2510.05709) v2 · conferido · Alan Turing Institute
- Modelo hierárquico bayesiano com clustering em espaço de embeddings
- **Baselines superestimam o número de amostras independentes em 1,3–5,6×.** MAE melhora
  4–73%; Hopkins 0,609–0,896 em todos os benchmarks
- Não usam terminologia ESS/Deff/ICC
- **Vizinho** — se os itens também são dependentes, o IC de um ρ̄ estimado sobre eles está
  otimista. Crítica previsível, melhor antecipar

## Contexto e vizinhança

### Goel et al. (2025) — Great Models Think Alike — ICML 2025
- [PMLR v267](https://proceedings.mlr.press/v267/goel25b.html) ·
  [arXiv:2502.04313](https://arxiv.org/abs/2502.04313) · conferido
- **CAPA**: `κ_p = (c_obs^p − c_exp^p)/(1 − c_exp^p)`, extensão probabilística do kappa de Cohen
- Erros ficam **mais** parecidos conforme a capacidade sobe
- **Melhor ponte moderna para kappa ↔ ICC** — e aviso de que ρ̄ não é constante entre gerações

### Verga et al. (2024) — Replacing Judges with Juries (PoLL)
- [arXiv:2404.18796](https://arxiv.org/abs/2404.18796) · conferido
- Painel de modelos menores supera juiz único grande a custo **>7× menor**, 6 datasets
- **Contexto necessário** — é a prática que Kohli e RoPoLL atacam; o argumento de custo do
  PoLL pressupõe que juízes somam informação, e N_eff é o que testa isso

### Turkmen, Buyukates & Bastopcu (2026) — Don't Always Pick the Highest-Performing Model
- [arXiv:2602.08003](https://arxiv.org/abs/2602.08003) · conferido
- Seleção como maximização de informação mútua; erros correlacionados por cópula gaussiana
- **Piso de erro informação-teórico** que explica a saturação
- **Vizinho** — formaliza o custo da correlação em termos de informação

### Maryanskyy, Budnikov & Kaliyev (2026) — When Agents Disagree: The Selection Bottleneck
- [arXiv:2603.20324](https://arxiv.org/abs/2603.20324) · conferido
- Win rate 0,810 (diverso + juiz) vs 0,512 (homogêneo); Glass's Δ = 2,07; 42 tarefas, N=210
- **Não reportam correlação nem ESS**
- **Vizinho, como contraponto** — N_eff alto é necessário mas não suficiente: só rende se o
  agregador conseguir explorar

### Komiyama, Oba & Oyamada (2025/2026) — Best-of-∞ — ICLR 2026
- [arXiv:2509.21091](https://arxiv.org/abs/2509.21091) · conferido
- Best-of-N com voto majoritário no limite N → ∞; peso ótimo por MILP
- **Vizinho, prioridade baixa** — teto assintótico, sem tratar confundimento
