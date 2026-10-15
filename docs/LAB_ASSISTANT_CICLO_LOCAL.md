# Lab Assistant — ciclo local completo (pré-testes do proprietário)

**Estado:** implementação na PR de desenvolvimento; **não integrada à main**.  
**Escopo deliberadamente excluído:** conector externo com o Assistant pessoal, autenticação remota e qualquer comunicação entre plataformas. Isso só será considerado **depois que o proprietário testar o Lab**.  
**Política vigente:** [LAB_ASSISTANT_POLITICA_OPERACIONAL.md](LAB_ASSISTANT_POLITICA_OPERACIONAL.md).

## 1. Funcionalidades implementadas

### Planejamento conversacional
- A aba **Lab Assistant** tem chat geral, separado das conversas de incidentes.
- O modelo operador pode consultar `lab.spec.template`, propor um `Spec` via linguagem natural (`POST /api/assistant/spec/draft`) e receber diagnósticos determinísticos; inválidos ou incompletos ficam como rascunhos, sem execução.
- O editor de `Spec` e `/api/assistant/plans/experiment` exibem objetivo, condição, ferramentas, participantes, modelos, repetições, requests preparados e fingerprint antes da coleta.
- Não existe inferência automática de capacidades/custos de modelos. Nunca substituir participante silenciosamente.

### Operações em dois estágios
- O modelo dispõe de `list_operations`, `describe_operation` e `call_operation` tipadas.
- Operações de **consulta**: experimentos, status, integridade/critérios, incidentes, comparação e relatório. `lab.spec.derive` devolve uma proposta derivada de uma base íntegra.
- Operações de **planejamento**, sem chamada LLM experimental: `lab.experiment.plan`, `lab.adjustment.plan`.
- Operação `lab.plan.execute` só é permitida para um plano **já apresentado** pela API da interface (`GET /api/assistant/plans` ou `/plans/{id}`). O plano é congelado, revalidado e consumido uma única vez. Antes de ser apresentado, o modelo recebe uma recusa. A UI oferece a mesma execução por botão.
- Não há ferramentas que deletam RAW, removem arquivos arbitrários ou acessam shell.

### Recuperação orientada ao framework
- Motor `criteria.py` mantém decisões originais de `check_contribution`: `usable` e `fully_valid` são distintos, assim como `pending`, `not_met` e `not_evaluable`.
- Ledger durável de incidentes por critério e observação sob `observer/`, com auditoria e ações de reconhecer/escalar.
- O observador prepara planos de ajustes isolados **uma única vez por observação**. O ajuste nunca corrige retroativamente o RAW nem vira repetição experimental independente.
- Recuperação automática é **configurável e inicia desativada**. Quando habilitada, um plano é persistido em um ciclo e pode ser executado em um ciclo posterior; nenhuma nova chamada é disparada no mesmo ciclo em que o plano foi criado.
- Parada emergencial, manual ou por repetição anômala, bloqueia novas ações; não cancela no meio a escrita de uma coleta existente.

### Acompanhamento, rotinas e retomada
- A API executa um observador local periódico (ciclo a cada ~10 segundos), com cursor por experimento/selo e reconciliação após reinício.
- A programação recorrente só aceita um `Spec` já preparado e apresentado: intervalo positivo em segundos, data inicial com fuso. Cada ocorrência recebe identificador próprio e um novo plano.
- Intervalos perdidos enquanto o Lab estava desligado não são reproduzidos em massa na reinicialização; o próximo horário segue a recorrência.
- Ações de efeito incerto marcadas `interrupted` após reinício **não são reexecutadas cegamente**; é preciso inspecionar a origem e o plano para evitar duplicação de chamadas pagas.
- Dados de acompanhamento, histórico, agendas, conversa e permissões residem separadamente do RAW.

### Comparação e relatórios internos
- `GET /api/assistant/compare?left=...&right=...` exige duas coletas **completas e íntegras**, pareia participante/repetição e calcula apenas estatísticas estruturais descritivas com ressalvas.
- `GET /api/assistant/reports/{experiment_id}` monta pacote de evidências versionado com desenho, checks, incidentes, observações por critério e hash do selo, sem substituir nem alterar respostas originais.
- Não há alegações de causalidade automática, nem exportação/transmissão externa.

### Permissões exclusivamente destrutivas
- Planejamento, consulta, início de coleta e ajustes isolados não exigem aprovação por tarefa.
- Para o Assistant, nenhuma operação de destruição é oferecida ao modelo.
- Uma ação local classificada como destrutiva foi implementada: **excluir um experimento da lista** (reversível, preservando arquivos RAW). Ela requer solicitação com validade de 10 minutos e confirmação explícita do proprietário. O registro de confirmação é de uso único.
- Remoção irreversível de RAW, edição arbitrária de credenciais e concessão de acesso remoto não foram disponibilizadas como capacidades do Assistant.

