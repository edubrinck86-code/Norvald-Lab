---
id: KNOWLEDGE-ISOLATION-AUDIT-001
status: Mitigated
version: 0.3.0
date: 2026-09-21
scope:
  - Library
  - Repository
  - Knowledge Graph
  - ResearchScope
  - Deliberation
  - Assistant
  - AROF
---

# Auditoria de Isolamento Epistemológico — Library, Repository e Knowledge Graph

## 1. Motivo

O AROF depende de observar trajetórias de raciocínio sob um contexto identificável.

Se o contexto recuperável pela LLM mistura conhecimento de escopos diferentes, uma mudança de trajetória pode ser causada pelo corpus disponível e não pelo modelo. Nesse cenário, medidas de divergência, transição, dependência, conformidade ou repetibilidade podem ser atribuídas ao agente quando na realidade foram produzidas por contaminação de contexto.

Esta auditoria verifica o fluxo:

    Repository / Library
        ↓
    Evidence / CDD
        ↓
    Knowledge Graph
        ↓
    retrieval
        ↓
    ferramentas / prompt
        ↓
    LLM

A auditoria não altera a política de conhecimento. Ela registra o comportamento atual e os pontos que exigem decisão arquitetural.

---

## 2. Semântica esperada dos ambientes

A distinção operacional considerada nesta auditoria é:

### Library

Fonte de conhecimento do Studio.

Seu conteúdo pode ser deliberadamente reutilizado entre contextos distintos quando foi admitido como conhecimento de escopo Studio-global.

### Repository

Fonte de conhecimento/material do workspace.

Documentos, notas, anexos e referências pertencem ao workspace e não devem atravessar para outro workspace apenas porque existe uma ferramenta ou um índice global.

### Working Context

Conhecimento construído da deliberação corrente.

É sessão-local e possui provenance.

### Knowledge Graph

Representação derivada.

O KG não deveria apagar o escopo das fontes que projeta. Uma projeção global pode existir, mas a recuperação oferecida a uma execução precisa conhecer qual parte é admissível naquele contexto.

---

## 3. Conclusão executiva

A implementação anterior possuía **promoção epistemológica sem autoridade** em mais de um ponto.

O principal problema nunca foi o fato de a Library ou do KG serem globais.

O problema era conteúdo originado em workspaces entrar na Library global automaticamente ou por uma LLM especialista, sem uma decisão de autoridade. Essa fronteira foi corrigida. O `retrieve_knowledge` continua global deliberadamente.

A situação atual pode ser resumida assim:

    Repository(workspace A)
            │
            │ encerramento / publicação
            ▼
       Library global
            │
            ▼
       KG global
            │
            ▼
    retrieve_knowledge
            │
            ├──────────────► deliberação workspace A
            ├──────────────► deliberação workspace B
            └──────────────► deliberação sem workspace

Sem uma decisão explícita de promoção, conhecimento local pode tornar-se conhecimento global.

Para o AROF, isso é um bloqueador antes do primeiro experimento que permita `retrieve_knowledge`.

---

## 4. Achado K1 — o KG é construído da Library inteira

**Decisão: comportamento correto e preservado.**

`build_knowledge_graph(items)` não recebe workspace, sessão ou política de visibilidade.

Os chamadores relevantes usam:

    build_knowledge_graph(library.list())

A Library é um store global:

    build_evidence_library()
      → EvidenceLibrary(build_library_store("evidence_library"))

Não existe namespace de workspace na chave do store.

Consequência:

> O grafo de descoberta é uma projeção do acervo global da Library.

Após a decisão arquitetural, isto é a semântica desejada: o que entrou legitimamente na Library pertence ao conhecimento global do Studio e pode alimentar descoberta em qualquer workspace.

---

## 5. Achado K2 — retrieve_knowledge percorre o KG global

**Decisão: comportamento correto e preservado.**

`build_scoped_library_tool_registry(library, scope)` aplica o `ResearchScope` a:

