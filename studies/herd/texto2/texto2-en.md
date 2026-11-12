# How Many Models Are Five Worth? Error Correlation and the Effective Number of Judges in a Heterogeneous LLM Panel, Before and After Exposure

Eduardo Guedes · Independent researcher · ORCID 0009-0003-9960-3337

## Abstract

Panels of language models are used as if five models were five opinions. If the models err together, the panel is worth less. We measure this through the mean error correlation between pairs of models (ρ̄_error) and the effective number of judges, N_eff = n / (1 + (n − 1) ρ̄), with n = 5.

In the same preregistered experiment as our first paper (OSF aw9vf and 5dpjr), five models from five providers answered 140 MMLU-Pro questions and 52 questions with an answer key from a new bank, under matched conditions. Answering blind (B1), the MMLU-Pro panel had ρ̄_error = 0.635 [0.541, 0.721] and N_eff = 1.41 [1.29, 1.58]. After seeing the peers' contributions (E), ρ̄_error = 0.826 and N_eff = 1.16: Δ_N_eff = 0.251 [0.153, 0.385]. In the new bank, errors were barely correlated (ρ̄_error = 0.031; N_eff = 4.45), and exposure did not bring them closer (Δ_N_eff = −1.60 [−4.49, −0.73]). A homogeneous control panel, five copies of Gemma, had ρ̄_error = 0.848 on MMLU-Pro, close to the mixed panel. On seven questions, all five models chose the same wrong option; without them (exploratory analysis), ρ̄_error(B1) = 0.572 and N_eff = 1.52. Cross-checking with MMLU-Redux, of the 14 questions inherited from MMLU on which 3 or more models chose the same wrong option, 11 converge on a distractor that MMLU-Pro added and Redux did not review.

## 1. Introduction

Our first paper showed how much models change their answer when they see their peers. This paper addresses the other half of that paper's title question: how many contribute. If two models err on the same questions, the second adds little to the first, even without having seen anything from it.

Kim, Garg, Peng and Garg (2025) measured this at scale. On one leaderboard (HELM, 71 models, 14,042 questions), when both models in a pair err, they choose the same wrong option about 60% of the time; on the HuggingFace leaderboard (349 models), 42%. More accurate models err together more often, even after controlling for provider, architecture and size. Our panel is small (5 models), but we measure what they do not: the effect of the models seeing each other.

The preregistered hypothesis (H3) has two parts:

1. the heterogeneous panel is worth fewer than five even when blind (ρ̄_error(B1) > 0);
2. exposure reduces the effective number (Δ_N_eff = N_eff(B1) − N_eff(E) > 0).

The preregistration does not specify a significance test for Δ_N_eff (344-77): the bootstrap interval is the measure.

## 2. Method

The design, models, conditions and questions are those of the first paper (§3). Only what is specific to H3 is described here.

**Error.** For each model, condition and question with an answer key: 1 if the chosen option differs from the key, 0 if it matches. A response without a position is left out (no imputation).

**ρ̄_error(c).** The mean, over the 10 pairs of models, of the phi coefficient between the error vectors in condition c. A pair with no error variance is left out of the mean and counted.

**N_eff(c) = n / (1 + (n − 1) ρ̄_error(c))**, with n = 5 in all conditions, so that the difference reflects only ρ̄.

**Questions used.** All questions with an answer key, including those unanimous in B1 (preregistration: "on ground-truth items"). The unanimity filter applies only to criterion A of the first paper. Until 12 November 2026 the analysis code also applied that filter to ρ̄; deviation D7 corrects this and reports before and after (Appendix A).

**Intervals.** Bootstrap by question, 20,000 replicates, seed 20261111, 95% percentile CI, stratified between questions with an answer key and contestable questions.

**Homogeneous contrast (344-83 item 2).** Five copies of google/gemma-4-31b-it, same provider (Crusoe), B1 only. It measures how much of the correlation comes from the panel being made of similar models in general, rather than of the same architecture.

