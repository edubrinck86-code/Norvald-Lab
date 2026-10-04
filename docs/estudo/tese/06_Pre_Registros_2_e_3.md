---
id: TESE-006
type: Pré-registros 2 e 3 — campos prontos para submissão
status: Redigido; não submetido
version: 1.0.0
date: 2026-10-04
references:
  - docs/tese/01_Protocolo_Experimental.md
  - docs/tese/05_Adendo_Escopo_Descritivo_e_Alteracao_Sob_Exposicao.md
  - docs/pesquisa/PESQUISA-NEFF-03_Precedentes_Criterio_de_Mensurabilidade_e_Alvo_do_ADR-1000.md
---

# Pré-registros 2 e 3 — campos prontos

Dois registros novos, independentes entre si e independentes do registro 1
(osf.io/5vy6e), que **permanece inalterado**. Nenhum dos dois é emenda do primeiro.

| | Objeto | Por que registro próprio |
| --- | --- | --- |
| **Registro 2** | O cruzamento do AROF: similaridade estrutural de traço prediz co-falha? | Pergunta diferente, desenho diferente. Protege a ideia antes de qualquer contato externo |
| **Registro 3** | Trajetória de N_eff por rodada de exposição | O registro 1 tem duas levas, não trajetória. Acrescentar rodadas ao registro 1 seria emendar depois de submeter |

Onde submeter: OSF Registries, mesmo formulário *OSF Preregistration* usado no
registro 1. Cada bloco abaixo corresponde a um campo, na ordem do formulário, com
a contagem de caracteres. Os limites medidos no registro 1 foram ~591 em
*Manipulated Variables* e ~1003 em *Measured Variables* e *Indices*; todos os
campos aqui estão abaixo disso.

Campos do formulário não listados aqui (data de início, existência de dados,
afiliação) são de preenchimento direto.

---

# Registro 2 — cruzamento do AROF

### Title

*92 caracteres*

```text
Does structural similarity between LLM reasoning traces predict co-failure on the same item?
```

### Description

*751 caracteres*

```text
Independent LLMs fail on the same items more often than independence implies, which reduces the effective size of a judge panel. Estimating that dependence currently requires either a labelled dataset or a wide panel (11-20 judges). Neither is available to a consumer running three to five models through provider APIs. This study tests whether structural features of the reasoning trace - the sequence of reasoning operators a model emits - carry per-item information about whether two models will fail together. If they do, dependence becomes estimable from a narrow panel without ground truth at inference time. The discriminating test is incremental: whether trace structure predicts co-failure beyond what answer agreement alone already predicts.
```

### Research Questions

*351 caracteres*

```text
Q1. Within an item, does the structural similarity between two models' reasoning traces predict whether both models answer that item incorrectly?

Q2. Does trace-structural similarity add predictive information beyond answer agreement alone?

Q3. Is error correlation higher between models of the same family than between models of different families?
```

### Hypotheses

*773 caracteres*

```text
H1. With item fixed effects, the coefficient of trace-structural similarity on co-failure is positive and its 95% CI excludes zero.

H2. Adding trace-structural similarity to a model containing answer agreement increases discrimination: the 95% CI of the AUC difference excludes zero. H2 is the discriminating test. H1 can hold trivially because hard items both raise co-failure and produce distinctive traces; item fixed effects address this, H2 addresses what remains.

H3. Mean pairwise error correlation (phi on binary error vectors) is higher for same-family pairs than for cross-family pairs.

If H2 is not supported, the premise that reasoning structure carries dependence information is not supported in this design. This outcome is reportable and will be reported.
```

### Manipulated Variables

*326 caracteres*

```text
None. Both arms are observational with respect to the primary question. No condition is assigned: every model answers every item once, under identical prompt, rubric and decoding settings. Family relation of a pair (same or different) is a measured grouping of pairs that already exist in the panel, not an assigned treatment.
```

### Measured Variables

*674 caracteres*

```text
Per item and model: the answer emitted; correctness against the declared key (binary); the full reasoning trace.
Per item and ordered-free pair of models: co-failure, 1 if both answers are incorrect (the outcome); answer agreement, 1 if both emitted the same answer regardless of correctness (the baseline predictor); trace-structural similarity (the test predictor); family relation, same or different.
Per item: panel error rate, the share of models answering incorrectly, used to characterise difficulty. Item identity enters every model as a fixed effect rather than as a covariate.
Decoding settings, prompt text and rubric are recorded and held constant within an arm.
```

### Indices

*736 caracteres*

