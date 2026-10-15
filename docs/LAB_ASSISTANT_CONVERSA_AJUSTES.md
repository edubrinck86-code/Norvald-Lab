# Lab Assistant — conversa sobre incidentes e ajustes planejados

**Estado:** PR rascunho; nenhuma alteração integrada na `main`.  
**Política atualizada:** [LAB_ASSISTANT_POLITICA_OPERACIONAL.md](LAB_ASSISTANT_POLITICA_OPERACIONAL.md). Essa política substitui a antiga proposta de token de autorização por ajuste.

## Capacidades desta etapa

- Nova entrada **Lab Assistant** na navegação React. Lista incidentes de critérios do AROF, evidências, histórico de auditoria e reavaliações.
- Modelo **operador** independente do grupo de participantes: configurar `kind` e `model` a partir das conexões já existentes; não adicioná-lo ao `Spec` experimental.
- Chat por incidente, gravado sob `observer/lab_assistant.sqlite3`. Cada resposta é interpretação contextual, não decisão do validador científico; sem chamada de ferramentas por parte da LLM.
- Ajuste **não destrutivo** com apresentação do planejamento antes de iniciar. A interface solicita uma prévia real ao `AdjustmentStore.prepare(..., persist=False)` e mostra as instruções e a mensagem preparadas. O Lab salva um `plan_id`; a execução opera apenas sobre esse plano, sem aprovação específica adicional.
- Ajuste executado pelo serviço já existente, com auditoria `assistant.adjustment_requested` e nova verificação da tentativa. A resposta original e o RAW experimental não são substituídos.
- Parada emergencial manual e por detecção de ciclos repetidos; retomada explícita.

## API atual

| Método | Rota | Função |
| --- | --- | --- |
| GET/PUT | `/api/assistant/settings` | Seleção de modelo operador |
| GET | `/api/assistant/incidents/{id}/conversation` | Histórico de chat |
| POST | `/api/assistant/incidents/{id}/message` | Uma consulta ao operador, sem ferramentas |
| POST | `/api/assistant/incidents/{id}/adjustment/plan` | Preparar pedido de ajuste com `plan_id` e prévia |
| POST | `/api/assistant/plans/experiment` | Preparar `Spec` e apresentar plano de experimento |
| GET | `/api/assistant/plans/{plan_id}` | Consultar estado e conteúdo do plano |
| POST | `/api/assistant/plans/{plan_id}/execute` | Iniciar execução do plano, com deduplicação |
| GET | `/api/assistant/emergency` | Consultar parada emergencial |
| POST | `/api/assistant/emergency/stop` / `resume` | Interromper/retomar novas operações |

Nenhum desses endpoints oferece exclusão de experimento, edição de chaves ou mutação de RAW. A proteção atual da API é local e não constitui autenticação remota; não expor a porta do Lab diretamente à internet.

## Política de recursos e permissões

O Assistant **não possui teto próprio** de chamadas, gasto diário, tarefas ou saída de resposta. A execução de ajustes e experimentos demanda os limites legítimos do contrato experimental e do provider. A leitura, o preparo e os ajustes separados não exigem confirmação de permissão. Ações destrutivas precisam de um contrato de permissão próprio antes de ser disponibilizadas ao Assistant.

O mecanismo emergencial **não é um orçamento**: suspende apenas novas ações quando explicitamente acionado ou quando observa repetição cíclica de operação/payload/evidência. Uma ação em andamento não é cancelada à força para não comprometer integridade do experimento.

## Testes e lacunas

- `tests/test_lab_assistant.py`: conversa, planejamento e execução de ajuste, idempotência, origem e RAW.
- `tests/test_assistant_plans.py`: parada persistente, detecção de looping, muitas operações diferentes e planejamento anterior à execução.
- `frontend/src/components/LabAssistant.tsx`: interface de incidentes e prévias de ajuste; compilação e testes frontend da CI.
- O painel específico de planejamento experimental pelo Assistant, uso geral do catálogo de ferramentas pela LLM e ligação ao Assistant pessoal **ainda não estão disponíveis na interface**.

**O plano em backend está implementado; isso não deve ser confundido com autonomia plena do Assistant.**