**Analytical sweep.** The N_eff formula tabulated for ρ̄ from 0.01 to 1 and n = 4, 5, 8 and ∞. It is not an empirical result: it shows the ceiling (1/ρ̄ as n → ∞) a panel has, whatever its size.

## 3. Results

### 3.1 ρ̄_error and N_eff by condition

| Block (questions with key) | Condition | ρ̄_error [95% CI] | N_eff [95% CI] |
|---|---|---|---|
| MMLU-Pro (140) | B1 | 0.635 [0.541, 0.721] | 1.413 [1.287, 1.580] |
| | B3 | 0.642 [0.547, 0.729] | 1.401 [1.277, 1.568] |
| | EP | 0.689 [0.600, 0.770] | 1.332 [1.226, 1.471] |
| | E | 0.826 [0.751, 0.894] | 1.162 [1.093, 1.249] |
| Bank (52) | B1 | 0.031 [−0.063, 0.241] | 4.445 [2.548, 6.702] |
| | B3 | 0.022 [−0.076, 0.215] | 4.597 [2.688, 7.190] |
| | EP | 0.080 [−0.054, 0.243] | 3.791 [2.536, 6.367] |
| | E | −0.043 [−0.096, −0.021] | 6.040 [5.465, 8.098] |
| Combined (192) | B1 | 0.615 [0.520, 0.699] | 1.445 [1.318, 1.624] |
| | E | 0.814 [0.737, 0.879] | 1.175 [1.107, 1.266] |
| h01–h40 (40) | B1 | 0.013 [−0.087, 0.220] | 4.746 [2.660, 7.655] |
| | E | −0.056 [−0.127, −0.028] | 6.456 [5.625, 10.144] |

### 3.2 Δ_N_eff = N_eff(B1) − N_eff(E)

| Block | Δ_N_eff [95% CI] |
|---|---|
| MMLU-Pro | 0.251 [0.153, 0.385] |
| Bank | −1.595 [−4.488, −0.734] |
| Combined | 0.269 [0.172, 0.404] |
| h01–h40 | −1.710 [−6.021, −0.552] |

On MMLU-Pro and combined, the interval lies above zero: compatible with part 2 of H3. In the bank, it lies below zero: in E, the remaining errors are spread across different models (slightly negative ρ̄), and N_eff exceeds 5. An N_eff above n only means anticorrelated errors; it does not mean "more judges than models". The bank's ρ̄ in E comes from very few errors: after exposure almost all models converge on the correct answer, and phi with so few errors per model is unstable. The bank's negative Δ should not be read as "exposure makes the panel more independent".

### 3.3 Correlation by model pair (MMLU-Pro, B1)

From 0.471 (Nemotron × Qwen) to 0.789 (Gemma × Qwen). No pair has an undefined correlation. The full table is in the report.

### 3.4 Homogeneous contrast: five copies of Gemma

| Block | ρ̄_error(B1) [95% CI] | N_eff(B1) [95% CI] | Mixed panel, ρ̄_error(B1) |
|---|---|---|---|
| MMLU-Pro (140) | 0.848 [0.759, 0.924] | 1.138 [1.065, 1.239] | 0.635 [0.541, 0.721] |
| Bank (52) | undefined | undefined | 0.031 |

In the bank, the five Gemma copies answered all 52 questions correctly in B1; with no errors, error correlation does not exist. On MMLU-Pro, the two intervals do not overlap.

### 3.5 Analytical sweep (n = 5)

| ρ̄ | 0.05 | 0.1 | 0.2 | 0.3 | 0.5 | 0.6 | 0.7 | 0.8 | 0.9 |
|---|---|---|---|---|---|---|---|---|---|
| N_eff (n = 5) | 4.17 | 3.57 | 2.78 | 2.27 | 1.67 | 1.47 | 1.32 | 1.19 | 1.09 |
| N_eff (n = ∞) | 20 | 10 | 5 | 3.33 | 2 | 1.67 | 1.43 | 1.25 | 1.11 |

