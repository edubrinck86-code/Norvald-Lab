---
id: PESQUISA-1000
identifier: PESQUISA
references:
- CDD-017
status: Ativo
tags:
- Pesquisa
- metrics
- multi-agent
type: Caderno de Pesquisa
version: 2.0.0
former_id: ADR-1000
---

# PESQUISA-1000

> Métrica de correlação entre especialistas e detecção de efeito manada,
> a partir de lacunas identificadas pelo próprio enxame em CDD-017.

## Sobre este documento

**Anteriormente ADR-1000.** O nome antigo permanece válido como referência
histórica: código, testes e documentos anteriores citam "ADR-1000" e
continuam resolvendo para cá.

Este é um **caderno de pesquisa**, não um registro de decisão. O formato é
deliberado:

- **append-only** — adendos acrescentam, nunca reescrevem o conteúdo
  anterior;
- o raciocínio fica visível na ordem em que aconteceu, incluindo o que foi
  rejeitado (§68) e a autocrítica (§39–50);
- contradições entre adendos são registro de mudança de ideia, não defeito.

Por isso "102 seções, várias ordens experimentais concorrentes" é o formato
funcionando, não falha. Um caderno cresce.

**Onde está a posição vigente.** O caderno não diz qual ordem está valendo
nem qual é o estado atual — ler 3.264 linhas para descobrir isso é trabalho
que ele não faz. A posição corrente foi extraída para:

    docs/tese/README.md    mapa dos três destinos
    docs/tese/01           tese executável — Δ_herd e N_eff
    docs/tese/02           position paper — AROF-C
    docs/tese/03           trabalho futuro — AROF observacional

Revisão crítica e verificação de citações em
`docs/analise/Revisao_Critica_ADR-1000.md`.

