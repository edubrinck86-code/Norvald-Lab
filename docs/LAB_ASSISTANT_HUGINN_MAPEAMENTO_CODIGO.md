# Lab Assistant — mapeamento direto do código Huginn ↔ Lab

**Estado:** inventário técnico da `main` dos dois repositórios em 2026-10-15; **nenhuma funcionalidade nova implementada**.  
**Documento conceitual:** [LAB_ASSISTANT_HUGINN_PROPOSTA.md](LAB_ASSISTANT_HUGINN_PROPOSTA.md).  
**Fontes:** `edubrinck86-code/Norvald-Lab` e `edubrinck86-code/Norvald-Huginn` (branches `main`).  
**Método:** leitura estática de classes, funções, rotas, componentes e testes. Não constitui execução de testes nem certificação de comportamento em produção.

## 1. Síntese

**É viável por adaptação seletiva**, sem copiar todo o Huginn. O Huginn já implementa catálogo de operações tipadas, ferramentas de Assistant, trilha de ações, incidentes persistidos, plantão, agendamento e recuperação operacional. O Lab já implementa `Spec`, pré-validação, contratos de execução imutáveis, parser/validador AROF, diagnósticos de `CONTRIBUTION`, ajuste independente, RAW, integridade e projeções para comparação.

**Ausências verificadas:** não há Lab Assistant, catálogo de operações do Lab, registro geral de critérios versionados, motor de incidentes por critério, protocolo autenticado entre Assistants, exportação comparativa estruturada de servidor ou fila durável de ações do Assistant.

## 2. Pontos do Huginn a reaproveitar

Os links abaixo apontam para a `main` do Huginn.

