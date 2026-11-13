# Does the Format of a Model's Own Previous Answer Anchor Reconsideration? Structured Items vs Plain Text in an LLM Panel

Eduardo Guedes · Independent researcher · ORCID 0009-0003-9960-3337

## Abstract

In the Δ_herd study (OSF gbx5m), models reviewing their own previous answer almost never change their chosen option (B3: 2.1%), while models shown only the letter they chose change much more often (B3L: 16.3%). The two conditions differ in content (B3 shows the declared reasoning) and in format (B3 shows it as structured items and relations). To separate the two, we added a new condition, B3T, with the same content as B3 presented as plain text, and a same-day replication of B3 (B3R) as a drift control. The panel and questions are those of Δ_herd: five models from five companies and the 91 non-unanimous questions (30 from a new bank and 61 from MMLU-Pro).

The confirmatory hypothesis held. Models changed their option 10.3% [7.5; 13.3] of the time in B3T and 3.9% [2.3; 5.8] in B3R: a difference of 6.5 points [3.7; 9.3], paired McNemar p = 0.00006, 431 pairs. The effect comes from MMLU-Pro (13.6% vs 4.5%, p = 0.00007); on the easier new bank there was no detectable difference (4.1% vs 2.7%, p = 0.69). The expected descriptive order held: B3R ≤ B3T ≤ B3L. Most of the extra changes in B3T replaced one wrong answer with another (20, against 4 in B3R), and the net correction was similar (+6 in B3T, +5 in B3R). In reconsideration, the structured format made the models more stable without reducing correction.

## 1. Introduction

Text 1 measured how much models change their answer when they see their peers, using reconsideration of their own answer (B3) as a baseline. That baseline was low, about 2%. When the model saw only the letter it had chosen (B3L, exploratory), the rate rose to 16%. Hao et al. (2026) report 37% in a design with other models and free text.

The gap between B3 and B3L has two possible explanations. Either what holds the model in place is seeing its own reasoning (content), or it is the way that reasoning is presented, as items with declared confidence and explicit relations (format). If it is the format, the choice of how to store and return a model's answer changes its behavior. This matters for any system in which a model reviews its own work across steps.

## 2. Method

**Conditions.** All are derived from the B1 answers already collected on 11 Nov 2026 (runs conf2-banco and conf2-mmlu). No B1 was collected again. The reconsideration instruction and the requested answer format are identical; only the presentation of the previous answer changes.

| Condition | The participant sees | Collected |
|---|---|---|
| B3 | its own B1 contribution, as structured items and relations | 11 Nov (conf2) |
| B3L | only the option chosen in B1 | 11 Nov (Δ_herd exploratory) |
| B3T | the same content as B3, as plain text: each item becomes a paragraph with its declared confidence, each relation a sentence | 12 Nov |
| B3R | the same as B3, collected again | 12 Nov |

The B3T text is rendered in the round's language (Lab PR #27). An automated test checks that every item, confidence and chosen option of B3 appears in the text, with no structure and nothing from peers.

**Panel.** The same five models as Δ_herd, each with the same fixed provider: Gemma 4 31B (Google), Nemotron 3 Nano 30B (NVIDIA), Mistral Small 2603, Qwen 3.8 27B (Alibaba) and Muse Glimmer 30B (Meta). Temperature 0.7, top_p 1.0, medium reasoning effort, max_tokens 4096.

**Questions.** Those not unanimous in B1, the same as B3L: 30 from the new bank and 61 from MMLU-Pro.

**Measure.** The option chosen in the condition differs from the B1 option. This is the same rule used for B3 and B3L.

**Hypotheses (preregistered).**
- H1, confirmatory: changing the chosen option is more frequent in B3T than in B3R. Exact paired McNemar per participant × question, two-sided, α = 0.05; both banks combined is the main analysis.
- H2, descriptive: expected order B3R ≤ B3T ≤ B3L, with bootstrap CIs.
- H3, descriptive: on keyed questions, each change classified as wrong → right, right → wrong or wrong → another wrong.

**Statistics.** Bootstrap by question, 20,000 replicates, seed 20261112, 95% percentile CI.

**Collection.** On 12 Nov 2026, 19:42 to 21:02 (Brasília time): 182 experiments, all complete, at a cost of US$ 0.886. Answers without a valid position were excluded without imputation: 20 in B3T and 22 in B3R, out of 455 expected in each.

## 3. Results

### 3.1 H1: plain text vs structured

