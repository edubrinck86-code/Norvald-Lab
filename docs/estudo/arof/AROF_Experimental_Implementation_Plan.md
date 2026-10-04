---
id: AROF-EXP-PLAN
status: Draft
version: 0.13.0
references:
  - docs/AROF_Glossary.md
  - docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
tags:
  - AROF
  - experiments
  - observability
  - implementation
---

# AROF — Plano Experimental de Implementação

## 1. Objetivo

Este documento define a primeira implementação experimental do **AROF — Agentic Reasoning Observability Framework** no Norvald Studio.

O objetivo desta fase não é implementar o AROF completo, reformular o CC nem validar hipóteses científicas finais.

O objetivo é construir o menor instrumento capaz de:

1. capturar execuções reais sem alterar o comportamento normal da deliberação;
2. preservar dados brutos suficientes para reprocessamento;
3. normalizar reasoning observável offline;
4. produzir trajetórias e métricas experimentais básicas;
5. executar testes controlados pequenos;
6. permitir escala gradual somente após gates explícitos.

Princípio operacional:

> **Primeiro construir um instrumento confiável. Depois perguntar o que ele mede. Só depois estudar se o que ele mede é útil para dependência, N_eff e CC.**

---

## 2. Restrições reais da fase inicial

A implementação deve assumir as seguintes restrições operacionais:

- nenhum modelo local;
- uso apenas de providers remotos já suportados pelo Studio;
- baseline inicial de **3 LLMs/modelos**;
- máximo operacional atual do Studio: 12 especialistas funcionais;
- disponibilidade potencial maior que 12 modelos, mas com taxa de falha relevante;
- uso de tiers gratuitos;
- capacidade diária aproximada:
  - até ~1000 requisições em um provider principal;
  - até ~500 requisições adicionais somando os demais providers;
- essas cotas são **limites disponíveis**, não orçamento experimental a ser consumido;
- o plano inicial deve permanecer muito abaixo delas.

Decisão:

> **A primeira implementação AROF não pode depender de força bruta, dezenas de modelos simultâneos ou grandes volumes de chamadas para ser útil.**

---

## 3. Escopo: somente AROF-O

Esta fase implementa exclusivamente o regime observacional definido no ADR-1000:

    execução
      → observação
      → dataset bruto
      → normalização offline
      → métricas
      → análise

Fora de escopo:

    métrica
      → decisão automática
      → alteração da população
      → nova execução

Portanto, esta fase não implementa AROF-C.

Nenhuma métrica AROF poderá:

- selecionar automaticamente modelos;
- convocar novos especialistas;
- encerrar deliberação;
- modificar Working Context;
- conceder ferramentas;
- alterar sampling;
- alterar reasoning effort;
- autorizar ação externa.

---

## 4. Fronteira arquitetural

A fronteira recomendada permanece:

    Norvald Studio
        ↓
    Observation Tap
        ↓
    Raw Observation Dataset
        ↓
    ───────── Observation Boundary ─────────
        ↓
    AROF Laboratory
        ↓
    normalização
        ↓
    trajetórias
        ↓
    métricas
        ↓
    resultados derivados
        ↓
    AROF overlay no Debate

O Studio produz observações.

O AROF Laboratory interpreta essas observações. Nesta fase, "Laboratory" é uma fronteira lógica/offline dentro do mesmo repositório, não uma segunda aplicação.

O AROF não participa da construção do Working Context.

### 4.1 Superfície visual mínima

Não haverá uma aplicação AROF separada.

A superfície do usuário fica na própria Deliberação, como overlay aberto pela aba:

    [ Dossiê ] [ AROF ] [ Configuração ]

O Debate continua sendo o estado-base e permanece intacto por baixo do overlay.

O overlay mostra também um indicador operacional RAW ativo/inativo. Esse indicador não é uma métrica AROF; apenas informa se o corpus L0 completo está sendo persistido. A consulta ocorre quando o overlay é aberto e não faz polling.

Durante uma execução, o overlay AROF mostra somente telemetria observacional já emitida pelo Studio, por exemplo:

- especialista/modelo/provider;
- aguardando/em execução/concluído/falhou;
- duração quando persistida;
- tokens quando reportados;
- presença de reasoning exposto.

A superfície não renderiza o reasoning em streaming e não executa análise científica em tempo real.