- `search_library`;
- `read_library_document`.

Entretanto registra:

    retrieve_knowledge → _handle_retrieve(library)

sem passar `scope`.

O próprio comentário atual afirma:

> o escopo limita a busca por texto, não o percurso do conhecimento consolidado.

Dentro de `_handle_retrieve`, todos os modos usam a Library global:

    query     → build_knowledge_graph(library.list())
    dimension → build_knowledge_graph(library.list())
    address   → build_knowledge_graph(library.list())

Portanto uma deliberação pode descobrir conhecimento global por `retrieve_knowledge`. Isso não é mais tratado como bypass: Library/KG são a memória global do Studio. O ResearchScope continua governando a investigação contextual, não a visibilidade epistemológica do acervo global.

---

## 6. Achado K3 — CDD de workspace era promovido automaticamente para Library global

**Estado: corrigido.**

Ao encerrar uma deliberação:

1. o CDD final é criado como Artifact;
2. `library.upsert_consolidated_document(...)` grava o CDD na Library;
3. se houver workspace, `_promover(..., workspace_id)` também copia o Artifact para o Repository daquele workspace.

O CDD gravado na Library não recebe `workspace_id`.

`Evidence` não possui campo canônico de escopo/workspace.

`upsert_consolidated_document` recebe:

- session_id;
- title;
- body;
- canonical_body;
- tags;
- semantic.

Não recebe workspace.

Consequência:

    conhecimento produzido no workspace
           ↓ encerramento
    Library global
           ↓
    KG global

Encerrar agora materializa o CDD como Artifact e mantém a persistência no Repository do workspace, mas não publica na Library. O CDD só entra no conhecimento global por promoção explícita.

---

## 7. Achado K4 — publicação por LLM podia promover conhecimento local para o escopo global

**Estado: corrigido.**

`publish_to_library`:

- recebe um Artifact da sessão;
- cria um novo `Evidence` na Library;
- não registra `workspace_id`;
- declara que o item passa a ser legível por qualquer deliberação futura.

A ferramenta pertence a `ARTIFACT_TOOL_NAMES`.

Em N+1+, esse conjunto entra no perfil ampliado da deliberação.

`ToolGrants.default_available` é `True` para sessões novas.

Logo, salvo revogação/configuração específica, uma LLM pode transformar um artefato local da deliberação em conhecimento global do Studio.

O problema não é a existência da operação de publicação.

O problema é a **mudança de escopo** não possuir hoje uma autoridade epistemológica própria.

Publicar no Repository e publicar na Library não são operações equivalentes:

    save_to_repository
      sessão/workspace → workspace

    publish_to_library
      sessão/workspace → Studio-global

A segunda é uma promoção de autoridade/escopo. `publish_to_library` foi removida do catálogo das LLMs especialistas e preservada no Assistant.

---

## 8. Achado K5 — mesma origem podia existir com identidades independentes

**Estado: mitigado com identidade canônica.**

No encerramento de uma deliberação vinculada a workspace, o mesmo CDD é materializado em:

### Library

    Evidence(kind="documento_consolidado")
    reference = session_id
    semantic = conteúdo estruturado

### Repository

    WorkspaceDocument
    workspace_id = workspace atual
    source_artifact_id = artifact.id

Não existe uma identidade canônica compartilhada entre as duas representações.

A Library não grava `source_artifact_id`.

O Repository não grava `library_id` do CDD.

Assim a mesma origem pode ser observada por caminhos diferentes:

    Repository context/search
          +
    KG / retrieve_knowledge

e aparentar ser duas fontes distintas.

Para o AROF isso é particularmente perigoso:

> duas recuperações textualmente/estruturalmente concordantes podem ser duplicações da mesma origem, não evidência independente.

---

## 9. Achado K6 — Evidence selecionada podia duplicar referência da Library no Repository em N+0

**Estado: corrigido na montagem do prompt.**

