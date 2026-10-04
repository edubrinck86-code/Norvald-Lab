---
id: DESK-04
tema: Conformidade, efeito manada e mudança de posição — Δ_herd
data: 2026-10-04
---

# Conformidade e exposição ao par

Sustenta o estimando Δ_herd e o desenho B1/B2/B3/E.

## Precedentes mais próximos do desenho

### Hao, X. et al. (2026) — Not All Flips Are Conformity
- [arXiv:2606.00820](https://arxiv.org/abs/2606.00820) · conferido · preprint, 30 mai 2026
- Decompõe mudança de posição em três mecanismos — instabilidade espontânea, conformidade
  induzida por postura, persuasão induzida por raciocínio — via condições contrafactuais
- **37% dos pares agente-questão mudam só sob auto-reflexão, sem input de pares.**
  Conformidade estrita 29%; **57–77% das conversões são correto→errado**; raciocínio vacuous
  produz 20–39% de adoção de erro entre agentes resistentes; conformidade nociva previsível
  a partir de features iniciais (AUC = 0,79); intervenção reduz em 13,6 p.p. (p < 0,001)
- **Ameaça novidade** — é o mesmo movimento conceitual, e já quantifica o análogo de B2

### Nikeghbal, Kargaran, Kolli & Diesner (2026) — Who Flips?
- [arXiv:2606.16011](https://arxiv.org/abs/2606.16011) · conferido no espelho HTML
- Flip sob contra-argumento plausível, 7 modelos frontier, 57 matérias do MMLU, variando a
  **atribuição** do argumento
- Flip rates de **17,5% a 97,3%**. **Atribuir o argumento ao próprio raciocínio anterior
  AUMENTA o flip** (média +7,1 p.p.; até +18,7 p.p. em Qwen3.5-4B). Cross-model é misto:
  +2,2 e +4,0 p.p. em Llama, mas −5,8 e −2,1 p.p. em GPT-5.1 e Qwen3.5-35B
- **Ameaça parcial + apoia** — é o mais próximo do contraste B3 vs. E, e traz um achado que o
  desenho deve antecipar: **B3 pode não ser piso.** Se B3 > B2, é replicação, não anomalia

### Shu (2026) — Unanimity Without Persuasion
- [arXiv:2609.26145](https://arxiv.org/abs/2609.26145) · conferido · ver `07_ALERTAS.md` §2
- Unanimidade 39,5% → 95,2% numa rodada; acurácia parada; 96,3% dos flips seguem a maioria exibida
- **A ameaça mais séria ao fenômeno** — mas não usa N_eff

## Magnitude e mecanismo

### Hussain, Z. & Nielbo, K. (2026) — Conformity Mitigations Lie on a Single Resistance–Receptivity Frontier
- [arXiv:2608.11247](https://arxiv.org/abs/2608.11247) · conferido no espelho HTML
- 23 modelos open-weight, 19 condições, 3 datasets, >1 milhão de respostas
- Maioria unânime errada reverte **22,8%** das respostas corretas em MMLU, **54,8%** em GPQA,
  **71,0%** em SimpleQA; **84–89%** das revertidas coincidem com a resposta dos pares. Seis
  métodos de mitigação caem sobre uma única fronteira (R² 0,80–0,90)
- **Apoia, e é a melhor referência de magnitude para E.** Implicação de desenho: **Δ_herd é
  unilateral** — convém reportar também a taxa de mudança *benéfica*, senão qualquer
  mitigação parece trivialmente boa

### Zhu, X. et al. (2024) — Conformity in Large Language Models
- [arXiv:2410.12428](https://arxiv.org/abs/2410.12428) · conferido
- Paradigma de Asch adaptado: MMLU, BigBenchHard, PopQA, CommonsenseQA
- Todos conformam, independentemente de a resposta inicial estar correta; **conformidade
  aumenta sob incerteza do modelo** (p < 0,001); instruction-tuned resistem mais
- **Apoia** — sugere condicionar Δ_herd à confiança inicial declarada, não reportar só a
  taxa marginal

### Weng, Chen & Wang (2025) — Do as We Do, Not as You Think — ICLR 2025
- [arXiv:2501.13381](https://arxiv.org/abs/2501.13381) · conferido
- BENCHFORM: 3.299 questões, 5 protocolos; métricas de **conformity rate** e **independence rate**
- 11 modelos, todos conformam. Protocolos enganosos: CRW 23,5%, CRT 31,3%, CRD 47,2%.
  Independência correlaciona com tamanho (Qwen2: 19,6% a 57,6%)
- **Vizinho forte** — fornece nomenclatura métrica já estabelecida em venue tier-1; vale
  alinhar Δ_herd a ela em vez de criar termo novo

### Kumaran, D. et al. (2025) — Overconfidence in Initial Choices and Underconfidence Under Criticism
- [arXiv:2507.03120](https://arxiv.org/abs/2507.03120) · conferido
- Confiança estimada **com e sem** memória da escolha inicial — manipulação impossível em humanos
- Forte **choice-supportive bias**: a própria resposta anterior reforça a confiança e resiste
  à revisão; simultaneamente sobreponderam conselho inconsistente
- **Apoia** — é a justificativa mecanística direta de B3: expor a própria resposta anterior é
  manipulação com efeito causal, não controle neutro

### Zhong, H. et al. (2025) — Disentangling the Drivers of LLM Social Conformity
- [arXiv:2508.14918](https://arxiv.org/abs/2508.14918) · conferido
- Paradigma de **cascata informacional**; 9 LLMs, 3 cenários, incerteza manipulada
- Influência informacional domina; sob incerteza baixa-média **subponderam** todas as
  evidências; sob alta incerteza, sinais públicos sobreponderados (**β > 1,55**) contra
  sinal privado (**β = 0,81**)
- **Vizinho** — oferece estimador alternativo mais fino (razão público/privado)

### Bito, M. et al. (2026) — Large Language Models Exhibit Normative Conformity
- [arXiv:2604.19301](https://arxiv.org/abs/2604.19301) · conferido no espelho HTML ·
  **ressalva: ano inferido pelo identificador arXiv, confirmar antes de citar**
- Separa conformidade informacional de normativa manipulando anonimato, menção a avaliação
  posterior, continuidade do relacionamento e atributos irrelevantes
- **4–5 dos 6 modelos exibem conformidade normativa.** Voto nominal aumenta vs. anônimo
- **Ameaça parcial à interpretação** — Δ_herd mistura dois mecanismos. Ou declarar que não
  os separa, ou incluir uma manipulação de anonimato

### Cho, Guntuku & Ungar (2025) — Herd Behavior: Peer Influence in LLM-based Multi-Agent Systems
- [arXiv:2505.21588](https://arxiv.org/abs/2505.21588) · conferido **parcialmente** —
  abstract confirmado, **números do corpo não extraídos**
- A lacuna entre autoconfiança e confiança percebida nos pares é o driver primário; o
  formato de apresentação modula; **o grau de manada é controlável sistematicamente**
- **Vizinho** — sustenta "swarm controlado" em vez de "efeito manada como falha inevitável"

## Debate como custo

### Wynn, Satija & Hadfield (2025) — Talk Isn't Always Cheap — ICML MAS Workshop 2025
- [arXiv:2509.05396](https://arxiv.org/abs/2509.05396) · conferido
- Grupos **heterogêneos em capacidade**, ao contrário dos estudos com agentes homogêneos
- Debate pode **reduzir** a acurácia mesmo quando modelos mais fortes são maioria; agentes
  migram de correto para incorreto e favorecem concordância
- **Apoia** — a mudança por pares é custo líquido

### Bertalanič & Fortuna (2026) — The Cost of Consensus
- [arXiv:2605.00914](https://arxiv.org/abs/2605.00914) · conferido · ver `01_ESS_e_dependencia.md`
- Debate pior que auto-correção com 2,1–3,4× mais tokens; sicofancia modal até 85,5%;
  consenso 90,1% vs 81,7%; **oracle gap até 32,3%**
- **Apoia, e tem o controle de ruído que o desenho deveria copiar**

### Li, Y.; Naito, A.; Shirado, H. (2025) — Systematic Failures in Collective Reasoning
- [arXiv:2505.11556](https://arxiv.org/abs/2505.11556) · conferido
- HiddenBench: 65 tarefas Hidden Profile, 15 LLMs frontier
- **30,1% de acurácia multiagente sob informação distribuída contra 80,7% de agente único
  com informação completa.** Modo de falha: **convergência prematura** sobre evidência
  compartilhada. Piora com o tamanho do grupo
- **Apoia** — melhor citação para "convergência prematura" como patologia nomeada

### Zhang, H. et al. (2025) — Stop Overvaluing Multi-Agent Debate
- [arXiv:2502.08788](https://arxiv.org/abs/2502.08788) · conferido · position paper
- 5 métodos MAD, 9 benchmarks, 4 modelos. MAD frequentemente **não** supera CoT e
  Self-Consistency, consumindo muito mais compute. Heterogeneidade é o único fator consistente
- **Apoia a motivação de fundo**, mas não mede mudança de posição

### Smit, A. et al. (2023/2024) — Should we be going MAD?
- [arXiv:2311.17371](https://arxiv.org/abs/2311.17371) · conferido
- MAD não supera confiavelmente self-consistency; protocolos sensíveis a hiperparâmetros.
  **Ajustar o nível de concordância entre agentes é uma das alavancas que mais melhora**
- **Vizinho** — argumento a favor de medir Δ_herd como propriedade do protocolo, não do modelo

### Okawa, M. (2026) — Emergence of Biased Consensus in Multi-Agent LLM Debates
- [arXiv:2608.02827](https://arxiv.org/abs/2608.02827) · conferido no espelho HTML
- Framework derivado de dinâmica social física, prevendo transição de fase
- Em T = 0,1 vieses iniciais levam a consenso enviesado em 1–2 rodadas; **ΔT ≈ 0,1 dispara
  decisões coletivas injustas**; heterogeneidade suaviza a transição
- **Vizinho, com implicação direta** — Δ_herd é sensível à temperatura. Fixar e reportar; o
  protocolo já fixa 0,7

### Kasprova, V. et al. (2026) — Too Polite to Disagree: Sycophancy Propagation in MAS
- [arXiv:2604.02668](https://arxiv.org/abs/2604.02668) ·
  [SIGDIAL 2026](https://aclanthology.org/2026.sigdial-1.56.pdf) · conferido
- Expor métricas de sycophancy melhora a acurácia final em **10,5 pontos absolutos**
- **Apoia** — bajulação agente-a-agente é distinta da modelo-usuário e tem efeito causal

### Pitre, Ramakrishnan & Wang (2025) — CONSENSAGENT — Findings of ACL 2025
- [ACL Anthology](https://aclanthology.org/2025.findings-acl.1141/) · conferido
- Sycophancy como causa de rodadas extras; 6 datasets, 3 LLMs
- **Vizinho** — enquadra conformidade como custo de eficiência

### Huang, J. et al. (2023) — LLMs Cannot Self-Correct Reasoning Yet — ICLR 2024
- [arXiv:2310.01798](https://arxiv.org/abs/2310.01798) · conferido
- LLMs têm dificuldade em se auto-corrigir sem feedback externo; por vezes o desempenho
  **degrada** após a auto-correção
- **Apoia** — citação canônica para justificar B2 e B3 como controles: revisão sem informação
  nova já degrada, antes de qualquer pressão de pares

## Lacuna identificada

**Não foi localizado trabalho que meça estabilidade de resposta sob repetição em sessão nova
e independente** — o B2 em sentido estrito — como objeto primário. O mais próximo é o 37% de
Hao et al., medido sob auto-reflexão na mesma sessão. "Asking Again and Again"
([arXiv:2412.07923](https://arxiv.org/abs/2412.07923), conferido) trata de repetição *dentro
do prompt*, não entre sessões.

É provavelmente a contribuição empírica mais limpa e menos disputada do desenho.