Depois que métricas AROF existirem, resultados derivados poderão aparecer no mesmo overlay. O usuário não precisa ler JSON/JSONL.

Invariante:

> **A UI AROF é uma projeção de leitura. Abrir, fechar ou manter o overlay aberto não pode alterar a execução nem produzir requisições adicionais a modelos.**

---

## 5. Reaproveitamento da arquitetura atual

O Studio já possui características adequadas para o piloto:

- execução assíncrona de especialistas;
- tarefas concorrentes por leva;
- processamento com `asyncio.as_completed`;
- HTTP assíncrono;
- HTTP/2;
- connection pooling e keep-alive;
- gate compartilhado por provider;
- tratamento explícito de rate limit;
- retry com backoff/jitter;
- streaming;
- telemetria de execução;
- métricas de TTFT e streaming;
- cache de prefixos/contexto em providers compatíveis;
- montagem única do Working Context por leva;
- persistência SQLite otimizada para o fluxo atual;
- observadores existentes que falham de forma não bloqueante.

Conclusão arquitetural:

> **Não é necessário criar um novo runtime multiagente para o AROF. O piloto deve reutilizar a execução existente e adicionar apenas captura observacional passiva.**

---

## 6. Regra de carga inicial

O baseline experimental é fixado em:

    modelos alvo                 3
    concorrência total máxima    3
    rodadas por piloto           1
    ferramentas                  OFF
    browser                      OFF
    MCP                          OFF
    criação de artefatos         OFF
    análise AROF online          OFF
    raw capture                  ON
    reasoning exposto            ON quando suportado

A concorrência experimental não deve herdar automaticamente o teto operacional de 12 agentes.

O fato de o Studio suportar até 12 especialistas não é justificativa para usar 12 em experimento inicial.

### 6.1 Falhas

Falha de modelo/provider é observação válida.

Regra inicial:

- não substituir automaticamente um modelo durante o mesmo run;
- não criar loop de reposição até atingir três respostas;
- registrar claramente falha, provider, modelo, tentativa e motivo;
- rerun é decisão explícita de um novo run;
- modelos reserva podem existir na configuração, mas não entram automaticamente no baseline.

Isso evita que indisponibilidade de provider altere silenciosamente a composição experimental.

---

## 7. Orçamento inicial de chamadas

O primeiro ciclo é cumulativo: dados gerados numa etapa devem ser reutilizados nas seguintes.

### Etapa E0 — infraestrutura sintética

    chamadas reais: 0

Fixtures e respostas sintéticas.

Objetivo:

- validar schema;
- validar serialização;
- validar IDs;
- validar ordenação;
- validar replay;
- validar versionamento;
- validar falhas parciais;
- validar que erro no observador não derruba a deliberação.

### Etapa E1 — smoke real

    3 modelos
    × 1 tarefa
    × 1 execução
    = 3 execuções lógicas

Objetivo:

- confirmar captura real;
- confirmar reasoning quando disponível;
- confirmar response;
- confirmar contexto efetivamente fornecido;
- confirmar metadata de provider/modelo;
- medir impacto local básico.

Não há inferência científica nesta etapa.

### Etapa E2 — repetição mínima

Reutiliza as três execuções de E1 e adiciona:

    3 modelos
    × 1 nova repetição da mesma tarefa
    = +3 execuções

Acumulado:

    6 execuções lógicas

Objetivo:

- testar replay e normalização repetida;
- observar se existe algum sinal intra-modelo;
- identificar instabilidade grosseira da representação.

Duas repetições não constituem amostra científica suficiente. Esta etapa é diagnóstico do instrumento.

### Etapa E3 — segunda tarefa

Adicionar:

    3 modelos
    × 1 segunda tarefa
    × 1 execução
    = +3 execuções

Acumulado:

    9 execuções lógicas

Objetivo:

- verificar se a representação não depende exclusivamente de uma única tarefa;
- descobrir problemas de schema/contexto;
- avaliar se as dimensões escolhidas continuam aplicáveis.

Ainda não é validação de generalização.

### Etapa E4 — piloto blind/exposed

Executar um teste próprio:

    3 modelos × condição blind
    +
    3 modelos × condição exposed
    = 6 execuções

Acumulado máximo do primeiro ciclo:

    15 execuções lógicas

Objetivo:

- provar que o dataset distingue precisamente o contexto recebido em cada condição;
- medir mudança observável após exposição;
- verificar se o pipeline consegue representar o Δ entre condição cega e exposta.