O Repository pode conter referências para itens da Library por `WorkspaceDocumentLinkStore`.

`render_project_block` inclui o corpo dessas referências vinculadas.

Separadamente, uma Evidence escolhida para a deliberação também pode ser uma cópia do mesmo item da Library.

Em N+0:

- `project_block` entra em `shared_instructions`;
- `evidence_block` também entra em `shared_instructions`.

Não existe deduplicação entre:

    Library item selecionado como Evidence
        ↕ mesma library_id
    Library reference vinculada ao Repository

Quando uma Evidence selecionada possui `library_id`, esse mesmo ID é excluído do bloco de referências Library do Repository em N+0. Os papéis continuam auditáveis, mas o corpo não é repetido na mesma requisição.

---

## 10. Achado K7 — lifecycle da Library

**Decisão: não podar o KG; expor o estado.**

`Evidence.status` existe e o nó documental preserva o valor.

Entretanto:

- `build_knowledge_graph(library.list())` inclui todos os itens;
- `search_knowledge` percorre todos os nós `knowledge`;
- `by_dimension` percorre todos os nós `knowledge`;
- `neighborhood` não filtra pelo status do documento pai;
- `catalog` não exclui documentos inativos.

Nós `knowledge` não carregam o status do documento pai.

Nenhum filtro foi adicionado ao KG. Em vez disso, `status` agora é herdado também por seções e unidades semânticas e pode ser visto na recuperação. A escolha preserva capacidade histórica e torna o lifecycle observável ao agente; filtros específicos podem ser adicionados futuramente como modo de consulta, não como perda silenciosa do grafo.

---

## 11. Achado K8 — GraphNode não preservava linhagem de origem

**Estado: corrigido e ampliado.**

Hoje `GraphNode` conhece, entre outros:

- document_id;
- document_identifier;
- author_id;
- round_number;
- source_type;
- source_location.

Não conhece:

- knowledge_scope;
- workspace_id;
- origin_session_id;
- promotion_authority;
- canonical_source_id.

Documento, seção e unidade semântica agora projetam:

- `canonical_source_id`;
- `origin_type`;
- `origin_workspace_id`;
- `origin_session_id`;
- `origin_artifact_id`;
- `origin_repository_document_id`;
- `promoted_by`;
- `promoted_at`;
- `source_hash`;
- `content_hash`;
- `content_changed_since_promotion`.

Essas propriedades são informacionais. Não restringem travessia nem tornam o KG workspace-scoped.

---

## 12. Achado K9 — teia inter-documento também é global e sem workspace

**Severidade: média hoje; alta se integrada à recuperação.**

`DocumentEdgeStore` vive em:

    build_library_store("document_edges")

A proveniência registra:

- session_id;
- round_number;
- author_id.

Não registra workspace.

Arestas de deliberações distintas acumulam provenance globalmente.

Hoje essa teia é usada principalmente para auditoria/visualização e não é o núcleo do `retrieve_knowledge`.

Portanto não é o vazamento principal atual.

Mas, se for incorporada ao KG/retrieval no futuro sem correção de escopo, ampliará a contaminação.

---

## 13. Achado K10 — Assistant usa Library/KG global deliberadamente

**Decisão: comportamento correto e autoridade mantida.**

`AssistantRuntime` nasce com:

    build_library_tool_registry(library)

e não com a versão escopada.

Portanto:

- search_library;
- read_library_document;
- retrieve_knowledge

operam sobre a Library global.

As ferramentas de workspace do Assistant são escopadas separadamente.

Isso produz dois domínios simultâneos:

    Assistant workspace tools → workspace ativo
    Assistant Library/KG      → global

Isso pode ser desejado para o Assistant, mas precisa ser explícito. Não deve ser usado como precedente para afirmar que uma deliberação AROF também deve navegar globalmente.

---

## 14. O que NÃO está contaminado no caminho atual