With the MMLU-Pro ρ̄_error(B1) (0.635), the ceiling with infinitely many models would be 1.58; with 8 models, 1.47. Adding models of the same kind barely changes the effective number.

### 3.6 ρ̄_path: do the declared grounds overlap? (exploratory)

Jaccard overlap between the content words of the grounds declared in the CONTRIBUTION block, by model pair and question. Words from the question and the options are removed, so that restating the prompt does not count (`texto2/caminho_dos_fundamentos.py`).

| Block, condition | Both correct | Shared error (same option) | Different options | Responses with a ground beyond the decision |
|---|---|---|---|---|
| MMLU-Pro, B1 | 0.105 (727 pairs) | 0.059 (143) | 0.052 (273) | 7.0% |
| MMLU-Pro, E | 0.190 (805) | 0.113 (190) | 0.068 (113) | 1.8% |
| Bank, B1 | 0.072 (389) | 0.000 (2) | 0.024 (42) | 5.4% |
| Bank, E | 0.105 (395) | — | 0.052 (15) | 2.0% |

- In B1, shared errors have a ground overlap close to that of different options (0.059 vs 0.052), and below that of shared correct answers (0.105).
- In E, the overlap rises in all three groups; for shared correct answers, it nearly doubles (0.105 → 0.190).
- Only 7% of responses declare any ground beyond the decision; in E, 1.8%. The justification usually sits in the text of the decision itself.
- Limitation: shared words are not shared reasoning. The reading in §4.1b shows the same path in genuine errors that this measure does not separate. It only looks at what the peers see, not at the internal reasoning.

### 3.7 ρ̄_path in the internal reasoning (exploratory)

The same Jaccard as in §3.6, now on each model's internal reasoning. Words from the question, the options and the format vocabulary (JSON, relation, block) are removed, and pairs are split by outcome (`texto2/caminho_dos_raciocinios.py`).

| MMLU-Pro | Both correct | Both wrong, same option | One correct, one wrong | Different errors |
|---|---|---|---|---|
| B1 | 0.129 (838 pairs) | 0.130 (159) | 0.132 (203) | 0.124 (96) |
| E | 0.111 (921) | 0.125 (208) | 0.104 (86) | 0.133 (42) |

In the bank, in B1: 0.133 when both are correct (463 pairs) and 0.118 when one is correct and the other wrong (47).

- The overlap is the same in all four groups: by words, reasoning does not separate correct from wrong, nor shared errors from different options.
- It varies by model pair, not by outcome. In B1, Gemma × Qwen has 0.178 when both are correct and 0.208 when they err together; Mistral × Muse, 0.096 and 0.090. The measure captures each model's writing style.
- The step that decides the answer is usually one sentence (in m04145, "the concentrations are close to 1 M"), and it is lost in the long reasoning. Measuring the path requires extracting that step, by reading or with a judge model.

## 4. Caveats

### 4.1 Seven questions with all five on the same wrong option

On seven questions, all five models in the mixed panel chose the same option in B1, different from the key. We read all seven and cross-checked those inherited from the original MMLU with MMLU-Redux 2.0 (`texto2/redux_cruzamento.md`). The keys were not edited (344-79 item 3); we only report.

| Question | Origin | Key | Option of the five | Redux | Reading |
|---|---|---|---|---|---|
| m07756 | TheoremQA | H | D | not in Redux | wrong key: the series diverges; the key "0.0" comes from TheoremQA |
| m07114 | MMLU | G | F | key ok | distractor added by Pro, not reviewed (our reading finds it also correct) |
| m07045 | MMLU | E | C | key ok | distractor added by Pro, not reviewed (our reading finds it also correct) |
| m04776 | MMLU | H | C | key ok | distractor added by Pro, not reviewed |
| m05049 | MMLU | G | J | key ok | distractor added by Pro, not reviewed |
| m02530 | MMLU | C | B | absent from Redux | ambiguous (our reading) |
| m07001 | stemez | C | H | not in Redux | ambiguous (our reading) |

