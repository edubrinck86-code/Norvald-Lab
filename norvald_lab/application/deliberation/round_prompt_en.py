"""Textos do prompt em inglês (spec `language: "en"`), criado em 11/11/2026.

Até esta data tudo o que o Lab injetava no prompt estava em português, e o
idioma ficava misturado com a capacidade medida. O dono decidiu que a coleta
do estudo seria em inglês, para os números serem comparáveis aos artigos
publicados.

É tradução fiel de `TEXTS_PT` (em `round_prompt.py`), chave a chave: a mesma
estrutura, a mesma ordem das seções, os mesmos marcadores
(`<<CONTRIBUTION>>`/`<<END_CONTRIBUTION>>`), as mesmas chaves JSON e os mesmos
nomes de tipos e relações. Nenhuma regra foi acrescentada ou removida. A
lógica de montagem não está aqui: continua em `render_shared_instructions`,
que só escolhe o catálogo de textos pelo idioma.

Escolhas de tradução:
- "Working Context", "Evidence", "Constitution", "Framework" e "CDD" ficam
  como no original: já são nomes do protocolo, em inglês.
- A confiança declarada pede `high`, `medium` ou `low`; o extrator normaliza
  para `alta`, `média` e `baixa` (ver `outcome_extract.py`).
"""

from __future__ import annotations

from typing import Dict

