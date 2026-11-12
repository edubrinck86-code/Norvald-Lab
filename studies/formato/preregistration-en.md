# Does the Format of a Model's Own Previous Answer Anchor Reconsideration? Preregistration

Eduardo Guedes · Independent researcher · ORCID 0009-0003-9960-3337

Version of 12 Nov 2026. Follow-up to OSF gbx5m (registrations aw9vf and 5dpjr). No data have been collected for this study. Portuguese original: `studies/formato/preregistro.md`.

## 1. Question

In the Δ_herd study (aw9vf, 5dpjr), models shown their own previous answer rarely change it (B3: about 3%). Models shown only the letter they chose change much more often (B3L: 18.8% on MMLU-Pro, 10.3% on the new bank). Hao et al. (2026) report 37% with other models and free text.

B3 differs from B3L in two ways:
- **Content:** B3 shows the declared reasoning, not just the letter.
- **Format:** in B3 the previous answer enters as structured items and relations, not as text.

This study separates the two with a new condition that keeps B3's content and changes only its format.

## 2. Conditions

Every condition is derived from the B1 answers already collected in `conf2-banco` and `conf2-mmlu` (11 Nov 2026). The reconsideration instruction and the requested answer format are identical across conditions. Only the presentation of the previous answer differs.

| Condition | The participant sees | Status |
|---|---|---|
| B3 | its own B1 contribution, loaded as structured items and relations | collected (conf2) |
| B3L | only the option it chose in B1 | collected (x-b3l, exploratory) |
| **B3T** (new) | the same content as B3, rendered as plain text: each item becomes a paragraph with its declared confidence, each relation a sentence | to be collected |
| **B3R** (new, control) | the same as B3, collected now | to be collected |

B3R controls for drift over time: provider and served version may have changed since 11 Nov. B3T is compared with B3R, collected on the same day with the same configuration. The original B3 is a check only.

## 3. Panel and questions

- **Panel:** the same five models, each with the same fixed provider (deviation D1 of Δ_herd), and the same temperature, top_p, effort and max_tokens.
- **Questions:** the same as B3L, i.e. the questions that were not unanimous in B1: 30 from the bank and 61 from MMLU-Pro.
- **Data:** only stored B1 answers are used. No B1 is collected again.

## 4. Hypotheses

**H1 (confirmatory).** Changing the chosen option is more frequent in B3T than in B3R.
- **Test:** paired McNemar per participant × question, two-sided, α = 0.05.
- **Analysis:** both banks combined is the main analysis; each bank is reported separately.
- **Reading:** if H1 holds, the structured format anchors reconsideration. If B3T stays close to B3R, what anchors is the content (seeing the reasoning), and the format does not matter.

**H2 (descriptive).** Expected order: B3R ≤ B3T ≤ B3L. The three rates are reported with bootstrap CIs.

## 5. Measure

**Changed option:** the option chosen in the condition differs from the B1 option. This is the same rule used for B3 and B3L. The strict and permissive readings of new_grounds are reported as in Δ_herd, without a test.

## 6. Exclusions and retries

The rules of registration 344-79 apply:
- one retry for technical failure;
- an answer without a position is left out of the measure, with no imputation;
- each participant × question exclusion is recorded.

The sample size is fixed as above. There is no early stopping.

## 7. Cost

- **Size:** 182 experiments, about 910 calls.
- **Estimated cost:** US$ 0.90, based on the actual cost of B3L on the same questions (US$ 0.45 for 534 calls).
- **Cost limit:** the collection script (`studies/formato/coleta.py`) stops opening experiments once the accumulated cost exceeds US$ 2.00.

## 8. Declared limitations

- The B3T text comes from a B1 answer produced under the structured-format instruction. The "plain text" is the same answer without the structure, not an answer written freely from the start. A truly free-text B1 would be a second, separately registered stage.
- B3L is exploratory in Δ_herd and was collected on another day. It enters only as a descriptive reference (H2), without a test.
- Results hold for this panel and these two banks.

## 9. Deviations

Any deviation is declared in `studies/formato/desvios.md` with date, reason and effect, before any results text.

## 10. Implementation

- **Code:** the exposure `self_text` (B3T) and `render_own_text`, merged in Lab PR #26 (commit 8bc7142). Lab PR #27 (commit b836785) renders the B3T text in the round's language: a dry run before registration showed Portuguese text inside English prompts.
- **Analysis code, written before collection:** `studies/formato/medidas.py` (H1 and H2 exactly as in §4).
- **Test:** `tests/test_self_text.py` checks that every content item, confidence and chosen option of B3 appears in the B3T text, with no author structure and nothing from peers.
- **Repository:** https://github.com/edubrinck86-code/Norvald-Lab