```text
Trace-structural similarity S for a pair on an item: each trace is segmented into reasoning operators and reduced to a normalised histogram over the operator vocabulary. S = 1 - JSD(h_a, h_b), the complement of the Jensen-Shannon divergence between the two histograms, base 2, so S lies in [0,1] with 1 denoting identical operator composition. The operator vocabulary and the segmenter are fixed before analysis and recorded; no operator is added, merged or dropped after inspecting outcomes.
Co-failure Y = 1 if both members of the pair are incorrect, else 0.
Error correlation: phi coefficient between the two members' binary error vectors across items, computed per pair, then averaged within the same-family and cross-family groups.
```

### Data collection procedures / Sample size

*811 caracteres*

```text
Two arms.

Arm A, secondary analysis. A public corpus of segmented reasoning traces from multiple models on benchmarks with verifiable answers, if one is obtainable. All items and all pairs in the corpus are analysed; no subsetting after seeing outcomes.

Arm B, in-instrument replication. Items drawn from a frozen bank and retained only if they survive a difficulty pilot run before the main collection: an item is retained when the panel error rate falls between 0.25 and 0.75. Target 45 retained items, floor 30. Panel of 6 models spanning at least 4 families, giving 15 pairs; 45 items yields 675 pair-item observations. One call per model per item; no optional stopping and no interim analysis. If fewer than 30 items survive the pilot, the bank is extended and the pilot rerun before any main collection.
```

### Statistical models / Analysis plan

*903 caracteres*

```text
Primary (H1): logistic regression of co-failure on trace-structural similarity with item fixed effects; standard errors clustered by item. Reported as coefficient with 95% CI.

Discriminating (H2): two nested logistic models, baseline with answer agreement alone and full with answer agreement plus trace-structural similarity, both with item fixed effects. Compared by likelihood-ratio test and by difference in AUC, with 95% CI from a bootstrap resampling items, not pair-observations, because pair-items are clustered by item and by model.

H3: phi per pair, averaged within group, compared by a permutation test that shuffles family labels across pairs, 10000 permutations.

Multiplicity: three hypotheses, Holm-Bonferroni across H1-H3.

Missing data: a pair-item is dropped if either trace is absent or unparseable; the number dropped is reported.

No analysis is run before collection is complete.
```

### Other

*771 caracteres*

```text
Relation to prior registration. This study is separate from the author's registration at osf.io/5vy6e, which concerns the effect of peer exposure on effective sample size. Neither amends the other.

Known precedent. Published work shows separately that operator-level trace features identify the source model with high accuracy and that they predict whether a single model's answer is correct. No published work tests whether structural similarity between two models' traces predicts failure of both on the same item. That cross is the object here.

Anticipated confound. Item difficulty raises co-failure and may also shape trace composition. Item fixed effects remove between-item difficulty; H2 addresses the remainder by requiring information beyond answer agreement.
```

---

# Registro 3 — trajetória de N_eff

### Title

*79 caracteres*

```text
Effective sample size across successive rounds of peer exposure in an LLM panel
```

### Description

*661 caracteres*

```text
A panel of LLM judges provides fewer independent votes than its headcount, because the members' errors are correlated: published estimates put nine judges at roughly two effective votes. Those estimates are measured with judges that never see each other's output. Separately, it is documented that a single round of mutual exposure collapses disagreement in such panels without improving accuracy. What is not documented is the same quantity measured across both regimes. This study measures effective sample size at each successive round of exposure and characterises the shape of its decay, on the same items, the same panel and the same estimator throughout.
```

### Research Questions

*221 caracteres*

```text
Q1. Does effective sample size decrease across successive rounds of peer exposure?

Q2. What share of the total decrease occurs in the first round?

Q3. Does the trajectory reach a plateau within three rounds of exposure?
```

### Hypotheses

*711 caracteres*

```text
H1. Effective sample size at round 3 is lower than at round 0, with the 95% CI of the difference excluding zero.

H2. At least 60 percent of the total decrease from round 0 to round 3 occurs between round 0 and round 1. The threshold is set in advance from prior reports of first-round concentration ranging from 59 to 93 percent, and 60 is chosen as the conservative end of that range.

H3. The change between round 2 and round 3 is smaller in magnitude than the change between round 0 and round 1, and its 95% CI contains zero.

If the CIs for round 0 and round 3 overlap such that H1 is not supported, there is no trajectory to characterise under this design. That outcome is reportable and will be reported.
```

### Manipulated Variables

*469 caracteres*