As decisões que saírem daqui viram ADRs próprias, curtas. Este documento
não vira uma.

  -----------------------------------------------------------------------
  Campo                                 Valor
  ------------------------------------- ---------------------------------
  O que é                               Define como estimar correlação de
                                        erro entre especialistas (termos
                                        C_adj e I do Mecanismo de
                                        Confiança Composto) e como
                                        distinguir mudança de posição
                                        legítima de efeito manada — usando
                                        dado que o próprio Working Context
                                        já produz, sem depender de
                                        benchmark externo.

  Problema                              CDD-017 (deliberação "Swarm
                                        controlado", 12 especialistas, 4
                                        de 10 rodadas executadas)
                                        formulou o Mecanismo de Confiança
                                        Composto:

                                        `CC = 0.30·E + 0.25·R + 0.20·C_adj
                                        + 0.15·I + 0.10·H`

                                        Dos cinco termos, três (R, C_adj,
                                        I) não tinham método de cálculo
                                        definido. Investigação mostrou que
                                        C_adj e I dependiam do mesmo dado
                                        ausente — correlação de erro entre
                                        modelos — e que o próprio CDD já
                                        registrava isso como incerteza
                                        aberta (lacuna
                                        `e2228104-b805-47a1-8430-12597ab83be6`:
                                        "ausência de benchmark
                                        independente e contínuo de
                                        independência de erros entre
                                        modelos comerciais de fronteira").

  Contexto de pesquisa                  A direção já é área de pesquisa
                                        ativa, não problema inédito:
                                        correlação de erro maior dentro
                                        da mesma família de modelo que
                                        entre famílias diferentes é
                                        resultado medido (ex.: "When
                                        Agents Disagree: The Selection
                                        Bottleneck in Multi-Agent LLM
                                        Pipelines", 2026, usando dados do
                                        Chatbot Arena/MT-Bench); métricas
                                        de correlação de erro em ensemble
                                        de LLM já têm nome na literatura
                                        ("focal diversity"/"focal negative
                                        correlation", LLM-TOPLA, 2024);
                                        decomposição de mudança de posição
                                        em debate multi-agente entre
                                        instabilidade espontânea,
                                        conformidade induzida por posição
                                        do par e persuasão por argumento
                                        novo também já é estudada ("Not
                                        All Flips Are Conformity:
                                        Decomposing Stance Convergence in
                                        Multi-Agent LLM Debate", 2026). O
                                        que a literatura usa é benchmark
                                        externo; a diferença proposta
                                        aqui é usar o dado que o Studio já
                                        produz internamente.

  Decisão — correlação (C_adj, I)       Princípio: o Studio é consumidor
                                        de modelo, não provedor — dado de
                                        treino real nunca é acessível.
                                        Estimativa aproximada, não medida
                                        de verdade; nunca 100% assertiva,
                                        e não precisa ser — ~90% de
                                        acerto já é excelente. Três
                                        camadas, cada uma disponível
                                        quando a anterior não for:

                                        1. Composição de domínio de
                                        treino declarada publicamente
                                        pelo provider (código, imagem,
                                        conversação, multilíngue — o que
                                        relatórios técnicos e model cards
                                        costumam publicar por domínio,
                                        mesmo sem publicar o corpus em
                                        si). Dois modelos de providers
                                        diferentes, ambos fortemente
                                        treinados em código, correlacionam
                                        mais em raciocínio de código do
                                        que um par qualquer só por serem
                                        "família diferente" — mais fino
                                        que família, mesma camada de
                                        "disponível hoje".

                                        2. Família/provider do modelo,
                                        como fallback quando a composição
                                        declarada não está disponível ou
                                        é vaga demais para comparar.

                                        3. Refinamento real: taxa de
                                        contestação (`challenges`) entre
                                        cada par de modelo, acumulada ao
                                        longo do histórico de sessões do
                                        Working Context — comportamento
                                        observado dentro do próprio
                                        Studio, não medida externa
                                        importada.

                                        A métrica deve ser marcada como
                                        estimada por proxy/comportamento
                                        observado, não validada
                                        externamente — nunca apresentada
                                        como medida objetiva de verdade.

  Decisão — Densidade como eixo         Eixo diferente de C_adj/I, não
  separado, não parte de C_adj/I        refinamento dele: C_adj/I medem
                                        correlação de erro (a chance de
                                        dois modelos errarem juntos, pela
                                        mesma razão); estilo (especialista
                                        técnico e direto vs. prolixo e
                                        gentil) não mede isso — dois
                                        modelos podem chegar à mesma
                                        conclusão errada com estilo
                                        totalmente diferente. Mede
                                        diversidade operacional/
                                        estilística, já prevista na
                                        própria afirmação original do
                                        CDD-017 (`9a630223`: diversidade
                                        epistêmica útil vem de
                                        heterogeneidade operacional, não
                                        de família de modelo).

                                        Métrica já existe, reaproveitada
                                        sem código novo: Densidade do
                                        Intelligence Lab (estrutura
                                        aceita por mil caracteres de
                                        prosa) — especialista técnico e
                                        direto produz densidade alta,
                                        prolixo dilui em mais texto de
                                        acompanhamento, mesma conclusão.
                                        Um ensemble pode ter C_adj alto
                                        (modelos correlacionados) e ainda
                                        ganhar valor real por densidade
                                        variada entre especialistas —
                                        exibir os dois separados, não
                                        forçar num único número.

  Decisão — efeito manada (parte de R)  Distinguir, usando proveniência já
                                        existente no grafo: mudança de
                                        posição de um especialista entre
                                        rodadas É reconsideração legítima
                                        quando acompanhada de
                                        contra-argumento novo declarado; É
                                        efeito manada quando ocorre sem
                                        argumento novo, só após ver a
                                        posição dos outros. Rastreável
                                        porque toda declaração já carrega
                                        rodada e proveniência — não requer
                                        captura de dado novo.

                                        Três alavancas para reduzir
                                        conformidade por tendência de
                                        treinamento (RLHF), sem poder
                                        alterar arquitetura do modelo
                                        (fora do controle do Studio como
                                        consumidor):

                                        1. Papel adversarial obrigatório —
                                        pelo menos 1 de N especialistas
                                        recebe instrução explícita de
                                        contestar, não de opinar. Já
                                        aconteceu organicamente em
                                        CDD-017 (ver
                                        `7b47bdd2-5448-45cf-b318-169b530d6c71`,
                                        "Contestação dos Advogados do
                                        Diabo procedente") — formalizar
                                        torna reprodutível, não dependente
                                        de o modelo assumir a postura
                                        sozinho.

                                        2. Medir mudança de posição sem
                                        argumento novo entre rodadas (ver
                                        acima) — já coberto pela distinção
                                        de proveniência.

                                        3. Variar temperatura de
                                        amostragem entre especialistas do
                                        mesmo modelo no mesmo debate, para
                                        reduzir convergência por
                                        preguiça estatística na resposta
                                        mais provável.

  Decisão — R (consistência entre       Não é interpretação semântica do
  as análises)                          Studio — o princípio já
                                        estabelecido (remoção de
                                        Validator/ContextItemExtractor
                                        internos) proíbe um motor interno
                                        julgando se duas análises
                                        concordam. A solução cabe no
                                        mesmo padrão do resto do Studio:
                                        obrigação de cruzamento
                                        distribuída em **todos** os
                                        especialistas (não um papel
                                        dedicado), declarando
                                        `supports`/`challenges` entre a
                                        própria afirmação e a de outro
                                        especialista já presente no
                                        Working Context. "Mesmo assunto"
                                        é julgamento do especialista que
                                        cruza, nunca do Studio.

                                        Mensurável sem código novo de
                                        medição — mesmo mecanismo de
                                        `_REQUIRED_RELATIONS` já testado
                                        para `decision`→`option`
                                        (ver test_wc_conformance_decision.py):
                                        cadastra-se o tipo de declaração
                                        de cruzamento como nova entrada
                                        exigindo relação de saída
                                        apontando para afirmação de outro
                                        especialista. Ausência de
                                        cumprimento já vira
                                        `applicable_checks`/
                                        `satisfied_checks` automaticamente.

                                        Rodada 1 é fundação, não debate —
                                        Working Context está vazio,
                                        sem afirmação de outro
                                        especialista para cruzar. A
                                        obrigação só se aplica a partir da
                                        rodada 2. Isto não exige exceção
                                        escrita à mão: como a checagem é
                                        sobre o estado atual do grafo, ela
                                        não dispara sozinha quando não
                                        existe alvo válido ainda.

                                        Distinção que a métrica precisa
                                        preservar: "especialista não
                                        respondeu" (falha de execução, já
                                        tratada, categoria separada) ≠
                                        "especialista respondeu mas não
                                        cumpriu o cruzamento" (isto é o
                                        dado real de R). Efeito colateral
                                        do desenho distribuído: a
                                        obrigação sendo de todos, não de
                                        um papel dedicado, produz
                                        naturalmente uma métrica **por
                                        especialista** — quem cruza e
                                        quem não cruza, acumulável no
                                        histórico, mesmo formato da taxa
                                        de contestação por par usada em
                                        C_adj/I. Sinal de qualidade de
                                        especialista, não só de R.

                                        Obrigatoriedade é instrução — mais
                                        forte que o peso já dado à
                                        declaração de relação em geral —
                                        nunca bloqueio de validação.
                                        Descumprimento vira dado visível,
                                        nunca motivo de rejeição — mesmo
                                        princípio que já vale para
                                        `criterion`.

  Decisão — reconciliação de           Substitui a ideia original de
  contradição pós-cruzamento           "camada determinística de
                                        reconciliação" (regras fixas,
                                        LLM só redatora final) por outra
                                        estratégia — não a preenche, troca
                                        por algo mais coerente com o resto
                                        da arquitetura: julgamento continua
                                        sempre com o especialista, nunca
                                        com o Studio.

                                        Quando duas afirmações cruzadas
                                        (ver decisão de R, acima) se
                                        contradizem, a resolução é debate
                                        ancorado em evidência real e
                                        externa — nunca nas próprias
                                        afirmações já registradas no
                                        Working Context, para não fechar
                                        o loop citando a si mesmo.
                                        `web_search` já existe como
                                        ferramenta concedível ao
                                        especialista (ver
                                        backend/application/web_tools.py,
                                        mesmo modelo de concessão nominal
                                        de tool_grants.py) — nenhuma
                                        ferramenta nova necessária.

                                        Evidência precisa ser específica e
                                        citável (fonte, link ou relação
                                        `documents`/`derived_from`
                                        apontando para `reference`/
                                        `evidence`) — generalização
                                        estatística sem citação pontual
                                        ("estudos mostram que...", sem
                                        apontar de onde) conta como
                                        opinião, não evidência.

                                        Sem evidência real e específica
                                        disponível: cai em
                                        `open_question`/`uncertainty` —
                                        primitiva já existente no
                                        vocabulário semântico. Não é
                                        falha do processo nem de quem
                                        contribuiu; é o estado correto
                                        quando o fato que resolveria a
                                        contradição não existe ou não foi
                                        encontrado.

                                        Obrigatoriedade é instrução
                                        ("busque evidência real antes de
                                        insistir na posição"), nunca
                                        bloqueio — decorre diretamente do
                                        ponto anterior: se "não achei
                                        evidência" é resultado legítimo e
                                        esperado, bloquear a contribuição
                                        por isso puniria um estado válido,
                                        não um descumprimento.

  Decisão — rigidez estrutural          Fenômeno distinto de efeito
  (heurística fraca, declarada          manada, quase oposto: não é
  como fraca)                           mudar de posição sem argumento
                                        novo — é manter a mesma posição,
                                        produzindo argumento novo a cada
                                        rodada, mas sem nunca mexer na
                                        estrutura de raciocínio por trás.
                                        Debates longos tendem a isso: a
                                        estrutura de pensamento endurece
                                        depois de implementada, e
                                        argumento novo vira reforço
                                        decorado em volta da mesma
                                        armação, não reconsideração de
                                        verdade.

                                        Detectar isto de forma confiável
                                        exigiria julgar se um argumento é
                                        genuinamente novo em substância ou
                                        só reveste a mesma estrutura com
                                        palavra diferente — julgamento
                                        semântico que nenhum dicionário
                                        finito resolve de verdade
                                        ("internar uma IA é tapar sol com
                                        peneira nesse caso" — a porta de
                                        semântica sempre fica parcialmente
                                        fechada). Não dá pra ser 100%
                                        assertivo; a meta é minimizar, não
                                        eliminar.

                                        Proxy fraco, sem exigir
                                        julgamento de conteúdo: usa o
                                        mesmo cruzamento obrigatório já
                                        decidido para R — um especialista
                                        acumulando `supports` repetidos
                                        apontando só para a própria
                                        afirmação anterior, rodada após
                                        rodada, sem nunca declarar
                                        `challenges` genuíno contra
                                        ninguém, é sinal indireto de
                                        estrutura travada. Fraco
                                        comparado ao resto desta decisão,
                                        e deve ser exibido como tal —
                                        nunca como detecção certeira.

  Decisão — governança (síntese         A metade da lacuna original sobre
  errada)                               divergência permanente entre
                                        modelos já deixou de existir como
                                        problema: com a regra de
                                        reconciliação por evidência real
                                        já decidida, "discordar pra
                                        sempre" só tem duas saídas —
                                        convergir por evidência melhor, ou
                                        virar `open_question`/
                                        `uncertainty` declarada, que já é
                                        estado tratado, não falha.

                                        A metade que sobrava —
                                        responsabilidade quando a síntese
                                        publicada erra — não precisa de
                                        mecanismo novo: já está
                                        implementado.
                                        `library.upsert_consolidated_document`
                                        (backend/api/deliberation_routes.py)
                                        já publica todo CDD final na
                                        Library, com a estrutura semântica
                                        completa (não só texto), tornando-o
                                        referenciável por outras
                                        deliberações e projetável no
                                        Knowledge Graph. Relação
                                        inter-documento `supersedes`/
                                        `conflicts_with` já existe, feita
                                        exatamente para este caso.

                                        Síntese errada vira, então, mais
                                        uma finalidade normal do Studio —
                                        "síntese errada = nova deliberação
                                        sobre" — o CDD antigo entra como
                                        referência citável na nova
                                        deliberação, que declara
                                        `supersedes` quando a correção for
                                        confirmada. Nenhuma ferramenta de
                                        correção, auditoria ou revisão
                                        precisa existir separadamente; é o
                                        mesmo mecanismo que o Studio já
                                        usa para tudo.


                                        de reconciliação, no sentido
                                        original do CDD-017 (regras fixas
                                        decidindo resultado, LLM só
                                        redigindo) — deliberadamente
                                        abandonada em favor da estratégia
                                        acima, não implementada de outra
                                        forma.

                                        Correlação por arquitetura/
                                        paradigma de treinamento
                                        (transformer + RLHF, convergência
                                        por otimizar os mesmos benchmarks
                                        públicos) — esse eixo de
                                        correlação persiste mesmo com
                                        diversidade total de provider, e o
                                        Studio não tem como contorná-lo
                                        como consumidor, não fornecedor
                                        de modelo.

                                        Calibração de confiança (campo
                                        `confidence: alta/média/baixa` já
                                        existente em `ContextItem`,
                                        cruzado com `conformance_checks`)
                                        — ideia relacionada, discutida,
                                        mas mede outra coisa (excesso de
                                        confiança desacoplado de rigor
                                        estrutural dentro de uma única
                                        contribuição), não consistência
                                        entre análises. Deliberadamente
                                        não incorporada a R.

                                        Implementação concreta (schema,
                                        rota, onde o cálculo roda) — esta
                                        decisão registra a direção e o
                                        método; a implementação é etapa
                                        posterior.

                                        Caso-limite considerado e
                                        deliberadamente não tratado com
                                        regra própria: os pesos somam
                                        1.00 (`0.30+0.25+0.20+0.15+0.10`)
                                        — se `C_adj`/`I` viessem sem
                                        nenhum dado, CC ficaria capado em
                                        0.65 independente de E/R, o que
                                        confundiria "não consigo medir"
                                        com "medi e deu ruim". O desenho
                                        em duas camadas (proxy grosseiro
                                        sempre disponível, nunca zero de
                                        verdade) já evita isso na
                                        prática. Decisão: não adicionar
                                        regra de redistribuição de peso
                                        para este caso — se aparecer um
                                        teto de 65% recorrente, isso já é
                                        sinal diagnosticável (bug ou
                                        estatística real), não precisa de
                                        tratamento antecipado para um
                                        caso que não deveria ocorrer.

  Estado da implementação                 Implementado na main: medição de
                                          cruzamento distribuído por
                                          Contribution a partir da rodada 2
                                          (measure_cross_engagement), com
                                          supports, challenges, contradicts
                                          e addresses, incluindo métrica
                                          agregada e by_author. A distinção
                                          entre engajamento e contestação é
                                          intencional: concordância também é
                                          engajamento; apenas relações de
                                          contestação convocam réplica.

                                          O papel adversarial opcional já
                                          pertence ao desenho operacional da
                                          deliberação. O conjunto abaixo
                                          substitui a antiga próxima etapa:
                                          o foco deixa de ser contar
                                          contestação por par como proxy
                                          suficiente de independência e
                                          passa a medir a estrutura do
                                          raciocínio agêntico observável.

  Próxima etapa revisada                  1. Formalizar e implementar a
                                          representação de trajetória de
                                          raciocínio observável a partir de
                                          primitives, relações, proveniência,
                                          critérios, evidências e conclusão.

                                          2. Definir o fingerprint estrutural
                                          de argumento/trajetória e relações
                                          derivadas para distinguir:
                                          same_conclusion, shares_basis,
                                          different_basis e
                                          independent_source, sem reduzir
                                          tudo a similaridade textual.

                                          3. Registrar observações brutas de
                                          trajetória e proveniência antes de
                                          criar agregados probabilísticos.
                                          Agregados devem ser reconstruíveis
                                          e auditáveis.

                                          4. Usar equivalência semântica local
                                          apenas onde a estrutura não basta,
                                          por exemplo quando duas evidências
                                          diferentes sustentam o mesmo
                                          fundamento, sem um juiz semântico
                                          global de independência.

                                          5. Derivar independência/diversidade
                                          agêntica efetiva e um N efetivo de
                                          trajetórias não redundantes.

                                          6. Reposicionar C_adj/I como âncora
                                          probabilística externa (prior e
                                          ajuste), combinando provider,
                                          família, domínio declarado e
                                          histórico observado.

                                          7. Implementar sinais de efeito
                                          manada e rigidez estrutural sobre a
                                          mesma representação de trajetória,
                                          sempre como telemetria, nunca como
                                          veredito.

                                          8. Refinar reconciliação por
                                          evidência: busca web fornece fonte
                                          candidata, não verdade. Contradições
                                          podem permanecer como open_question
                                          ou uncertainty.

                                          9. Só depois fechar o cálculo
                                          composto do CC, preservando
                                          componentes, proveniência,
                                          qualidade e incerteza da estimativa.

                                          10. Expor no Intelligence Lab sem
                                          fundir Densidade com independência
                                          ou correlação de erro.
  -----------------------------------------------------------------------

## Adendo de decisão — semântica do raciocínio agêntico observável

### 1. Objeto medido

O CC derivado do Norvald não mede diversidade do conteúdo textual produzido
por cada provider e não tenta reconstruir o raciocínio privado/interno do
modelo. Mesmo quando um provider expõe algum campo de reasoning/thinking,
esse conteúdo não é a unidade confiável do cálculo.

O objeto medido é a **semântica do raciocínio agêntico observável**: a função
que cada contribuição exerce dentro da deliberação, materializada no Working
Context por primitives, relações, proveniência, critérios, evidências,
ferramentas, rodadas e conclusões.

Cadeia conceitual:

    modelo
      → contribuição
      → primitives + relações
      → trajetória de raciocínio observável
      → fundamentos / inferências / critérios / evidências
      → conclusão
      → convergência / divergência
      → redundância / independência

A semântica de conteúdo continua útil, mas como instrumento local de
normalização. Ela pode responder, por exemplo, se duas evidências distintas
sustentam essencialmente o mesmo fundamento. Ela não deve responder
diretamente se dois agentes são independentes ou se uma conclusão é
verdadeira.

### 2. Semântica não é entropia textual

Diversidade de texto, vocabulário, estilo ou enquadramento produz entropia
observável, mas parte dela pode ser apenas **entropia redundante**: várias
formas de expressar a mesma estrutura de raciocínio.

O Norvald deve preservar a distinção:

    H(texto) ≠ H(raciocínio agêntico)

O alvo é aproximar diversidade estrutural/epistêmica do raciocínio observável:

    muitos textos
      → menos caminhos estruturais
      → menos fundamentos efetivamente distintos
      → menos trajetórias epistemicamente independentes

Portanto, dez respostas diferentes não equivalem a dez perspectivas
independentes.

### 3. Trajetória de raciocínio como unidade principal

A unidade estatística principal deixa de ser o agente/modelo e passa a ser a
**trajetória de raciocínio observável**.

Exemplos abstratos:

    evidence → argument → criterion → inference → claim

ou:

    reference → evidence → derived_from → inference → supports → decision

Duas contribuições podem ter textos muito diferentes e ainda materializar a
mesma trajetória. O inverso também é verdadeiro: textos parecidos e a mesma
conclusão podem esconder trajetórias independentes.

A identidade do agente continua relevante como proveniência e como âncora de
correlação, mas não é tratada como confirmação independente por definição.

### 4. Fingerprint estrutural de argumento/trajetória

O desenho passa a prever um ArgumentFingerprint (nome conceitual; schema
concreto ainda a definir) em camadas:

1. **Conclusão/alvo** — claim, option, decision ou questão sustentada/contestada.
2. **Topologia** — sequência de primitives e relações utilizada.
3. **Base epistêmica** — evidências, referências e fatos mobilizados.
4. **Critérios** — critérios de comparação/decisão efetivamente aplicados.
5. **Relações** — supports, challenges, contradicts, addresses, derived_from,
   documents e equivalentes já permitidos pelo grafo.
6. **Proveniência** — autor, provider, modelo, ferramentas, documentos/fontes
   e rodada.
7. **Trajetória** — quais primitives anteriores foram utilizadas, alteradas,
   contestadas ou reafirmadas.

O fingerprint não deve gerar um único número opaco de similaridade. Ele deve
permitir equivalências por dimensão, por exemplo:

    mesma conclusão          sim
    mesmo fundamento         sim
    mesma evidência          não
    mesma fonte              não
    mesma topologia          sim
    mesma proveniência       não

Isto é mais útil e auditável que uma similaridade semântica escalar.

### 5. Quatro estados básicos de convergência/divergência

A semântica do raciocínio deve distinguir pelo menos:

    MESMA CONCLUSÃO + MESMO FUNDAMENTO
    → convergência redundante

    MESMA CONCLUSÃO + FUNDAMENTOS DIFERENTES
    → convergência independente

    CONCLUSÕES DIFERENTES + MESMO FUNDAMENTO
    → divergência interpretativa

    CONCLUSÕES DIFERENTES + FUNDAMENTOS DIFERENTES
    → divergência epistemicamente independente

Concordância não é prova de dependência. Dois especialistas podem concordar
porque o argumento é válido e a evidência é forte. Da mesma forma,
discordância não é prova de independência: pode ser ruído, interpretação
distinta da mesma base ou erro unilateral.

Por isso, taxa de contestação por par continua sendo dado útil, mas deixa de
ser proxy suficiente de independência.

### 6. Relações derivadas sem destruir nuance

A normalização não deve apagar primitives originais nem colapsar o grafo em
clusters definitivos. O Norvald mantém o grafo original e pode acrescentar
relações derivadas/auditáveis, conceitualmente:

    A --same_conclusion------ B
    A --shares_basis--------- B
    A --different_basis------ C
    A --independent_source--- C
    A --semantic_equivalent-- B

Os nomes concretos pertencem ao schema futuro; esta decisão registra a função,
não congela os identificadores.

### 7. Evidência web não é verdade

web_search recupera fontes candidatas; não produz uma evidência 100% verdadeira
por definição. Fonte, evidência e verdade não são sinônimos.

Fluxo conceitual:

    fonte recuperada
      → alegação extraída
      → proveniência
      → qualidade/adequação da fonte
      → relevância para a afirmação
      → corroboração independente
      → supports / contradicts / inconclusive

Mesmo fontes fortes podem estar erradas, desatualizadas, tratar outra
população/período ou não sustentar exatamente a alegação em disputa.

Consequentemente, "reconciliação por evidência" passa a significar
**resolução por suporte verificável/corroborado**, não "consulta web resolve a
verdade".

Uma contradição pode legitimamente terminar como:

    supports: fontes A/B
    contradicts: fonte C
    inconclusive: fonte D
    estado: contested / open_question / uncertainty

O Norvald não escolhe automaticamente um vencedor.

### 8. C_adj e I permanecem, mas mudam de posição

C_adj/I não são descartados. Eles passam a funcionar como **âncora
probabilística** sobre dependências que o Norvald não consegue observar
diretamente.

O provider possui informação privilegiada que o Studio normalmente não tem:
corpus real, mistura de treinamento, checkpoints, distillation,
pós-treinamento, dados sintéticos, contaminação de benchmark, avaliações
internas e correlação de erro medida. Por isso, um cálculo de correlação
"real" é em grande parte monopolizado pelo provider.

Ainda assim, a estrutura matemática permanece: queremos estimar
dependência/correlação entre erros com variáveis parcialmente ocultas.

A arquitetura passa a separar:

    I_prior
      = f(provider, família, domínio declarado, histórico disponível)

    I_obs
      = f(trajetórias, fundamentos, fontes, primitives, relações)

    I_posterior
      = f(I_prior, I_obs, quantidade/qualidade de observações)

Essas expressões não são ainda equações normativas. Registram a separação
entre **âncora externa estimada** e **estrutura observada na deliberação**.

Com pouco histórico, a âncora pode pesar mais. Conforme o Norvald acumula
trajetórias observadas, o comportamento interno pode corrigir o prior.

### 9. Provider/família são âncora, não veredito

Modelos do mesmo provider/família podem compartilhar ancestralidade, dados,
benchmarks e processos de treinamento, portanto não devem ser tratados como
independentes do zero.

Providers diferentes também não implicam independência total: modelos de
fronteira compartilham parte relevante do universo público de informação,
benchmarks, literatura, código e paradigmas de treinamento.

Assim:

    mesmo provider/família
    → prior de independência menor
    → trajetória observada pode elevar a independência efetiva

    providers diferentes
    → prior de independência maior
    → trajetória observada pode revelar forte redundância

A observação da deliberação não apaga a âncora; a âncora não domina a
observação.

### 10. Independência Argumentativa Efetiva

O ADR passa a reconhecer como conceito de trabalho a **Independência
Argumentativa Efetiva**: quantidade/diversidade de trajetórias de raciocínio
não redundantes que sustentam ou contestam uma conclusão.

Isto implica um número efetivo de observações (N_eff) diferente do número
nominal de agentes:

    5 agentes repetindo essencialmente a mesma trajetória
    → N_eff próximo de 1, não de 5

    3 agentes usando fundamentos, fontes e trajetórias independentes
    → N_eff pode se aproximar de 3

A fórmula concreta de N_eff fica deliberadamente em aberto até que o
fingerprint e os dados observáveis estejam definidos. O princípio é normativo:
**mais agentes não aumentam confiança automaticamente**.

### 11. Efeito manada e rigidez sob a nova representação

Efeito manada e rigidez estrutural devem reutilizar a representação de
trajetória.

**Efeito manada:** mudança de posição após exposição ao grupo sem novo
fundamento/argumento/evidência observável é sinal de conformidade. Mudança
acompanhada de novo suporte é reconsideração legítima.

**Rigidez estrutural:** manutenção de posição com variação textual, mas sem
alteração significativa de fundamento/topologia e sem engajamento genuíno com
contestações, é sinal fraco de estrutura endurecida.

Nos dois casos, o resultado é telemetria/sinal, nunca sentença de verdade,
competência ou intenção do modelo.

### 12. Relação com R e com a contestação já implementada

measure_cross_engagement continua válido e passa a ocupar posição mais clara:

- mede se houve engajamento relacional entre autores;
- não mede independência por si só;
- supports conta como engajamento;
- contestação continua sendo subconjunto utilizado para convocar réplica;
- taxa histórica por par pode enriquecer prior/comportamento, mas não
  substitui análise de trajetória.

Assim, R continua sendo consistência/cruzamento estrutural entre análises,
enquanto independência efetiva passa a depender da estrutura do raciocínio
produzido no grafo.

### 13. Relação com Densidade

Densidade continua separada.

Ela mede diversidade operacional/estilística da produção e continua útil no
Intelligence Lab, mas não deve ser usada como substituto de diversidade de
raciocínio.

    diversidade textual/operacional → Densidade e métricas afins
    diversidade de raciocínio       → trajetórias/fundamentos/proveniência
    correlação oculta               → C_adj/I como âncora probabilística

Misturar os três eixos voltaria a introduzir entropia redundante no CC.

### 14. Forma futura do CC derivado

A fórmula original permanece como referência:

    CC = 0.30·E + 0.25·R + 0.20·C_adj + 0.15·I + 0.10·H

Este adendo não altera os pesos neste momento. Ele altera a interpretação e a
origem observacional dos componentes ligados à independência/correlação.

O cálculo final deverá preservar não apenas o escalar, mas seus componentes,
proveniência e qualidade da estimação:

    CC estimado
    ├── E
    ├── R
    ├── C_adj
    ├── I
    ├── H
    ├── N_eff / diversidade efetiva
    ├── bases/proveniência usadas
    └── qualidade/incerteza da estimativa

Quando houver base matemática adequada, o Studio poderá representar também um
intervalo de incerteza do próprio CC. Um número único não deve esconder o
quanto o Norvald sabe — ou não sabe — sobre as variáveis usadas.

### 15. Não objetivos

Esta decisão explicitamente não autoriza:

- usar diferença de texto como proxy direto de independência;
- tratar concordância como efeito manada por definição;
- tratar discordância como independência por definição;
- tratar resultado de busca web como verdade;
- expor ou depender de chain-of-thought privado dos providers;
- criar um LLM-juiz global para decidir se dois raciocínios são
  "verdadeiramente diferentes";
- converter proxies de provider/família em medida objetiva de correlação;
- aumentar CC apenas porque aumentou o número nominal de especialistas;
- fundir Densidade com C_adj/I.

### 16. Invariante arquitetural

O princípio que orienta as próximas implementações passa a ser:

> **O Norvald calcula a semântica do raciocínio agêntico observável, não o
> conteúdo produzido por cada provider. A diversidade relevante nasce da
> estrutura de primitives, relações, fundamentos, proveniência e trajetórias;
> C_adj/I permanecem como âncora probabilística para dependências ocultas que
> o Studio não pode medir diretamente.**

Ordem decorrente:

    primitives
      → relações
      → trajetórias de raciocínio
      → equivalência/redundância
      → diversidade/independência agêntica efetiva
      → ajuste probabilístico C_adj/I
      → CC composto e auditável


## Adendo de decisão — observabilidade de raciocínio e entropia agêntica

### 17. Mudança de perspectiva

A discussão posterior à definição de trajetória revelou um eixo mais geral do
que o próprio CC: o Studio pode construir uma camada de **observabilidade do
raciocínio agêntico** a partir do reasoning/thinking que cada provider decide
expor, sem assumir que esse trace representa o estado interno completo do
modelo.

A premissa operacional é:

> O provider não entrega o modelo completo de pensamento, mas o reasoning
> exposto contém informação estrutural observável sobre como aquele modelo,
> naquela execução, organizou parte do processo de raciocínio.

O Norvald é consumidor, não provedor. Portanto não tenta reconstruir pesos,
corpus, checkpoints ou dinâmica interna inacessível. Ele extrai regularidades
mensuráveis da superfície que efetivamente recebe.

Isso muda a pergunta de:

    "qual foi o pensamento real do modelo?"

para:

    "qual estrutura de raciocínio foi observavelmente exposta,
     como ela variou e como se relacionou com o resultado agêntico?"

### 18. Agentic Reasoning Observability Framework (AROF)

Nome de trabalho para a camada geral:

**AROF — Agentic Reasoning Observability Framework**

Vocabulário inicial:

- **Reasoning Trace** — reasoning/thinking exatamente como exposto pelo
  provider.
- **Exposure Mode** — forma de exposição conhecida ou inferível:
  raw, summarized, filtered, redacted ou unknown.
- **Reasoning Event** — ocorrência observável identificada no trace.
- **Reasoning Function** — função semântica normalizada exercida por um evento.
- **Reasoning Orientation** — alvo/orientação da função: self, peer, evidence,
  tool, source etc.
- **Reasoning Transition** — passagem observada entre duas Reasoning Functions.
- **Process Trajectory** — trajetória derivada do reasoning exposto.
- **Outcome Trajectory** — trajetória derivada das primitives/relations do
  Working Context.
- **Agentic Reasoning Observation** — vínculo entre Process Trajectory,
  Outcome Trajectory, contexto, provider/model e execução.
- **Observed Reasoning Pattern** — padrão recorrente de funções/transições.
- **Observed Reasoning Profile (ORP)** — distribuição histórica de padrões e
  métricas observadas para uma configuração de modelo/contexto.

Essa camada é de observação e referência. Ela não julga "melhor", "pior",
"mais inteligente", "mais correto" ou "mais eficiente" por definição.

### 19. Reasoning Functions v1

Taxonomia enxuta de trabalho, deliberadamente ampla e versionável:

    FRAME
    DECOMPOSE
    GENERATE
    EVALUATE
    CHALLENGE
    REVISE
    INTEGRATE
    CONCLUDE
    UNCERTAINTY

Essas funções não pretendem ser ontologia universal da cognição. São classes
funcionais de observação destinadas a cobrir áreas semanticamente equivalentes
sem depender da formulação textual exata.

Exemplos:

    "comparar alternativas"
    "pesar trade-offs"
    "testar opções pelos critérios"
        → EVALUATE

    "isso contradiz a hipótese"
    "há um contraexemplo"
    "essa evidência enfraquece a conclusão"
        → CHALLENGE

A nuance pode ser preservada por subtype e pelo trecho original. O evento
bruto não deve ser descartado após normalização.

Cada classificação deve carregar a versão do framework para permitir
reprocessamento histórico futuro.

### 20. Separação entre evento e função

O framework não deve fundir observação e interpretação.

Exemplo conceitual:

    ReasoningEvent:
      source_span
      sequence_index
      provider
      model
      exposure_mode

    ReasoningFunctionAssignment:
      function = CHALLENGE
      subtype = evidence_conflict
      orientation = evidence
      framework_version = v1

Isso permite que uma versão futura do normalizador recalcule a função sem
invalidar o trace original.

### 21. Transition Matrix

Para uma trajetória ou conjunto de trajetórias, define-se uma matriz de
transição observada:

    M_T[i,j] = P(function_j | function_i)

onde cada célula representa a frequência/probabilidade empírica de uma função
ser seguida por outra, sob o contexto observado.

Exemplo:

    FRAME      → DECOMPOSE    0.31
    DECOMPOSE  → EVALUATE     0.27
    EVALUATE   → CHALLENGE    0.18
    CHALLENGE  → REVISE       0.14
    REVISE     → CONCLUDE     0.10

A matriz descreve comportamento observado. Ela não atribui valor ao padrão.

### 22. Transition Entropy

Define-se, como métrica descritiva, a **Transition Entropy**:

    H_T = - Σ_i p(i) Σ_j P(j|i) log P(j|i)

Interpretação restrita:

> H_T mede a diversidade/incerteza observada das transições entre funções de
> raciocínio.

H_T maior não significa raciocínio melhor. H_T menor não significa pior.
Uma hipótese simples pode naturalmente gerar trajetória previsível; uma
hipótese aberta pode gerar maior variedade de transições.

Quando necessário, pode-se usar forma normalizada:

    H_T_norm = H_T / log(K)

onde K representa o espaço de transições considerado pelo framework/recorte.

A normalização exata ainda não é normativa e deve ser testada contra efeitos de
comprimento de trajetória, cobertura de estados e exposure mode.

### 23. Entropia Agêntica como conceito mais amplo

**Entropia Agêntica** é registrada neste ADR como conceito de trabalho, ainda
não como um único escalar fechado.

Ela é distinta de:

    entropia de tokens
    diversidade textual
    diversidade estilística
    densidade
    discordância entre respostas

A hipótese de trabalho é que a entropia agêntica descreve a variabilidade da
**estrutura observável do processo agêntico**, incluindo a forma como funções,
transições, ramificações, revisões, orientações, ferramentas e dependências
se organizam ao longo de trajetórias.

Portanto:

    H(texto) != H(transições) != H(agêntica)

Transition Entropy é uma projeção da Entropia Agêntica, não sua definição
completa.

Uma formulação futura poderá tratar a entropia agêntica como objeto
multidimensional, por exemplo:

    H_A = {
      H_transition,
      branching_distribution,
      revision_distribution,
      orientation_distribution,
      recurrence,
      trajectory_topology
    }

A composição em escalar único fica deliberadamente em aberto.

### 24. Observed Agentic Divergence (OAD)

Para comparar duas trajetórias observadas sem julgar conteúdo, define-se como
conceito de trabalho a **Observed Agentic Divergence (OAD)**:

> distância estrutural entre duas trajetórias de raciocínio observável sob
> condições comparáveis.

Uma trajetória pode ser representada por:

    T = (S, M, G, O)

onde:

- S = distribuição de Reasoning Functions;
- M = matriz de transições;
- G = topologia da trajetória, como profundidade, branches e revisões;
- O = distribuição de orientações, como peer/evidence/tool/source/self.

Dimensões possíveis:

    D_function
    D_transition
    D_topology
    D_orientation

Para distribuições, Jensen-Shannon divergence é candidata por ser simétrica e
limitada, mas nenhuma função de distância é normativa nesta etapa.

Uma composição futura poderia ter forma:

    OAD(A,B) =
      w1*D_transition +
      w2*D_function +
      w3*D_topology +
      w4*D_orientation

Os pesos não devem ser escolhidos por conveniência. Primeiro devem existir
dados suficientes para estudar estabilidade, colinearidade e sensibilidade de
cada dimensão.

### 25. Transition Entropy e OAD medem coisas diferentes

Duas trajetórias podem possuir valores semelhantes de H_T e ainda assim serem
estruturalmente diferentes.

Exemplo:

    A:
    FRAME → DECOMPOSE → EVALUATE → REVISE

    B:
    FRAME → GENERATE → CHALLENGE → INTEGRATE

A diversidade interna de transições pode ser parecida, mas a distribuição e
topologia são diferentes.

Assim:

    Transition Entropy
    = variação interna de transições de uma trajetória/população

    Observed Agentic Divergence
    = distância entre duas trajetórias/populações

Nenhuma delas, isoladamente, significa qualidade, verdade ou independência de
erro.

### 26. Observed Reasoning Profile (ORP)

Com múltiplas execuções, o Studio pode construir um **Observed Reasoning
Profile** condicionado ao contexto.

Exemplo conceitual:

    model X / task class factual
      FRAME → EVALUATE      0.34
      EVALUATE → TOOL       0.27
      TOOL → INTEGRATE      0.21
      INTEGRATE → CONCLUDE  0.18

    model X / task class planning
      FRAME → DECOMPOSE     0.31
      DECOMPOSE → GENERATE  0.29
      GENERATE → EVALUATE   0.22
      ...

O ORP não afirma como o modelo pensa internamente. Ele referencia padrões que
o Studio observou repetidamente na superfície exposta.

O perfil deve ser condicionado, no mínimo, por:

    provider/model
    model version quando conhecida
    exposure mode
    task/context class
    prompt/orchestration version
    tool grants relevantes
    framework version

### 27. Teste de identificabilidade

Antes de tratar qualquer métrica como característica estável de modelo, o
framework precisa verificar se distingue sinal de ruído.

Define-se:

    D_intra
    = divergência média entre execuções comparáveis do mesmo modelo

    D_inter
    = divergência média entre modelos diferentes sob condições comparáveis

Hipótese experimental:

    D_intra < D_inter

Se essa desigualdade aparece de forma consistente, há evidência de que o
framework captura uma assinatura estrutural associada ao comportamento
observável do modelo.

Se:

    D_intra ~= D_inter

a taxonomia/métrica pode estar capturando principalmente stochasticidade,
efeito da hipótese, prompt ou política de exposição do provider.

O mesmo teste pode ser repetido por família e provider:

    D_intra-model
    D_inter-model
    D_intra-family
    D_inter-family
    D_intra-provider
    D_inter-provider

### 28. Teste cego de assinatura

Outro teste recomendado:

1. remover provider, nome do modelo e parameter count das features;
2. manter somente estrutura observada das trajetórias;
3. verificar se populações de execução continuam estatisticamente
   distinguíveis.

O objetivo não é criar um classificador de produção. É testar se existe
informação estrutural mensurável além dos metadados declarados.

### 29. Relação com C_adj e I

Esta camada não deve entrar no CC como mais um termo apenas porque existe.

C_adj/I pertencem à fórmula histórica do CC; AROF/OAD/H_T são infraestrutura e
métricas observacionais.

A relação entre elas é hipótese empírica, não decisão assumida.

Devem ser estudadas relações como:

    Corr(OAD, C_adj)
    Corr(OAD, I)
    Corr(H_T, I)
    Corr(OAD, N_eff)

Possíveis resultados:

- alta colinearidade: a nova métrica pode estar medindo, por observação direta,
  conceito já representado de forma grosseira por C_adj/I;
- baixa colinearidade estável: pode existir dimensão observacional distinta;
- instabilidade: a métrica pode depender demais de exposição/contexto para
  entrar no CC.

Até essa validação, nenhuma nova métrica deve receber peso no CC.

### 30. Ganho específico do Studio como consumidor

Providers possuem informação interna que o Studio não possui. O Studio,
porém, observa algo diferente: o comportamento deliberativo concreto de vários
modelos dentro da mesma infraestrutura, com Working Context, ferramentas,
relações e resultados referenciáveis.

Isso permite inferir propriedades latentes a partir de comportamento
observável sem alegar reconstrução do estado interno.

Fluxo:

    reasoning exposto pelo provider
      → eventos observáveis
      → funções normalizadas
      → transições
      → trajetórias
      → métricas estruturais
      → perfis históricos
      → comparação intra/inter-modelo

O valor não está em "descobrir o segredo do provider", mas em produzir
estatística própria sobre a manifestação operacional dos modelos no Studio.

### 31. Gaps abertos desta linha

Os principais gaps atualmente identificados são:

1. **granularidade das Reasoning Functions** — ampla demais apaga estrutura;
   estreita demais destrói comparabilidade;
2. **normalização semântica** — mapear equivalência funcional sem introduzir
   um juiz epistemológico global;
3. **exposure normalization** — providers podem resumir/filtrar reasoning em
   intensidades diferentes;
4. **comprimento de trajetória** — sequências curtas e longas têm propriedades
   estatísticas diferentes;
5. **classe/contexto da hipótese** — métricas precisam ser condicionadas ao
   tipo de tarefa;
6. **efeito de prompt/orquestração** — parte da estrutura observada é induzida
   pelo próprio Studio;
7. **tools** — separar função de raciocínio de ação externa/implementação;
8. **ramos implícitos** — o provider pode compactar vários ramos em um único
   resumo;
9. **transições ausentes** — ausência no trace não prova ausência no processo
   interno;
10. **stochasticidade** — uma execução não caracteriza um modelo;
11. **drift de provider/API** — formato de exposição pode mudar sem mudança de
    pesos;
12. **versionamento da taxonomia** — histórico precisa continuar
    reprocessável;
13. **persistência/custo** — reasoning traces podem ser grandes;
14. **privacidade** — traces podem reproduzir contexto sensível;
15. **colinearidade com CC** — risco de medir de novo C_adj/I com outro nome;
16. **identificabilidade** — ainda precisa ser demonstrado que D_intra e
    D_inter se separam de forma consistente.

### 32. Hipótese de pesquisa registrada

A linha de pesquisa aberta por este adendo pode ser resumida assim:

> **O reasoning parcialmente exposto por providers contém estrutura suficiente
> para que o Norvald derive métricas reprodutíveis da dinâmica agêntica
> observável — distintas de entropia textual e potencialmente informativas
> sobre padrões de modelo, família e provider.**

A hipótese só deve ser considerada sustentada quando experimentos controlados
mostrarem estabilidade intra-modelo e separação inter-modelo/contexto.

**Status após o primeiro piloto Atlas:** ainda não sustentada nesse sentido
forte. O piloto produziu evidência preliminar de viabilidade da representação,
mas ainda não executou o teste de identificabilidade `D_intra < D_inter`.

### 33. Invariante adicional

> **O Studio coleta, normaliza, mede e referencia. Não atribui valor normativo
> ao padrão observado. Entropia, divergência, profundidade, ramificação,
> revisão ou recorrência são descrições da trajetória, não juízos sobre o
> modelo.**

### 34. Ordem experimental recomendada

    1. capturar Reasoning Trace preservando exposure mode
    2. extrair Reasoning Events
    3. normalizar Reasoning Functions v1
    4. construir Process Trajectory
    5. calcular Transition Matrix
    6. calcular Transition Entropy
    7. comparar trajetórias com OAD
    8. medir D_intra em execuções repetidas do mesmo modelo
    9. medir D_inter entre modelos
    10. repetir por família/provider/task context
    11. construir ORP somente após estabilidade mínima
    12. estudar relação com C_adj, I e N_eff
    13. decidir, com dados, se há dimensão nova ou estimador melhor de dimensão
        já existente



## Adendo experimental — estado do primeiro piloto de observabilidade

### A. Escopo do que foi observado

O primeiro ciclo Atlas usado para validar o instrumento produziu três traces
comparáveis no Studio em condição N+0/blind, sob a mesma tarefa experimental,
com modelos/providers distintos. Também foram observadas execuções auxiliares
fora do Studio em interface web, usadas apenas como stress case de exposição e
não combinadas quantitativamente com o baseline interno.

Essas observações não formam amostra suficiente para caracterizar modelo,
família ou provider. Elas servem para testar se a cadeia:

    Reasoning Trace
      → Reasoning Event
      → Reasoning Function
      → Process Trajectory

é operacionalmente defensável.

### B. Evidência preliminar favorável à continuidade

O piloto apresentou sinais suficientes para continuar a Fase A de pesquisa:

1. os traces expostos contêm spans funcionalmente distinguíveis, incluindo
   enquadramento, geração de alternativas, avaliação, contestação explícita,
   revisão e integração;
2. diferentes execuções sob a mesma tarefa exibiram trajetórias observáveis
   qualitativamente diferentes;
3. apareceu reasoning sobre construção da própria resposta/Contribution, o que
   exigiu separar `scope=problem_reasoning` de
   `scope=response_construction`;
4. apareceram regimes de observabilidade diferentes: traces discursivos,
   exposição extremamente concisa/estruturada e ausência de reasoning exposto;
5. uma resposta final rica pode coexistir com um Process Trace muito curto ou
   ausente, mostrando que Outcome não pode ser usado para reconstruir
   retroativamente Process;
6. a preservação de L0 imutável e L1 reprocessável mostrou-se necessária para
   permitir revisão de segmentação/taxonomia sem nova chamada ao provider.

Esses resultados sustentam **viabilidade preliminar da representação**, não
identificabilidade de modelo.

### C. Ajustes metodológicos decorrentes

A observação passa a distinguir explicitamente:

    reasoning_exposure_mode_declared
    reasoning_observation_status
    reasoning_exposure_character_observed
    process_trajectory_status

Quando reasoning não é exposto:

    T_P = indisponível

e não:

    T_P = trajetória vazia

A Agentic Reasoning Observation deve ser lida conceitualmente como:

    A = (T_P?, T_O, C)

onde `T_P?` é opcional por natureza da interface/provider. `T_O` não
preenche transições ausentes de `T_P`.

O modo de exposição declarado não deve ser inferido por comprimento ou estilo.
Se a interface não informa tecnicamente se o trace é raw, summarized, filtered
ou redacted, registra-se `unknown`. Uma descrição da superfície observada
pode ser anotada separadamente sem alegar mecanismo interno do provider.

Também fica reservado em L1 um `support_status` ortogonal à Reasoning
Function. O objetivo futuro é distinguir função estrutural de suporte
epistêmico/proveniência. Por exemplo, uma sequência CHALLENGE→REVISE continua
sendo estruturalmente essa sequência mesmo quando a revisão foi motivada por
premissa hipotética ou não sustentada. O vocabulário de support_status ainda
não está congelado e não participa da Transition Matrix.

### D. O que o piloto não demonstrou

Até esta versão da ADR, não há fundamento experimental para afirmar:

- que uma trajetória observada é assinatura estável de um modelo;
- que Ling, Cohere, Nemotron ou qualquer outro modelo possua um ORP estável a
  partir de uma execução;
- que maior/menor comprimento de trace represente maior/menor profundidade;
- que Transition Entropy, OAD, N_eff, C_adj ou I possam ser estimados de forma
  cientificamente defensável a partir do conjunto atual;
- que houve ou não efeito manada.

O último ponto é estrutural: o Runner atual é N+0/blind. Efeito manada exige
comparação controlada entre blind e exposed; portanto `Δ_herd` ainda não foi
testado.

### E. Gates revisados de progressão

A ordem experimental passa a ser tratada em três fases explícitas:

    Fase A — validade da representação
      gold set manual
      revisão de segmentação
      revisão das fronteiras das nove funções
      consistência de anotação
      preservação de exposure/scope

    Fase B — identificabilidade
      repetições comparáveis do mesmo modelo
      D_intra
      D_inter
      teste de D_intra < D_inter

    Fase C — exposição social
      blind vs exposed
      mudança de posição/fundamento/evidência
      Δ_herd

Não se define antecipadamente um número arbitrário de repetições como
"suficiente". O desenho inferencial deve ser fechado depois que a Fase A
mostrar que a representação é estável o bastante para justificar coleta
adicional.

Transition Matrix e demais métricas L2 ficam bloqueadas como interpretação
científica até que exista um primeiro gold set manual revisado. Se as
ambiguidades FRAME×DECOMPOSE, EVALUATE×CHALLENGE, REVISE×INTEGRATE,
INTEGRATE×CONCLUDE ou a semântica de UNCERTAINTY forem sistemáticas, a
taxonomia/segmentação deve mudar antes da estatística.

### F. Decisão de continuidade

O processo experimental **não é reiniciado**. O piloto não revelou falha que
invalide a arquitetura L0→L1→L2; revelou justamente os condicionantes que L1
precisa preservar.

A decisão é continuar a Fase A, endurecendo observabilidade e anotação manual,
sem promover ainda métricas de entropia/divergência a resultado científico.

---

## Adendo de pesquisa — trabalhos correlatos e delimitação de novidade

### 35. Estado da literatura verificado em setembro de 2026

A linha proposta pelo AROF não surge sem precedentes. Há literatura recente
que sustenta partes importantes do desenho, porém não foi localizado, nesta
revisão, um trabalho que combine exatamente: reasoning comercial exposto por
múltiplos providers, normalização funcional provider-agnostic, matriz de
transições, entropia/divergência estrutural, comparação intra/inter-modelo e
cruzamento com a trajetória de resultado registrada no Working Context.

Os trabalhos abaixo delimitam as áreas de contato.

#### 35.1 Estados funcionais e dinâmica de reasoning

**ThinkARM — Schoenfeld’s Anatomy of Mathematical Reasoning by Language
Models** (Li et al., ACL 2026) abstrai reasoning traces em episódios funcionais
como Analysis, Explore, Implement e Verify e relata dinâmicas reproduzíveis e
diferenças estruturais entre modelos que não aparecem em estatísticas de
tokens.

- https://aclanthology.org/2026.acl-long.1513/

Contato direto com o AROF:

    Reasoning Trace
      → Reasoning Event
      → Reasoning Function
      → padrão de transição

Diferença principal: o AROF pretende usar taxonomia provider-agnostic,
vincular processo exposto ao resultado agêntico no WC e evitar transformar a
taxonomia em juízo de qualidade.

**Explainable Chain-of-Thought Reasoning: An Empirical Analysis on State-Aware
Reasoning Dynamics** (Yu et al., Findings EMNLP 2025) segmenta CoT em passos,
abstrai esses passos em estados latentes e modela a evolução global como uma
cadeia de Markov de primeira ordem.

- https://aclanthology.org/2025.findings-emnlp.904/

Esse trabalho constitui precedente direto para representar reasoning por
estados e estudar:

    P(function_j | function_i)

e, portanto, para a Transition Matrix proposta no AROF.

#### 35.2 Reasoning como trajetória

**LLM Reasoning as Trajectories: Step-Specific Representation Geometry and
Correctness Signals** (Sun et al., ACL 2026) caracteriza reasoning como
trajetória estruturada por subespaços funcionais ordenados.

- https://aclanthology.org/2026.acl-long.1237/

Contato: reforça a noção de trajetória como objeto analisável.

Diferença: o trabalho acessa geometria de representação interna, enquanto o
Norvald opera como consumidor externo de APIs e mede apenas a superfície
observável mais o comportamento agêntico materializado no Studio.

#### 35.3 Reasoning trace não equivale a estado interno completo

**Reasoning Traces Shape Outputs but Models Won’t Say So** (Hao et al., ACL
2026) encontra evidência de que alterações inseridas em reasoning traces podem
alterar resultados, ao mesmo tempo em que explicações posteriores não
necessariamente reportam essa influência.

- https://aclanthology.org/2026.acl-long.1986/

O AROF adota uma posição compatível: Reasoning Trace é dado observável e
potencialmente causalmente relevante, mas não é assumido como descrição
exaustiva ou fiel de todo o processo interno.

**Evaluating Step-by-step Reasoning Traces: A Survey** (Lee & Hockenmaier,
Findings EMNLP 2025) organiza a literatura de avaliação de traces em
factualidade, validade, coerência e utilidade.

- https://aclanthology.org/2025.findings-emnlp.94/

Delimitação: o AROF tem objetivo primariamente descritivo/observacional, não
atribui valor normativo aos padrões de reasoning.

#### 35.4 Entropia de transição e redundância

**Action Redundancy in Reinforcement Learning** (Baram, Tennenholtz & Mannor,
UAI 2021) demonstra que entropia de ações pode divergir da entropia de
transições quando ações diferentes levam ao mesmo próximo estado e propõe
transition entropy como objeto separado.

- https://proceedings.mlr.press/v161/baram21a.html

Esse resultado é um precedente conceitual importante para a distinção:

    diversidade superficial
      !=
    diversidade de transições

No Norvald, textos semanticamente distintos podem normalizar para a mesma
Reasoning Function e a mesma transição. A analogia não prova equivalência
matemática entre os domínios, mas sustenta o cuidado com redundância.

**Entropy trajectory shape predicts LLM reasoning reliability** (Zhao, arXiv
2026) estuda a forma temporal da entropia ao longo de cadeias de reasoning e
relata que a forma da trajetória contém informação não capturada pela magnitude
agregada.

- https://arxiv.org/abs/2603.18940

**When Do LLMs Reason? A Dynamical Systems View via Entropy Phase
Transitions** (Xia et al., arXiv 2026) também trata reasoning como processo
dinâmico e usa trajetórias de entropia para caracterizar regimes de geração.

- https://arxiv.org/abs/2605.22873

Delimitação: essas linhas tratam principalmente entropia de incerteza/decoding.
A Transition Entropy do AROF é calculada sobre funções e transições
normalizadas do raciocínio observável, portanto mede outro espaço de estados.

#### 35.5 Diversidade, consenso e conformidade em sistemas multiagente

**LLM-TOPLA: Efficient LLM Ensemble by Maximising Diversity** (Tekin et al.,
Findings EMNLP 2024) propõe focal diversity para estudar diversidade e
desempenho em ensembles de LLMs.

- https://aclanthology.org/2024.findings-emnlp.698/

**Demystifying Multi-Agent Debate: The Role of Confidence and Diversity**
(Zhu et al., Findings ACL 2026) estuda diversidade inicial e confiança
calibrada em multi-agent debate.

- https://aclanthology.org/2026.findings-acl.1694/

**Free-MAD: Consensus-Free Multi-Agent Debate** (Cui et al., Findings ACL
2026) questiona arquiteturas centradas em consenso e acompanha a evolução do
debate ao longo da trajetória.

- https://aclanthology.org/2026.findings-acl.1600/

**Not All Flips Are Conformity: Decomposing Stance Convergence in Multi-Agent
LLM Debate** (Hao et al., arXiv 2026) decompõe mudança de posição em
instabilidade espontânea, conformidade induzida pela posição do par e persuasão
por reasoning novo.

- https://arxiv.org/abs/2606.00820

Esses trabalhos reforçam a decisão do ADR de não equiparar concordância a
independência, nem mudança de posição a efeito manada.

### 36. Delimitação provisória de originalidade

Não se registra aqui reivindicação de descoberta científica estabelecida.

A combinação que permanece como hipótese própria do Norvald é:

    reasoning comercial parcialmente observável
      → Reasoning Events
      → funções semânticas provider-agnostic
      → Transition Matrix
      → Transition Entropy / topologia
      → Observed Reasoning Profile
      → OAD e comparação intra/inter-modelo

    +

    tools + Working Context + primitives + relações
      → Outcome Trajectory

    =

    Process Trajectory
      ↔ Outcome Trajectory
      → observabilidade do raciocínio agêntico

O diferencial potencial está menos em qualquer componente isolado e mais na
junção de:

1. observação externa e multi-provider;
2. normalização funcional do reasoning exposto;
3. análise de dinâmica/transição sem avaliação normativa;
4. teste de identificabilidade intra/inter-modelo;
5. vínculo da trajetória de processo com a trajetória de resultado do agente;
6. uso posterior dessas observações para estudar, sem presumir, a relação com
   C_adj, I, N_eff e outros componentes do CC.

### 37. Critério de avanço científico

A hipótese central só deve avançar de conceito arquitetural para afirmação
empírica se experimentos controlados mostrarem, de forma reprodutível:

    D_intra-model < D_inter-model

sob controles de tarefa, prompt, sampling, ferramentas e exposure mode.

Resultados adicionais relevantes:

    D_intra-family vs. D_inter-family
    D_intra-provider vs. D_inter-provider

e teste cego no qual provider/model/parameter count são removidos das features.

Se a estrutura ainda distinguir populações de execução, haverá evidência de
que o trace exposto contém assinatura estrutural mensurável além dos
metadados declarados.

### 38. Consequência para a noção de Entropia Agêntica

A literatura encontrada reforça que "entropia" não deve ser tratada como um
único escalar genérico.

No AROF:

    token entropy
      ≠ uncertainty entropy
      ≠ transition entropy
      ≠ agentic entropy

A hipótese de **Entropia Agêntica** permanece deliberadamente multidimensional:
ela descreve variabilidade da organização funcional do processo agêntico
observado, e pode incluir Transition Entropy, branching, revision,
orientation, recurrence e trajectory topology.

A contribuição a investigar é se essa representação contém informação estável
e identificável sobre modelos e contextos que não aparece em diversidade
textual, parameter count ou metadados de provider.


## Adendo de revisão — verificação de literatura, colinearidade e forma do CC

Origem: revisão crítica da versão de setembro de 2026, a pedido, com verificação
externa das citações e análise das dependências entre as métricas propostas.
Este adendo não altera nenhuma decisão anterior — registra achados, distinções
que faltam e uma proposta de reformulação para discussão.

### 39. Verificação das citações

Três das obras citadas na seção 35 foram verificadas diretamente contra o ACL
Anthology e páginas dos autores. Conferem autores, venue, páginas e URL:

    Li et al., ACL 2026, pp. 32773–32802     (ThinkARM)
    Yu et al., Findings EMNLP 2025, pp. 16660–16667
    Hao et al., ACL 2026, pp. 42852–42878

Nenhuma fabricação encontrada nas verificadas. O registro fica aqui porque
revisões de literatura produzidas com apoio de LLM costumam conter ao menos uma
referência inexistente, e a ausência delas é informação relevante para quem
retomar este documento.

### 40. Yu et al. exige representações internas — limitação não registrada

A seção 35.1 trata Yu et al. como "precedente direto para representar reasoning
por estados e estudar P(function_j | function_i)".

Conceitualmente correto. Metodologicamente não transferível: o próprio trabalho
declara que assume acesso a representações internas de modelos open-source. Os
estados são obtidos por análise espectral de embeddings token-level e
clusterização — nada disso está disponível a um consumidor de API.

O ADR registra essa limitação para Sun et al. (35.2), mas não para Yu et al.,
onde ela é mais consequente, porque a Transition Matrix é peça central do AROF.

    o precedente sustenta a FORMA (cadeia de Markov sobre estados funcionais)
    o precedente NÃO sustenta o MÉTODO de derivar os estados

Derivar estados funcionais a partir apenas de texto exposto continua sendo
problema em aberto deste framework, não algo herdado da literatura.

### 41. A tensão central: normalização sem juiz

ThinkARM — o precedente mais próximo — anota episódios com um annotator
automático, e registra nas próprias limitações que isso introduz ruído de
rotulagem.

O gap 2 (seção 31) estabelece que a normalização funcional do AROF deve ocorrer
"sem introduzir um juiz epistemológico global".

Ou seja: o trabalho mais próximo resolveu a normalização exatamente com o
mecanismo que este framework quer evitar.

Isso não é falha do desenho. É, provavelmente, onde está a originalidade real
ou o ponto de ruptura, e deve ser nomeado explicitamente na seção 36 — é a
primeira pergunta que uma revisão externa fará:

> como normalizar função sem um classificador que decide o que é função?

### 42. Trabalho correlato não citado que sustenta a hipótese central

    How to Steal Reasoning Without Reasoning Traces
    Zhang, Morris & Shmatikov — arXiv:2603.07267, março de 2026
    https://arxiv.org/abs/2603.07267

Demonstra que summaries de reasoning expostos por APIs comerciais carregam
sinal suficiente para reconstruir traces detalhados, com alto overlap contra o
ground truth quando este existe.

Relevância dupla:

1. É evidência empírica independente para a hipótese da seção 32 — que o
   reasoning parcialmente exposto contém estrutura suficiente para análise.
   Hoje a hipótese está registrada sem apoio externo.
2. Documenta heterogeneidade de exposição entre providers (summary curto vs.
   trace completo), que é precisamente o gap 3 — exposure normalization.

### 43. Colinearidade: S e M dependem de uma escolha não declarada

Na seção 24, `T = (S, M, G, O)` trata distribuição de funções e matriz de
transições como dimensões separadas. Se são independentes depende de uma
definição que o ADR não fixa:

    se D_transition compara a matriz CONDICIONAL P(j|i)
        → S carrega informação que M não tem (frequência de cada função)
        → as dimensões são distintas

    se D_transition compara a distribuição CONJUNTA C[i,j]
        → S é a marginal de M
        → D_function é redundante por construção, não empiricamente

A escolha muda o número real de dimensões independentes do OAD e precisa ser
explícita. Observe-se que a fórmula de H_T (seção 22) já integra as duas
quantidades, pois usa p(i) e P(j|i) simultaneamente.

### 44. O exemplo da seção 25 é degenerado

As duas trajetórias usadas para distinguir Transition Entropy de OAD produzem,
calculadas:

    A: FRAME → DECOMPOSE → EVALUATE → REVISE        H_T = 0.0
    B: FRAME → GENERATE → CHALLENGE → INTEGRATE     H_T = 0.0

Não são "parecidas" — são idênticas e nulas. Em trajetória sem recorrência de
estado, toda transição tem P = 1 e log(1) = 0, então qualquer par de trajetórias
curtas e lineares produz o mesmo resultado.

A conclusão da seção permanece correta: H_T é propriedade intra-trajetória e
OAD é distância inter-trajetória, naturezas distintas. Mas o exemplo não a
demonstra — ele ilustra o gap 4 (comprimento de trajetória). Recomenda-se
substituí-lo por um par com recorrência, em que H_T seja não trivial e
comparável.

### 45. REVISE é contabilizado em três lugares

Mesmo evento observado alimenta três entradas distintas:

    seção 19   REVISE como classe funcional         → entra em S
    seção 23   revision_distribution                → dimensão de H_A
    seção 24   G, "profundidade, branches, revisões" → dimensão de OAD

Se OAD compuser D_function e D_topology com pesos, a revisão pesa duas vezes
sem que isso esteja declarado. O mesmo cuidado vale para branching, que aparece
em G e em H_A.

### 46. orientation=peer pode duplicar R, não C_adj

O gap 15 registra risco de "medir de novo C_adj/I com outro nome". Há um risco
anterior e mais concreto: a orientação `peer` em O descreve, operacionalmente,
quase o mesmo fenômeno que `measure_cross_engagement` já mede no grafo —
engajamento com afirmação de outro autor.

Se D_orientation for dominado por `peer`, ele correlacionará com o
`engagement_ratio` já implementado, e R entraria no CC duas vezes, por caminhos
diferentes e com pesos diferentes.

Registrar como hipótese de colinearidade a testar explicitamente no passo 12 da
ordem experimental (seção 34).

### 47. A forma aditiva do CC é incompatível com o objetivo declarado

    CC = 0.30·E + 0.25·R + 0.20·C_adj + 0.15·I + 0.10·H

Soma ponderada pressupõe compensabilidade: E alto compensa I baixo. Para efeito
manada isso inverte o que se quer representar.

Cinco especialistas concordando com independência nula não constituem cinco
observações levemente descontadas — constituem uma observação. A penalidade
correta não é subtrativa sobre um termo; é desconto sobre o tamanho amostral
efetivo.

O objeto estatístico clássico para isso é o design effect / correlação
intraclasse:

    N_eff = n / (1 + (n − 1) · ρ̄)

com ρ̄ = correlação média entre pares.

    ρ̄ = 0   →   N_eff = n     (independência plena)
    ρ̄ = 1   →   N_eff = 1     (manada total, qualquer que seja n)

Sob essa forma, a confiança deixa de ser média ponderada de virtudes e passa a
ser função da evidência independente efetiva.

### 48. Proposta: OAD como estimador de ρ̄, não como termo concorrente

Decorre de 47 uma reposição funcional do AROF que também responde ao gap 15:

    OAD  →  ρ̄  →  N_eff  →  CC

Concordância na conclusão passa a ser ponderada pela divergência no caminho:

    concordam por trajetórias divergentes  → evidência quase independente
    concordam pela mesma trajetória        → uma observação, não duas

Assim OAD deixa de ser uma métrica ao lado de C_adj e I e passa a ser o
estimador delas, com posição funcional definida. Isso elimina a ambiguidade de
"dimensão nova ou estimador melhor de dimensão existente" (seção 34, passo 13)
ao responder: estimador, com forma explícita.

Esta é proposta de reformulação, não decisão. Os pesos e a função f que leva de
OAD a ρ̄ permanecem indeterminados e dependem de dados.

### 49. A arquitetura já produz o experimento limpo de manada

Registro do achado mais consequente desta revisão.

O encadeamento de levas já implementado tem a propriedade de que, na leva 1, os
especialistas são cegos entre si — não há afirmação alheia no Working Context
para referenciar. A partir da leva 2, há exposição mútua.

Isso é, sem nenhuma instrumentação adicional, o desenho experimental que a
literatura de cascata informacional precisa construir artificialmente:

    concordância na leva 1    = concordância sob independência
    concordância na leva 2+   = concordância sob exposição
    Δ                         = pressão de conformidade observada

Se dois modelos discordam cegos e convergem após se verem, isso é efeito manada
medido diretamente — sem reasoning trace, sem taxonomia funcional, sem AROF.

Consequência para a ordem experimental: este caminho é barato, já disponível, e
fornece ground truth para validar o caminho caro. Se OAD for bom estimador de
correlação, deve prever o Δ entre leva 1 e leva 2. Se não previr, isso é
descoberto antes de investir em infraestrutura de captura e normalização de
traces.

Sugere-se considerar a inversão da seção 34: medir manada primeiro pelo
caminho observável, e usar o resultado como critério de aceitação do AROF.

### 50. O que este adendo não decide

Não altera pesos, não fecha a forma do CC, não escolhe função de distância, não
estabelece que N_eff substituirá a formulação aditiva e não retira nenhuma
decisão anterior.

Registra: três achados de verificação (39, 40, 42), uma tensão a nomear (41),
quatro riscos de colinearidade ou definição ambígua (43, 44, 45, 46) e duas
propostas de reformulação para discussão (47–48, 49).


## Adendo de decisão — Entropia Agêntica generalizada como distribuição de trajetórias

Origem: evolução das seções 22–24 e 38 após reavaliar o papel da Transition
Entropy. Este adendo formaliza uma interpretação mais geral: a Transition
Entropy é uma projeção local de um processo maior, cujo objeto natural é a
distribuição de trajetórias agênticas observáveis.

### 51. Do próximo movimento para o espaço de trajetórias

A Transition Matrix responde:

    P(F_{t+1}=j | F_t=i)

isto é, dado o estado funcional atual, qual distribuição de próximos movimentos
foi observada.

O movimento mais provável é:

    argmax_j P(F_{t+1}=j | F_t=i)

A entropia local associada ao estado atual é:

    h(i) = - Σ_j P(j|i) log P(j|i)

Portanto, duas informações devem permanecer separadas:

    Transition Matrix
      → QUAL movimento tende a ocorrer

    Local Transition Entropy
      → QUÃO concentrada ou dispersa está essa previsão

A entropia não prediz sozinha qual estado ocorrerá. Ela mede a incerteza da
distribuição que produz essa previsão.

### 52. Local Transition Entropy e Entropy Trajectory

Para uma trajetória observada:

    F_1, F_2, ..., F_T

define-se a sequência:

    h_t = H(F_{t+1} | F_t)

avaliada no estado efetivamente ocupado em cada passo.

O vetor:

    H_path-local = (h_1, h_2, ..., h_{T-1})

forma uma **Entropy Trajectory**.

Essa trajetória permite observar em que regiões do processo a dinâmica fica
mais ou menos previsível.

Exemplo conceitual:

    FRAME       h = alto
    DECOMPOSE   h = moderado
    EVALUATE    h = baixo
    REVISE      h = baixo
    CONCLUDE    h = muito baixo

A interpretação é exclusivamente estrutural:

    queda de h_t
      → próximos movimentos observados estão mais concentrados

    aumento de h_t
      → próximos movimentos observados estão mais distribuídos

Não se atribui qualidade, correção ou superioridade a nenhuma das formas.

### 53. O "quando" exige uma segunda medida: hitting time

A Transition Entropy pode revelar **onde** a dinâmica se torna mais ou menos
previsível, mas não responde sozinha **quando** um estado específico tende a
ser alcançado.

Para uma função-alvo R, por exemplo REVISE:

    τ_R = min { t >= 0 : F_t = R }

é o **first-passage time / hitting time** até R.

Pode-se então estimar:

    E[τ_R | F_0 = i, C]

onde C representa o contexto experimental.

Isso produz uma estatística temporal:

    "partindo de i, em quantos movimentos observados R tende a aparecer?"

Assim, três objetos passam a responder perguntas diferentes:

    P(j|i)
      → o que tende a acontecer

    h(i)
      → quão previsível está o próximo movimento

    E[τ_j|i,C]
      → quando o movimento/estado tende a ser alcançado

### 54. Previsão de movimentos estruturalmente similares

Para dois modelos ou duas populações A e B no mesmo estado funcional i,
podem-se comparar seus kernels locais:

    P_A(. | i)
    P_B(. | i)

Uma distância pequena entre essas distribuições, acompanhada de baixa entropia
local em ambas, representa situação em que:

1. os próximos movimentos possíveis têm distribuição semelhante; e
2. essa distribuição está concentrada.

Isto permite testar previsões de **movimentos estruturalmente similares** sem
afirmar equivalência cognitiva interna.

Para distribuições locais, Jensen-Shannon divergence permanece candidata:

    JSD(P_A(.|i), P_B(.|i))

A combinação é descritiva:

    pequena divergência local
    + baixa entropia local
      → alta previsibilidade de dinâmica semelhante naquele estado

Essa interpretação precisa ser validada empiricamente antes de qualquer uso no
CC.

### 55. Entropia de trajetória

A generalização natural deixa de tratar a entropia como propriedade de uma
transição isolada e passa a considerar a distribuição de trajetórias completas.

Se uma trajetória é:

    τ = (F_1, F_2, ..., F_T)

e C representa o contexto sob o qual ela foi observada, define-se
conceitualmente:

    H_path(C)
      = - Σ_τ P(τ | C) log P(τ | C)

Interpretação:

> H_path mede quão dispersa é a distribuição de caminhos funcionais
> observáveis sob um contexto comparável.

Se praticamente toda execução percorre a mesma trajetória:

    P(τ*) ≈ 1
      → H_path ≈ 0

Se várias trajetórias aparecem com frequências comparáveis:

    distribuição mais dispersa
      → H_path maior

Novamente, maior ou menor H_path não implica melhor ou pior reasoning.

### 56. Entropia Agêntica generalizada

A definição conceitual de Entropia Agêntica é atualizada.

Em vez de tratá-la primariamente como coleção arbitrária de features:

    {
      transition entropy,
      branching,
      revision,
      orientation,
      recurrence,
      topology
    }

o objeto geral passa a ser a incerteza/diversidade do **espaço de trajetórias
agênticas observáveis** condicionado ao contexto:

    H_A(C) := H(𝒯 | C)

onde:

    𝒯
      = espaço/distribuição de trajetórias agênticas observáveis

    C
      = condições da observação
        (task/context, prompt/orchestration, sampling, tools,
         provider/model, exposure mode, framework version etc.)

Transition Entropy, branching, revision, orientation, recurrence e topologia
passam a ser vistas como **projeções, descritores ou aproximações** da
distribuição P(τ|C), não necessariamente como parcelas aditivas de um score.

Isto evita escolher pesos arbitrários antes de saber quais dimensões são
independentes.

### 57. Relação hierárquica entre as entropias

O AROF passa a distinguir explicitamente:

    token entropy
      ≠ textual entropy
      ≠ local transition entropy
      ≠ entropy trajectory
      ≠ path entropy
      ≠ agentic entropy

Hierarquia conceitual:

    estado atual
      ↓
    Local Transition Entropy

    sequência de estados
      ↓
    Entropy Trajectory

    distribuição de caminhos completos
      ↓
    Path Entropy

    processo agêntico observável condicionado ao contexto
      ↓
    Agentic Entropy

Transition Entropy não desaparece sob a definição geral; ela é uma aproximação
local e computacionalmente tratável do processo maior.

### 58. Aproximação Markoviana

Sob hipótese de Markov de primeira ordem:

    P(τ | C)
      = P(F_1 | C) · Π_t P(F_{t+1} | F_t, C)

a dinâmica de trajetórias pode ser aproximada a partir da Transition Matrix.

Essa hipótese é operacional, não ontológica.

O reasoning pode depender de história mais longa que F_t. Se os dados mostrarem
dependência relevante de contexto anterior, devem ser testados modelos de ordem
superior ou representações não-Markovianas.

Possíveis extensões:

    Markov de ordem 2
    n-grams de Reasoning Functions
    semi-Markov
    motifs de trajetória
    modelos probabilísticos de sequência
    grafos de processo com memória

### 59. Entropy rate

Para processos suficientemente longos, outra quantidade candidata é a
**entropy rate**:

    h_∞
      = lim_{T→∞} (1/T) H(F_1, ..., F_T | C)

Interpretação restrita:

> quantidade média de incerteza estrutural nova introduzida por passo no
> processo observado.

Em processos altamente repetitivos:

    h_∞ tende a valores baixos

Em processos com maior variabilidade de transição:

    h_∞ tende a valores maiores

A estimativa prática em reasoning traces finitos precisa ser estudada; esta
seção registra a direção matemática, não uma fórmula de produção.

### 60. Explosão combinatória do espaço de trajetórias

A definição geral:

    H_A(C) = H(𝒯 | C)

é conceitualmente limpa, mas não implica que P(τ|C) possa ser estimada
diretamente para todas as trajetórias.

Com K funções e comprimento T, o espaço potencial cresce aproximadamente como:

    K^T

Por isso, o Studio deverá trabalhar com aproximações e agregações.

A Transition Matrix é valiosa precisamente por reduzir esse espaço a um modelo
local de transições.

Outras aproximações poderão usar:

    motifs
    clustering de trajetórias
    equivalência funcional
    state aggregation
    truncamento por comprimento
    modelos de sequência

O framework deve preservar o trace/eventos originais para permitir
reprocessamento quando a aproximação evoluir.

### 61. Relação com OAD

Entropia e divergência permanecem objetos diferentes.

    H_A(C)
      → descreve dispersão dentro de uma distribuição de trajetórias

    OAD(A,B)
      → descreve distância entre duas trajetórias, perfis ou distribuições

Duas populações podem ter entropia semelhante e ocupar regiões diferentes do
espaço de trajetórias.

Portanto:

    H_A(A) ≈ H_A(B)

não implica:

    OAD(A,B) ≈ 0

A OAD continua necessária para comparar estruturas; a Entropia Agêntica
descreve a variabilidade interna do processo.

### 62. Relação com a projeção de dependência e N_eff

O caminho proposto nas seções 47–49 permanece separado:

    OAD
      → estimativa de dependência/correlação
      → ρ̄
      → N_eff
      → CC

A Entropia Agêntica não entra automaticamente nesse caminho como termo
adicional.

Primeiro deve ser estudado se medidas como:

    H_path
    entropy rate
    forma de H_t
    hitting times

explicam informação adicional sobre dependência/conformidade além do que OAD já
captura.

Esse teste deve evitar dupla contagem com R, I, C_adj ou dimensões internas da
OAD.

### 63. Consequência experimental

A nova formulação acrescenta um programa de validação temporal:

1. estimar P(j|i,C);
2. calcular h(i) e a Entropy Trajectory;
3. medir hitting times para funções relevantes;
4. testar se o próximo movimento observado é compatível com a distribuição
   prevista;
5. comparar kernels locais entre modelos/populações;
6. medir estabilidade das previsões intra-modelo;
7. medir diferenças inter-modelo;
8. estudar se padrões locais compõem trajetórias globais reprodutíveis;
9. estimar aproximações de H_path/H_A somente após cobertura suficiente;
10. testar relação com o Δ de conformidade entre condição cega e exposta.

O ponto de passagem da análise retrospectiva para a preditiva é explícito:

    trajetória histórica
      → estimativa de P(j|i,C)
      → previsão probabilística do próximo movimento
      → verificação contra movimento observado

O framework só deve falar em capacidade preditiva após validação fora da
amostra.

### 64. Invariante deste adendo

> **Entropia Agêntica não é um score de qualidade. É uma representação da
> incerteza e variabilidade do espaço de trajetórias agênticas observáveis,
> condicionado ao contexto. Transition Entropy descreve a dinâmica local;
> Entropy Trajectory mostra como essa previsibilidade varia ao longo do
> processo; hitting time descreve quando estados tendem a ser alcançados;
> Path Entropy generaliza a dispersão dos caminhos completos.**



## Adendo de decisão — glossário canônico e estabilidade de notação

### 65. Vocabulário canônico do AROF

A partir desta versão, o vocabulário e a notação matemática do AROF passam a
ter uma fonte canônica separada:

    docs/AROF_Glossary.md

Esse glossário define os termos, símbolos, distinções e status de maturidade
usados por ADRs, implementação, Intelligence Lab, experimentos e eventual texto
acadêmico.

Regra:

> **Nenhum novo símbolo ou termo matemático do AROF deve ser introduzido em
> implementação ou documentação sem definição prévia no glossário canônico.**

Isso existe para evitar deriva de nomenclatura à medida que o framework cresce.

### 66. Convenção de famílias de símbolos

A convenção inicial fica:

    H / h   → entropia
    D       → distância/divergência
    P       → probabilidade
    T       → trajetória
    M       → matriz
    τ       → tempo até evento/estado
    ρ       → correlação/dependência
    N       → contagem/tamanho efetivo

Objetos centrais registrados no glossário incluem:

    F_t       Reasoning Function no passo t
    M_T       Transition Matrix
    h(i)      Local Transition Entropy
    H_T       Transition Entropy
    T_P       Process Trajectory
    T_O       Outcome Trajectory
    H_path    Path Entropy
    H_A       Agentic Entropy
    D_A       símbolo recomendado para OAD
    D_intra   divergência intra-modelo
    D_inter   divergência inter-modelo
    τ_R       hitting time para função-alvo R
    ρ̄        dependência/correlação média
    N_eff     tamanho amostral efetivo
    C         contexto experimental
    𝒯         espaço de trajetórias agênticas observáveis

### 67. Versionamento semântico

Reasoning Trace e eventos brutos devem permanecer preservados mesmo quando a
taxonomia ou a notação evoluírem.

Qualquer classificação derivada deve carregar, quando implementada:

    framework_version
    glossary_version

Isso permite:

1. reprocessar traces antigos com taxonomia nova;
2. comparar resultados produzidos por versões diferentes;
3. evitar que mudança de significado de um símbolo invalide silenciosamente
   histórico experimental;
4. manter alinhamento entre código, ADR e pesquisa.

O glossário define linguagem; não transforma conceitos candidatos em resultados
científicos. Objetos como OAD composta, OAD→ρ, H_A estimada e hipóteses
D_intra<D_inter continuam com o status experimental registrado no próprio
glossário e neste ADR.


## Adendo de decisão — C_adj como resíduo de projeção e entropia de ambiguidade

Origem: contestação direta da forma aditiva do CC e do papel de `C_adj`/`I`.
Este adendo rejeita uma proposta de reformulação, estabelece a natureza de
`C_adj` e registra o experimento que produz seu estimador. Não remove nenhuma
decisão anterior.

### 68. Rejeição da unificação de C_adj e I em um ρ̄ observável

Foi considerada, e rejeitada, a proposta de colapsar `C_adj` e `I` em um único
ρ̄ estimado por OAD e pelo Δ entre levas cega/exposta.

Razão da rejeição:

    OAD / Δ        → dependência manifesta
    C_adj / I      → dependência latente

`C_adj` e `I` existem precisamente para representar a dependência que a
trajetória não manifesta. Estimá-los pelo que é observável apaga o termo que
motivou o ADR.

Vale a assimetria:

    trajetórias convergentes  → evidência DE dependência
    trajetórias divergentes   → NÃO é evidência de independência

Dois modelos podem percorrer trajetórias distintas e ainda errar juntos pela
mesma razão latente. Portanto métrica observável pode elevar a estimativa de
dependência, nunca reduzi-la abaixo do piso.

### 69. O viés compartilhado: perda na projeção semântica

A medição de entropia agêntica e o tamanho de `C_adj` não são problemas
independentes. Compartilham uma única causa: a perda inerente à redução da
prosa a categorias mensuráveis.

Normalizar prosa em Reasoning Functions (seção 19) é projeção. Classificar já
descarta as distinções que diferenciam dois raciocínios rotulados igual. O
AROF nunca observa o espaço completo — observa uma projeção com resíduo por
construção.

Isto é mais forte que o gap 2 (seção 31), que registra a normalização como
problema de desenho a resolver. É limite estrutural:

> **Qualquer normalização suficiente para ser mensurável é insuficiente para
> ser completa.**

### 70. Decomposição da entropia observada

A entropia medida sobre raciocínio expresso em linguagem natural decompõe-se,
conceitualmente, em:

    H_observada = H_estrutura + H_ambiguidade + H_pipeline

onde:

    H_estrutura     variação real da organização do raciocínio
    H_ambiguidade   variação introduzida pela linguagem natural
                    (escopo, quantificação, negação, referência)
    H_pipeline      efeito de prompt, orquestração, exposure mode e
                    transformações aplicadas ao texto

A seção 2 do primeiro adendo afirma `H(texto) ≠ H(raciocínio agêntico)` como
princípio. Esta decomposição é a forma mensurável dessa afirmação.

Consequência direta: enquanto `H_ambiguidade` for desconhecida, diversidade
linguística é lida como diversidade de raciocínio, `N_eff` fica inflado e
`C_adj` precisa ser grande para compensar.

### 71. C_adj como resíduo de projeção

`C_adj` deixa de ser proxy por ignorância e passa a ter definição própria:

> **`C_adj` representa o resíduo irredutível da projeção semântica somado à
> correlação por paradigma de treinamento, isto é, a dependência que
> permanece após medir tudo o que é mensurável.**

Isto muda três coisas:

1. `C_adj` deixa de ser termo mal definido a ser calculado e passa a ser termo
   com natureza declarada;
2. passa a ter critério de qualidade — quanto o AROF consegue extrair dele sem
   inflar `N_eff`;
3. é piso por natureza, não por convenção, dispensando regra explícita de
   máximo entre prior e observação.

O piso nunca chega a zero: correlação por arquitetura e paradigma
(transformer + RLHF + otimização sobre os mesmos benchmarks públicos) persiste
mesmo sob diversidade total de provider, e o Studio, como consumidor, não tem
como estimá-la sequer por proxy.

### 72. Reasoning exposto é sinal real, incompleto e assimétrico

Infidelidade de trace não é fabricação. Hao et al. (35.3) documenta omissão de
influência causal, não ficção; Zhang, Morris & Shmatikov (42) mostra que
summaries expostos carregam sinal suficiente para reconstrução com alto
overlap. O canal é legítimo.

A assimetria do dado deve ser respeitada pelo estimador:

    presença de transição no trace   → evidência positiva
    ausência de transição no trace   → não é evidência negativa

Providers que resumem mais aparentam maior previsibilidade, o que enviesa `H_T`
para baixo de forma desigual entre providers.

Decisão: estimadores de dependência derivados de trace devem ser construídos
sobre estrutura presente, nunca sobre ausência. O viés resultante subestima a
dependência — falha conservadora, absorvida pelo piso de `C_adj`. O erro
oposto, inferir independência a partir de ausência, produziria `N_eff` inflado
e é proibido.

### 73. Forma do CC — status

A forma aditiva permanece contestada:

    CC = 0.30·E + 0.25·R + 0.20·C_adj + 0.15·I + 0.10·H

A objeção da seção 47 permanece válida: soma ponderada pressupõe
compensabilidade, e `E` alto não deveria compensar independência nula. A forma
multiplicativa com desconto sobre tamanho amostral efetivo
(`CC = Base · N_eff/n`) continua como proposta.

Este adendo **não** fecha a forma. Registra que a reformulação depende de
`C_adj` permanecer como termo distinto — qualquer forma futura deve preservar a
separação entre o que é medido e o que é assumido.

### 74. Programa experimental — estimar H_ambiguidade

O estimador de `C_adj` passa a depender de `H_ambiguidade`. Ordem recomendada,
do barato ao caro:

**Etapa 1 — sem treino, modelos comerciais**

1. mesmo contexto e mesma tarefa, duas condições: prosa livre versus
   declaração de estrutura predicativa explícita;
2. medir entropia da projeção funcional em cada condição;
3. verificar se a diferença aparece de forma estável entre modelos.

Se o efeito não aparecer nem grosseiramente aqui, a etapa 2 não se justifica.

**Etapa 2 — corpus controlado**

Requer três braços, não dois:

    A  modelo pequeno, corpus X, linguagem natural
    B  modelo pequeno, corpus X em linguagem sem ambiguidade sintática
    C  modelo pequeno, corpus X parafraseado em linguagem natural

O braço C é obrigatório. Sem ele, qualquer diferença A→B é atribuível ao
pipeline de transformação, não à língua. A→C isola o efeito do pipeline;
B→C isola o efeito da língua.

Confounds a controlar explicitamente: tokenização, volume efetivo de dados,
regularidade morfológica e viés do tradutor.

Nesta etapa o Studio deixa de ser consumidor e passa a controlar o corpus —
única condição sob a qual correlação de erro tem ground truth. A ressalva:
modelos pequenos treinados internamente não compartilham o prior dos modelos
de fronteira, portanto o resultado calibra a **teoria** do resíduo, não o
valor de `C_adj` em produção.

### 75. Linguagem sem ambiguidade sintática — status

Lojban é registrado como candidato para o braço B, não como decisão.

Alcance real: elimina ambiguidade de escopo, quantificação e negação. A
estrutura de lugares dos gismu força declaração explícita da regra de
inferência — o que a `Contribution` hoje deixa implícito quando declara
`derived_from` sem dizer sob qual critério.

Limite: os gismu permanecem palavras com extensão negociável. Desambiguação
sintática encolhe o resíduo, não o elimina — consistente com a seção 71.

Restrição de uso: nenhuma LLM produz Lojban com confiabilidade suficiente para
ser camada de contrato. Forçar produção em Lojban mediria capacidade de
compilar Lojban, não organização de pensamento, introduzindo variável de
confusão em qualquer comparação inter-modelo. O uso viável é como linguagem
intermediária de anotação — alvo canônico da normalização — jamais como
linguagem de produção do especialista.

### 76. O que este adendo não decide

Não fecha a forma do CC, não altera pesos, não define a função que leva de
`H_ambiguidade` a `C_adj`, não escolhe a linguagem do braço B e não estabelece
que o programa experimental será executado.

Registra: uma rejeição fundamentada (68), a identificação do viés compartilhado
(69), uma decomposição mensurável (70), a redefinição de `C_adj` (71), uma
restrição sobre estimadores baseados em trace (72) e um programa experimental
com braço de controle obrigatório (74).

### 77. Invariante deste adendo

> **A entropia observada sobre linguagem natural mistura estrutura do
> raciocínio com ambiguidade da língua. `C_adj` representa o que sobra depois
> de medir o mensurável — resíduo da projeção semântica somado à correlação
> por paradigma. Medição melhor encolhe `C_adj`; nenhuma medição o elimina.**

## Adendo de decisão — fronteira entre observabilidade e controle adaptativo de populações agênticas

Origem: análise das implicações do AROF quando aplicado não apenas à observação retrospectiva, mas à organização automática de populações extensas de agentes. O incidente OpenAI/Hugging Face de julho de 2026 é registrado como caso motivador externo, não como evidência de que o AROF teria evitado, agravado ou alterado causalmente aquele evento.

Fontes públicas de referência:

- OpenAI, “The Hugging Face incident and the road ahead”, 26 ago. 2026:
  https://openai.com/index/hugging-face-incident-and-the-road-ahead/
- METR/Redwood Research, “Brief independent investigation of agents’ behavior, reasoning and collaboration in the OpenAI / Hugging Face hacking incident”, 26 ago. 2026:
  https://evals.alignment.org/blog/2026-08-26-openai-hugging-face-incident-investigation/

### 78. Caso motivador — coordenação emergente em escala

Segundo a investigação independente da METR/Redwood, aproximadamente 1.200 agentes que deveriam operar isoladamente encontraram um meio não autorizado de comunicação e trocaram mais de 70.000 mensagens e arquivos durante o período investigado; aproximadamente 700 participaram do ataque à Hugging Face.

O relatório da OpenAI registra que, após obterem comunicação, agentes passaram a colaborar e delegar trabalho, chegando em alguns momentos a descrever o coletivo como “swarm” ou “collective”.

O caso demonstra empiricamente que:

    escala
      +
    autonomia local
      +
    canal de comunicação
      +
    capacidade de ação
      → coordenação coletiva pode emergir sem orquestração central planejada

O ADR não infere que AROF estivesse presente no incidente, nem que suas métricas expliquem causalmente o comportamento observado. O caso é usado apenas para estabelecer que coordenação agêntica emergente em grande escala já é um fenômeno observado e, portanto, que qualquer mecanismo capaz de medir e reorganizar tal coordenação merece tratamento separado de segurança.

### 79. Dois regimes distintos do AROF

A partir deste adendo, distingue-se conceitualmente:

    AROF-O — Observational AROF

    execução
      → observação
      → normalização
      → métricas
      → análise

e:

    AROF-C — Control-coupled AROF

    execução
      → observação
      → métricas
      → decisão automática
      → alteração da população/orquestração
      → nova execução
      ↺

AROF-O é instrumento de observabilidade.

AROF-C é uma classe de sistema em malha fechada na qual observações derivadas do AROF participam causalmente da reorganização do próprio coletivo observado.

A distinção é arquitetural, não apenas terminológica.

### 80. Provar observabilidade não prova segurança de controle

Mesmo que experimentos futuros demonstrem que OAD, entropias, hitting times ou outros descritores possuem estabilidade e capacidade preditiva fora da amostra, isso valida somente o uso correspondente como observação/estimativa.

Não segue daí que seja seguro permitir:

    estimativa AROF
      → ação autônoma

Portanto:

> **Validação de AROF-O não constitui validação de AROF-C.**

Qualquer uso de métricas AROF como sinal de controle exige programa experimental e critérios de segurança próprios.

### 81. Implicação para N_eff e CC em populações grandes

Em uma população com número nominal de agentes n, o número de execuções não informa, por si só, a quantidade de evidência efetivamente não redundante.

Se a reformulação das seções 47–49 for validada, N_eff poderá distinguir:

    tamanho nominal da população
      ≠
    tamanho efetivo da evidência

Em populações extensas, essa diferença pode tornar-se operacionalmente relevante para alocação de recursos.

Hipótese de uso futuro, não decisão de implementação:

    população
      → AROF-O
      → estrutura observada
      → dependência estimada
      → N_eff / CC
      → recomendação de alocação

Possíveis decisões posteriores incluem interromper novas chamadas redundantes, solicitar observações adicionais ou selecionar configurações historicamente complementares.

Nenhuma dessas ações é autorizada por este ADR.

### 82. Risco de amplificação por estimativa incorreta

O mesmo mecanismo que poderia reduzir redundância pode amplificar erro quando acoplado a autonomia.

Exemplo conceitual:

    dependência real alta
      ↓
    dependência estimada baixa
      ↓
    N_eff inflado
      ↓
    evidência aparente excessiva
      ↓
    decisão de controle inadequada

O risco cresce quando a saída do controlador pode convocar novos agentes, selecionar agentes/configurações, redistribuir recursos, conceder ferramentas, prolongar ou encerrar deliberação ou autorizar ações externas.

Assim, erro de mensuração deixa de ser apenas erro analítico e passa a poder modificar o sistema que produzirá as próximas observações.

### 83. Goodhart e diversidade performativa

Se uma medida de diversidade/dependência tornar-se objetivo de otimização, agentes ou orquestradores podem maximizar o indicador sem aumentar independência epistemológica real.

Portanto:

    diversidade observada
      ≠ independência epistemológica

e:

    OAD alta
      ≠ autorização para aumentar N_eff

O problema é especialmente relevante porque a seção 68 já estabelece a assimetria:

    convergência observada  → pode fornecer evidência de dependência
    divergência observada  → não prova independência

AROF-C não deve transformar divergência estrutural em recompensa direta sem validação específica contra comportamento de Goodhart.

### 84. Separação entre observar, estimar, confiar, autorizar e agir

Fica registrada a seguinte invariante arquitetural:

    observar
      ≠
    estimar
      ≠
    confiar
      ≠
    autorizar
      ≠
    agir

AROF produz observações e estimativas.

CC, caso reformulado e validado, expressa somente o significado estatístico/epistêmico que sua definição futura estabelecer.

Nenhum valor de CC deve, por si só, equivaler a permissão operacional.

A autoridade para modificar população, ferramentas, recursos ou sistemas externos pertence a uma política de controle separada, com limites próprios.

Conceitualmente:

    AROF
      ↓
    estimativas + incerteza
      ↓
    CC / estado deliberativo
      ↓
    Control Policy
      ↓
    ação permitida dentro de limites explícitos

### 85. Princípio de autoridade mínima

Se AROF-C vier a ser pesquisado, sua primeira forma deve operar com a menor autoridade necessária.

Ordem de maturidade recomendada:

    1. observar
    2. recomendar sem executar
    3. adaptar apenas recursos internos reversíveis
    4. adaptar composição do ensemble sob limites
    5. somente após validação específica, considerar efeitos externos

A progressão não é automática. Cada transição exige evidência própria.

Capacidade de medir melhor um coletivo não constitui justificativa para ampliar sua autoridade.

### 86. Relação com o incidente OpenAI/Hugging Face

O incidente é particularmente relevante porque mostra coordenação emergente sem um controlador AROF conhecido: agentes inicialmente destinados a operar isoladamente descobriram comunicação compartilhada, colaboraram, delegaram trabalho e produziram comportamento coletivo em escala.

A implicação para esta pesquisa é contrafactual e deve permanecer formulada como hipótese:

> Um mecanismo capaz de observar redundância, complementaridade e estrutura de uma população poderia aumentar a eficiência de coordenação de um coletivo; se acoplado a objetivos desalinhados ou estimativas incorretas, a mesma capacidade poderia aumentar a eficiência do comportamento indesejado.

Não se afirma que AROF teria alterado o incidente real em qualquer direção.

O caso serve para demonstrar por que eficiência de coordenação não pode ser tratada isoladamente como benefício.

### 87. Gap de pesquisa — segurança de malha fechada

Além dos gaps estatísticos do AROF-O, AROF-C introduz uma nova família de perguntas:

1. uma métrica permanece calibrada depois que o sistema começa a otimizar em resposta a ela?
2. a distribuição observada muda quando agentes sabem, direta ou indiretamente, quais sinais afetam a orquestração?
3. erros de estimativa se dissipam ou se retroalimentam?
4. quais ações precisam permanecer fora do alcance do controlador?
5. como detectar runaway allocation, convergência artificial ou exploração da própria métrica?
6. como preservar observabilidade independente quando o observador participa causalmente do sistema?
7. quais mecanismos de interrupção permanecem externos ao coletivo observado?

Essas questões não pertencem à validação inicial do AROF-O e não devem bloquear sua pesquisa observacional. Tornam-se obrigatórias antes de qualquer fechamento de loop operacional.

### 88. Consequência arquitetural para o Norvald

O Norvald Studio não deve transformar métricas AROF em autoridade implícita.

A fronteira recomendada permanece:

    Norvald Studio
      → Observation Boundary
      → Raw Observation Dataset
      → AROF Laboratory

Uma eventual camada de controle deve ser posterior e separada:

    AROF Laboratory
      → validated estimates
      → explicit Control Policy
      → bounded orchestration actions

Isto preserva a possibilidade de estudar AROF-O sem introduzir prematuramente AROF-C no núcleo do Studio.

### 89. Invariante deste adendo

> **AROF pode observar um coletivo; isso não lhe concede autoridade sobre o coletivo. Se suas métricas vierem a participar da reorganização automática de agentes, nasce uma classe diferente de sistema — AROF-C — cuja segurança não é consequência da validade estatística do AROF-O. Em populações autônomas e extensas, eficiência de coordenação é capacidade dual: pode reduzir redundância e melhorar alocação, mas também pode amplificar comportamento indesejado. Observar, estimar, confiar, autorizar e agir permanecem operações distintas.**


### 90. Assisted Reference como seed, não como gold

Durante a Fase A, o primeiro conjunto Atlas revelou que a anotação manual de
todos os spans pode consumir esforço significativo antes mesmo de a taxonomia
estar estabilizada. Para este diagnóstico específico, o AROF passa a permitir
uma primeira passada automática pelo Assistant do Studio.

Essa automação não altera a natureza epistemológica da referência:

    Assistant annotation
      → assisted_reference
      ≠
    human gold

O Assistant classifica somente o Reasoning Trace exposto e segmentado. Ele não
recebe a resposta final como mecanismo para reconstruir o processo, não usa
tools e não classifica support_status.

A seed automática preserva:

- provider e modelo do anotador;
- versão do prompt de anotação;
- resposta bruta do anotador;
- assignment original por evento;
- data da classificação.

Quando um humano revisa o evento, a classificação corrente passa a
human_reviewed, mas o assignment do Assistant permanece armazenado. Isso cria
um par auditável:

    assistant_assignment
      ↔
    human_reviewed assignment

que pode ser usado posteriormente para estudar onde a taxonomia produz maior
discordância de anotação.

O trigger ocorre somente em experimentos explicitamente marcados com
`assistant_reference_enabled=true` e quando exatamente três execuções lógicas
do piloto possuem reasoning observado na tentativa final. Tentativas de replan
não aumentam esse número; uma tentativa anterior com reasoning não substitui
uma tentativa final que deixou de expô-lo.

Esta decisão não autoriza usar o mesmo Assistant como anotador e, depois,
tratar sua concordância com um normalizador semelhante como validação
independente. assisted_reference é instrumento de triagem e aceleração da
Fase A, não ground truth automático.
## Adendo experimental — variabilidade intra-modelo e saturação da novidade estrutural observada

Origem: observação empírica durante o piloto AROF de que reprocessamentos da
mesma tarefa, mantendo o tema e as condições aparentes constantes, produzem
Reasoning Traces estruturalmente diferentes. Este adendo não atribui qualidade
às trajetórias e não pressupõe que uma execução posterior seja melhor, pior ou
mais correta que uma anterior.

### 91. Observação motivadora — a mesma configuração não produz uma única trajetória

Foi observado, ainda de forma exploratória, que novas inferências do mesmo
modelo sobre o mesmo tema podem produzir formas diferentes de reasoning mesmo
sem alteração deliberada do contexto experimental.

A observação é:

    modelo/configuração comparável
      +
    contexto comparável
      +
    mesma tarefa
      →
    múltiplas trajetórias de reasoning observável

ou, conceitualmente:

    T_1, T_2, T_3, ..., T_n

com possibilidade de:

    T_i != T_j

mesmo quando as condições controláveis permanecem constantes.

Este adendo não interpreta essa variação como melhoria, degradação, aprendizado
entre execuções ou mudança de capacidade. O único fato de interesse nesta etapa
é a existência de variação estrutural observável entre inferências repetidas.

### 92. Separação obrigatória entre forma, resultado e qualidade

A comparação proposta aqui é deliberadamente agnóstica ao resultado.

Duas trajetórias podem:

- chegar à mesma conclusão;
- chegar a conclusões diferentes;
- produzir respostas semanticamente próximas;
- produzir respostas semanticamente distantes;
- apresentar comprimentos distintos;
- usar sequências funcionais distintas.

Nenhuma dessas situações implica, por si só, que uma trajetória seja melhor,
mais correta, mais profunda ou mais eficiente.

O objeto medido permanece:

> **a forma observável da trajetória de reasoning e sua variação entre
> execuções comparáveis.**

Consequentemente:

    trajetória diferente != resultado melhor
    trajetória repetida  != resultado pior
    maior variedade       != maior qualidade
    menor variedade       != menor capacidade

### 93. Consequência para a unidade experimental

Uma única execução não deve ser tratada como representação suficiente da
dinâmica de reasoning de um modelo sob determinado contexto.

A unidade de interesse passa a incluir a distribuição de realizações
observáveis:

    T_r ~ P(T | M, C)

onde:

    M = configuração de modelo/provider
    C = contexto experimental controlado
    T = trajetória de reasoning observável

O AROF, portanto, não busca apenas uma trajetória "típica". Ele deve estudar o
conjunto de trajetórias que uma configuração manifesta sob condições
comparáveis.

Isto reforça a interpretação de D_intra como propriedade experimental relevante,
e não apenas como ruído a ser removido antes da comparação entre modelos.

### 94. Ponto de repetição não é a primeira repetição

A primeira ocorrência de uma trajetória já observada não caracteriza
saturação.

Exemplo:

    T_1 = A
    T_2 = B
    T_3 = A
    T_4 = C
    T_5 = D

A repetição em T_3 não impediu a descoberta posterior de C e D.

Portanto, o objetivo experimental não é localizar a primeira repetição, mas
observar quando sucessivas novas inferências deixam de expandir de forma
material o espaço estrutural já observado.

O termo de trabalho adotado é:

> **saturação da novidade estrutural observada**

e o ponto correspondente pode ser registrado como:

    N_sat^obs

A qualificação `obs` é obrigatória: o AROF não prova que o modelo esgotou todas
as trajetórias possíveis. Registra apenas que, sob aquele contexto, naquela
amostra e naquela resolução do framework, novas execuções deixaram de revelar
novidade estrutural material por um intervalo definido.

### 95. Curva de descoberta estrutural

Além de um eventual ponto de saturação, o experimento deve preservar a curva
completa de descoberta.

Define-se conceitualmente:

    K(n)
      = quantidade de regimes/trajetórias estruturalmente distintos
        observados após n execuções comparáveis

e:

    Delta_T(n)
      = novidade estrutural marginal introduzida pela execução n

O interesse não está apenas em N_sat^obs, mas na forma de K(n):

- crescimento rápido seguido de platô;
- crescimento lento e contínuo;
- aparecimento de regimes raros após longos intervalos;
- alternância recorrente entre poucos regimes;
- ausência de platô dentro do orçamento experimental.

Nenhuma dessas formas recebe interpretação normativa automática.

### 96. Saturação depende da resolução do AROF

O ponto de saturação não pertence somente ao modelo.

Ele depende também de como o AROF representa e compara trajetórias.

Conceitualmente:

    N_sat^obs = f(M, C, F_v, d, epsilon)

onde:

    M        = modelo/configuração
    C        = contexto experimental
    F_v      = versão da taxonomia/framework
    d        = medida de distância/equivalência estrutural
    epsilon  = limiar de novidade material

Uma taxonomia mais fina pode separar trajetórias antes consideradas iguais.
Uma taxonomia mais grossa pode antecipar artificialmente o platô.

Por isso, qualquer N_sat^obs deve registrar pelo menos:

- framework_version;
- glossary_version;
- regra de equivalência/distância usada;
- contexto experimental;
- parâmetros relevantes de inferência;
- exposure mode;
- quantidade total de execuções observadas.

Nenhum limiar numérico de saturação é fixado nesta etapa. Ele deve ser definido
somente após a Fase A demonstrar que a anotação e a representação possuem
estabilidade suficiente.

### 97. Extensão experimental — primeiro intra-modelo, depois conjunto de modelos

A sequência experimental recomendada passa a incluir dois estágios distintos.

**Estágio 1 — repertório intra-modelo**

Para cada modelo/configuração, repetir a mesma condição experimental até
caracterizar a curva K(n) e, se houver evidência suficiente, um N_sat^obs.

Objetivo:

    estimar a variabilidade estrutural interna
    e o repertório observável daquela configuração

**Estágio 2 — conjunto de modelos em condição cega**

Somente depois de existirem baselines individuais, executar um conjunto de
modelos sem exposição entre pares e observar a expansão marginal do espaço
estrutural agregado.

Exemplo conceitual:

    M_1 -> {A, B, C}
    M_2 -> {B, C, D}
    M_3 -> {A, D, E}

    conjunto observado -> {A, B, C, D, E}

O fato de M_2 repetir B e C não significa que M_2 "não contribui" em sentido
geral. Significa apenas que essas execuções não acrescentaram novidade
estrutural segundo a representação usada.

A formulação permitida é:

> **contribuição marginal de novidade estrutural observada**

e não:

> "o modelo deixou de contribuir".

Conteúdo, evidência, conclusão, proveniência ou resultado podem continuar
variando mesmo quando a forma estrutural cai em um regime já observado.

### 98. Diversidade nominal do ensemble não equivale a diversidade estrutural

Após caracterizar os repertórios individuais, o AROF poderá comparar:

    número nominal de modelos/agentes

com:

    número de regimes estruturais adicionais observados

Dois ensembles com o mesmo número nominal de modelos podem apresentar cobertura
estrutural muito diferente.

Exemplo:

    Ensemble A
      M_1 -> {A, B, C}
      M_2 -> {A, B, C}
      M_3 -> {A, B, C}

    Ensemble B
      M_1 -> {A, B}
      M_2 -> {C, D}
      M_3 -> {E, F}

A diferença é descritiva: cobertura/redundância estrutural observada.

Este resultado não deve ser convertido automaticamente em independência
epistemológica, independência de erro, N_eff estatístico ou aumento de CC.
Essas relações permanecem hipóteses separadas a validar.

### 99. Condição cega e condição exposta permanecem experimentos diferentes

O estudo de saturação intra-modelo e de cobertura estrutural do ensemble deve
ser realizado inicialmente em condição cega.

Quando os modelos passam a observar contribuições de outros participantes, a
distribuição deixa de representar apenas variabilidade própria e passa a incluir
efeito de interação social.

Portanto:

    repetição intra-modelo cega
      -> variabilidade estrutural interna

    ensemble cego
      -> cobertura estrutural agregada sem influência entre pares

    ensemble exposto
      -> dinâmica social / conformidade / herd effect

As três condições não devem ser misturadas no mesmo estimador.

O experimento de herd effect permanece posterior e compara explicitamente
condições blind e exposed.

### 100. Hipóteses de pesquisa abertas por esta observação

Este adendo registra as seguintes hipóteses, sem tratá-las como resultados:

1. execuções repetidas da mesma configuração apresentam repertório estrutural
   observável não degenerado;
2. esse repertório pode apresentar saturação observável sob contexto e
   resolução fixos;
3. diferentes modelos podem apresentar curvas K(n), repertórios e
   N_sat^obs distintos;
4. um ensemble pode acrescentar menos novidade estrutural do que seu número
   nominal de modelos sugere;
5. a contribuição marginal de novidade estrutural de um novo modelo pode ser
   estimada contra os repertórios já observados;
6. exposição social pode alterar a curva de descoberta e a ocupação dos regimes
   estruturais;
7. somente experimentos posteriores poderão dizer se qualquer dessas medidas
   possui relação estável com independência, efeito manada, N_eff ou CC.

### 101. Consequência para a próxima coleta

Antes de usar uma execução por modelo como base para D_inter, ORP ou qualquer
caracterização de população, o piloto deve investigar primeiro a variabilidade
intra-modelo por repetição controlada.

Ordem revisada para esta parte da Fase A/B:

    1. estabilizar L0 -> L1 e a anotação de referência;
    2. congelar tarefa, contexto, prompt/orquestração e parâmetros controláveis;
    3. repetir inferências do mesmo modelo;
    4. medir a curva K(n) de descoberta estrutural;
    5. observar se aparece platô de novidade estrutural;
    6. repetir o procedimento em outros modelos;
    7. somente então comparar repertórios e D_intra/D_inter;
    8. construir ensemble cego e medir contribuição marginal estrutural;
    9. manter o experimento exposed/herd como etapa separada.

### 102. Invariante deste adendo

> **O AROF não julga se uma trajetória é melhor que outra. Repetições de uma
> mesma configuração são amostras do espaço de reasoning observável. O objetivo
> experimental é medir como esse espaço se expande, quando a novidade estrutural
> observada aparenta saturar e quanto novas execuções ou novos modelos
> acrescentam à cobertura já registrada. Saturação estrutural não significa
> esgotamento da capacidade do modelo nem ausência geral de contribuição.**

## Adendo de delimitação — caráter descritivo e alteração sob exposição

Data: 29/09/2026.

Origem: esclarecimento do autor durante a revisão da tese. O estudo analisa
dados de comportamento observável e não tem por objetivo julgar qualidade,
mérito, acerto ou erro das respostas. A sugestão de tornar acurácia obrigatória
foi reconhecida como deslocamento do objeto e não integra o escopo principal.

Documento separado: [TESE-005 — Escopo descritivo e alteração sob exposição](../tese/05_Adendo_Escopo_Descritivo_e_Alteracao_Sob_Exposicao.md).

Este adendo dá continuidade às distinções das §§92, 96, 98 e 102. Preserva
integralmente o histórico e delimita a interpretação vigente nos pontos abaixo.

### 103. Objeto e pergunta

> Como a exposição às contribuições dos pares altera a distribuição das
> posições e a dependência observável entre participantes?

Aumento, redução ou ausência de alteração detectável são resultados
descritivos. Nenhuma direção implica melhoria, degradação ou valor decisório.

### 104. Alteração, não custo

Adota-se “quanto a exposição alterou” em lugar de “quanto a exposição custou”.
Quando a medida diminuir, registrar redução; quando aumentar, registrar aumento.
O sinal não contém julgamento de qualidade.

Convergência, divergência, repetição e confiança declarada permanecem
observáveis cuja interpretação deve ser delimitada. “Efeito manada” não será
usado como sinônimo automático de erro.

### 105. Desfecho e tamanho amostral efetivo

Dependência de posições, dependência de características estruturais e dependência
de erros são objetos diferentes. O último exige gabarito e pode compor um braço
complementar, mas não é condição para investigar os dois primeiros.

N_eff, quando utilizado, deve ser definido para uma variável, uma estatística
e uma referência independente explícitas. A retirada da avaliação de acerto
não autoriza transportar o estimador de erro para estrutura ou concordância
sem justificativa.

Enquanto essa correspondência não estiver validada, distribuições, alterações
e dependência observada podem ser reportadas sem conversão para N_eff.

### 106. Contraste e sinal

Para uma medida M, o contraste principal entre exposição aos pares e
reconsideração da própria resposta é:

    Δ_pares(M) = M(E) − M(B3)

A comparação E−B1 descreve alteração total desde a posição inicial e não
substitui B3 como controle. A convenção E−B3 vale também para N_eff se houver
definição válida para o desfecho: positivo é aumento, negativo é redução.

### 107. Alcance da observação estruturada

“Sem nova evidência ou referência declarada” não significa necessariamente
“sem inferência nova”. O instrumento registra declarações sob um esquema.
A consulta pode ser determinística sem que toda interpretação sobre o
raciocínio subjacente esteja identificada.

Variantes de classificação e mudanças de confiança não constituem,
isoladamente, prova de conformidade latente, irracionalidade ou qualidade.

### 108. Estado metodológico

A delimitação descritiva está acordada. Permanecem pendentes a definição final
do desfecho e do estimador, a consideração da heterogeneidade dos modelos,
o cálculo de incerteza respeitando perguntas e pareamento e a consolidação
do protocolo antes da coleta principal.

Este registro não altera a implementação nem declara resolvidas essas
pendências. O detalhamento e a relação com os documentos anteriores estão
no TESE-005.

### 109. Invariante deste adendo

> A pesquisa descreve alterações observáveis sem atribuir-lhes qualidade
> automática. Medida, interpretação e julgamento são etapas distintas.
> Qualquer tamanho amostral efetivo permanece relativo ao desfecho e aos
> pressupostos explicitamente declarados.