| | B3R (structured) | B3T (plain text) | Difference B3T − B3R | McNemar p |
|---|---|---|---|---|
| Combined (H1) | 3.9% [2.3; 5.8] | 10.3% [7.5; 13.3] | 6.5 [3.7; 9.3] | 0.00006 |
| MMLU-Pro | 4.5% [2.4; 7.1] | 13.6% [9.9; 17.4] | 9.2 [5.5; 12.9] | 0.00007 |
| New bank | 2.7% [0.7; 5.5] | 4.1% [1.3; 8.1] | 1.4 [−2.0; 4.7] | 0.69 |

H1 is supported. With the same content, models changed their option about 2.6 times as often when the previous answer came as plain text. The strict reading (changed without new grounds) gives the same or nearly the same numbers (`resultados.md`).

### 3.2 H2: the order of the four conditions

| Condition | Changed option |
|---|---|
| B3 (11 Nov) | 2.1% [0.9; 3.5] |
| B3R (12 Nov) | 3.9% [2.3; 5.8] |
| B3T | 10.3% [7.5; 13.3] |
| B3L (letter only) | 16.3% [12.8; 19.9] |

The expected order (B3R ≤ B3T ≤ B3L) held. Plain text sits between the structured format and the letter alone. B3R was slightly above the original B3, with overlapping CIs; this may be day-to-day drift, which is why the confirmatory comparison uses B3R.

### 3.3 H3: what the changes did

Keyed questions, both banks combined:

| Condition | Wrong → right | Right → wrong | Wrong → another wrong | Pairs |
|---|---|---|---|---|
| B3 | 5 | 3 | 1 | 333 |
| B3R | 9 | 4 | 4 | 339 |
| B3T | 14 | 8 | 20 | 341 |
| B3L | 26 | 13 | 19 | 314 |

B3T changed more, but most of the excess replaced one wrong answer with another (20, against 4 in B3R). Net correction (wrong → right minus right → wrong) was +6 in B3T and +5 in B3R. The structured format did not reduce correction; it reduced changes without gain.

### 3.4 Final accuracy (exploratory, post hoc)

This analysis was not in the registration; it was done after seeing the data (`desvios.md`). On keyed questions, final accuracy was 53.8% in B3T (184/342) and 53.3% in B3R (180/338). In pairs, B3T was right and B3R wrong 12 times, and the reverse 11 times (McNemar p = 1.0). There was no difference in accuracy between the formats.

## 4. Caveats

- **The plain text comes from a structured answer.** B1 was produced under the structured-format instruction. B3T is the same answer without the structure, not an answer written freely from the start. A free-text B1 would be a second, separately registered stage.
- **The effect is in MMLU-Pro.** On the new bank almost no one changes in any condition, and the study has no power to detect a difference there.
- **B3L is from another day and is exploratory.** It enters only as a descriptive reference.
- **MMLU-Pro has questions with a debatable key** (text 2, section 4.1). This affects H3 (what counts as right), not H1, which measures change, not accuracy.
- **Collection before registration approval.** The registration was submitted at 17:08 on 12 Nov; collection began at 19:42, while OSF was still awaiting automatic approval. The registered content does not change with approval.
- **One panel, two banks, one day.** The results hold for this panel.

## 5. Discussion

The near-total anchoring of B3 does not come only from the model seeing its own reasoning. An important part comes from the format: with the same content, presentation as structured items and relations reduced option changes from 10.3% to 3.9%. The format accounts for almost half of the distance between B3 and B3L (6.4 of 14.2 points).

H3 shows that this stability came at no cost to correction. What the structured format removed was mostly the replacement of one wrong answer with another, a change that does not improve the answer. For systems in which a model reviews its own work across several steps, this suggests that how the previous answer is stored and returned is a design choice with a measured effect, not merely a matter of presentation.

The result does not say that the structured format makes the model more accurate: final accuracy was the same under both formats (section 3.4). The gain is in consistency.

## Declaration of interest

The structured format used in conditions B3 and B3R was developed by the author in his own software. The code that generates the conditions (B3, B3T and B3R) is public in the repository listed below, and the description in section 2 is sufficient to reproduce them.

## References

- Guedes, E. (2026). Δ_herd: herd effect in a heterogeneous LLM panel (text 1). OSF gbx5m; registrations aw9vf and 5dpjr.
- Guedes, E. (2026). How Many Models Are Five Worth? (text 2). OSF gbx5m.
- Hao et al. (2026). arXiv 2606.00820.

## Code and data

- Preregistration: `studies/formato/preregistration-en.md` (OSF gzvk5, registration 46erj).
- Collection: `studies/formato/coleta.py`. Measures: `studies/formato/medidas.py`, written before collection.
- Exposure `self_text`: Lab PR #26 and #27. Repository: https://github.com/edubrinck86-code/Norvald-Lab