```text
Round of exposure, within subject. Round 0 is blind: each model answers with no sight of any other model's output. In rounds 1, 2 and 3 each model is shown the other members' declared positions from the immediately preceding round and answers again. Exposure is simultaneous within a round: every model receives the same prior-round artifact, so no model sees another's current answer. Items, prompt, rubric, panel and decoding settings are held constant across rounds.
```

### Measured Variables

*633 caracteres*

```text
Per item, model and round: the option selected; correctness against the declared key (binary); declared confidence; whether the selected option changed from the preceding round.
Per item and pair of models, per round: co-failure, 1 if both are incorrect; agreement on the selected option.
Per item and round: the share of models selecting the modal option, and whether the panel is unanimous.
Derived per round: mean pairwise error correlation across pairs, and effective sample size.
Recorded and held constant: panel membership, decoding settings, prompt and rubric text, and the exact format in which peer positions are presented.
```

### Indices

*636 caracteres*

```text
Error correlation per round: for each pair of models, the phi coefficient between their binary error vectors across items at that round; rho-bar is the mean over pairs.
Effective sample size per round, Kish form: N_eff(t) = n / (1 + (n-1) * rho-bar(t)), with n the panel size.
Total decrease: N_eff(0) - N_eff(3). First-round share: (N_eff(0) - N_eff(1)) divided by the total decrease, computed only when the total decrease is positive.
Unanimity rate per round: the share of items on which every model selects the same option.
Change rate per round: the share of model-item cells whose selected option differs from the preceding round.
```

### Data collection procedures / Sample size

*713 caracteres*

```text
Items from a frozen bank, retained only if they survive a difficulty pilot run before the main collection: an item is retained when the panel error rate at round 0 falls between 0.25 and 0.75, so that both improvement and degradation remain observable. Target 45 retained items, floor 30. Below the floor the bank is extended and the pilot rerun before any main collection.

Panel of 6 models spanning at least 4 families, one call per model per item per round, 4 rounds: 45 items x 6 models x 4 rounds = 1080 calls.

The bank is frozen by fingerprint before the first main call and no item is edited afterwards. No optional stopping, no interim analysis, and no round is added or removed after collection begins.
```

### Statistical models / Analysis plan

*858 caracteres*

```text
Effective sample size is computed at each round from rho-bar at that round. Confidence intervals come from a bootstrap resampling items, not model-item cells, because observations are paired within item and dependent within round; 10000 resamples; the same resample indices are reused across rounds so that differences between rounds are paired.

H1: the bootstrap distribution of N_eff(3) - N_eff(0), reported with a 95% CI.

H2: the bootstrap distribution of the first-round share, reported with a 95% CI, and compared against the pre-specified threshold of 0.60.

H3: the bootstrap distributions of the round 2 to 3 change and the round 0 to 1 change, with CIs.

Multiplicity: three hypotheses, Holm-Bonferroni across H1-H3.

Secondary and clearly labelled as such: unanimity rate and change rate per round, reported descriptively with the same bootstrap.
```

### Other

*827 caracteres*

```text
Relation to prior registration. This study is separate from the author's registration at osf.io/5vy6e, which registered a two-wave design and remains unchanged. The trajectory across rounds is a different design and is registered here rather than added to the earlier one, so that the earlier registration is not amended after submission.

Scope. Effective sample size here is specific to the outcome measured, the item population and the panel. It is not a count of independent minds and not a measure of panel quality. A decrease is reported as a decrease; no direction is given a normative reading by definition.

Known precedent. Effective sample size has been reported for blind panels and disagreement collapse has been reported for exposed panels, in different numeraires. The per-round trajectory has not been reported.
```

---

# Notas de submissão

**Ordem.** Submeter o registro 2 **antes** de qualquer contato com autores
externos sobre corpus de traços. O registro é carimbo público e imutável de data.

**Painel de validação ≠ painel de produto.** Os dois registros usam 6 modelos.
Isso é escolha de poder estatístico, não mudança da tese comercial: pares crescem
quadraticamente, e 6 modelos dão 15 pares contra 6 de um painel de 4. A
reivindicação sobre painéis comerciais estreitos continua sendo sobre 3 a 5.

**Dependência do piloto de dificuldade.** Os dois registros condicionam a coleta
principal ao piloto, com piso de 30 itens sobreviventes. O piloto é alavanca de
poder, não só controle de qualidade: item com taxa de erro perto de 0,5 produz
2,4 vezes mais eventos de co-falha que item com taxa 0,25.

**O que ainda não está nos registros.** O fingerprint do banco de perguntas, que
entra depois pelo recurso de *update*, como no registro 1.