## 2. Regras de operação

- **Sem orçamento do Assistant:** nada de cota artificial de chamadas, gasto, tokens ou número de tarefas. Os limites impostos por providers e as invariantes próprias dos experimentos (`Spec.budget`, timeout, concurrency, pareamento) permanecem.
- **Plano antes de executar:** pode ser criado pelo modelo ou no editor, mas nunca iniciado pelo mesmo estágio de preparação. A execução pelo modelo exige um plano anteriormente apresentado.
- **Permissão especial somente destrutiva:** outras ações não exigem autorização individual; a separação entre planejamento e execução existe para transparência, não como cota ou veto.
- **RAW e protocolos científicos são soberanos:** ajustes e análises não alteram evidências originais; nenhum modelo operador define conformidade por opinião.
- **Somente local:** proteção de origem é para aplicação local, não autenticação remota. Nunca expor a porta interna do Lab publicamente.

## 3. Endpoints principais

| Grupo | Endpoints |
| --- | --- |
| Conversa geral | `GET /api/assistant/conversation`, `POST /api/assistant/chat` |
| Modelo operador | `GET/PUT /api/assistant/settings` |
| Planejamento natural | `POST /api/assistant/spec/draft` |
| Planos | `POST /api/assistant/plans/experiment`, `GET /api/assistant/plans`, `GET /api/assistant/plans/{id}`, `POST /api/assistant/plans/{id}/execute` |
| Incidentes | `GET /api/criteria/incidents`, `GET /api/criteria/incidents/{id}`, `POST /api/experiments/{id}/criteria/reconcile` |
| Recuperação | `POST /api/assistant/incidents/{id}/adjustment/plan`, `GET /api/assistant/automation/recovery`, `PUT /api/assistant/automation/recovery/settings` |
| Rotinas | `GET/POST /api/assistant/routines`, `GET /api/assistant/routines/{id}/history`, `POST /api/assistant/routines/{id}/state` |
| Supervisor | `POST /api/assistant/automation/monitor`, `POST /api/assistant/automation/tick`, `GET /api/assistant/emergency`, `POST /api/assistant/emergency/stop`, `POST /api/assistant/emergency/resume` |
| Análise | `GET /api/assistant/compare`, `GET /api/assistant/reports/{experiment_id}` |
| Ação destrutiva | `POST /api/assistant/destructive/exclusion/plan`, `GET /api/assistant/destructive/requests`, `POST /api/assistant/destructive/requests/{id}/confirm` |

## 4. Testes e roteiro de validação pessoal

Antes de considerar pronto para sua bancada, confirmar os checks da PR e executar os testes de Python 3.10/3.12, frontend e regressões:

```bash
python -m pytest -q
cd frontend && npm test && npm run build
```

Roteiro de avaliação manual:
1. Configurar provider/modelo operador e habilitar o modo real no Lab, usando somente uma chave local.
2. Conversar com o Assistant geral sobre um experimento. Pedir `Spec` e revisar os participantes, a condição e o corpus propostos.
3. Conferir o plano, iniciar estudo e observar seu fechamento. Testar um modelo real e critérios estruturais.
4. Propor e executar um ajuste isolado; verificar integridade da coleta original e registro de tentativa distinta.
5. Testar a fila automática inicialmente desligada; ligá-la explicitamente, verificar planos antes de cada execução e desativar novamente.
6. Preparar uma rotina, conferir agenda/histórico e experimentar pausa e retomada.
7. Gerar comparação e relatório entre duas coletas completas; adulterar uma cópia de teste e verificar o bloqueio por hash.
8. Acionar parada emergencial e verificar bloqueio de novas operações; retomar.
9. Exercitar a solicitação destrutiva de exclusão da lista, cancelar/expirar/repetir e conferir que RAW continua íntegro.
10. Reiniciar o Lab durante um trabalho de teste e verificar que planos incertos não são reproduzidos automaticamente.

**Testes automatizados com provedores simulados não substituem este roteiro manual em máquina real.**

## 5. Fora do escopo — aguardando decisão e testes do proprietário

- Integração ao Assistant pessoal externo, transporte autenticado, conector, exportação de dados entre plataformas e execução remota.
- Implantação na `main` sem aprovação/revisão do proprietário.
- Alteração de invariantes científicas, reescrita de RAW ou troca silenciosa de modelos participantes.
- Garantias de alta disponibilidade em múltiplos servidores: esta arquitetura é de um único backend local.

**Não habilitar integrações externas antes da validação pessoal completa.**