O primeiro ciclo completo, portanto, fica limitado a aproximadamente **15 execuções lógicas úteis**, desde que todos os gates anteriores sejam aprovados.

Tentativas de rede/retries devem ser contabilizadas separadamente das execuções lógicas.

---

## 8. Gates de progressão

Nenhuma etapa escala automaticamente.

### Gate G0 — integridade da captura

Pergunta:

> O Studio consegue gravar uma execução completa sem alterar seu comportamento?

Requisitos mínimos:

- resposta bruta preservada;
- reasoning preservado quando exposto;
- contexto preservado;
- provider/modelo preservados;
- sampling/reasoning effort preservados;
- tool state preservado;
- ordenação preservada;
- dados reprocessáveis.

Falha → corrigir captura.

### Gate G1 — estabilidade do pipeline

Pergunta:

> O mesmo dado bruto produz a mesma representação quando reprocessado pela mesma versão?

Falha → corrigir normalização/versionamento.

### Gate G2 — utilidade estrutural mínima

Pergunta:

> A representação produz trajetórias não triviais e comparáveis?

Falha → rever taxonomia/representação antes de aumentar chamadas.

### Gate G3 — sinal preliminar

Pergunta:

> Existe algum sinal que justifique aumentar repetições ou número de tarefas?

Falha → não escalar por força bruta.

### Gate G4 — validade externa inicial

Pergunta:

> Alguma medida observada possui relação estável com um fenômeno externo, como Δ blind/exposed ou erro verificável?

Somente após este gate estudar ligação com dependência, N_eff ou CC.

---

## 9. Camadas de dados

### L0 — Raw Observation

Imutável.

Deve preservar, por execução:

    experiment_id
    condition_id
    run_id
    task_id
    execution_id

    provider
    model
    model_version quando disponível
    specialist_role

    reasoning_effort
    sampling enviado
    parâmetros efetivos quando retornados

    system/shared/wave instructions
    user message
    exact Working Context supplied
    tool definitions/grants
    exposure condition

    reasoning_raw
    response_raw
    tool calls/results
    Contribution raw
    Contribution parsed
    provider metadata
    usage
    timestamps/order
    framework version

Regra:

> **L0 nunca é sobrescrito por normalização posterior.**

### L1 — Normalized Observation

Derivada de L0.

Inclui:

    ReasoningTrace
      → ReasoningEvent[]
      → função macro
      → scope
      → ambiguidade
      → dimensões
      → orientação
      → relações
      → provenance do span original

Além dos eventos, L1 registra explicitamente a condição de observabilidade do
processo:

    reasoning_exposure_mode_declared
    reasoning_observation_status
    reasoning_exposure_character_observed
    process_trajectory_status

Ausência de reasoning exposto é representada como
`process_trajectory_status=unavailable_reasoning_not_exposed`, nunca como uma
trajetória válida de comprimento zero.

Toda classificação deve carregar versão do normalizador e da taxonomia.

### L2 — Analytical

Derivada de L1.

Pode incluir:

- Function Distribution;
- Transition Matrix;
- Local Transition Entropy;
- Transition Entropy;
- Entropy Trajectory;
- hitting times;
- Process Trajectory;
- Outcome Trajectory;
- distâncias dimensionais;
- comparações intra/inter.

L2 nunca altera L0 ou L1.

---

## 10. Representação do Reasoning Event

As nove Reasoning Functions atuais permanecem como **macrofunções provisórias**, não como representação completa do reasoning.

Um evento deve ser extensível.

Estrutura conceitual:

    ReasoningEvent
      ├── raw_span
      ├── macro_function
      ├── scope
      ├── ambiguous
      ├── dimensions {}
      ├── orientation
      ├── relations []
      └── metadata {}

As ~9 macrofunções formam uma espinha temporal tratável.

`scope` não é uma décima macrofunção. Ele distingue, no mesmo trace,
raciocínio sobre o problema (`problem_reasoning`), construção da resposta/
Contribution (`response_construction`), raciocínio instrumental sobre tools
(`tool_reasoning`) e casos ainda não determinados (`unknown`).

`ambiguous` registra incerteza da anotação sem criar um estado Markoviano
extra. As dimensões descrevem diferenças internas que uma taxonomia plana
perderia.

Decisão:

> **Não criar uma matriz plana de centenas de estados.**

Motivo:

- computacionalmente seria possível;
- estatisticamente exigiria volume muito maior de observações;
- produziria matriz extremamente esparsa;
- tornaria o piloto dependente de força bruta.

A representação deve ser multidimensional e hierárquica.

---

## 11. Relação com frameworks dimensionais extensos

O AROF deve permitir integração futura de dezenas ou centenas de dimensões e subdimensões sem exigir mudança no dado bruto.

Entretanto, a fase inicial não implementará todas.

Critério:

- L0 captura o máximo de matéria-prima;
- L1 possui estrutura extensível;
- novas dimensões podem ser introduzidas por novas versões do normalizador;
- o mesmo corpus pode ser reprocessado sem nova chamada aos providers.

Isto permite:

    execução cara/limitada
      → capturada uma vez

    normalização barata
      → repetida quantas vezes forem necessárias

---

## 12. Persistência

O corpus bruto AROF não deve ser armazenado como expansão indiscriminada do banco principal do Studio.

Motivos:

- reasoning traces podem crescer muito;
- o Studio já utiliza SQLite intensamente;
- existe histórico documentado de crescimento anormal de WAL sob processos presos;
- experimentos exigem reprocessamento e versionamento próprios.

Estrutura adotada a partir do P3:

    NORVALD_DATA_DIR/
      arof/
        sessions/
          <session_id>/
            raw/
              observations.jsonl
        experiments/
          <experiment_id>/
            manifest.json
            raw/
              <run_id>/
                observations.jsonl
            completion.json
            capacity.json

Capturas ad hoc do Studio ficam em sessions/. Coleta controlada fica em experiments/. Isso impede que uma sessão comum seja confundida com dataset experimental certificado.

No ambiente Docker de teste, NORVALD_DATA_DIR=/data, que já está ligado ao volume persistente do Studio. Em desenvolvimento local, o fallback permanece sob backend/data.

A captura RAW é opt-in nesta fase:

    NORVALD_AROF_CAPTURE=1

Sem essa variável, o Observation Sink é Null: o overlay continua mostrando a telemetria operacional já existente, mas nenhum prompt/reasoning completo é copiado para o corpus científico.

Razões:

- evitar crescimento silencioso de armazenamento em deliberações comuns;
- o RAW contém prompt, Working Context, resposta e reasoning exposto;
- separar claramente uso normal do Studio de coleta experimental;
- manter o banco operacional fora do caminho do corpus científico.

O banco do Studio continua responsável pelo Studio.

O dataset AROF possui ciclo de vida próprio.

A organização por experiment_id e manifests entra no Dataset Writer/Replay (P3). O L0 já reserva experiment_id, condition_id, run_id, task_label e exposure_mode, mas não inventa esses valores quando ainda não há Experiment Runner.

Parquet ou banco analítico podem ser avaliados posteriormente, somente se volume justificar.

---

## 13. Observation Tap

Adicionar uma fronteira passiva de captura no fluxo existente.

Requisitos:

1. não modificar response;
2. não modificar Contribution;
3. não modificar Working Context;
4. não modificar ordem da deliberação;
5. falha de persistência observacional não pode falhar o turno;
6. não executar normalização durante a chamada do provider;
7. não chamar LLM adicional.

Fluxo:

    ExecutionResult
        ↓
    Observation Tap
        ├── fluxo normal do Studio continua
        └── cópia imutável → dataset AROF

Implementação adotada:

- o tap fica na fronteira SpecialistExecutionAgent, onde o ExecutionRequest completo e o ExecutionResult coexistem;
- a persistência entra por RawObservationSink injetado, com implementação Null por padrão;
- construção/serialização/gravação do L0 ocorrem fora do event loop e depois da resposta do provider;
- falha de construção, serialização ou gravação do registro é absorvida e nunca muda o resultado do turno;
- execução lógica e tentativa são identificadas separadamente por logical_execution_id + attempt_index;
- started_at e captured_at preservam a janela temporal de cada tentativa;
- attempt_index conta tentativas/replanejamentos na fronteira do agente, não retries HTTP internos do provider;
- o request registrado é explicitamente a fronteira do SpecialistExecutionAgent, não é apresentado como payload nativo de cada provider;
- nesta fase, com ferramentas desativadas nos experimentos, essa fronteira preserva todo o conteúdo textual relevante sem acoplar o AROF aos adapters.

Não criar um AROFEngine dentro do caminho deliberativo.