| Responsabilidade | Arquivo / símbolos reais | Situação e adaptação |
| --- | --- | --- |
| Operação tipada | [`domains/operations/operation.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/operations/operation.py), `Operation(name, kind, summary, input, run)` | **Padrão diretamente útil**; definir operações próprias do Lab |
| Catálogo e autorização | [`domains/operations/catalogue.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/operations/catalogue.py), `Catalogue.describe/allowed/call` | Pydantic `model_validate`, visibilidade por ator, registro de resultado. **O controle atual `owner` vs `reserved` é insuficiente** para autorizar custo/correção/exportação no Lab |
| Três ferramentas da LLM | [`domains/assistant/tools.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/assistant/tools.py), `definitions`, `CatalogueTools.index/run` | `list_operations`, `describe_operation`, `call_operation`; úteis após substituir catálogo pelo do Lab |
| Laço do Assistant | [`domains/assistant/service.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/assistant/service.py), `Assistant.ready/send/turn/answer` | Provider operador configurado, passos limitados, histórico e eventos; adaptar prompt e política. Threads ativas em `self.working` **não são fila durável** |
| Configuração do operador | [`domains/assistant/contracts.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/assistant/contracts.py), `AssistantSettings` | Provider/model do Assistant, `max_steps`, `daily_token_cap`, `duty_attempts`; separar do `Spec.participants` |
| HTTP/UX do Assistant | [`domains/assistant/routes.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/assistant/routes.py), `/api/assistant/...` | Referência de superfície HTTP; **não copiar rotas cegamente**, criar namespace/segurança locais |
| Histórico de conversa | [`domains/assistant/repository.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/assistant/repository.py), `AssistantRepository` | SQLite para mensagens/passos/consumo; dados separados do RAW do experimento |
| Diário de ações | [`domains/diary/repository.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/diary/repository.py), `Diary.record` | Append-only de ator, operação e desfecho, com redaction/truncamento |
| Log e cursor de eventos | [`infrastructure/event_log.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/infrastructure/event_log.py), `EventLog.record/after/cursor` | Persistência SQLite para operação/incident watch. **Não substituir** `events.jsonl` experimental |
| Detector de incidentes | [`domains/incidents/watch.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/incidents/watch.py), `IncidentWatch.pump/handle/recover/start` | Lê eventos após cursor e isola erros de processamento; `Reading` atual interpreta eventos de pesquisa/publicação, exige adaptador AROF |
| Estado do incidente | [`domains/incidents/service.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/incidents/service.py), `Incidents.signal/close/escalate` | Agregação, limite de sinais, timeout e escalonamento; identidade deve incluir **critério, observação e versão** |
| Persistência de incidentes | [`domains/incidents/repository.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/incidents/repository.py), `IncidentRepository` | Registro, cursor e recuperação; adaptar schema por critério |
| Plantão do Assistant | [`domains/incidents/duty.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/incidents/duty.py), `Duty.consider/finished` | Limite de tentativas, reativação e escalonamento. Usar autorizações específicas, sem operar conserto científico por prompt apenas |
| Diagnóstico operacional | [`domains/research/recovery.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/research/recovery.py), `failure/eligible/Recovery` | Aproveitar classificação; **NÃO** copiar substituição automática de modelos na coleta AROF |
| Persistência de retries/efeitos | [`domains/research/recovery_repository.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/research/recovery_repository.py), `RecoveryRepository` | Leases, tentativas, receipts e orçamento persistentes; referência para idempotência das **operações do Assistant** |
| Scheduler de dependências | [`domains/research/scheduler.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/research/scheduler.py), `WorkScheduler.enqueue/start/mark_satisfied/invalidate/snapshot` | Workers paralelos, dependências, limite por provider, `coordinating`; **estado do scheduler em memória**, adicionar persistência própria de jobs |
| Rotinas recorrentes | [`domains/routines/service.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/routines/service.py), `Routines.pending/create/tick/start` e [`repository.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/domains/routines/repository.py) | Persistência de agenda/ocorrências, idempotência, horário/fuso; hoje fortemente acoplado a research/content/edições |
| Montagem dos serviços | [`api/composition.py`](https://github.com/edubrinck86-code/Norvald-Huginn/blob/main/core/huginn/api/composition.py), `compose` | Demonstra injeção de dependências; no Lab é necessária composição própria |

**Limite do reuso:** o prompt existente do Huginn diz para não pedir confirmação salvo ambiguidade; isso **não serve** como autorização automática para novos experimentos pagos, ajustes e transferências de dados. A permissão deve ser imposta no serviço/catálogo, não apenas no prompt.

## 3. Pontos do Lab que já oferecem a capacidade de domínio

| Necessidade do Assistant | Código concreto do Lab | Operação/contrato existente |
| --- | --- | --- |
| Template para preencher | [`experiment_management.py`](../norvald_lab/experiment_management.py), `experiment_template` | `GET /api/experiment-template` |
| Editar cópia independente | `ExperimentManagement.editable_copy` | `GET /api/experiments/{id}/editable-copy`; nova base B1 e ID |
| Validar campos do framework | [`config.py`](../norvald_lab/config.py), `validate_spec` (linhas 40–140) | IDs, modelo, provider, sampling, corpus, exposição, repetições e budgets |
| Conferência integral | [`runner.py`](../norvald_lab/runner.py), `ExperimentRunner.prepare` (78–158) | `POST /api/prepare` retorna Spec normalizado, requests, fingerprint |
| Congelar chamadas e executar | `PreparedExperiment`, `ExperimentRunner.run/_run` (160–271) | `POST /api/experiments` aceita coleta; manifesto, requests, RAW, eventos e result |
| Derivar B3/E | [`cli.py`](../norvald_lab/cli.py), `derive_spec` (24–31); `ExperimentRunner.prepare` | `POST /api/derive`; exige B1 completa, íntegra, pareada, corpus e configuração equivalentes |
| Providers/modelos | [`models.py`](../norvald_lab/models.py), `ModelCatalog.provider/get/test`, `normalize_model` | `POST /api/models`, `POST /api/settings/connections/{kind}/test` |
| Credenciais | [`settings.py`](../norvald_lab/settings.py), `LocalSettings`; [`api.py`](../norvald_lab/api.py) | `GET/PUT /api/settings...`; chaves são privadas e não voltam à UX |
| Diagnóstico de resposta | [`contribution_check.py`](../norvald_lab/contribution_check.py), `check_contribution/check_records` | `usable`, `fully_valid`, `code`, declarados/aceitos, recusas e motivos |
| Parser e semântica estrutural | [`domain/deliberation/contribution.py`](../norvald_lab/domain/deliberation/contribution.py), `Contribution.parse`; [`contribution_validation.py`](../norvald_lab/domain/deliberation/contribution_validation.py), `validate_and_convert` | **Fonte da verdade**: não reimplementar por heurística de LLM |
| Diagnóstico para correção | [`adjustment_prompt.py`](../norvald_lab/adjustment_prompt.py), `adjustment_diagnostic/diagnostic_instructions` | Pormenoriza JSON inválido, campo ausente, relação rejeitada e tipos permitidos |
| Ajuste separado e rastreável | [`adjustments.py`](../norvald_lab/adjustments.py), `AdjustmentStore.prepare/run/start` | `POST /api/adjustments/{id}/preview` e `POST /api/adjustments/{id}`; não independente |
| Snapshot e checks | [`observer.py`](../norvald_lab/observer.py), `snapshot` (33–51) | `GET /api/experiments/{id}/observe`; inclui eventos, requests, RAW, `contribution_checks` |
| Integridade e RAW | [`storage.py`](../norvald_lab/storage.py), `seal/verify_experiment/read_verified_records` | `GET /api/experiments/{id}/verify` e `/raw` |
| Declarado vs validado | [`application/arof/outcome_validation.py`](../norvald_lab/application/arof/outcome_validation.py), `validation_from_payload` | Lê o próprio RAW/contexto para colunas validadas ao lado do declarado em `outcomes.csv` |
| Comparação atual | [`frontend/src/components/Compare.tsx`](../frontend/src/components/Compare.tsx) | reúne `/observe` da família, exige integridade válida e calcula diff textual no **frontend** |
| Tela de preparo | [`frontend/src/components/Prepare.tsx`](../frontend/src/components/Prepare.tsx) | usa settings/template/model picker/prepare/start; mudar campo invalida preview |
| UI de correção existente | [`frontend/src/components/AdjustResponse.tsx`](../frontend/src/components/AdjustResponse.tsx) | prepara pedido, mostra diagnóstico, envia tentativa sob ação explícita |

### 3.1 Fluxo real de preparo/validação do Lab

```text
Prepare.tsx / Assistant futuro
  -> GET /api/experiment-template
  -> POST /api/models        (catalogar/selecionar, quando necessário)
  -> POST /api/prepare
       -> api.create_app.prepare
       -> ExperimentRunner.prepare
       -> validate_spec
       -> para B3/E: read_verified_records + comparação fingerprint + pareamento
       -> seed_peer_contributions + check_contribution para diagnóstico
       -> PreparedExperiment(snapshot_json, requests_json, fingerprint)
  -> aprovação/controle de gasto
  -> POST /api/experiments
       -> runner.prepare (valida novamente)
       -> runner.run -> _run -> RAW/eventos/manifesto/fechamento/sha256
```

`POST /api/prepare` **não executa chamadas LLM**. `POST /api/experiments` devolve `202 Accepted`, não o resultado fechado.

### 3.2 Fluxo real de critério estrutural e recuperação

```text
GET /api/experiments/{id}/observe
  -> observer.snapshot
  -> check_records(records, requests)
  -> check_contribution(content, autor, working_context)
  -> Contribution.parse + validate_and_convert
  -> code, usable, fully_valid, declared/accepted, rejected[]
       -> incidente do Assistant (NOVO, fora do RAW)
       -> análise da política e permissão
       -> POST /api/adjustments/{id}/preview
       -> POST /api/adjustments/{id} (quando autorizado)
       -> AdjustmentStore.prepare -> adjustment_diagnostic
       -> AdjustmentStore.run -> tentativa própria + check + seal
       -> nova avaliação da tentativa, sem reescrever a original
```

**Nuance obrigatória:** `usable` não é `fully_valid`. Uma contribuição com unidades aceitas e uma relação recusada pode ter `code=partial` e continuar utilizável para semeadura das unidades aceitas, como registram `test_part_tolerant_parsing.py` e `test_contribution_check.py`. Um novo critério de **conformidade integral** pode classificar o mesmo caso como insuficiente **sem alterar** a política atual de semeadura nem dizer que o dado foi validado por inteiro.

Códigos **já implementados** no diagnóstico: `usable`, `partial`, `empty_response`, `missing_block`, `unclosed_block`, `invalid_json`, `invalid_schema`, `empty_knowledge`, `rejected_knowledge`, `execution_failed`. Códigos como `criterion_missing` seriam **categoria de incidente nova**, nunca substituição desses diagnósticos.

### 3.3 Limites de integridade, execução e observação

- `runner.py` cria diretório exclusivo do experimento, escreve `spec.json`, `requests.json`, `seed_audits.json`, `events.jsonl`, observações RAW, resultados e `integrity.json`.
- `storage.py:read_verified_records` exige status `complete` e integridade válida para uso como origem.
- `observer.snapshot` sinaliza `provisional` se ainda não há selo; se houver selo inválido, **não entrega** as respostas como válidas.
- `api.py:create_app` mantém `jobs` e `failures` **em memória**. O shutdown cancela jobs em andamento; o novo Assistant precisa de mecanismo próprio de trabalho durável/reconciliação se prometer retomada robusta.
- O middleware em `api.py` impõe guardas de origem apenas a grupos sensíveis específicos; **não fornece autenticação remota geral**. Não expor `127.0.0.1:8766` diretamente.
- O fluxo de ajuste da UX é manual e a coleta original continua elegível ou bloqueada conforme o próprio validador, não conforme o sucesso posterior de um ajuste.
- Não há hoje endpoint de comparação calculada nem exportador externo versionado; `Compare.tsx` apenas compara os snapshots no cliente.

## 4. Encaixe proposto por função — sem duplicação

| Função nova | Inspirar no Huginn | Chamar a autoridade do Lab | Construir |
| --- | --- | --- | --- |
| Descoberta e execução de ações | `Operation/Catalogue/CatalogueTools` | `ExperimentRunner`, `ModelCatalog`, stores | módulo `lab_operations` e guardas |
| Conversa com o Assistant | `Assistant`, repo, contracts, routes | nenhum modelo experimental como operador implícito | Assistant próprio, configurações e histórico |
| Diagnóstico por critério | `Incidents`, `IncidentWatch`, `Duty` | `check_contribution`, `validate_spec`, `verify_experiment` | adaptadores, registro versionado de critérios e eventos derivados |
| Reparar pré-execução | catálogo + diário | `validate_spec`, `runner.prepare` | correção de rascunhos, comparação de mudanças e aprovação |
| Ajustar pós-execução | plantão/tentativas limitadas | `AdjustmentStore.prepare/run` | autorização, política, limite e ligação ao incidente |
| Dependências e rotinas | `WorkScheduler`, `Routines` | `runner.run` como job indivisível de coleta | estado durável das tarefas do Assistant, idempotência |
| Exportação/integração | eventos, contratos tipados | `snapshot`, `verify_experiment`, outcomes | projeção versionada, proteção de dados e conector seguro |
| Comparar | trilha/operador | `observer.snapshot`, `outcome_validation` | serviço de leitura/comparação estruturada, sem inferência causal automática |

## 5. Regras de permissão a acrescentar

1. **Leitura:** modelos, configuração pública, estado, diagnósticos e resultados autorizados.
2. **Rascunho:** sugerir e validar `Spec` sem custo LLM experimental.
3. **Execução onerosa:** iniciar coleta apenas com autorização expressa ou política de orçamento delegada e registrada.
4. **Recuperação:** permitir automaticamente apenas correções de rascunhos dentro das invariantes. Ajustar resposta custa API, exige política explícita e **não sana o RAW**.
5. **Segredos/administração:** editar credencial, abrir endpoints remotos, excluir irreversivelmente ou ampliar permissão fica reservado ao proprietário.
6. **Exportar para outra plataforma:** identidade autenticada, consentimento, escopo de datasets, redaction e comprovação de entrega.

A guarda deve ser programática, acima do nível de prompt. O `Catalogue.allowed` atual do Huginn não separa essas seis classes.

## 6. Testes concretos a usar como referência

| Repositório | Teste | Regra preservada |
| --- | --- | --- |
| Lab | `tests/test_lab.py` | pareamento B1/B3/E, fingerprint/corpus, concorrência, cancelamento, RAW |
| Lab | `tests/test_part_tolerant_parsing.py` | recusa por parte, sem auto-reparo, relação rejeitada e semeadura parcial |
| Lab | `tests/test_contribution_check.py` | diagnósticos não inventam conteúdo, `partial`, campo/relação recusado |
| Lab | `tests/test_adjustments.py` | ajuste preserva origem, apenas um participante, tentativa separada e diagnóstico |
| Lab | `tests/test_observer.py` | dado adulterado bloqueado, provisório e falha de preflight |
| Lab | `tests/test_settings.py` | credenciais, capabilities declaradas e redaction |
| Huginn | `core/tests/test_assistant.py` | catálogo, ações autorizadas, trilha, steps, limites e background |
| Huginn | `core/tests/test_incidents.py` | incidente, plantão, limites, escalonamento e retomada |
| Huginn | `core/tests/test_recovery.py` | classificação, retry/idempotência, leases e modelo alternativo — **somente para operador** |
| Huginn | `core/tests/test_routines.py` | agenda, fuso, ocorrências e idempotência |

**Testes futuros necessários:** cenário de `missing_block` → incidente → proposta → aprovação → ajuste → novo `check` preservando RAW; `partial` com relação recusada; B3/E com origem incompatível; consulta de resultados após restart; corrida entre duas ações idempotentes; tentativa excedida/escalonamento; erro e redaction no conector; proibição de troca automática de modelo participante; proibição de exportar sem autorização.

## 7. Ordem de implementação recomendada

1. **Primeiro:** definir `CriterionEvaluation` versionado e mapear diagnósticos existentes, sem alterar `check_contribution` nem `runner`.
2. **Segundo:** catálogo de operações do Lab, permissões/diário e camada de serviços compartilhada com a UI; começar por consultas e `prepare`.
3. **Terceiro:** incidentes e ações autorizadas (`plan`, `preview`, `request`), com limites de tentativas e auditoria persistente.
4. **Quarto:** Assistant nativo e UX; garantir que sua própria LLM use recursos e credenciais separados dos participantes.
5. **Quinto:** tarefas duráveis, scheduler de dependências e reconciliação da coleta, sem duplicar execução.
6. **Sexto:** projeção/exports versionados e conector seguro com a plataforma do Assistant pessoal.
7. **Sétimo:** recorrência/autonomia ampliada, apenas com proteção de custos, integridade, permissões e testes de fechamento.

## 8. Veredito

O maior ganho imediato não é copiar o scheduler inteiro do Huginn: é **combinar o catálogo de operações e o tratamento de incidentes do Huginn com `check_contribution`, `runner.prepare`, `AdjustmentStore` e a integridade existente no Lab**.

O maior risco é automatizar uma “correção” que transforme falha de critério em sucesso aparente ou altere a amostra. Esse comportamento é proibido pelo desenho proposto. O motor de conformidade deve produzir **evidência, diagnóstico, decisão, ação rastreável e reavaliação**, não apagar falhas.

Nenhuma implementação, migração de banco, endpoint ou mudança de UX foi executada nesta etapa.
