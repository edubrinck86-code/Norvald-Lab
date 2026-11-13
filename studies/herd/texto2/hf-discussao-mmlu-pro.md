# Rascunho: discussão no Hugging Face (TIGER-Lab/MMLU-Pro)

Leitura pendente — proprietário. Publicar só com a aprovação do texto final.

---

**Title:** Added options that are also correct: question_id 7045, 7114 and 9169

Hi, and thanks for MMLU-Pro. While analysing a panel of five open models (Gemma 4 31B, Nemotron 3 Nano 30B, Mistral Small 2603, Qwen 3.8 27B, Muse Glimmer 30B), we found three questions inherited from the original MMLU in which one of the options added by MMLU-Pro is also correct. In each case the original key is fine (MMLU-Redux 2.0 marks it "ok"), but the added option is correct too, and most of the panel chose it.

**question_id 7045** (high_school_microeconomics), "A monopsonist is identified by one of the following:"
- Key: E, "A wage payment lower than the marginal revenue product of labor."
- Also correct: C, "A single buyer of labor services." This is the definition of a monopsony. All five models chose C.

**question_id 7114** (high_school_microeconomics), "Which of the following is most likely to decrease the demand for kindergarten teachers?"
- Key: G, "A decrease in the average number of children per household."
- Also correct: F, "A decrease in the population of school-aged children." This reduces demand for kindergarten teachers at least as directly as G. All five models chose F.

**question_id 9169** (college_physics), "Which of the following statements regarding radiation spectra is NOT correct?"
- Key: F, "Lines in the infrared, visible, and ultraviolet regions of the spectrum reveal primarily the nuclear structure of the sample."
- Also not correct: A, "All spectra are essentially the same for all elements." Each element has its own spectrum, so A is false as well. Three of five models chose A.

**Why it matters.** In our panel, these questions make models look as if they share an error when they are choosing a defensible answer. This inflates both the measured error rate and the measured error correlation between models. In our sample, of the 14 questions from the original MMLU where three or more models chose the same non-key option, 11 converge on an option added by MMLU-Pro. We confirmed the three above; the others may deserve a look. This is the same kind of issue as two of the cases in #55 (an added option that makes the key non-unique), on different items.

Details, data and code (preregistered study, CC BY 4.0): https://osf.io/gbx5m/ (text 2, section 4.1b) and https://github.com/edubrinck86-code/Norvald-Lab

Eduardo Guedes, independent researcher (ORCID 0009-0003-9960-3337)