### Repository stores

`WorkspaceDocument`, `WorkspaceNote`, `WorkspaceAttachment` e `WorkspaceBlock` carregam `workspace_id`.

As listagens usam `list_for_workspace(workspace_id)`.

### search_repository da deliberação

Não consulta todo o store.

Pesquisa o `repository_material` previamente montado para o workspace da sessão e carregado no `ExecutionContext`.

Portanto o caminho normal de Repository é local ao workspace.

### Working Context

É sessão-local.

### search_library/read_library_document na deliberação

Quando construídos por `build_scoped_library_tool_registry`, passam pelo `ResearchScope`.

O vazamento principal da Library na deliberação é o `retrieve_knowledge`, não essas duas operações.

---

## 15. Distinção necessária: conhecimento global legítimo vs contaminação

Library global não é, por definição, contaminação.

Se um documento foi explicitamente admitido como conhecimento do Studio, ele deve poder atravessar workspaces.

O problema é não distinguir:

    origem local
    ≠
    promoção global

Hoje estas categorias colapsam na mesma Library:

- documento criado diretamente na Library;
- CDD automático de workspace;
- artefato publicado por especialista;
- CDD de deliberação sem workspace;
- documento global selecionado como Evidence.

Depois do colapso, o KG trata todos como equivalentes quanto ao escopo.

---

## 16. Invariante proposto

> **Conhecimento pode atravessar uma fronteira de escopo somente por uma promoção explícita e auditável.**

Em forma operacional:

    session
      ≠ workspace
      ≠ studio-global

e:

    observar uma fonte
      ≠ referenciá-la
      ≠ incorporá-la ao WC
      ≠ promovê-la ao Repository
      ≠ promovê-la à Library global

---

## 17. Modelo mínimo de escopo recomendado

Não criar múltiplos Knowledge Graphs persistentes.

Manter o KG como projeção derivada, mas preservar a identidade de escopo nas fontes.

Metadados mínimos para itens da Library que possam ter origem em execução:

    knowledge_scope:
      studio | workspace

    workspace_id:
      <id> | null

    origin_session_id:
      <id> | null

    origin_artifact_id:
      <id> | null

    promotion:
      automatic | human | agent | system

Esses nomes são proposta arquitetural, não contrato implementado.

Para um item realmente global:

    knowledge_scope = studio
    workspace_id = null

Para material produzido em workspace e ainda não promovido globalmente:

    knowledge_scope = workspace
    workspace_id = W

---

## 18. Visão de recuperação adotada

A decisão final não cria uma Knowledge View restrita por workspace.

A LLM pode consultar o KG global da Library. A qualificação vem da provenance dos nós e da autoridade na entrada do acervo:

    KG físico/derivado global
            ↓
    filtro de visibilidade
            ↓
    Knowledge View da execução

Para uma deliberação de workspace W:

    contexto local =
        Repository(W)
        + Evidence(session)
        + Working Context(session)

    conhecimento global =
        Library
        → Knowledge Graph

Conteúdo originado em outro workspace só chega ao segundo conjunto depois de promoção autorizada para a Library.

---

## 19. Regra de identidade para evitar falsa multiplicidade

Representações diferentes da mesma origem precisam de uma identidade canônica.

Exemplo:

    CDD Library
       ↕ canonical_source_id
    CDD Repository

AROF deve poder reconhecer:

    duas aparições
    uma origem

Artifact, WorkspaceDocument e Evidence promovida agora preservam `canonical_source_id`. Um CDD usa `cdd:<session_id>`; um artefato comum usa `artifact:<artifact_id>`. Isso permite ao AROF reconhecer várias representações como uma única origem epistemológica.

---

## 20. Implicação direta para AROF

Até esta questão ser resolvida, não é seguro usar livremente `retrieve_knowledge` no primeiro experimento científico.

### 20.1 Auto-contaminação entre repetições