---

## 14. Normalização offline

A normalização ocorre após a coleta.

Fluxo:

    L0 raw
      ↓
    normalizer vN
      ↓
    L1 normalized

Cada evento deve permitir rastrear:

    classe derivada
      ↓
    evento normalizado
      ↓
    trecho bruto original

Isso permite auditoria e reclassificação.

---

## 15. Métricas v0

A implementação inicial deve evitar score composto.

Prioridade:

1. Function Distribution;
2. Transition Matrix;
3. Local Transition Entropy;
4. Transition Entropy;
5. hitting time;
6. trajetória completa;
7. descritores dimensionais básicos.

Fora de v0:

- pesos de OAD;
- OAD composta normativa;
- função OAD → ρ;
- N_eff em produção;
- CC reformulado.

---

## 16. Três classes de teste

Invariante adicional:

> **No Norvald, execução end-to-end implica chamada online. Um mock pode validar software; não pode validar o pipeline experimental.**


Nunca confundir:

### A. Software tests

Pergunta:

> O código funciona?

Pode usar fixtures e mocks.

### B. Measurement validation

Pergunta:

> O instrumento transforma o mesmo dado de forma estável e auditável?

Usa corpus fixo e reprocessamento.

### C. Scientific experiments

Pergunta:

> O fenômeno hipotetizado aparece nos dados?

Usa execuções controladas reais.

Um teste de software verde não valida uma hipótese científica.

---

## 17. Controle de recursos

O Experiment Runner deve registrar e impor limites explícitos.

Configuração inicial recomendada:

    target_models: 3
    max_concurrency_total: 3
    max_concurrency_per_provider: 2
    max_logical_executions_per_batch: 6
    tool_profile: studio_native
    tools_off_override: false
    online_analysis: false

O limite de `max_concurrency_per_provider: 2` é deliberadamente mais conservador que o gate operacional do Studio.

Motivo:

> O experimento inicial privilegia previsibilidade e observação, não throughput máximo.

Também devem ser registrados:

- execuções lógicas;
- requisições reais enviadas ao provider;
- retries;
- rate limits;
- falhas;
- tokens;
- duração;
- cache;
- reasoning tokens quando disponíveis.

---

## 18. Estratégia de escala

Escala somente após evidência de necessidade.

Ordem recomendada:

    3 modelos
      ↓
    mais repetições com os mesmos 3
      ↓
    mais tarefas com os mesmos 3
      ↓
    5 modelos
      ↓
    8 modelos
      ↓
    até 12, se houver pergunta experimental que exija

Aumento de modelos não é padrão automático.

Em muitos experimentos, aumentar repetições será estatisticamente mais útil do que aumentar variedade de modelos.

Os modelos adicionais disponíveis funcionam como capacidade futura de heterogeneidade, não como requisito do piloto.

---

## 19. Critério para usar chamadas adicionais

Uma nova chamada deve responder uma pergunta que o dataset existente não consegue responder.

Perguntas aceitáveis:

- precisamos de nova repetição para verificar estabilidade?
- precisamos de segunda tarefa para verificar dependência do contexto?
- precisamos de outro provider para testar diferença estrutural?
- precisamos da condição exposed para medir Δ?
- precisamos de ground truth para estudar correlação de erro?

Pergunta não aceitável:

> “Vamos gerar mais dados porque mais dados parecem melhores.”

---

## 20. Ordem de implementação

### Pacote P0 — protocolo

Criar/fechar:

- este plano;
- manifest de experimento;
- definição das condições;
- nomenclatura de IDs;
- regras de falha;
- gates.

### Pacote P0.5 — AROF Telemetry Overlay

Adicionar a aba `AROF` ao Debate, ao lado de Dossiê e Configuração.

Nesta fase, ela consome apenas:

- stream de execução já existente;
- PromptAudit já persistido;
- resposta/reasoning já presentes no chat feed.

Sem endpoint novo, polling novo ou análise online.

### Pacote P1 — Raw Observation Contract

Implementar schema L0 versionado.

Sem chamada adicional de LLM.

### Pacote P2 — Observation Tap

Captura passiva no fluxo real.

Sem normalização online.

### Pacote P3 — Dataset Writer + Replay + Manifest

Implementar:

- JSONL;
- manifest imutável, gravado antes da coleta;
- completion imutável, separado do manifesto;
- SHA-256, bytes, linhas e contagem válida/inválida por arquivo;
- fechamento complete recusado quando houver RAW inválido ou de outro experiment_id;
- caminhos relativos no completion para o dataset continuar portátil entre máquinas;
- replay offline sem importar orchestrator;
- detecção de JSON inválido, schema incompatível e identidade ausente;
- leitura/filtro por experiment/run/model/task;
- separação física entre captura ad hoc de sessão e experimento controlado.

### Pacote P3.5 — Capacity Harness

Implementado como medição operacional separada das métricas AROF.

Registra:

- CPU do processo e do sistema;
- RSS do processo;
- memória disponível/percentual do sistema;
- espaço livre em disco;
- crescimento do dataset;
- duração;
- execuções lógicas, tentativas e falhas informadas pelo runner.

Não possui threshold embutido e não classifica a máquina.

### Pacote P4 — Experiment Runner mínimo

Implementar o coordenador experimental reutilizando o runtime online do Studio.

Pode possuir testes unitários com mocks/stubs para:

- orçamento;
- congelamento de condição;
- IDs experimentais;
- concorrência;
- cancelamento;
- propagação de falhas.

Esses testes não representam execução experimental.

Não implementar modo "offline experiment", provider falso como alternativa operacional ou pipeline sintético de ponta a ponta.

### Pacote P5 — E1: primeiro smoke online com 3 modelos

Somente após P0–P4 passarem nos testes de software.

E1 é o primeiro teste end-to-end do AROF e requer providers reais.

### Pacote P6 — Normalizer v0

Implementar representação hierárquica e extensível.

### Pacote P7 — Measurement validation

Reprocessar o mesmo L0 múltiplas vezes e verificar estabilidade.

### Pacote P8 — Metrics v0

Implementar métricas básicas sem score composto.

### Pacote P9 — E2/E3

Acumular até 9 execuções lógicas reais se os gates permitirem.

### Pacote P10 — E4 blind/exposed

Chegar ao primeiro ciclo máximo de aproximadamente 15 execuções lógicas.

### Pacote P11 — revisão

Decidir, com base nos dados:

- escalar repetições;
- escalar tarefas;
- escalar modelos;
- rever taxonomia;
- interromper determinada hipótese.

---

## 21. O que não implementar agora

Explicitamente fora da primeira fase:

- aplicação AROF separada;
- dashboard científico sofisticado;
- banco analítico dedicado;
- todas as dimensões/subdimensões possíveis;
- usar tools_off como baseline silencioso (tools_off é intervenção experimental);
- seleção automática de ensemble;
- controle adaptativo;
- AROF-C;
- score único de reasoning;
- ranking de modelos;
- OAD composta com pesos arbitrários;
- OAD → ρ sem validação;
- N_eff operacional;
- novo CC;
- integração automática com CDD;
- dezenas de modelos simultâneos.

---

## 22. Definition of Done da primeira implementação

A primeira implementação AROF está concluída quando:

1. uma execução de especialista gera um L0 íntegro;
2. falha do observador não interfere no Studio;
3. três modelos podem ser executados em um piloto pequeno;
4. o mesmo L0 pode ser reprocessado offline;
5. eventos derivados mantêm provenance para o span bruto;
6. versões de taxonomia/normalizador são registradas;
7. as métricas v0 podem ser recalculadas sem nova chamada;
8. blind e exposed preservam contextos distintos;
9. nenhuma métrica AROF controla a execução;
10. o primeiro ciclo pode ser realizado com teto aproximado de 15 execuções lógicas úteis;
11. a telemetria observacional é acessível pelo overlay AROF sem exigir leitura de JSON/JSONL.

---

## 23. Invariante do plano

> **O piloto começa com três LLMs e escala somente quando os dados existentes mostrarem que uma pergunta experimental exige mais. O recurso escasso é a execução real; por isso, captura-se o máximo de matéria-prima uma vez e reprocessa-se offline. A arquitetura deve permitir complexidade futura sem exigir complexidade inicial.**


## 24. Conclusão natural de ferramentas no Studio

O baseline nativo do Studio não impõe mais número fixo de tool calls,
iterações de tool loop ou pesquisas Web por turno.

A execução normal termina quando o agente devolve sua resposta/Contribution
sem novas tool calls.

Proteções preservadas:

- rate limits e retries do provider;
- timeouts;
- compactação do contexto de ferramentas;
- permissões/grants;
- deduplicação de chamada equivalente;
- guard de ciclos sem progresso.