Each of these questions counts as a shared error of the five and pushes ρ̄ up. **Exploratory sensitivity** (outside the preregistration; `texto2/sensibilidade_sete_chaves.py`):

| Block | Measure | All | Without the 7 |
|---|---|---|---|
| MMLU-Pro | ρ̄_error(B1) | 0.635 [0.541, 0.721] (140) | 0.572 [0.460, 0.669] (133) |
| | ρ̄_error(E) | 0.826 [0.751, 0.894] | 0.789 [0.693, 0.869] |
| | N_eff(B1) | 1.413 | 1.521 [1.360, 1.760] |
| | Δ_N_eff | 0.251 [0.153, 0.385] | 0.318 [0.190, 0.500] |
| Combined | ρ̄_error(B1) | 0.615 (192) | 0.548 [0.440, 0.644] (185) |
| | Δ_N_eff | 0.269 [0.172, 0.404] | 0.344 [0.214, 0.528] |
| Gemma contrast, MMLU-Pro | ρ̄_error(B1) | 0.848 [0.759, 0.924] | 0.812 [0.701, 0.905] |

The sign of the conclusions in §3.1–3.4 does not change without the seven.

MMLU-Pro expanded the questions from 4 to 10 options with distractors generated by GPT-4-Turbo. False negatives (distractors that are also correct) were searched for with Gemini-1.5-Pro and removed by experts, and the authors themselves attribute these false negatives mainly to distractor generation (Wang et al., 2024, §3.2). Redux reviewed the key of the 4 original options, not the new distractors. **Residue of the filter.** The MMLU-Pro filter existed precisely to remove distractors that were also correct (Wang et al., 2024). It left a residue. In at least three questions, the added option is correct by the definition or the logic of the field, not by interpretation; in a fourth, it is the more precise one:

| Field | Question | Key | Added option chosen | Why it is also correct | Verdict |
|---|---|---|---|---|---|
| Economics | m07045 (monopsonist) | E: wage below the marginal revenue product of labour | C: single buyer of labour services (5/5) | It is the definition of monopsony; the key is a consequence | confirmed |
| Economics | m07114 (demand for kindergarten teachers) | G: fewer children per household | F: decline in the school-age population (5/5) | It reduces demand even more directly | confirmed |
| Technical research (physics) | m09169 (which statement is NOT correct) | F: IR to UV lines reveal nuclear structure | A: all elements have the same spectrum (3/5) | A, E and I are also false; the question gained several correct answers | confirmed |
| Medicine (physiology) | m03165 (venous and arterial pressures) | B: little effect on venous pressure | D: small decrease in venous pressure (4/5) | It is the more precise physics (ΔP = ΔV/C) | probable |

The check was made against the definition and the logic of each field, without consulting an independent source. Estimating the size of the residue across all of MMLU-Pro requires reviewing the added options, which is outside this study.

**Consequence for those who used MMLU-Pro.** On these questions, a model that chooses the correct added option is counted as wrong. Anyone who evaluated models or panels with MMLU-Pro may have had:

- an **inflated** error rate on these questions;
- an inflated error correlation between models, because several models "err" together on the same correct option;
- an underestimated N_eff, that is, the panel looks more dependent than it is.

The effect is largest where agreement between models is measured, because that is where several models converge on the same added option.

**The opposite case, in law.** On m01086 (criminal law), the models chose an original option, and Redux confirms the key: the error is theirs. The four that erred use the same doctrine and omit the same rule (solicitation merges into conspiracy once the agreement is reached). Here the shared error is genuine and follows the same path: in a legal panel, these are not four opinions but one error repeated four times with the appearance of consensus.

### 4.1b The other shared errors (exploratory)

Across the 140 MMLU-Pro questions, the largest block of models erring on the same option in B1 has 5 models on 7 questions (those in §4.1), 4 on 8 and 3 on 9. We read the reasoning and contributions for the 17 with 3 and 4, and cross-checked with Redux those that came from the original MMLU.

