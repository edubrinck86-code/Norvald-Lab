# Lab Assistant — terceira fatia: conversa, prévia e autorização de ajustes

**Estado:** implementação em PR rascunho, testes CI. **Não é ainda um agente autônomo do laboratório**.  
**Data:** 2026-10-15  
**Branch:** `feature/lab-assistant-criteria-operations`  
**Referências:** [proposta](LAB_ASSISTANT_HUGINN_PROPOSTA.md), [mapeamento Huginn↔Lab](LAB_ASSISTANT_HUGINN_MAPEAMENTO_CODIGO.md), [motor de critérios](LAB_ASSISTANT_PRIMEIRA_FATIA.md) e [incidentes](LAB_ASSISTANT_INCIDENTES_CRITERIOS.md).

## Entrega

A aplicação React ganha uma entrada **Lab Assistant** na navegação, com leitura de incidentes, histórico, estado de critérios e diálogo contextualizado. O backend agora inclui um **operador LLM próprio**, configurável via provider/modelo, que utiliza os transports já presentes em `norvald_execution`. Ele **não é participante do estudo** e não é automaticamente incluído em um `Spec`.

O Assistant só conversa sobre o incidente selecionado. Recebe metadados, diagnóstico e plano estruturado, sem uma cópia automática do RAW integral. Uma resposta do operador LLM é uma **interpretação auxiliar**, jamais nova aprovação do validador. Não há tool calling autorizado ao modelo nessa etapa.

Novos arquivos:
- `norvald_lab/lab_assistant.py`: configuração do modelo operador, laço de **uma chamada explícita por mensagem** sem ferramentas, histórico SQLite por incidente, autorizações de prévia com token aleatório e validade de **10 minutos**, uso único.
- `frontend/src/components/LabAssistant.tsx`: UX de incidentes, chat, orientação de ajuste, prévia, confirmação explícita, execução e consulta do histórico.
- `frontend/src/styles/assistant.css`: interface responsiva.
- `tests/test_lab_assistant.py`: fluxo integrado de modelo operador simulado, token de autorização, ajuste isolado e proteção de origem.

Alterados: `norvald_lab/api.py`, `norvald_lab/criterion_incidents.py` (evento de auditoria), `frontend/src/App.tsx`, `frontend/src/main.tsx` e workflow de CI.

## Fluxo de uso

1. Abrir **Lab Assistant** pela navegação.
2. Selecionar um incidente registrado. Se necessário, selecionar antes o experimento na Bancada e clicar para reconciliar os critérios.
3. Configurar provider e ID de modelo **operador** (usando conexão existente) e salvar. O uso de modelo requer chamadas reais habilitadas em Configurações.
4. Enviar uma pergunta sobre o incidente; o texto de resposta é registrado ao lado do provedor, modelo e tokens reportados.
5. Se o plano indicar `preview_adjustment` e a fonte for uma coleta real, fechada e íntegra, revisar/editar orientação e limite de saída.
6. Clicar **Examinar pedido antes de autorizar**. O Lab monta o request com o `AdjustmentStore.prepare(..., persist=False)`. Não chama modelo nem grava novo ajuste.
7. Ler as instruções e a mensagem mostradas, marcar confirmação explícita e clicar **Autorizar e executar ajuste**.
8. O backend resgata um ticket vinculado a incidente, experimento, payload revisado e hash do selo da origem, **expirado após 10 min e consumido apenas uma vez**, confere o plano novamente, chama o serviço existente de ajustes e registra `assistant.adjustment_requested` no histórico de auditoria.
9. Acompanhar o ajuste, reabrir incidente e comparar os critérios **do ajuste** com os do **RAW original**. A original permanece classificada pelo validador original.

**Limite de segurança:** confirmação via UI/API local é autorização do operador local, não autenticação de outra plataforma. A API continua restrita à instalação local e não deve ser exposta diretamente na internet.

## Endpoints adicionados

| Método | Endpoint | Comportamento |
| --- | --- | --- |
| GET | `/api/assistant/settings` | Lê somente kind, modelo e limite de saída, não credenciais |
| PUT | `/api/assistant/settings` | Salva operador com `kind`, `model`, `max_output_tokens` |
| GET | `/api/assistant/incidents/{id}/conversation` | Histórico persistido por incidente |
| POST | `/api/assistant/incidents/{id}/message` | `{"text":"..."}`: chamada explícita ao operador, sem ferramentas |
| POST | `/api/assistant/incidents/{id}/adjustment/preview` | `{"instruction":"...", "max_tokens":null}`: prévia gratuita de LLM |
| POST | `/api/assistant/incidents/{id}/adjustment/authorize` | `{"approved":true,"approval_token":"..." }`: consume aprovação e inicia ajuste permitido, devolve 202 |

Todos estão sujeitos à proteção local de origem e respostas não armazenáveis em cache; `/api/assistant/...` não é uma API remota autenticada.

## Persistência e custos

- Configuração do operador em `<root>/private/settings.json` sob `lab_assistant`; API keys continuam no armazenamento já existente do Lab, fora dos chats.
- Conversa e tickets em `<root>/observer/lab_assistant.sqlite3`, fora do selo experimental; em sistemas POSIX, arquivo criado com modo `0600`.
- Conversar consome tokens do provider escolhido. Cada mensagem faz no máximo **uma** chamada de modelo, com timeout 90 s, contexto/histórico delimitados e máximo de tokens de saída configurável (256–8000). Sem chamadas automáticas em background pelo modelo operador.
- Prévia não chama a LLM nem constitui uma nova observação; autorização solicita um **ajuste** do participante original e terá custo separado.
- Se o ajuste falhar, ele continua registrado separadamente; a autorização não transforma automaticamente o incidente em resolvido. Falhas de chamadas de conversa não recebem respostas artificiais de sucesso.

## Proteções e limites

- Só aparecem na interface ações de ajuste para `recovery.allowed=true` com modo `live`, integridade e diagnóstico estrutural adequado.
- A rota `authorize` revalida plano, vínculo ao incidente, expiração, correspondência de `observation_id` e hash do selo original; o ticket não admite reutilização.
- `assistant.adjustment_requested` é evento append-only, não altera `status` científico de critério.
- `Assistant` não pode executar ferramentas genéricas, mudar provedores/modelos dos participantes, editar RAW ou rodar experimentos nesta fatia.
- `acknowledge` e `escalate` continuam decisões do usuário, não equivalentes a resolução científica.
- A conversa não exporta dados para o Assistant pessoal de outra plataforma; conector/autenticação remota permanecem pendentes.
- O token de aprovação é enviado apenas para a interface local de prévia; deve ser tratado como credencial temporária sensível e nunca publicado em logs ou no GitHub.
- A qualidade da explicação da LLM depende do modelo configurado; as únicas avaliações normativas vêm de `criteria.py` e dos validadores AROF.

## Verificação

```bash
python -m pytest -q tests/test_lab_criteria.py tests/test_criterion_incidents.py tests/test_lab_assistant.py
python -m pytest -q
cd frontend
npm ci
npm test && npm run build
```

No workflow do PR, o backend roda Python 3.10 e 3.12; a UI é compilada/testada. Consultar a CI antes de declarar aprovação.

## Próxima fase

Com a conversa e os ajustes autorizados já disponíveis, implementar catálogo de ferramentas **somente para operações autorizadas**, orçamento por agente e conector autenticado entre o Lab Assistant e o Assistant pessoal. Esse passo exige uma política de permissões separando consulta, gasto, ajuste, configuração, exclusão e exportação.