Uma chamada repetida é devolvida como feedback ao modelo e não encerra o turno.
Somente múltiplos ciclos consecutivos sem nova execução bem-sucedida acionam
o stall guard.

Limites numéricos continuam suportados pelo contrato, mas passam a ser
**intervenções explícitas**. O Experiment Runner deve marcar
`tool_limits_explicit=true` quando uma condição científica exigir budget
fixo.

Isso permite distinguir no L0:

    natural_completion
    specialist_no_progress
    tool_call_budget_exceeded
    iteration_limit

e evita tratar um corte invisível da infraestrutura como comportamento natural
do modelo.


## 25. Estado do Runner v0

Implementado sem chamadas reais durante desenvolvimento:

    source session limpa
        ↓
    snapshot N+0/blind
        ├── Working Context congelado
        ├── project block congelado
        └── Library congelada + fingerprint
        ↓
    Manifest write-once
        ↓
    3 especialistas pelo motor online normal
        ↓
    Observation Tap RAW v4
        ↓
    Completion + integridade
        ↓
    Capacity report opcional

O Runner não chama WorkingContextCommitService. Contribution validada é resultado
experimental, não mutação da deliberação fonte.

O v0 recusa sessão com rodada já concluída, contribution.created na timeline ou
conhecimento de especialista no WC. Ele também recusa peer_exposure_mode=exposed.

N+1/exposed será uma extensão posterior e não deve ser inferida a partir do v0.


## 26. Normalizer de referência v0

Implementado o primeiro scaffold L1 para anotação de referência.

Características:

- reprocessa somente RAW já coletado; não chama providers;
- segmentação inicial determinística por blocos/parágrafos separados por linha
  em branco (`paragraph-block-v0`);
- preserva `start_char`, `end_char` e `raw_span` exatos;
- mantém attempts/replans separados por `observation_id`;
- não classifica macrofunções automaticamente;
- cada span nasce com `macro_function=null`, `scope=unknown`,
  `ambiguous=true` e `support_status=null`;
- `support_status` fica reservado sem vocabulário fechado nesta etapa e não
  participa da sequência de macrofunções;
- a anotação humana pode atribuir uma das nove macrofunções, scope,
  ambiguidade e uma nota livre de referência;
- a nota é editada em overlay dentro do próprio AROF e pertence ao L1, nunca ao
  RAW;
- o trace diferencia reasoning observado de reasoning não exposto e registra
  explicitamente a disponibilidade de T_P;
- o modo de exposição declarado não é inferido a partir do comprimento/estilo
  do trace;
- L0 nunca é alterado;
- L1 é derivado e versionado como `arof.l1.reference.v0`.

A escolha deliberada de não usar heurística para preencher as classes evita
que a primeira referência de validação seja construída pelas mesmas regras que
mais tarde serão avaliadas como normalizador automático.

Não existem métricas L2 nesta etapa.

---

## 27. Resultado do piloto de observabilidade e gates revisados

O primeiro conjunto real Atlas forneceu três execuções comparáveis dentro do
Studio em condição N+0/blind, além de observações auxiliares externas em
interface web. O conjunto é diagnóstico do instrumento, não amostra científica.

### 27.1 O que o piloto sustenta até aqui

Há evidência preliminar de **viabilidade da representação**, porque:

- traces reais contêm spans com funções observáveis que podem ser anotadas sem
  reduzir tudo a similaridade lexical;
- apareceram diferenças qualitativas de trajetória sob a mesma tarefa;
- `scope=response_construction` mostrou-se necessário para impedir que
  planejamento de formato seja contado como profundidade do problema;
- regimes de exposição diferentes apareceram empiricamente, incluindo reasoning
  discursivo, exposição concisa/estruturada e ausência de reasoning exposto;
- o caso de exposição curta mostrou que comprimento do trace não pode ser
  interpretado como profundidade do processo;
- Outcome e Process precisam permanecer separados: resposta final estruturada
  não autoriza reconstruir transições não observadas.

Isso aprova apenas a continuação da **Fase A — validade da representação**.

### 27.2 O que ainda não foi demonstrado

Ainda não foi testada a hipótese de identificabilidade:

    D_intra < D_inter

Uma execução por modelo não permite separar efeito de modelo de stochasticidade,
política de exposição, formato da API ou acaso da execução.

