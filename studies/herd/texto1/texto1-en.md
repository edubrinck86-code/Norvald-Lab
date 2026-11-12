# How Many Contribute and How Many Just Agree? Reconsidering Is Not Instability: What a Model Sees of Itself Explains Part of the Change Attributed to Peers

Eduardo Guedes · Independent researcher · ORCID 0009-0003-9960-3337

## Abstract

When a language model changes its answer after seeing other models, has it contributed something new or merely agreed? Studies of debate among LLMs usually read this change as peer influence, and recent work finds more than a third of answers changing even without peers, which is read as model instability. We show that this baseline depends on what the model is shown about itself.

In a preregistered experiment (OSF aw9vf and 5dpjr), five models from five providers answered 224 multiple-choice questions, 140 from MMLU-Pro and 84 from a new bank, under five matched conditions: blind, blind again, seeing their own previous contribution, also seeing the peers' positions, and seeing the peers' full contributions. The measure, with no judge, is changing the option without declaring a new ground.

On the questions where the panel started divided, answering again blind changed 23% of the answers; seeing one's own reasoning reduced this to 2%. Seeing the peers' contributions brought the change back to 20%: positions alone pulled little (+3.6 points) and the peers' reasoning pulled much more (+14.0 points). All five confirmatory tests passed after Holm correction, and accuracy barely changed. In an exploratory arm that shows the model only the letter of its previous answer, as in the most common control, the change rose back to 19% and 10%. Reconsidering is not instability: it depends on what the model sees of itself, and this difference explains part of the change attributed to peers.

## 1. Introduction

This work grew out of an observation made while building a document-engineering software assisted by several AI agents, built from scratch on a framework of my own, without AutoGen. In the debates among the models, a composite confidence metric (CC) emerged, proposed to assess the feasibility of a second system, for autonomous software construction. The debates themselves showed that the CC was not feasible: one of its components, the adjusted agreement (C_adj), depends on information that companies do not disclose, and therefore cannot be measured, nor can the parts that make it up (the overlap of training data, alignment and architecture between models). Even so, because the platform recorded the contributions as running text, it was possible to see that the models agreed, and insisted, precisely on this unmeasurable point. This agreement about something none of them could verify raised the question of this study: where does agreement among LLMs come from, how much of it is independent, and how much reflects individual contribution? In short: how many LLMs were contributing, and how many were just agreeing?

Even before any measurement, the observations already suggested a pattern: changing the way of asking changed the way of answering, but the conclusion held. The data partly confirm this and refine it. When the model sees its own previous contribution, it rewrites the argument in other words and almost never changes its answer (fewer than 3 in 100). But when the question is contested and the model answers again blind, 21 to 25 answers in 100 change. The observed stability therefore does not come from the model alone. It also comes from the model seeing what it had already thought. Our hypothesis is that the previous reasoning works as an argument: if the model finds it convincing, it tends to keep it.

These results matter to anyone who uses several agents to evaluate models, or for any task that depends on more than one opinion or execution. If showing the peers' work changes answers without adding arguments and with almost no change in accuracy, exposure makes the process more expensive without improving the decision. The most informative vote is the first-round, blind one. The next question, which we address in complementary work, is how many agents actually add an independent opinion: knowing this allows fewer agents to be used, in parallel, on the same task, saving cost without losing performance.

Consider a bank that uses two or three agents to assess a credit application, each one reviewing the previous one's assessment. What guarantees that the second or third assesses independently, rather than simply following the first? Nothing, unless the system separates what the agent decided on its own from what changed after it saw the others. This work measures exactly that separation: how much an agent changes by chance, how much it holds on to its own reasoning, and how much it is pulled by its peers without having received a new argument.

## 2. Related work

**Debate versus voting.** Choi et al. (2025) show that most of the gain from multi-agent debate comes from majority voting. Wynn et al. (2025) find that agents abandon correct answers when faced with incorrect reasoning, in panels of agents with different capabilities. Bertalanič and Fortuna (2026), with teams of identical small models, find that isolated self-correction is cheaper and equally or more accurate than debate.

**Conformity.** Cho et al. (2025) and Zhu et al. (2025) document herd behaviour and Asch-style conformity in LLMs. Baltaji et al. (2024) treat conformity as one form of persona inconstancy in multi-agent collaboration. Sharma et al. (2023) show that models tend to follow the user even when the user is wrong (sycophancy).

**Matched decomposition.** Hao et al. (2026) evaluate each model under three matched conditions: self-reflection, positions only, and full reasoning. With five GPT-4o agents on MMLU-Pro, 36.98% of answers change under self-reflection alone, and 29.30% of those that stayed stable adopt a peer's answer when seeing only positions. Their control shows only the letter of the previous answer and asks the model to reconsider. Blind repetition appears only on an auxiliary benchmark (GPQA: 22.4%).