O risco mais grave para os testes de repetibilidade é temporal:

    run 1
      ↓
    deliberação termina
      ↓
    CDD do run 1 entra automaticamente na Library global
      ↓
    KG é reconstruído da Library
      ↓
    run 2 começa
      ↓
    retrieve_knowledge pode descobrir o resultado do run 1

Portanto duas repetições aparentemente idênticas deixam de compartilhar a mesma condição experimental.

Em particular, isso pode contaminar:

- D_intra, porque a repetição posterior dispõe de conhecimento criado pela anterior;
- D_inter, se modelos executados em ordem diferente observarem corpora diferentes;
- blind/exposed, porque "blind" em relação aos pares da execução corrente não impede acesso a resultados de execuções anteriores;
- Δ_conformity, porque convergência pode ter sido induzida por memória persistente do KG;
- qualquer estimativa de dependência, porque uma fonte comum invisível aumenta correlação entre agentes.

Esse efeito existe mesmo com três modelos e poucas chamadas. É uma questão de ordem causal, não de escala.

O primeiro protocolo científico precisa garantir que o corpus de descoberta permaneça congelado durante todas as repetições de uma condição.

O problema não é computacional.

É de validade interna.

Se dois modelos produzem trajetórias diferentes porque um encontrou um CDD de outro workspace e o outro não, o AROF pode medir a diferença corretamente, mas a interpretação "diferença estrutural entre modelos sob a mesma condição" será falsa.

A condição não era a mesma de forma epistemologicamente controlada.

Precisamos registrar no RAW, além da lista de tools:

- scope da view de conhecimento;
- IDs/fontes elegíveis;
- workspace_id;
- itens globais/local autorizados;
- canonical_source_id quando houver duplicação;
- documentos efetivamente recuperados.

---

## 21. Gates antes do primeiro experimento com KG

### G-K1 — política de promoção

Decidir explicitamente:

> Um CDD encerrado em workspace vira Studio-global automaticamente?

Não assumir.

### G-K2 — metadata de escopo

Persistir informação suficiente para distinguir Studio-global de workspace-local.

### G-K3 — retrieve_knowledge escopado

A recuperação precisa receber a view da execução, não `library.list()` irrestrito.

### G-K4 — lifecycle

Itens inativos/arquivados não entram na view ativa salvo pedido explícito de auditoria histórica.

### G-K5 — deduplicação de origem

Library/Repository/Evidence que representem a mesma origem precisam ser identificáveis como tal.

### G-K6 — promoção por agente

Definir se um especialista pode publicar na Library global autonomamente ou se isso requer autoridade humana/política separada.

### G-K7 — teste de isolamento

Criar pelo menos:

    workspace A → segredo epistemológico A
    workspace B → segredo epistemológico B
    Library global → conhecimento G

e verificar:

    execução em A encontra A + G
    execução em B encontra B + G
    A não encontra B
    B não encontra A

O teste precisa cobrir query, dimension e address.

---

## 22. Estado para o AROF

**A barreira de autoridade foi corrigida; falta congelar/verificar o corpus global por condição experimental.**

Não está bloqueado:

- desenvolvimento do Dataset Writer;
- replay;
- Capacity Harness;
- testes de software do Experiment Runner;
- captura RAW.

O Experiment Runner ainda precisa registrar um snapshot/fingerprint da Library no início da condição e verificar que o corpus não mudou entre repetições. Isso protege contra alterações externas feitas pelo usuário/Assistant durante um experimento, sem reduzir o KG ou criar um grafo paralelo.

Um smoke operacional online ainda pode ser feito futuramente para provar plumbing, mas não deve ser tratado como observação científica enquanto a view de conhecimento não estiver isolada.

---

## 23. Invariante final

> **O Knowledge Graph pode ser global como representação; a evidência disponível a uma execução não pode ser global por acidente.**

E:

> **Promoção de escopo é uma ação epistemológica, não uma consequência automática de armazenamento.**