Também não foi testado efeito manada. O Runner atual é N+0/blind; portanto ele
não estima:

    Δ_herd = Convergence_exposed - Convergence_blind

Nem Transition Entropy, OAD, N_eff, C_adj, I ou CC devem ser interpretados a
partir deste piloto.

### 27.3 Fases experimentais daqui em diante

    Fase A — validade da representação
      L0 → eventos → funções → trajetória
      gold set manual
      revisão de fronteiras da taxonomia
      consistência de anotação

    Fase B — identificabilidade
      repetições comparáveis do mesmo modelo
      comparação intra-modelo e inter-modelo
      teste de D_intra < D_inter

    Fase C — exposição social
      blind vs exposed sob controles equivalentes
      estudo de Δ_herd e mudança de fundamento/evidência

Somente depois dessas fases deve ser retomada a cadeia candidata:

    OAD → dependência estimada → N_eff → C_adj/I → CC

### 27.4 Gate antes de L2

Antes de implementar Metrics v0, o conjunto de referência deve mostrar que as
fronteiras entre pelo menos estes pares são utilizáveis de forma consistente:

    FRAME × DECOMPOSE
    EVALUATE × CHALLENGE
    REVISE × INTEGRATE
    INTEGRATE × CONCLUDE

`UNCERTAINTY` permanece macrofunção quando a gestão explícita da incerteza é
a função dominante do span. Incerteza embutida em outro movimento pode ser
registrada por dimensão/nota futura sem obrigar um décimo estado concorrente.

Se a anotação manual revelar ambiguidade sistemática, a taxonomia ou a
segmentação deve ser revista **antes** de qualquer entropia/divergência.

### 27.5 Exposure como condicionante obrigatório

Comparações quantitativas futuras devem ser condicionadas pela condição de
exposição observada. Conceitualmente:

    T_P | C, Exposure

e não uma trajetória descontextualizada.

`reasoning_exposure_mode_declared=unknown` deve permanecer unknown quando o
provider/interface não declarar tecnicamente o modo. Uma caracterização humana
da superfície observada pode ser registrada separadamente, mas não autoriza
inferir mecanismo interno do provider.

---

## 28. Assisted Reference — exceção controlada desta fase

Para o diagnóstico atual de sensibilidade à orquestração, o AROF pode usar o
Assistant do Studio como **anotador de primeira passada** quando o experimento
for criado explicitamente com `assistant_reference_enabled=true` e exatamente
três execuções lógicas do piloto possuírem reasoning observado na tentativa
final.

Fluxo:

    3 logical executions com reasoning
      → trigger AROF
      → Assistant interno, sem tools
      → classificação dos spans L1
      → reference_tier=assisted_reference
      → revisão humana seletiva

Regras:

- replans permanecem no RAW e não contam como especialistas adicionais;
- o Assistant recebe somente o Reasoning Trace segmentado, não a resposta final;
- macro_function=null permanece uma classificação válida;
- o Assistant não classifica support_status;
- provider/modelo do anotador, versão do prompt e resposta bruta do anotador
  ficam registrados no L1 para auditoria;
- uma edição humana posterior muda o evento para
  reference_tier=human_reviewed;
- a seed original do Assistant permanece preservada em assistant_assignment,
  permitindo comparação entre anotação assistida e revisão humana;
- a classificação automática não é denominada gold e não valida o próprio
  Normalizer.

Esta automação é deliberadamente uma exceção para reduzir trabalho mecânico
nesta fase de inspeção. Ela não substitui a necessidade de referência humana
nos eventos usados para avaliar concordância ou validar um normalizador
automático.

### 28.1 Trigger operacional

O endpoint:

    GET  /api/arof/experiments/{experiment_id}/assistant-reference
    POST /api/arof/experiments/{experiment_id}/assistant-reference

expõe estado e execução da classificação assistida.

Estados:

    waiting
    ready
    classifying
    complete

O POST é idempotente depois de complete. O backend revalida a flag explícita e
que existem exatamente três execuções lógicas cuja **tentativa final** expõe
reasoning. Tentativas substituídas permanecem no RAW, mas não contam para o
trigger; se um replan final não expuser reasoning, um trace de tentativa
anterior não é herdado.

O overlay AROF dispara o POST automaticamente quando o terceiro reasoning
canônico estiver disponível e mostra o estado do Assistant no mesmo ambiente.