**Matched reflection and reasoning versus answer.** Batra et al. (2026) use a control in which the agent sees its own previous response without the peers (the equivalent of our B3) and show, through the model's internal probabilities, that the peers' reasoning carries more weight than their answer (69% of the influence). They use copies of a single model, with no blind repetition and no preregistration.

**Changing the answer is not changing the mind.** Ni and Zou (2026) show that a model that yields to the majority still represents its original premise internally, and that hiding the previous answer increases conformity.

**What this work adds.** We confirm the anchoring found by Batra et al. and the greater pull of reasoning over positions, at the level of behaviour and in a panel of five providers. What is new here is: blind repetition (B2) in the main design, separating chance from anchoring; preregistration of the analysis; a heterogeneous panel with each model pinned to one provider; a measure with no judge; a new question bank; and an exploratory arm (B3L) that reproduces the control of Hao et al. on our panel and explains part of the difference between their figures and ours.

## 3. Design

**Conditions, in protocol order.**

| Condition | What the model sees |
|---|---|
| B1 | The question and its options (no documents, no external tools) |
| B2 | The same, sampled again |
| B3 | Its own full B1 contribution: reasoning, grounds, choice and confidence |
| EP | Its own contribution, plus only the options chosen by the peers |
| E | Everyone's full contributions, in an order randomised at each execution |

In B3, EP and E the model receives the same instruction: "Reconsider the task in light of the contributions available in the context."

