---
id: AROF-EXECUTION-READINESS
status: Active
version: 0.7.0
references:
  - docs/AROF_Experimental_Implementation_Plan.md
  - docs/AROF_Glossary.md
  - docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
---

# AROF — Execution Readiness Gate

## 1. Objetivo

Antes de executar qualquer experimento AROF com chamadas reais de LLM, verificar se o Norvald Studio possui as capacidades operacionais necessárias para que a execução seja controlada, identificável e reprodutível dentro do que os providers permitem.

Este gate não valida hipótese científica.

Ele responde apenas:

> O instrumento consegue executar e registrar o experimento sem perder, misturar ou inventar variáveis?

---

## 2. Regra arquitetural

Não transformar lacunas do Studio em um novo motor AROF.

Quando faltar uma capacidade:

1. verificar se a responsabilidade já pertence a uma estrutura existente;
2. corrigir a estrutura existente quando a lacuna for geral do Studio;
3. implementar no AROF Laboratory/Experiment Runner quando a necessidade for exclusivamente experimental;
4. não contaminar o fluxo deliberativo normal com controle experimental.

---

## 3. Capacidades verificadas na main atual

### 3.1 Execução multi-provider/modelo

Disponível.

Participantes carregam provider, modelo e reasoning effort individualmente.

### 3.2 Sampling por participante

A infraestrutura existe para temperature, top_p e max_tokens.

Foi encontrada e corrigida uma lacuna: o caminho de configuração pelo start aceitava esses campos no DTO, mas configure_participants não os transferia para Participant. Isso fazia a primeira execução poder divergir da configuração declarada.

### 3.3 Concorrência

Disponível no Studio normal.

A rodada executa participantes em paralelo e o ProviderGate coordena concorrência por provider.

Isso NÃO substitui o limite experimental. O Experiment Runner deve possuir seu próprio teto de chamadas e concorrência.

### 3.4 Perfil nativo de contexto e ferramentas

O protocolo operacional é:

| Fase | WC/âncoras | Evidence direta | Library/Repository/WC | MCP/Web |
|---|---|---|---|---|
| N+0 | sim | sim, recorte selecionado | sim | não |
| N+1+ | sim | não; permanece como âncora/proveniência | sim | sim, quando configurados |

A implementação anterior desligava as ferramentas em N+0 e reconstruía o bloco de Evidence em todas as rodadas. Isso divergia do protocolo e foi corrigido antes do Experiment Runner.

tools_off continua tecnicamente possível, mas é uma intervenção experimental. Não é o baseline nativo e deve aparecer explicitamente no manifest quando utilizado.

### 3.5 Reasoning exposto

Captura disponível quando o provider devolve reasoning.

Ausência de reasoning não pode ser interpretada como ausência de processo.

---

## 4. Lacunas que bloqueiam experimento controlado

### R1 — Identidade experimental

**Implementado no Experiment Runner v0.**

O Studio normal continua sem entidade experimental, por design. O Runner injeta:

- experiment_id;
- condition_id;
- run_id;
- task_label;
- execution_id;
- source_session_id.

Esses campos chegam ao RAW sem contaminar o DeliberationSetup normal.

---

### R2 — Manifest imutável da condição

**Implementado para o Runner v0.**

manifest.json é write-once e é gravado antes da primeira chamada. Registra tarefa,
modelos/providers, sampling, reasoning effort, condição, budget, versões e
fingerprint do corpus global da Library.

---

### R3 — Replay offline

**Implementado.**

replay_jsonl:

- não importa orquestrador/provider;
- valida schema;
- preserva ordem;
- reporta linhas inválidas sem descartar as válidas;
- filtra por experimento/run/model/task.

---

### R4 — Integridade do dataset

**Implementado.**

completion.json é write-once e registra hash, bytes, linhas válidas/inválidas,
execuções lógicas e attempts. Fechamento complete recusa RAW inválido, RAW de
outro experimento e contagem diferente de planned_logical_executions.

---

### R5 — Orçamento experimental

**Implementado no escopo do Runner v0.**

ExperimentBudget controla max_logical_executions, max_attempts e max_concurrency.
O v0 admite no máximo um replan por execução lógica e exige budget de attempts
capaz de cobrir essa fronteira. Retries HTTP continuam internos ao provider e
não viram observações independentes.

---

### R6 — Repetições sobre contexto congelado

**Implementado para N+0.**

O Runner v0:

- recusa sessão fonte já deliberada;
- congela Working Context;
- congela project block do Repository;
- congela a Library em memória e usa esse snapshot nas tools/KG;
- grava fingerprint da Library no manifest e no RAW;
- remove timeline/contributions de pares do prompt N+0;
- nunca commita Contribution na sessão fonte.

N+1/exposed continua fora do v0.

---