TEXTS_EN: Dict[str, str] = {
    "goal": "Your goal is to produce the best possible contribution to the deliberation objective. The LLM is responsible for interpreting the question, reasoning, deciding whether it needs the tools available in this phase, and evaluating the results obtained.",
    "wc_truth": "The Working Context is the source of truth for deliberative knowledge. What is in it has been declared and validated. Do not treat a tool result, document, search or intermediate reasoning as Working Context knowledge unless you declare it in the CONTRIBUTION block.",
    "tools_optional": "Tools are optional means, not the goal of the turn. You may answer directly. Do not use tools just because they are available. The only operational exception is scan_context when the runtime reports that the Working Context projection is partial: go through all the blocks before concluding.",
    "n0": "N+0: use the initial WC, its anchors and the attached Evidence that was passed directly in this first execution. Library/Repository/WC may be consulted when available in this execution; MCP/Web are not yet part of this phase.",
    "n1plus": "N+1 onward: first consult/evaluate the WC and the positions already declared. If the WC does not fit entirely in the resident projection, Studio does not choose which parts are relevant: the remainder is presented in canonical order by scan_context. When reading each block, retain_ids must contain only the addresses that you yourself judge possibly relevant for later retrieval. The Evidence anchors remain in the WC, but the attached body is not resent as a block every round. Library/Repository may be used when available in this execution; MCP/Web may be used when configured, permitted and materially necessary.",
    "no_dump": "Do not dump catalogs, graphs, raw results or complete documents into the deliberation context. Use the tools to investigate and turn the result into knowledge only when there is a valid deliberative declaration.",
    "evidence": "Evidence may come from the Context tab, Library, Repository or a source declared by the specialist. When using Evidence, preserve the citation and provenance; do not incorporate the complete document into the WC.",
    "after_tool": "After a tool, evaluate the result and decide whether to answer or investigate further. Do not repeat a query without a new reason. If the evidence is sufficient, stop searching and compose the contribution.",
    "focus": "The deliberation objective is the permanent problem. The MODERATOR FOCUS, when present in the message, governs this round only: use it to decide where to concentrate the analysis, even if the previous round was following a different emphasis. It does not erase or rewrite the permanent objective.",
    "respond_prev": "If the previous round appears in the message, respond to it: agree with grounds, disagree with grounds, or advance the point. Do not repeat what has already been said.",
    "tool_rules": "The available tools are real capabilities of Studio. The runtime controls permission, security, time and execution; it does not choose the tool for you. There is no native number of calls that you need to save: investigate while there is material progress and stop when there are sufficient grounds to compose the Contribution. Repeated calls without new information do not advance the task.",
    # Cabeçalho do bloco obrigatório, até o delimitador de abertura inclusive.
    "contribution_intro": "MANDATORY: end your answer with the block below, exactly with these delimiters and plain JSON (no code fence, no indentation and no line breaks inside the JSON):\n<<CONTRIBUTION>>\n",
    "contribution_example": '{"knowledge":[{"local_id":"k1","type":"inference","content":"...","confidence":"medium"}],"relations":[{"relation_type":"derived_from","source":"k1","target":"evidence-<id>"}]}\n',
    # {types} recebe DECLARABLE_KNOWLEDGE_TYPES.
    "contribution_tail": "type is one of: {types}. One unit per statement of yours. "
    "For claim, argument, counterargument, inference and decision, declare "
    "`confidence` (high, medium or low): without it the reader of the document "
    "cannot tell a finding from a bet. It is not a certification of truth "
    "— it is the weight you yourself assign to your statement. "
    "Brevity rules apply to the prose, not to this block: without it nothing enters the Working Context and the round leaves no knowledge.",
    # Termina em ":\n"; o guia de relações é anexado depois.
    "relations": "RELATIONS declare the fabric between units — they are not an optional "
    "extra. A unit without a relation stays isolated in the graph: it does not "
    "count toward the coverage of any criterion and does not appear linked to "
    "anything when the CDD is consulted later. Whenever a unit of yours "
    "answers, refines, challenges, supports or derives from another — yours "
    "or one already in the Working Context —, declare the corresponding "
    "relation; that counts as much as declaring the unit itself. Only do not "
    "declare one when the relation genuinely does not exist: fabricating one "
    "to fill the gap is worse than declaring too few, but declaring too few "
    "has a real cost. `source` is a `local_id` from this contribution; `target` "
    "is a `local_id` from this contribution OR an id already existing in the "
    "Working Context (this case's evidence appears as `evidence-<id>` in the "
    "evidence block and is a valid target). The allowed ones:\n",
    "lifecycle": "GAP LIFECYCLE: an existing [gap] is addressable by the UUID "
    "shown in the Working Context. If your new knowledge really fills an "
    "existing gap, do not create another textual copy: declare the new "
    "claim/evidence and a resolves relation pointing to the gap's UUID. "
    "If the problem still exists but needs to be reformulated, declare the "
    "new gap and a supersedes relation pointing to the UUID of the previous "
    "gap. Only create a new gap without these relations when it is a "
    "genuinely new gap. Studio does not decide by similarity whether two "
    "gaps are the same; that semantic judgment is yours.",
    "channels": "KEEP THE TWO CHANNELS SEPARATE. The prose is the argument addressed to the other "
    "specialists: what you maintain and why. The block is the structured "
    "declaration, read by Studio. Do not narrate the block in the prose — "
    "do not write \"I declare a claim\", do not list the types, the "
    "local_id, the relations, the confidence or the dimensions in running "
    "text. That is already in the block, and repeating it in the prose "
    "clutters the reading without adding knowledge. Write the prose as "
    "you would write to a colleague who does not know the format.",
    # Seguido dos nomes das dimensões e de ".".
    "dimensions": 'In each unit, include "dimension_id" with the Framework dimension it belongs to, when there is one that fits. Omit the field if none fits. Use exactly the name, in lowercase and with a hyphen in place of the space (e.g.: "Human Factors" becomes "human-factors"). Dimensions: ',
    # render_constitution_block; {bodies} recebe as Constitutions.
    "constitution": "RULES OF THIS DELIBERATION (Constitution). They are not material to "
    "deliberate on: they are instructions to follow in this turn, and they prevail "
    "over your preferences of format or approach. Where they "
    "conflict with the declared objective, follow the rule and point out the "
    "conflict in the prose.\n\n{bodies}",
    # runner.prepare
    "lab_profile": "LAB PROFILE: the corpus and the context above are complete and frozen. The only possible tools are list_documents and read_document when offered. There is no access to Studio, web search or other documents. scan_context does not exist in this execution.",
    "identity": "You are {name}, acting as {role}.",
    "reconsider": "Reconsider the task in light of the contributions available in the context.",
    "corpus_header": "FROZEN CORPUS OF THIS EXPERIMENT:",
    "wc_header": "COMPLETE WORKING CONTEXT:",
}
