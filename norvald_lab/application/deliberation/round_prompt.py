"""Montagem determinística do prompt de uma rodada.

Nenhuma LLM participa daqui: é recorte e concatenação do que já está na
timeline e no Working Context.

O prompt distingue conhecimento deliberativo persistente de investigação
efêmera. O WC é a fonte de verdade; KG, Library e demais ferramentas são
capacidades sob demanda e seus resultados não são despejados no contexto por
catálogo.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from norvald_lab.domain.deliberation.dimension_registry import DimensionRegistry
from norvald_lab.domain.deliberation.turn_policy import phase_text, policy_for
from norvald_lab.domain.deliberation.contribution import DECLARABLE_KNOWLEDGE_TYPES, strip_contribution_block

PREVIOUS_TURN_CHARS = 800


def directives_for_round(
    timeline: List[Dict[str, Any]],
    round_number: int,
    *,
    participant_id: str = "",
) -> List[str]:
    """Diretivas explicitamente destinadas a uma rodada.

    A posição física do control.prompt na Timeline não define mais
    consumo. Uma fala do moderador enviada enquanto N ainda está em voo
    pode estar cronologicamente antes de round.completed N e, mesmo
    assim, pertence a N+1. target_round separa esses dois conceitos.

    Eventos antigos continuam legíveis: sem target_round, o campo
    histórico round é usado como destino.
    """
    notes: List[str] = []
    for entry in timeline:
        if not isinstance(entry, dict) or entry.get("event") != "control.prompt":
            continue
        try:
            target_round = int(entry.get("target_round") or entry.get("round") or 0)
        except (TypeError, ValueError):
            continue
        if target_round != round_number:
            continue
        if str(entry.get("visibility") or "shared") == "private":
            continue
        raw_target_ids = entry.get("target_participant_ids")
        if raw_target_ids is not None:
            target_ids = {
                str(value)
                for value in (raw_target_ids or [])
                if str(value)
            }
            if not target_ids:
                continue
            if participant_id and participant_id not in target_ids:
                continue
        note = str(entry.get("instruction") or entry.get("note") or "").strip()
        if note:
            notes.append(note)
    return notes


def previous_round_digest(timeline: List[Dict[str, Any]], round_number: int) -> List[str]:
    if round_number <= 1:
        return []
    previous = round_number - 1
    digest: List[str] = []
    for entry in timeline:
        if entry.get("event") != "contribution.created" or entry.get("round") != previous:
            continue
        text = strip_contribution_block(str(entry.get("response") or "")).strip()
        if not text:
            continue
        if len(text) > PREVIOUS_TURN_CHARS:
            text = text[:PREVIOUS_TURN_CHARS].rstrip() + " […]"
        # Quanto daquela fala virou conhecimento. Sem isto o agente lê
        # "fica a dúvida do custo" na prosa, vê um `criterion` no WC e
        # não sabe se são a mesma coisa — nem se a dúvida do colega
        # evaporou por não ter sido declarada. É a informação que evita
        # redeclarar o que já entrou e recuperar o que se perdeu.
        declarado = int(entry.get("items_added") or 0)
        marca = (
            f" [declarou {declarado} unidade{'s' if declarado != 1 else ''}]"
            if declarado
            else " [não declarou conhecimento]"
        )
        digest.append(f"{entry.get('participant_name') or 'Especialista'}{marca}: {text}")
    return digest


def render_tool_catalog(catalog: List[tuple]) -> str:
    if not catalog:
        return ""
    liberadas = [(n, d) for n, d, ok in catalog if ok]
    sob_pedido = [(n, d) for n, d, ok in catalog if not ok]
    partes = ["FERRAMENTAS"]
    if liberadas:
        partes.append(
            "Disponíveis para você: "
            + ", ".join(name for name, _ in liberadas)
            + ".\nA descrição de cada uma está no contrato de ferramentas desta requisição.\n\n"
            "A disponibilidade é uma capacidade, não uma instrução. "
            "Decida você mesmo se alguma ferramenta melhora materialmente a confiabilidade, "
            "atualidade, completude ou fundamentação da resposta. Você pode responder diretamente "
            "sem usar nenhuma, exceto quando o runtime declarar uma varredura canônica obrigatória "
            "do Working Context: nesse caso scan_context é parte da leitura do próprio WC, não "
            "uma investigação opcional. Pode encadear ferramentas quando isso for necessário, mas "
            "não pesquise apenas porque uma ferramenta existe."
        )
    if sob_pedido:
        partes.append(
            "Indisponíveis nesta deliberação: "
            + ", ".join(name for name, _ in sob_pedido)
            + ". Você pode pedir liberação ao moderador."
        )
    return "\n\n".join(partes)


def _relation_guide() -> str:
    """Guia de relações derivado do próprio grafo, agrupado por tipo.

    Vem de `_ALLOWED_RELATIONS` para nunca divergir das regras que a
    validação aplica: instruir uma relação que o grafo rejeita ensinaria
    o especialista a produzir contribuição inválida.
    """
    from norvald_lab.domain.deliberation.working_context_graph import _ALLOWED_RELATIONS

    por_relacao: Dict[str, List[str]] = {}
    for source, relation, target in sorted(_ALLOWED_RELATIONS):
        por_relacao.setdefault(relation, []).append(f"{source}\u2192{target}")
    linhas = [
        f"- {relation}: {'; '.join(pares)}"
        for relation, pares in sorted(por_relacao.items())
    ]
    return "\n".join(linhas)


def render_shared_instructions(
    *,
    constitution_block: str = "",
    evidence_block: str = "",
    project_block: str = "",
    has_library_tools: bool = True,
    dimensions: Optional["DimensionRegistry"] = None,
    round_number: int = 1,
) -> str:
    """As instruções do turno.

    Variam com a rodada porque a fase varia. N+0 recebe Evidence direta,
    âncoras do WC e ferramentas ancoradas de Library/Repository/WC.
    N+1+ mantém as âncoras e amplia o catálogo com capacidades externas.
    """
    parts = [
        "Seu objetivo é produzir a melhor contribuição possível para o objetivo da deliberação. A LLM é responsável por interpretar a pergunta, raciocinar, decidir se precisa das ferramentas disponíveis nesta fase e avaliar os resultados obtidos.",
        "O Working Context é a fonte de verdade do conhecimento deliberativo. O que está nele foi declarado e validado. Não trate resultado de ferramenta, documento, busca ou raciocínio intermediário como conhecimento do WC sem declará-lo no bloco CONTRIBUTION.",
        "Ferramentas são meios opcionais, não o objetivo do turno. Você pode responder diretamente. Não use ferramentas apenas porque elas estão disponíveis. A única exceção operacional é scan_context quando o runtime informar que a projeção do Working Context é parcial: percorra todos os blocos antes de concluir.",
        "N+0: use o WC inicial, suas âncoras e a Evidence anexada que foi passada diretamente nesta primeira execução. Library/Repository/WC podem ser consultados quando estiverem disponíveis nesta execução; MCP/Web ainda não fazem parte desta fase.",
        "N+1 em diante: primeiro consulte/avalie o WC e as posições já declaradas. Se o WC não couber integralmente na projeção residente, o Studio não escolhe quais partes são relevantes: o restante é apresentado em ordem canônica por scan_context. Ao ler cada bloco, retain_ids deve conter apenas os endereços que você próprio julgar possivelmente pertinentes para reencontro posterior. As âncoras de Evidence permanecem no WC, mas o corpo anexado não é reenviado como bloco a cada rodada. Library/Repository podem ser usados quando estiverem disponíveis nesta execução; MCP/Web podem ser usados quando configurados, permitidos e materialmente necessários.",
        "Não despeje catálogos, grafos, resultados brutos ou documentos completos no contexto da deliberação. Use as ferramentas para investigar e transforme o resultado em conhecimento somente quando houver uma declaração deliberativa válida.",
        "Evidence pode vir da aba Contexto, Library, Repository ou de fonte declarada pelo especialista. Ao usar Evidence, preserve a citação e a proveniência; não incorpore o documento completo ao WC.",
        "Depois de uma ferramenta, avalie o resultado e decida se deve responder ou investigar mais. Não repita uma consulta sem motivo novo. Se a evidência for suficiente, pare de pesquisar e componha a contribuição.",
        "O objetivo da deliberação é o problema permanente. O FOCO DO MODERADOR, quando presente na mensagem, governa somente esta rodada: use-o para decidir onde concentrar a análise, mesmo que a rodada anterior estivesse seguindo outra ênfase. Ele não apaga nem reescreve o objetivo permanente.",
        *(
            [
                "Se a rodada anterior aparecer na mensagem, responda a ela: concorde com fundamento, discorde com fundamento ou avance o ponto. Não repita o que já foi dito.",
            ]
            if round_number > 1
            else []
        ),
    ]
    if has_library_tools and policy_for(round_number).include_tool_rules:
        parts.append(
            "As ferramentas disponíveis são capacidades reais do Studio. O runtime controla permissão, segurança, tempo e execução; ele não escolhe a ferramenta por você. Não existe um número nativo de chamadas que você precise economizar: investigue enquanto houver progresso material e pare quando houver fundamento suficiente para compor a Contribution. Chamadas repetidas sem informação nova não avançam a tarefa."
        )
    parts.append(
        "OBRIGATÓRIO: termine sua resposta com o bloco abaixo, exatamente com estes delimitadores e JSON puro (sem cerca de código, sem indentação e sem quebras de linha dentro do JSON):\n"
        "<<CONTRIBUTION>>\n"
        '{"knowledge":[{"local_id":"k1","type":"inference","content":"...","confidence":"média"}],"relations":[{"relation_type":"derived_from","source":"k1","target":"evidence-<id>"}]}\n'
        "<<END_CONTRIBUTION>>\n"
        "type é um de: " + ", ".join(DECLARABLE_KNOWLEDGE_TYPES) + ". Uma unidade por afirmação sua. "
        "Em claim, argument, counterargument, inference e decision, declare "
        "`confidence` (alta, média ou baixa): sem ela o leitor do documento "
        "não distingue constatação de aposta. Não é certificação de verdade "
        "— é o peso que você mesmo atribui à sua afirmação. "
        "Regras de brevidade valem para a prosa, não para este bloco: sem ele nada entra no Working Context e a rodada não deixa conhecimento."
    )
    parts.append(
        # O conhecimento sem relação é uma pilha de afirmações soltas: o
        # Framework mede cobertura pela relação, não pela contagem de
        # itens, e um Working Context sem arestas fica em 0% por mais
        # unidades que tenha. O exemplo antigo mostrava `relations:[]` —
        # o único modelo de relação que o especialista via era o vazio, e
        # ele reproduzia o vazio. Aqui ele vê como declarar e para o quê
        # cada relação serve, sem ser obrigado a inventar uma que não
        # exista.
        #
        # O exemplo sozinho não bastou: a instrução de conteúdo é
        # OBRIGATÓRIA com consequência declarada ("sem ele nada entra no
        # WC"), e a de relação era só um alerta contra fabricar — sem
        # custo declarado para quem omite. Um especialista otimizando
        # por conformidade trata a primeira como inegociável e a segunda
        # como melhor-esforço. Resultado observado numa deliberação real
        # de 12 especialistas, 10 rodadas: ~30 unidades de conhecimento,
        # 1 relação declarada em todo o CDD — um contra-argumento que
        # claramente refinava uma fórmula anterior, sem nenhuma relação
        # ligando os dois. A correção dá à omissão o mesmo peso que o
        # bloco de conteúdo já tinha, sem enfraquecer o alerta contra
        # fabricar.
        "RELAÇÕES declaram o tecido entre as unidades — não são um extra "
        "opcional. Uma unidade sem relação fica isolada no grafo: não "
        "conta para cobertura de nenhum critério e não aparece ligada a "
        "nada quando o CDD for consultado depois. Sempre que uma unidade "
        "sua responde, refina, contesta, apoia ou deriva de outra — sua "
        "ou já existente no Working Context —, declare a relação "
        "correspondente; isso vale tanto quanto declarar a própria "
        "unidade. Só não declare quando a relação genuinamente não "
        "existir: fabricar uma para preencher é pior do que declarar de "
        "menos, mas declarar de menos tem custo real. `source` é um "
        "`local_id` desta contribuição; `target` é um `local_id` desta "
        "contribuição OU um id já existente no Working Context (as "
        "evidências deste caso aparecem como `evidence-<id>` no bloco de "
        "evidências e são alvos válidos). As permitidas:\n"
        + _relation_guide()
    )
    parts.append(
        "LIFECYCLE DE LACUNAS: um [gap] já existente é endereçável pelo "
        "UUID mostrado no Working Context. Se seu novo conhecimento realmente "
        "preenche uma lacuna existente, não crie outra cópia textual: declare "
        "o claim/evidence novo e uma relação resolves apontando para o UUID "
        "do gap. Se o problema continua existindo mas precisa ser reformulado, "
        "declare o novo gap e uma relação supersedes apontando para o UUID do "
        "gap anterior. Só crie um gap novo sem essas relações quando for uma "
        "lacuna genuinamente nova. O Studio não decide por similaridade se "
        "duas lacunas são a mesma; esse julgamento semântico é seu."
    )
    parts.append(
        # Os dois canais, e o que não fazer em cada um.
        #
        # A instrução mandava terminar com o bloco e nunca dizia que a
        # prosa não deve repeti-lo. O especialista então declarava duas
        # vezes: uma no JSON, que vai para o Working Context, e outra em
        # texto corrido — "declaro claim: X, confiança alta" —, que só
        # ocupa a tela. Quem lê o chat recebe a estrutura interna do
        # Studio em vez do argumento.
        "SEPARE OS DOIS CANAIS. A prosa é o argumento dirigido aos outros "
        "especialistas: o que você sustenta e por quê. O bloco é a "
        "declaração estruturada, lida pelo Studio. Não narre o bloco na "
        "prosa — não escreva \"declaro um claim\", não liste os tipos, os "
        "local_id, as relações, a confiança nem as dimensões em texto "
        "corrido. Isso já está no bloco, e repetir na prosa polui a "
        "leitura sem acrescentar conhecimento. Escreva a prosa como "
        "escreveria a um colega que não conhece o formato."
    )
    if dimensions is not None and dimensions.dimensions:
        names = sorted(d.name for d in dimensions.dimensions.values() if d.state == "ACTIVE")
        parts.append(
            'Em cada unidade, inclua "dimension_id" com a dimensão do Framework a que ela pertence, quando houver uma que sirva. Omita o campo se nenhuma servir. Use exatamente o nome, em minúsculas e com hífen no lugar do espaço (ex.: "Human Factors" vira "human-factors"). Dimensões: '
            + ", ".join(names)
            + "."
        )
    # A norma antes do material, e separada dele: Constitution é regra a
    # seguir, não objeto sobre o qual deliberar. Misturada às evidências
    # ela disputaria espaço com o material e seria lida como algo a
    # discutir (ADR-017 §2.5).
    if constitution_block:
        parts.append(constitution_block.strip())
    if project_block:
        parts.append(project_block.strip())
    if evidence_block:
        parts.append(evidence_block.strip())
    return "\n\n".join(parts)


def render_constitution_block(constitutions: List[Any]) -> str:
    """As Constitutions referenciadas, como instrução do turno.

    Ordem de anexo, que é estável e declarada — não reordenada por
    relevância: norma não se seleciona por trecho.
    """
    corpos = [
        f"### {c.name or c.reference}\n{(c.canonical_body or c.body or '').strip()}"
        for c in constitutions
        if (c.canonical_body or c.body or "").strip()
    ]
    if not corpos:
        return ""
    return (
        "REGRAS DESTA DELIBERAÇÃO (Constitution). Não são material a "
        "deliberar: são instruções a seguir neste turno, e prevalecem "
        "sobre preferências suas de formato ou abordagem. Onde "
        "conflitarem com o objetivo declarado, siga a regra e aponte o "
        "conflito na prosa.\n\n" + "\n\n".join(corpos)
    )


def render_instructions(
    *,
    participant_name: str,
    participant_role: str,
    round_number: int,
    max_rounds: Optional[int],
    evidence_block: str = "",
    has_library_tools: bool = True,
    adversarial_role: bool = False,
) -> str:
    return render_shared_instructions(
        evidence_block=evidence_block,
        has_library_tools=has_library_tools,
    ) + "\n\n" + render_participant_tail(
        participant_name=participant_name,
        participant_role=participant_role,
        round_number=round_number,
        max_rounds=max_rounds,
        adversarial_role=adversarial_role,
    )


_FASE_PRIMEIRA_RODADA = (
    "Esta é N+0: ninguém se posicionou ainda. A Evidence vinculada é passada diretamente, "
    "e o Working Context contém suas âncoras estáveis. Library/Repository/WC podem ser "
    "consultados quando necessário; MCP/Web entram somente a partir de N+1."
)

_FASE_DEMAIS_RODADAS = (
    "Esta é N+1 ou posterior. Há posições declaradas nas rodadas anteriores. Primeiro use "
    "o Working Context e suas âncoras. Library/Repository continuam disponíveis; MCP/Web "
    "passam a integrar o perfil ampliado quando configurados."
)


def _catalogo_resumido(catalogo: str) -> str:
    """Compatibilidade de API: o catálogo não é mais despejado no prompt."""
    if not catalogo.strip():
        return ""
    return (
        "Há conhecimento histórico no acervo do projeto. Ele não é carregado automaticamente para esta rodada. "
        "Use a ferramenta de recuperação somente se o Working Context e a Evidence não forem suficientes."
    )


def render_fase(round_number: int) -> str:
    """O texto da fase, agora vindo da política.

    Estava aqui uma segunda cópia da regra `round_number <= 1`, e o
    prompt e a estrutura podiam divergir — foi o que aconteceu quando o
    texto pedia para não investigar e as ferramentas continuavam sendo
    oferecidas.
    """
    return phase_text(policy_for(round_number))


_ADVERSARIAL_ROLE_TEXT = (
    "PAPEL ADVERSARIAL: nesta deliberação, cabe a você contestar ativamente. "
    "Não concorde por cortesia nem deixe uma afirmação frágil passar sem "
    "questionamento — procure o ponto fraco do que foi dito e declare a "
    "contestação (challenges/contradicts) quando ele existir. Isto não muda "
    "o que é verdade; muda o quanto você deve testar antes de aceitar."
)


def render_participant_tail(
    *,
    participant_name: str,
    participant_role: str,
    round_number: int,
    max_rounds: Optional[int],
    tool_catalog: str = "",
    adversarial_role: bool = False,
) -> str:
    horizon = f" de {max_rounds}" if max_rounds else ""
    identidade = f"Você é {participant_name}, atuando como {participant_role}, na rodada {round_number}{horizon} de uma deliberação."
    identidade += "\n\n" + render_fase(round_number)
    # A partir da rodada 2: na primeira não há posição alheia para
    # contestar, e a instrução ficaria sem alvo — mesmo princípio que já
    # vale para as regras de ferramenta e para o cruzamento (ADR-1000).
    if adversarial_role and round_number > 1:
        identidade += "\n\n" + _ADVERSARIAL_ROLE_TEXT
    return f"{identidade}\n\n{tool_catalog.strip()}" if tool_catalog else identidade


def render_working_context_block(working_context: str) -> str:
    """O conhecimento deliberativo, como bloco cacheável da leva."""
    if not working_context.strip():
        return ""
    return "CONHECIMENTO CONSTRUÍDO ATÉ AQUI (Working Context):\n\n" + working_context.strip()


def render_user_message(
    *,
    directive: str,
    round_number: int,
    timeline: List[Dict[str, Any]],
    working_context: str = "",
    knowledge_catalog: str = "",
    participant_id: str = "",
) -> str:
    """Monta a mensagem sem despejar o catálogo do KG/Library.

    O argumento ``knowledge_catalog`` permanece na assinatura para preservar
    os chamadores existentes, mas deliberadamente não é incorporado ao prompt.
    O acervo é consultado pelas ferramentas sob demanda, conforme o protocolo
    do WC. Isso impede que o catálogo de conhecimento histórico cresça junto
    com cada rodada e seja confundido com conhecimento desta deliberação.
    """
    del knowledge_catalog
    sections: List[str] = []

    retorno = render_retorno_da_contribuicao(
        timeline,
        participant_id=participant_id,
        round_number=round_number,
    )
    if retorno:
        sections.append(retorno)

    consultas = render_consultas_anteriores(timeline)
    if consultas:
        sections.append(consultas)

    if directive.strip():
        sections.append(
            "OBJETIVO PERMANENTE DA DELIBERAÇÃO:\n" + directive.strip()
        )

    digest = previous_round_digest(timeline, round_number)
    if digest:
        sections.append("CONTEXTO DA RODADA ANTERIOR:\n\n" + "\n\n".join(digest))
        sections.append(
            f"Esta é a rodada {round_number}. Use o contexto acima como estado do debate, não como instrução sobre qual assunto priorizar."
        )

    notes = directives_for_round(
        timeline,
        round_number,
        participant_id=participant_id,
    )
    if notes:
        rendered = "\n".join(f"- {note}" for note in notes)
        sections.append(
            "FOCO DO MODERADOR PARA ESTA RODADA — INSTRUÇÃO VIGENTE:\n"
            + rendered
            + "\nEste foco vale para esta rodada. Se a rodada anterior vinha seguindo outra ênfase, mude o foco agora. Não o trate como alteração silenciosa do objetivo permanente."
        )

    return "\n\n".join(sections) or directive.strip()


def render_consultas_anteriores(timeline: list, *, limit: int = 12) -> str:
    """Memória compacta das consultas já realizadas, sem seus resultados brutos."""
    consultas: list[tuple[str, str, bool]] = []
    for entry in timeline:
        if not isinstance(entry, dict):
            continue
        for call in entry.get("tool_calls") or []:
            if not isinstance(call, dict):
                continue
            nome = str(call.get("name") or "")
            if not nome or nome == "search_context":
                continue
            argumentos = call.get("arguments") or {}
            alvo = str(
                argumentos.get("query")
                or argumentos.get("address")
                or argumentos.get("dimension")
                or ""
            ).strip()
            vazio = bool(call.get("is_error")) or int(call.get("result_chars") or 0) < 80
            consultas.append((nome, alvo[:80], vazio))

    if not consultas:
        return ""

    vistas: set = set()
    unicas: list[tuple[str, str, bool]] = []
    for consulta in consultas:
        chave = (consulta[0], consulta[1])
        if chave in vistas:
            continue
        vistas.add(chave)
        unicas.append(consulta)

    linhas = ["Já consultado nesta deliberação (não repita sem motivo novo):"]
    for nome, alvo, vazio in unicas[-limit:]:
        marca = " — sem resultado" if vazio else ""
        linhas.append(f"  {nome}{f' · {alvo}' if alvo else ''}{marca}")
    return "\n".join(linhas)


def render_retorno_da_contribuicao(
    timeline: List[Dict[str, Any]],
    *,
    participant_id: str,
    round_number: int,
) -> str:
    """Mostra ao especialista o efeito validado da contribuição anterior."""
    if round_number <= 1:
        return ""

    anterior = None
    for entry in timeline:
        if (
            isinstance(entry, dict)
            and entry.get("event") == "contribution.created"
            and entry.get("participant_id") == participant_id
            and entry.get("round") == round_number - 1
        ):
            anterior = entry
    if anterior is None:
        return ""

    itens = int(anterior.get("items_added") or 0)
    relacoes = int(anterior.get("relations_added") or 0)
    rejeitados = anterior.get("rejected") or []

    partes = [f"{itens} unidade(s) e {relacoes} relação(ões) entraram no Working Context"]
    if not itens and not relacoes:
        partes = ["nenhuma unidade entrou no Working Context"]

    linhas = [f"Sua contribuição da rodada {round_number - 1}: " + ", ".join(partes) + "."]
    if rejeitados:
        linhas.append("Descartado na validação — corrija se ainda valer:")
        for rejeitado in rejeitados[:5]:
            if not isinstance(rejeitado, dict):
                continue
            motivo = str(rejeitado.get("reason") or rejeitado.get("error") or "inválido")
            alvo = str(rejeitado.get("local_id") or rejeitado.get("source") or "")
            linhas.append(f"  {alvo or 'item'} — {motivo}")
        if len(rejeitados) > 5:
            linhas.append(f"  (+{len(rejeitados) - 5} outros)")
    return "\n".join(linhas)