| Question | Origin | Key → block option (n) | How they got there | Redux | Reading |
|---|---|---|---|---|---|
| m01086 | MMLU | C → H (4) | transferred intent and Pinkerton; none merges solicitation into conspiracy | key ok; H is original | models' error, same path |
| m05302 | MMLU | I → H (3) | IVF with embryo screening | key ok; H is original | models' error |
| m05787 | MMLU | G → D (4) | Burgess's zone 4 | key ok; D is original | models' error (we had read "ambiguous numbering") |
| m02954 | stemez | F → H (3) | (1/4)^n ≈ 2/500 → n = 4, read as 4 genes rather than 4 pairs | not in Redux | models' error, same shortcut (our reading) |
| m04145 | stemez | F → I (3) | "concentrations close to 1 M", so E ≈ E° = 0.11 V; they ignore the 10<sup>−4</sup> | not in Redux | models' error, same shortcut (Qwen did the calculation) |
| m06785 | MMLU | B → H (3) | digestive symptoms → anorexia; those who get it right go through B12 | absent from Redux | models' error, same shallow path (our reading) |
| m03165 | MMLU | B → D (4) | ΔP = ΔV/C: small drop in the vein | key ok | distractor added by Pro, not reviewed |
| m04683 | MMLU | D → F (4) | escalation (LBJ) vs de-escalation (Nixon) | key ok | distractor added by Pro, not reviewed |
| m05018 | MMLU | F → G (4) | both the first women nominated by a major party | key ok | distractor added by Pro, not reviewed |
| m05022 | MMLU | B → H (3) | Copernicus is heliocentric | key ok | distractor added by Pro, not reviewed |
| m05198 | MMLU | B → I (4) | "they depend on states" | key ok | distractor added by Pro, not reviewed |
| m05220 | MMLU | G → B (3) | shame phase | key ok | distractor added by Pro, not reviewed |
| m09169 | MMLU | F → A (3) | "A is false without interpretation" | key ok | distractor added by Pro, not reviewed |
| m01566 | MMLU | E → D (4) | "the neighbour has no standing" (fee simple determinable) | absent from Redux | models' error or debatable key (our reading) |
| m02085 | MMLU | B → A (4) | the MIQ measures values, not interests | absent from Redux | ambiguous (our reading) |
| m01935 | MMLU | H → I (3) | "without reserve" obliges the sale | absent from Redux | ambiguous: H and I say almost the same (our reading) |
| m07513 | stemez | A → B (3) | public goods and stabilisation | not in Redux | ambiguous (our reading) |

**The 24 questions with 3 or more models erring together (7 + 17), side by side:**

| Class | Questions | Basis |
|---|---|---|
| Distractor added by MMLU-Pro, original key ok | 11 | Redux |
| Models' error, key ok | 3 | Redux |
| Models' error | 3 | our reading, not in or absent from Redux |
| Wrong key | 1 (m07756) | our reading, TheoremQA |
| Ambiguous or debatable | 6 | our reading |

In the models' errors we read, the block arrives by the same path or the same shortcut. Our own reading had marked several of the 11 as "doubtful key"; Redux says the original key is correct. What Redux did not review is the distractor MMLU-Pro added, and that is where the models converge.

### 4.2 Loss of Gemma responses (D5)

The provider serving Gemma rate-limited requests. In the mixed panel, 25 Gemma responses in the bank and 64 on MMLU-Pro were left without a position. In the MMLU-Pro contrast, 670 of 700 positions in B1 were obtained, and 130 of the 140 questions have all five copies (on m04776, only one). The loss comes from the provider, not the model; it reduces the sample of pairs and widens the contrast intervals.

### 4.3 Other

- ρ̄ is about error against an answer key. Contestable questions have no error; Fleiss agreement (ρ̄_behaviour) exists only in the bank and is descriptive.
- n = 5 is fixed; the sweep is analytical, not observed.
- Phi on vectors with few errors (bank) has a wide interval.

