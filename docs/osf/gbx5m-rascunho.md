# Rascunho do registro gbx5m (OSF Preregistration)

Leitura pendente — proprietário. Texto em inglês, no tom do autor. Cada bloco corresponde a um campo do formulário.

## Hypotheses (344-2)

This is a follow-up to my preregistration aw9vf (osf.io/aw9vf, 29 Sep 2026). The main questions stay the same. What changed is the design, after calibration pilots. The changes are listed under "Other".

RQ1. When an LLM first answers alone and then sees what its peers answered, how often does it change position without giving a new reason?

RQ2. Does it change because of the peers' choices (the scoreboard) or because of the peers' written justifications?

RQ3. How many independent judges is the panel worth before and after exposure (effective sample size)?

H1 (peer exposure, same as aw9vf). The rate of position change without new grounds is higher in E (sees all peers' contributions) than in B3 (sees only its own previous answer).
Delta_herd = rate(E) - rate(B3)

H2 (self-anchoring, same as aw9vf). Delta_self = rate(B3) - rate(B2), reported as a result on its own.

H3 (effective sample size, same as aw9vf). N_eff = n / (1 + (n - 1) * rho_bar) is well below n, and exposure lowers it.
Delta_N_eff = N_eff(B1) - N_eff(E)

H4 (new). Seeing only the peers' choices moves models less than seeing their justifications.
Delta_position = rate(EP) - rate(B3)
Delta_justification = rate(E) - rate(EP)
I have no prediction for the sign of Delta_justification. Either sign is a result.

What I do not claim: that agreement is an error, that a model that changes is worse, or that dependence comes from conformity rather than shared training data. The design does not separate those.

## Existing data (344-4)

Option: Registration prior to creation of data.

Explanation: No confirmatory data exist. Before this registration I ran smoke tests and calibration pilots on 11 Nov 2026, between 14:33 and 16:34 Brasília time (UTC-3), as aw9vf allows ("pilot runs are used only to calibrate"). They are listed under "Other" with dates, sizes and costs. They used items that are excluded from the confirmatory sample, and they will not be pooled with it. I looked at their results; that is how the design changes below were decided.

## Explanation of existing data (344-14)

Instrument: Norvald Lab, my open multi-LLM deliberation lab (repository edubrinck86-code/Norvald-Lab, commit ba9c507). It replaces Norvald Studio, used in aw9vf, for this study. Every execution stores prompt, raw response, parsed structure, configuration, timestamps and the drawn order of peers.

The pilots showed four things that changed the design: (1) with 4 models, 3 of 5 contestable items tied 2 x 2, so a majority rarely existed; (2) my 12 ground-truth items were too easy (errors on only 2 of them); (3) calculation questions hit the 4096-token limit; (4) one model often broke the output format. The fixes are below.

## Study type (344-17)
Randomized Experiment (same as aw9vf).

## Blinding (344-32)
Subjects will not be aware of the assigned treatment (subjects are not human).

## Study design (344-40)

Fully within-subject. Every model answers every item in every condition.

PANEL. Five models from five families, all open-weight, 27B to 31B, released Dec 2025 to Aug 2026, all through OpenRouter:
google/gemma-4-31b-it, nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free, mistralai/mistral-small-2603, qwen/qwen3.8-27b, meta/muse-glimmer-30b.
Five instead of four so binary items cannot tie.
Same settings for all: reasoning effort "medium", temperature 0.7, top_p 1.0, max_tokens 8192, timeout 300 s. Prompts in English.
Architecture is declared per model (studies/herd/painel-arquiteturas.md): four dense, Nemotron is mixture-of-experts with 3B active parameters.

CONTRAST PANEL (positive control, same as aw9vf). Five instances of google/gemma-4-31b-it, B1 only, same settings.

CONDITIONS. Five. One thing is added at each step:
B1  first answer, blind, fresh session.
B2  blind repetition of B1, fresh session.
B3  sees only its own B1 contribution, asked to reconsider.
EP  (new) sees its own B1 contribution plus only which option each peer chose. No peer text, no peer confidence.
E   sees its own B1 contribution plus the full contributions of all peers (choice, justification, confidence).
So B3 is inside EP, and EP is inside E. Exposure is simultaneous: in the second wave nobody sees anyone else's second-wave answer.

Peers are shown with neutral labels (Analyst 1..5) that do not reveal the model. The order of peers is drawn per execution (sha256 of experiment, repetition and participant) and recorded.

ITEMS. Two blocks, frozen by sha256 before collection:
Block 1, my bank (studies/herd/bank.en.json, sha256 47e1dbacaf2c9ece...): 32 contestable items with 2 or 3 options, and 52 ground-truth yes/no items (g01-g12 from aw9vf plus h01-h40). h01-h40 were written with help from an AI assistant and checked against primary sources; they are reported separately from the other blocks.
Block 2, MMLU-Pro (TIGER-Lab/MMLU-Pro, test split, revision b189ec7): 10 items per category, 14 categories, 140 items, ranks 3 to 12 of a sha256 ordering within each category (salt "norvald-herd-mmlupro-v1"). Ranks 1-2 were the pilot and are excluded. Sampling does not look at answers or at disagreement. Ground truth is MMLU-Pro's key.

ORDER. B1 and B2 alternate item by item. B3, EP and E rotate across items (Latin square), so no condition always comes first.

EXECUTIONS. Block 1: 84 items x 5 conditions x 5 models = 2100. Block 2: 140 x 25 = 3500. Contrast panel: 224 items x 5 in B1 = 1120. About 6700 calls in total.

## Randomization (344-44)
Two randomisations, both per execution and both recorded: the order of peers in EP and E, and the interleaving of conditions across items (B1/B2 alternating, B3/EP/E rotating). No assignment of models to groups; all models see all conditions.

## Sampling (344-47)
Units are model x item. Models chosen within one size class, so dependence is not confused with capability. Items as described in Study design. The bank is frozen by sha256 before the confirmatory round and no item, option or key is edited after that. If a ground-truth key turns out wrong, the item is reported as such and kept out of the error analysis; it is not edited.

## Sample size (344-51)
Block 1: 84 items. Block 2: 140 items. 5 models, 5 conditions. Contrast panel: 224 items in B1.

## Sample size rationale (344-53)
Not a power analysis. In the pilot (28 MMLU-Pro items) the intervals of the main rates were roughly +-6 points; four times more items halves that width. 140 items is the largest block that fits the budget (about US$ 7 for the whole study). Block 1 has 84 items because that is the frozen bank.

## Stopping rule (344-55)
Collection starts when this registration is approved and stops when the planned matrix is complete. No interim analysis, no data-dependent stopping.
One retry per model and execution when the answer has no valid option (transport failure, empty answer or broken format), same configuration. Both attempts are kept; the retry is used; first-attempt failure rates are reported per model. This extends aw9vf, which retried only transport failures, because one model broke the format in about 7% of pilot calls.

## Manipulated variables (344-58)
One factor, five levels (B1, B2, B3, EP, E): what is in the Working Context when the model answers. Held fixed: items, options, models, provider, sampling settings, prompt language.

## Measured variables (344-62)
Same as aw9vf: selected_option, read mechanically from decision --selects--> option. Derived: changed_position (second-wave option differs from own B1 option), new_grounds (strict and permissive readings, as in aw9vf), error (ground-truth items), declared confidence. Also recorded: model, condition, item, timestamps, configuration, peer order, raw response, attempt number.

## Indices (344-66)
As in aw9vf:
rate(c) = changed_position AND NOT new_grounds, for c in B2, B3, EP, E.
Delta_self = rate(B3) - rate(B2); Delta_herd = rate(E) - rate(B3).
New: Delta_position = rate(EP) - rate(B3); Delta_justification = rate(E) - rate(EP).
rho_bar = mean pairwise phi between binary error vectors, ground-truth items; N_eff = n / (1 + (n - 1) * rho_bar) per condition, n = 5; Delta_N_eff = N_eff(B1) - N_eff(E).

## Statistical models (344-71)
Paired throughout.
Confirmatory tests, two-sided, alpha 0.05, Holm-Bonferroni across all five:
1. McNemar exact, E vs B3 (Delta_herd).
2. McNemar exact, B3 vs B2 (Delta_self).
3. Paired Wilcoxon on per-item dispersion change, E vs B3.
4. McNemar exact, EP vs B3 (Delta_position).
5. McNemar exact, E vs EP (Delta_justification).
Tests 1-3 are the ones registered in aw9vf; 4-5 are new. Reported corrected and uncorrected.
Effect sizes with bootstrap 95% intervals, resampling items, 20,000 replicates, fixed seed.
N_eff: no test; point estimate, bootstrap interval and the analytic sweep over rho in (0, 1] and n in {4, 5, 8, inf}, as in aw9vf.
Each block (my bank, MMLU-Pro) is analysed separately and then pooled; h01-h40 also reported alone.

## Transformations (344-75)
Same as aw9vf. No numeric transformation. Two dependence estimators kept apart: rho_bar_error (ground truth) feeds N_eff; rho_bar_behaviour (agreement beyond chance, contestable items) is descriptive.

## Inference criteria (344-77)
Same as aw9vf: alpha 0.05, two-sided, Holm over the five confirmatory tests. A null Delta_herd is a result. If Delta_self is large and Delta_herd is null, studies that compare round 1 with round N have been attributing self-anchoring to peers.

## Data exclusion (344-79)
Same rules as aw9vf, applied as the main analysis:
1. Items where all five models choose the same option in B1 are excluded from the main analysis; the discard rate is reported.
2. A model with no structured B1 contribution was seen by nobody and is excluded from the exposure analysis for that item.
3. Ground-truth keys are checked before collection; a key found wrong later is reported, not edited.
Deviation from aw9vf, declared: the same analyses are also reported with unanimous items kept, because in the pilot unanimous items were 36-57% of the sample and agreement itself is part of the question.

## Missing data (344-81)
Same as aw9vf. No imputation. Missing confidence handled pairwise. Parser rejections reported per condition and per model.

## Exploratory analysis (344-83)
Everything here is exploratory and will be labelled so.
1. Everything listed in aw9vf (rho behaviour vs error, contrast panel, pairwise asymmetry, peer position effects, literal collision, normalisation audit).
2. Conceptual replication of Hao et al. (2026, arXiv 2606.00820) on the same data: their five-way partition, strict conformity, C->W / W->C / W->W transitions and support-standardised harm minus benefit, mapping their a_0, a_sr, a_so, a_r to my B1, B3, EP, E. Computed on all items and on items with B1 disagreement (their filter). My B3 and EP show the model its full previous justification, theirs only the letter; this difference is mine and is declared.
3. Criteria from other papers (studies/herd/criterios-1.2.md, A-I), each with its compatibility rule written before collection.
4. Same answer, different reasons: similarity of justifications among models that agree, B1 vs E. Text similarity only; it may rise just because models copy words they read.
5. Who convinced whom: for models that change in E or EP, which peer's choice they moved to and whether list position matters.

## Other (344-86)
RELATION TO aw9vf. Same questions, same main measures, expanded design. Changes and why:
- 4 -> 5 models: ties (pilot).
- Prompts in English: language as a capability confound.
- New condition EP: separates choices from justifications.
- Ground truth 12 -> 52 items plus 140 MMLU-Pro items: the original 12 were too easy.
- max_tokens 8192 and one retry for broken format: pilot failures.
- Unanimous items also reported kept.
- Instrument: Norvald Lab instead of Norvald Studio.

DATA ALREADY COLLECTED, AND WHAT EACH ONE IS FOR. All on 11 Nov 2026, Brasília time. All of it is published with this registration (files attached: collection log, raw summaries and the pilot measures report). None of it is pooled with the confirmatory data.

1. Instrument check (smoke). Did the lab run end to end and record what it should?
fumaca-1 14:33-14:35, B1/B2, 2 items, 16 calls, US$ 0.006
fumaca-2 14:36-14:38, B1/B2/B3/E, 2 items, 32 calls, US$ 0.019
Found: free Mistral key had zero quota; free Gemma failed; Nemotron cut its answer at 2000 tokens; peer order was missing from the raw record. All fixed before the pilots.

2. Calibration. Used to set the design. Results grounded the changes listed above.
piloto-1 14:42-14:46, B1, 17 items, 4 models, Portuguese, 68 calls, US$ 0.034. Ground truth too easy.
piloto-2 14:47-14:51, B1, 17 items, 4 models, Portuguese, 68 calls, US$ 0.037. Errors on only 2 of 12 ground-truth items; 3 of 5 contestable items tied 2 x 2.
piloto-3 14:54-14:56, B1, 10 items, 5 models, Portuguese, 50 calls, US$ 0.036. With 5 models: 5 majorities, 3 ties, 2 unanimous.
piloto-mmlu-1 15:18-15:30, B1, 28 MMLU-Pro items (ranks 1-2), 5 models, English, 140 calls, US$ 0.144. 5 answers hit 4096 tokens; format failures.

3. Pilot of the full design (grounds the sample size and is reported as a pilot result, not as confirmation).
piloto-mmlu-2 15:36-16:34, all five conditions, the same 28 MMLU-Pro items, 5 models, English, 722 calls, 22 retries, US$ 0.731. Its full measures report is attached. Main numbers, descriptive only: 2.9% changed on self-reflection, 2.2% changed on seeing only peers' choices, 6.5% changed only after reading peers' justifications; unanimity in E vs B3 +17.9 points with no change in accuracy; N_eff 1.64 of 5.

4. Confirmation. Only the data collected after this registration is approved, on the items and settings described above. Only these data test H1-H4.

RELATED WORK KNOWN BEFORE DATA. Kohli (2026, arXiv 2605.29800) and Acharya, Pan and Verkhovsky (2026, RoPoLL, arXiv 2606.30931) use the same effective-sample-size formula for panels that do not interact. Hao et al. (2026) decompose stance changes with stance-only and full-reasoning conditions on copies of one model. This study measures heterogeneous panels under exposure.

USE OF AI. I used an AI assistant (Anthropic Claude) to write the lab code, run analyses, draft items h01-h40 and draft text, including this registration. Design decisions and their reasons are mine and are logged with dates. The assistant is not one of the observed models.
