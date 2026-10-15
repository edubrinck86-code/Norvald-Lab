# Lab Assistant — política operacional e revisão da migração

**Estado:** implementação em PR rascunho, sem merge na main. Atualizado em 2026-10-15.

## Decisão vigente

- **Sem orçamento do Assistant:** não limitar chamadas, quantidade de tarefas, gasto diário, histórico ou tamanho das respostas por uma cota própria. Limites técnicos que o provider realmente impõe e invariantes do Spec/Runner não são substituídos por esta decisão.
- **Planejamento antes da execução:** produzir um plano persistente, com IDs, operação, configuração/diagnóstico e evidências de origem. Mostrá-lo ao operador antes de solicitar a execução. A execução recebe apenas o ID imutável, sem mutação do conteúdo planejado.
- **Sem permissão por ação não destrutiva:** preparar specs, iniciar novas coletas, ler evidências e gerar um ajuste separado são ações rotineiras. Não exigem token/checkbox de aprovação a cada chamada.
- **Permissões para ações destrutivas:** eliminar registros, alterar irreversivelmente dados ou credenciais e ampliar acessos continuarão dependentes de autorização específica. O catálogo de operações deste estágio não oferece essas ações ao modelo.
- **Controle emergencial apenas contra looping:** detector por repetição da mesma operação/payload/evidência, parada manual persistente, bloqueio de novas ações e retomada explícita. Muitos trabalhos **diferentes** não ativam um teto de quantidade.

## Código da política

- `norvald_lab/assistant_plans.py`: planos SQLite em `observer/lab_assistant_plans.sqlite3`, `create/get/claim/finish/fail`, `stop/resume/control`. Chaves por plan_id e operação de claim idempotente. Um ciclo repetido (quatro ocorrências de assinatura igual ou sequência repetida de 2–3 assinaturas) suspende novos planos; é um alarme por padrão repetido, **não uma cota de uso**.
- `norvald_lab/assistant_plan_routes.py`: `POST /api/assistant/incidents/{incident_id}/adjustment/plan`, `POST /api/assistant/plans/experiment`, `GET /api/assistant/plans/{id}`, `POST /api/assistant/plans/{id}/execute`, `GET/POST /api/assistant/emergency...`. Nenhuma ação destrutiva é permitida nesses endpoints.
- `norvald_lab/lab_assistant.py`: configuração do operador contém `kind` e `model` (sem teto próprio de saída ou de chamadas). Uma pergunta exige envio explícito, usa provider existente e não tem ferramentas mutantes.
- `frontend/src/components/LabAssistant.tsx`: chat contextual, consulta de incidentes, prévia real do pedido de ajuste, execução do plano já apresentado e controle emergencial visível.
- `norvald_lab/criterion_recovery.py`: nenhum pedido adicional de permissão por ajuste isolado. Continua bloqueando correções do RAW e propostas sem integridade/condição experimental válida.

### Semântica de execução

Preparar um plano não chama LLM nem altera experimentos. Um plano enviado à execução é verificado novamente contra a origem e consumido apenas uma vez. Se a origem mudou, a execução exige um **novo plano**, não nova autorização.

A parada emergencial bloqueia novos `claim` de planos e não cancela automaticamente execuções que já estavam em andamento; isso evita interromper a escrita do experimento no meio e preservar integridade. A UI informa o estado e permite retomar. O detector de ciclo roda na execução de planos do Assistant; não altera o Runner existente.

## Validação

Executar:
```bash
python -m pytest -q tests/test_lab_criteria.py tests/test_criterion_incidents.py tests/test_lab_assistant.py tests/test_assistant_plans.py
python -m pytest -q
cd frontend && npm test && npm run build
```

Os testes específicos cobrem plano antes da coleta, não escrita durante planejamento, bloqueio por parada, retomada, idempotência, repetição automática, uso de muitas tarefas distintas, ajuste posterior e preservação de RAW.

**Pendências fora desta revisão:** validação manual em navegador com provider real, catálogo ampliado de ferramentas da LLM, autenticação remota e integração ao Assistant pessoal. O endpoint de plano para experimento está disponível no backend, mas a interface dedicada de planejamento experimental pelo Assistant ainda não foi integrada. A interface tradicional `Prepare` permanece disponível.

## Nota de compatibilidade

As antigas rotas `/api/assistant/incidents/{id}/adjustment/preview` e `.../authorize` e o token de aprovação expresso em documentação anterior foram retirados desta branch; a integração deve usar `.../adjustment/plan` seguido de `/api/assistant/plans/{plan_id}/execute`. Contratos de ajustes tradicionais `/api/adjustments` continuam independentes e preservados.