**Main measure.** Changing the option, relative to B1, without declaring a new ground. "New ground" has two readings, reported side by side: the strict one, registered as primary (a ground that only points to a peer's contribution does not count as new), and the permissive one (it counts). Δ_self = rate(B3) − rate(B2); Δ_herd = rate(E) − rate(B3).

**Panel.** Five models, each pinned to a single provider through OpenRouter (deviation D1): Gemma 4 31B (Crusoe), Qwen3.8 27B (DeepInfra), Muse Glimmer 30B (DeepInfra), Mistral Small 2603 (Mistral) and Nemotron 3 Nano Omni (Nvidia). Same settings for all: temperature 0.7, top_p 1.0, reasoning effort "medium", up to 8,192 tokens, prompts in English. Each execution may have one retry with the same settings. We chose open mid-sized models because large commercial models do not expose their full reasoning, and the measure depends on reading what each participant declared. The aim is not to know whether answers are right, but to measure how many independent contributions the panel produces.

**Questions.** 140 from MMLU-Pro (Wang et al., 2024) and 84 from a new bank: 32 contestable items with no answer key, and 52 keyed items (12 from the author's earlier test map and 40 new ones). Questions on which the panel was unanimous in B1 are excluded from the main analysis, as registered (79 and 54 of them); results including them are reported in the appendix.

**Exclusions.** A participant without a valid contribution in B1 is excluded only from that question (registration 344-79, item 2): 30 cases in 28 questions, mostly due to provider rate limits on Gemma.

**Pilots and cost.** Smoke tests and calibration pilots were run on 11 November 2026, before the collection was registered, on items outside the confirmatory sample; they are declared in the registration and not pooled. API cost was about US$5 (US$1.33 for the bank, US$3.76 for MMLU-Pro).

**Analysis.** Five confirmatory tests, two-sided, α = 0.05: exact McNemar for E versus B3 (H1), B3 versus B2 (H2), EP versus B3 and E versus EP (H4), and a paired Wilcoxon test on per-question dispersion, with Holm correction over the five. Each bank separately, pooled, and items h01–h40 alone. Effect sizes with 95% bootstrap intervals resampling questions (20,000 replicates, fixed seed).

## 4. Results

Rate of change without a new ground, on questions where the panel started divided:

| Condition | MMLU-Pro | New bank |
|---|---|---|
| B2, blind again | 24.5% | 21.2% |
| B3, sees itself | 2.9% | 0.7% |
| EP, sees positions | 6.2% | 5.6% |
| E, sees peers' full contributions | 21.6% | 17.4% |
| Δ_self | −0.211 [−0.268; −0.156] | −0.196 [−0.261; −0.136] |
| Δ_herd | 0.186 [0.142; 0.232] | 0.163 [0.110; 0.217] |

**What pulls more (both banks pooled).** Seeing only the positions (EP versus B3): +3.6 points [1.7; 5.7], p = 0.003. Seeing the reasoning beyond the positions (E versus EP): +14.0 points [10.6; 17.5], p < 0.001.

**Tests.** With Holm correction over five, all five tests pass on the bank, on MMLU-Pro and pooled; EP versus B3 passes narrowly in each bank (p = 0.031 and 0.049). On items h01–h40 alone, only H1 and H2 pass.

**Accuracy.** Barely changes: +3.6 per 100 move to the correct option and 1.3 per 100 move from correct to incorrect.

**In the categories of Hao et al.** Instability 2.9% (37% there); strict conformity 5.3% (29.3% there).

**Exploratory arm B3L (not preregistered).** Seeing only its own previous letter, 18.8% of answers change on MMLU-Pro and 10.3% on the bank, between B2 (24.5% and 21.2%) and B3 (2.9% and 0.7%). B3L − B3: +16.2 points [11.6; 21.1] on MMLU-Pro and +8.4 [3.5; 14.2] on the bank, p < 0.001 in both (exact McNemar, uncorrected). 73 of 91 B3L executions completed.

## 5. Discussion

**Why the peers' reasoning pulls more than their positions.** Models are trained mostly on text and tend to follow the direction of the text they receive. It is the same mechanism that makes a model follow the user even when the user is wrong, so-called sycophancy (Sharma et al., 2023). A position alone is a weak signal; a full line of reasoning is argued text, and argued text induces more. Two pieces of evidence point in this direction. In Hao et al. (2026), wrong but plausible reasoning led to adoption of the wrong answer more often than the bare position (87% versus 64%, GPT-4o). In our data, models that change after seeing their peers change without declaring a new ground: what is adopted seems to be the direction of the others' text, not an argument the model comes to hold. This explanation is a hypothesis; testing it would require comparing models with different alignment.

**The difference from Hao et al.** The difference between their 37% and our 3% lies in the design of the control itself. In both cases the model is invited to reconsider. There, it sees only the letter of its previous answer; here, it sees its own full reasoning, with grounds and confidence. Without the reasoning, reconsidering is close to answering again, and chance decides; with it, the model finds a ready-made argument and tends to keep it. We tested this on our panel with an exploratory arm that reproduces their control (B3L): showing only the letter brought the change to 18.8% on MMLU-Pro and 10.3% on the bank, between blind repetition (24.5% and 21.2%) and the full reasoning (2.9% and 0.7%). The "reconsideration instability" is therefore not a fixed property of the model: it depends on what the control shows. The form of the control explains much of the difference, but not all of it: even with the letter only, our panel stays below 37%. The rest should come from other differences between the studies, such as the models and the temperature, which we did not measure.

**Reach and caution.** The reach goes beyond the platform where the observation started. Multi-agent systems are beginning to be used where one agent reviews another's work before a decision: a second opinion on a diagnosis, the review of a credit assessment, the check of a legal draft. This study measured none of these areas, and its results come from multiple-choice questions. But the mechanism we describe, changing one's answer on seeing another's reasoning without bringing a new argument, does not depend on the domain. Where it exists, the second opinion stops being independent without anyone noticing. These areas can therefore benefit from the design, with caution and testing: before trusting review among agents, measure in the domain itself how much each agent changes when blind (B2), when seeing itself (B3) and when seeing the others (E), and only then decide what to show each one.

## 6. Limitations

- Five small and mid-sized models, a single round of exposure, multiple-choice only.
- Pinning each model to one provider trades routing noise for a single provider's rate limit, which affected Gemma most (D5).
- The new bank is small: 30 divided questions remain.
- Effective sample size (H3) and the memory hypothesis are left to a companion paper.
- The "new ground" is what the model declares in the structured block. Nobody checks whether the declared ground is true or whether it actually weighed in the decision.

**AI in the tool and in the analysis.** The collection tool and the analysis code were built with the help of AI, and the collection itself was orchestrated with it. Three safeguards reduce this risk without eliminating it. First, the measures are deterministic: no language model judges whether an answer changed or brought a new ground; both are mechanical comparisons over each contribution's structured block. No collected or analysed data were judged right or wrong, good or bad, by the author or by the AI, except through the answer keys of the banks (MMLU-Pro's and the new bank's, fixed before collection); we only collect the data and evaluate them algebraically. Part of the new bank's key (40 of the 52 keyed items; the other 32 are contestable and have no key) was drafted with the help of AI and checked item by item against primary documentation (RFCs, official documentation) before the collection was registered; the check is public, and one item (h11) was replaced for lack of a primary source. Second, the analysis plan was registered before any data, and deviations are publicly declared. Third, the code, raw data and automated tests are public. The remaining risk is an implementation error not covered by the tests; during this work two such errors were found and fixed, and are documented: the lab excluded a whole question when one participant failed, whereas the registration requires excluding only that participant (D4), and the analysis ran three of the five registered tests (D6). We therefore invite independent replication.

**The format of the contribution.** The contribution each model sees is presented in the structured format of the author's document-engineering framework, developed in his Studio platform: the choice, the grounds as typed relations (derived_from, documents) and the confidence. B3 therefore measures self-anchoring in this format. Reasoning presented as free text may anchor less, and the difference between formats was not measured. The same applies to exposure to peers (E). Comparing the same control in free text and in structured format is a direct next step.

## Data and code availability

Preregistration: OSF aw9vf (29 September 2026) and 5dpjr (11 November 2026); deviations D1–D6 in OSF component gbx5m. Code, banks, raw records and analysis: github.com/edubrinck86-code/Norvald-Lab (Lab PRs #17–#23; commit 5bfe39d).

## Use of AI

The text was written by the author in Portuguese and translated into English with Claude (Anthropic, Opus), and the author reviewed the translation. Data collection was orchestrated, and the analysis code was written, with Claude. Design decisions, interpretation and the text are the author's, who is fully responsible for the content.

## References

Baltaji, R., Hemmatian, B., & Varshney, L. R. (2024). Conformity, confabulation, and impersonation: Persona inconstancy in multi-agent LLM collaboration. In *Proceedings of the 2nd Workshop on Cross-Cultural Considerations in NLP (C3NLP)*, 17–31. ACL.

Batra, A., Khandelwal, A., Khemani, J., Thukral, K., Gumber, A., Lim, D. F., Kumar, U., & Tan, P. X. (2026). Who convinced whom? Tracing how LLMs change their minds in multi-agent systems. arXiv:2610.35930.

Bertalanič, B., & Fortuna, C. (2026). The cost of consensus: Isolated self-correction prevails over unguided homogeneous multi-agent debate. arXiv:2605.00914.

Cho, Y.-M., Guntuku, S. C., & Ungar, L. (2025). Herd behavior: Investigating peer influence in LLM-based multi-agent systems. arXiv:2505.21588.

Choi, H. K., Zhu, X., & Li, S. (2025). Debate or vote: Which yields better decisions in multi-agent large language models? *NeurIPS 2025*. arXiv:2508.17536.

Hao, X., Wu, Z., Qiu, Y.-X., Xiao, C., Xu, R., Zheng, S., & Qin, J. (2026). Not all flips are conformity: Decomposing stance convergence in multi-agent LLM debate. arXiv:2606.00820.

Ni, Z., & Zou, P. (2026). Silent dissent: LLM agents that yield to the majority still represent their original premise. arXiv:2610.02702.

Sharma, M., Tong, M., Korbak, T., et al. (2023). Towards understanding sycophancy in language models. arXiv:2310.13548.

Wang, Y., Ma, X., Zhang, G., et al. (2024). MMLU-Pro: A more robust and challenging multi-task language understanding benchmark. *NeurIPS 2024 Datasets and Benchmarks Track*. arXiv:2406.01574.

Wynn, A., Satija, H., & Hadfield, G. (2025). Talk isn't always cheap: Understanding failure modes in multi-agent debate. ICML 2025 Workshop on Multi-Agent Systems. arXiv:2509.05396.

Zhu, X., Zhang, C., Stafford, T., Collier, N., & Vlachos, A. (2025). Conformity in large language models. In *Proceedings of ACL 2025*. arXiv:2410.12428.

## Appendix A — Results including unanimous questions

Same measures with the questions that were unanimous in B1 kept in (all 140 and 84 questions). Rates fall because unanimous questions rarely change; the direction of every effect is the same.

| Condition | MMLU-Pro | New bank | Pooled |
|---|---|---|---|
| B2 | 12.4% | 9.5% | 11.3% |
| B3 | 1.4% | 0.2% | 0.9% |
| EP | 2.7% | 2.0% | 2.4% |
| E | 9.2% | 6.2% | 8.1% |
| Δ_self | −10.9 points [−13.9; −8.0] | −8.9 [−12.2; −6.0] | −10.1 [−12.4; −8.0] |
| Δ_herd | +7.7 [5.4; 10.3] | +5.8 [3.4; 8.5] | +7.0 [5.2; 8.9] |
| EP − B3 | +1.2 [0.0; 2.5] | +1.5 [0.5; 2.8] | +1.3 [0.5; 2.2] |
| E − EP | +6.4 [4.3; 8.7] | +4.3 [2.1; 6.8] | +5.6 [4.0; 7.4] |

With Holm over five, all tests pass in every block except EP versus B3 on MMLU-Pro (p = 0.096); pooled, all five pass.
