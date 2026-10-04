---
id: DESK-03
tema: Diversidade, capacidade e por que diversidade não é independência
data: 2026-10-04
---

# Diversidade ≠ dependência de erro

Sustenta a separação que o desenho impõe: painel de 4 famílias distintas, **mesma classe
de tamanho**, para não confundir capacidade com dependência.

## O confundimento, medido

### Kim, D. (2026) — Are Diversity Metrics Measuring Diversity?
- [arXiv:2607.20768](https://arxiv.org/abs/2607.20768) · conferido · autor único, Aidentyx
- 31.900 subconjuntos de 30 LLMs (MMLU-Pro; 29 em TruthfulQA), 5 métricas, controles de capacidade
- Ganho oracular positivo em **100%** dos subconjuntos, mas voto simples supera o melhor
  membro em apenas **9,98%** (tamanho 3); taxa agregada tamanhos 2–4 = **1,27%**
- "Diversidade estrita" quase colinear com (1 − acurácia média): **Spearman ρ = +0,991**
  (MMLU-Pro) / **+0,988** (TruthfulQA); capacidade explica **98,9% / 98,5%** da variância
- Resíduo após controle: co-falha par a par **−0,432** (linear) / **−0,474** (não-linear)
- **Apoia premissa** — é a demonstração direta de que métricas de diversidade re-expressam capacidade

### Ali, J. (2026) — Quantifying Diversity of Thought: A Predictive Law of Weighted LLM Ensemble Lift
- [arXiv:2607.17384](https://arxiv.org/abs/2607.17384) · conferido
- 767.520 inferências, 10 modelos open-weight, SuperGPQA + GPQA Diamond + forense digital
- **φ bruto não tem praticamente poder preditivo (R² ≤ 0,09)**; φ_adj ajustado por acurácia
  é marcadamente superior (**R² = 0,67** em SuperGPQA). Transfere com ρ = 0,84 / 0,51 / 0,84
- **Apoia premissa** — o par φ/φ_adj é a formalização mais próxima de separar diversidade de
  dependência

### Awuni et al. (2026) — Who Judges Matters: Family-Conditioned Preference in LLM-as-Judge Panels
- [arXiv:2609.17857](https://arxiv.org/abs/2609.17857) · conferido
- Desenho pareado totalmente cruzado, 4 famílias open-weight, 9.312 julgamentos
- **A estatística por família usual correlaciona com habilidade Bradley-Terry em r = 0,95.**
  Com estimador corrigido: lift para a própria família 3,4–8,4 p.p.; FPS global 0,067
  (IC 95% [0,053, 0,084], p = 0,0002). Composição do painel muda **18,5%** dos resultados
- **Apoia** — o confundimento no eixo de família, com r explícito, mais o padrão metodológico

## Insuficiência algébrica de métricas par a par

### Chen, J. (2026) — When Does Combining Language Models Help? A Co-Failure Ceiling
- [arXiv:2606.27288](https://arxiv.org/abs/2606.27288) · conferido · autor único
- β = taxa em que **todos** os modelos erram a mesma query; teto: acurácia ≤ 1 − β. 67 modelos,
  21 provedores
- **ρ não consegue identificar β** — leis de erro com marginais e correlações par a par
  idênticas podem ter taxas all-wrong diferentes. Matemática aberta: β observado 0,052 vs
  0,023 sob cópula gaussiana (**≈2,5× de subprecificação**, IC 90% 1,7–3,4); código 0,079;
  GPQA-Diamond 0,127
- **Apoia, e é a peça algébrica mais forte** — prova que diversidade par a par é insuficiente
  *por construção* para dependência de ordem superior

## Diversidade de família não compra independência

### Nogueira, Pattabiraman, Vieira & Campos (2026) — Evaluating Failure Independence in LLM-Generated Code
- [arXiv:2607.02808](https://arxiv.org/abs/2607.02808) · conferido
- **Separa diversidade estrutural de diversidade comportamental.** 224 problemas, 12 modelos,
  5 linguagens, 3 estratégias de prompt
- Modelos diferentes produzem soluções mais distintas — mas **falham nos mesmos testes muito
  mais do que sob independência**. Ensembles de 3 e 5 versões realizam **0,43 e 0,44** do
  ganho alcançável sob independência (abaixo de 0,3 no mesmo modelo). Padrões de falha
  diferentes frequentemente compartilham a mesma causa raiz
- **Apoia — é o que mais literalmente instancia a distinção da tese**, e quantifica: a
  heterogeneidade de família compra menos da metade da independência

### Li, W.; Lin, Y.; Xia, M.; Jin, C. (2025) — Rethinking Mixture-of-Agents
- [arXiv:2502.00674](https://arxiv.org/abs/2502.00674) · conferido
- Self-MoA (um único LLM top) **supera** MoA misto: **+6,6%** em AlpacaEval 2.0, **+3,8%** em
  média (MMLU, CRUX, MATH). Misturar LLMs diferentes **frequentemente rebaixa a qualidade média**
- **Apoia pelo contraexemplo** — justifica fixar a classe de tamanho

### Rosales, R. & Miret, S. (2025/2026) — Diverse LLMs or Diverse Question Interpretations? — LREC 2026
- [arXiv:2507.21168](https://arxiv.org/abs/2507.21168) · conferido · LREC 2026, pp. 5116–5128
- Diversidade de **modelo** vs. diversidade de **interpretação da pergunta**, em boolq,
  strategyqa, pubmedqa
- Diversidade de interpretação leva consistentemente a melhor acurácia; **diversidade de
  modelo tipicamente produz resultados entre o melhor e o pior membro, sem melhoria clara**
- **Ameaça parcial** — o painel de 4 famílias precisa defender por que família é o eixo certo

### Kohli, G. (2026) — Nine Judges, Two Effective Votes
- [arXiv:2605.29800](https://arxiv.org/abs/2605.29800) · conferido
- 9 juízes de 7 famílias = **~2 votos efetivos**; déficit de 8–22 p.p.
- **Apoia, com alerta quantitativo** — um painel de 4 precisa declarar que mede n_eff, não contagem

## Métricas de diversidade: o que elas são

### Friedman, D. & Dieng, A. B. (2023) — The Vendi Score — TMLR
- [arXiv:2210.02410](https://arxiv.org/abs/2210.02410) · conferido · TMLR 07/2023
- Exponencial da entropia de Shannon dos autovalores de uma matriz de similaridade; **não
  requer dataset de referência nem rótulos**
- Mesmo GANs que capturam todos os modos podem ser menos diversos que o dataset original
- **Vizinho, e peça obrigatória de fundamentação** — mede similaridade de outputs, **nunca
  co-falha**. É o exemplo mais claro de que as duas famílias são ortogonais

### Tekin, Ilhan, Huang, Hu & Liu (2024) — LLM-TOPLA — Findings of EMNLP 2024
- [ACL Anthology](https://aclanthology.org/2024.findings-emnlp.698/) · conferido na página
  (abstract e números extraídos do PDF — a landing page não renderiza abstract)
- **Diversidade focal (λ_focal)** definida sobre falhas conjuntas: 0 (todos falham juntos) a
  1 (falhas não correlacionadas)
- +2,2% em MMLU sobre o melhor ensemble, +2,1% em GSM8k, 3,9× em F1 em SearchQA, +38 ROUGE-1 em XSum
- **Vizinho** — antecedente para argumentar que "diversidade" no sentido útil sempre foi
  dependência de erro disfarçada

### Shaib et al. (2024) — Standardizing the Measurement of Text Diversity
- [arXiv:2403.00553](https://arxiv.org/abs/2403.00553) · conferido
- Validade convergente de escores de diversidade textual; pacote `diversity`
- **A maioria das métricas textuais é redundante entre si** — um conjunto de 4 basta
- **Vizinho** — diversidade textual é um eixo colapsável de poucos graus de liberdade, e
  portanto incapaz de carregar a informação de dependência de erro

## Escala, colapso e saturação

### Yang, Y. et al. (2026) — Understanding Agent Scaling via Diversity — ICLR 2026
- [arXiv:2602.03794](https://arxiv.org/abs/2602.03794) · conferido
- **K\***, contagem efetiva de canais **sem rótulos**. **2 agentes diversos igualam ou
  superam 16 homogêneos**
- **Apoia + ameaça novidade** — K* é métrica de dependência efetiva distinta de diversidade
  superficial

### Chen, N. et al. (2026) — Diversity Collapse in Multi-Agent LLM Systems
- [arXiv:2604.18005](https://arxiv.org/abs/2604.18005) · conferido (metadados via API;
  números da página HTML v2)
- 10.000+ propostas, 20 tópicos, Vendi Score em 3 níveis
- Modelos mais alinhados mostram **ganhos marginais decrescentes de diversidade apesar de
  maior qualidade por amostra**. Colaboração horizontal "júnior" Vendi 8,08 vs 4,65
  (especialistas). Diversity Utilization Ratio cai de 1,03 (N=3) para 0,47 (N=7). Vendi
  concorda com juízo humano em 87%
- **Apoia** — o confundimento capacidade↔diversidade com sinal invertido, no regime generativo

### Zhu, X. et al. (2026) — Demystifying Multi-Agent Debate: Confidence and Diversity
- [arXiv:2601.19921](https://arxiv.org/abs/2601.19921) · conferido (metadados API; números HTML v3)
- Diversidade inicial correlaciona com desempenho do debate, mas com **efeito minúsculo**
  (Qwen r = 0,070, p < 0,001; Llama r = 0,019, p = 0,002). Inicialização ciente de diversidade
  eleva Pass@5 de 0,7921 → 0,9097 (Qwen) e 0,7423 → 0,9026 (Llama)
- **Apoia** — r ≈ 0,07 é, por si, evidência de que a diversidade medida não é a quantidade que importa

### Vallecillos-Ruiz, Hort & Moonen (2025) — Wisdom and Delusion of LLM Ensembles
- [arXiv:2510.21513](https://arxiv.org/abs/2510.21513) · conferido
- 10 LLMs de 5 famílias, 3 benchmarks de geração e reparo de código
- **Upper bound teórico até 83% acima do melhor modelo isolado**, mas consenso cai numa
  "armadilha de popularidade"; estratégia baseada em diversidade realiza até **95%** do
  potencial, mesmo com 2 modelos
- **Apoia** — separa potencial de realização

### Tran, D. & Kiela, D. (2026) — Single-Agent LLMs Outperform Multi-Agent Systems Under Equal Thinking Token Budgets
- [arXiv:2604.02460](https://arxiv.org/abs/2604.02460) · conferido
- Com tokens de raciocínio constantes, single-agent iguala ou supera MAS em multi-hop;
  identifica artefatos de controle de orçamento via API que **inflam ganhos aparentes de MAS**
- **Vizinho + ameaça metodológica** — a tese deve declarar se o painel de 4 é comparado a um
  single-agent com orçamento igualado

### Li, Liu & Yuen (2026) — Measuring Collapse and Correction
- [arXiv:2609.35279](https://arxiv.org/abs/2609.35279) · conferido
- Screen pré-debate: associação em nível de família ρ = 0,893 (p = 0,0123), **mas a acurácia
  da maioria inicial é comparador próximo (ρ = 0,821), e por isso os autores recusam
  explicitamente tratar como predição calibrada**
- **Apoia** — precedente metodológico de autores que se recusam a declarar predição por não
  terem controlado capacidade

### Kim, E. M. et al. (2025) — Correlated Errors in LLMs
- Ver `02_Erro_correlacionado.md`. Relevante aqui porque **a correlação é maior entre modelos
  grandes e acurados mesmo de arquiteturas distintas** — corta contra fixar a classe de
  tamanho no topo