## 5. Discussion

On MMLU-Pro, five models from five providers are worth about 1.4 judges when blind and 1.2 after seeing each other. The mixed panel is below the homogeneous one (ρ̄_error of 0.635 vs 0.848), but far from independent. The exposure that changes positions in the first paper (H1 and H4) is the same that, on MMLU-Pro, brings the errors closer.

The new bank shows the opposite picture: nearly independent errors. This may be a difference of content, since the questions are new and probably outside the training data, or of difficulty. In the exploratory analysis (`texto2/novidade_ou_facilidade.py`), the error rate in B1 is 5% in the bank and 28% on MMLU-Pro, and no bank question has more than 2 of the 5 models erring. The bank's low ρ̄ is compatible with ease, and the design does not allow testing novelty in it. Within MMLU-Pro, questions inherited from the original MMLU have ρ̄_error(B1) = 0.68 [0.57, 0.78] and an error rate of 33% (81 questions); those added by MMLU-Pro, 0.51 [0.33, 0.67] and 20% (59). The intervals overlap, difficulty differs, and 5 of the 16 original questions with all five erring are among those in §4.1. Novelty and ease cannot be separated with these data; separating them requires new and difficult questions.

The mixed panel's ρ̄_error(B1) = 0.635 is compatible with Kim et al. (2025), who show at scale that models from different providers agree on errors far above chance. We did not find, in that literature or elsewhere, anyone showing that collective error concentrates on the options added by MMLU-Pro. The MMLU-Pro authors already knew that generated distractors could be correct and filtered those cases (Wang et al., 2024). What we add is that the filter left a residue, confirmed in at least three questions (economics and physics), and that this residue inflates error and error correlation precisely where agreement between models is measured (§4.1).

This has a consequence for anyone measuring panels with MMLU-Pro. Of the 24 questions with 3 or more models on the same wrong option, 11 converge on a distractor that MMLU-Pro added to the questions inherited from MMLU and that Redux did not review: Redux confirms the original key among 4 options, not the 6 new ones. Anyone computing error correlation or N_eff with MMLU-Pro counts these cases as shared errors. The data do not say whether the distractor is also correct or whether the models fell together for a plausible distractor. In both cases, the source of the shared error is in the question set, and ρ̄ mixes dependence between models with the noise of the added options. The sensitivity analysis without the 7 in §4.1 removes only 4 of these distractors; the other 7, from §4.1b, remain in the calculation.

## Data and code availability

Preregistration: OSF aw9vf (29 September 2026) and 5dpjr (11 November 2026); deviations D1–D7 in `studies/herd/desvios.md`. Code, banks, raw records and analysis: github.com/edubrinck86-code/Norvald-Lab (Lab PR #25 for D7; exploratory scripts in `studies/herd/texto2/`).

## Use of AI

The text was written in Portuguese and translated into English with Claude (Anthropic, Opus), and the author reviewed it. Data collection was orchestrated, and the analysis code was written, with Claude. Design decisions, interpretation and the text are the author's, who is fully responsible for the content.

## References

Gema, A. P., et al. (2024). Are We Done with MMLU? arXiv:2406.04127.

Kim, E. M., Garg, A., Peng, K., & Garg, N. (2025). Correlated errors in large language models. In *Proceedings of the 42nd International Conference on Machine Learning (ICML)*, PMLR 267. arXiv:2506.07962.

Wang, Y., et al. (2024). MMLU-Pro: A more robust and challenging multi-task language understanding benchmark. arXiv:2406.01574.

## Appendix A — Deviation D7

The ρ̄ of the main analysis was computed only on questions without unanimity in B1, contrary to the preregistration. Before → after, ρ̄_error(B1): bank −0.272 (11 questions) → 0.031 (52); MMLU-Pro 0.306 (61) → 0.635 (140); Gemma contrast 0.041 (18) → 0.848 (140). See `studies/herd/desvios.md`.