### R7 — Exposição aos pares vs exposição do reasoning

**Corrigido no contrato; instrumentação parcial.**

São variáveis diferentes:

- peer_exposure_mode = blind | exposed;
- reasoning_exposure_mode = raw | summarized | filtered | redacted | unknown.

O Studio consegue derivar blind/exposed da política atual de rodada.

O modo de reasoning permanece unknown enquanto não houver evidência explícita por provider.

Não inferir raw/summarized a partir da simples presença de texto.

---

### R8 — Versão exata do modelo

**Parcial.**

O Studio conhece o identificador solicitado e o identificador retornado quando disponível.

Isso não garante revisão interna imutável quando o provider usa aliases.

O experimento deve registrar o que é observável e usar null/unknown para versão não exposta.

Não fabricar model_version.

---

### R9 — Seed cross-provider

**Ausente e não deve ser fingido.**

Não existe suporte uniforme de seed entre providers/modelos.

A reprodutibilidade do AROF deve ser estatística por repetição, não dependente de uma falsa promessa de determinismo idêntico.

---

### R10 — Capacidade do notebook

**Implementado como instrumento; ainda não executado com providers reais.**

A telemetria atual mede execução/modelo, mas não fornece um Capacity Harness experimental com:

- CPU do processo/sistema;
- RAM;
- espaço livre/crescimento em disco;
- duração total;
- taxa de falha;
- volume RAW produzido.

O CapacityMonitor mede CPU do processo/sistema, RAM, disco, crescimento do dataset, duração e contagens operacionais. Ele não contém thresholds e não decide se a máquina "aguenta".

A medição é criada somente durante um experimento e é persistida separadamente em capacity.json.

**Próximo gate:** executar o harness junto do E1 antes de escalar o lote.

---

## 5. O que não bloqueia o primeiro piloto

Não são pré-requisitos para as primeiras chamadas:

- CDD adicional;
- nova UI;
- banco analítico;
- OAD;
- entropia;
- normalizador;
- N_eff;
- CC;
- AROF-C;
- seleção adaptativa de modelos.

---

## 6. Nova ordem de implementação

    G0  Execution Readiness
        ├── corrigir configuração perdida
        ├── separar exposições
        └── congelar requisitos

    P3  Dataset Writer / Replay / Manifest                 ✓
        ↓
    P3.5 Capacity Harness                                   ✓ instrumento
        ↓
    P4  Experiment Runner mínimo N+0/blind                 ✓ código
        ├── 3 modelos
        ├── Library/WC/Repository congelados
        ├── tools_off somente como override explícito
        ├── orçamento explícito
        ├── RAW v4
        └── repetições controladas sem commit
        ↓
    testes de software com fixtures/mocks
        │
        │ não constituem execução AROF
        ↓
    E1  primeiro smoke end-to-end ONLINE
        3 modelos × 1 tarefa × 1 execução
        Capacity Harness ativo
        ↓
    somente então normalização e métricas

---

## 6.1 Gate de isolamento epistemológico

A auditoria detalhada está em:

    docs/Knowledge_Isolation_Audit_AROF.md

A decisão arquitetural foi refinada: Library e Knowledge Graph são globais por definição. O isolamento não ocorre cortando o KG por workspace; ocorre na autoridade de promoção para a Library.

Implementado:

- CDD não entra mais automaticamente na Library ao encerrar;
- LLM especialista não possui `publish_to_library`;
- Assistant mantém autoridade de publicação sob comando do usuário;
- Assistant pode promover documento do Repository para Library;
- Artifact → Repository → Library preserva `canonical_source_id`;
- KG projeta provenance, hashes e deriva documental sem reduzir travessia;
- Evidence selecionada não repete no prompt a mesma referência Library do Repository.

Pendente para o Experiment Runner:

    snapshot/fingerprint do corpus Library por condição

O runner deve verificar que a Library usada por run 1, run 2 e run 3 é a mesma. Mudança externa do corpus invalida a condição ou exige novo run_id/condition_id.

---

## 7. Invariantes

> **O Studio não possui pipeline de execução offline. Toda validação end-to-end do AROF exige chamadas reais de API.**

Fixtures, mocks, stubs e replay offline existem para validar software e reprocessar dados já coletados. Eles não substituem uma execução real do Studio e nunca devem ser contabilizados como run experimental.

O offline começa **depois** que a execução online produziu RAW.

### Invariante de capacidades


> Uma capacidade necessária ao experimento não será presumida porque o Studio possui algo parecido.

Concorrência do Studio não é orçamento experimental.

Sessão repetida não é condição repetida.

Presença de reasoning não define seu modo de exposição.

Configuração exibida não é variável controlada enquanto não for preservada até o request efetivo.

RAW gravado não é dataset válido enquanto não houver manifesto e verificação de integridade.
