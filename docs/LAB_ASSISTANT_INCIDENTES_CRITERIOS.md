# Lab Assistant — segunda fatia: incidentes duráveis por critério e recuperação segura

**Estado:** implementado na branch de desenvolvimento; integração na `main` depende de revisão/CI.  
**Branch:** `feature/lab-assistant-criteria-operations`.  
**Origem do desenho:** [proposta](LAB_ASSISTANT_HUGINN_PROPOSTA.md), [mapeamento no código](LAB_ASSISTANT_HUGINN_MAPEAMENTO_CODIGO.md), [primeira fatia](LAB_ASSISTANT_PRIMEIRA_FATIA.md).

## O que foi construído

1. `norvald_lab/criterion_incidents.py`: registro SQLite de incidentes de critérios, com ID determinístico, estados `open` / `acknowledged` / `escalated`, eventos append-only, atualização apenas quando a evidência muda e persistência entre reinícios.
2. `norvald_lab/criterion_recovery.py`: planos explicativos sem execução; consulta diagnósticos do validador e inspeciona ajustes **separadamente selados e vinculados** à origem.
3. `norvald_lab/api.py`: endpoints locais de leitura, reconciliação e decisões do proprietário. Para experimentos iniciados por `POST /api/experiments`, a detecção ocorre também após o fechamento do Runner; se o registro auxiliar falhar, a coleta já encerrada permanece intacta e a exceção é registrada no log do servidor.
4. `norvald_lab/lab_operations.py`: novas **consultas internas** `lab.incidents.list` e `lab.incident.get` no catálogo inspirado no Huginn. **Nenhuma operação de correção ou mutação é acessível à LLM nesta fatia.**
5. `tests/test_criterion_incidents.py`: detecção automática, persistência, reconciliação repetida sem duplicar, decisões auditáveis, proteção de origem, integridade e revalidação em ajustes isolados.

Apenas os comportamentos comprovados pelo código e pelos testes executados devem ser apresentados como concluídos.

## Endpoints

| Método | Caminho | Função |
| --- | --- | --- |
| `GET` | `/api/criteria/incidents?experiment_id=...&status=...&limit=100` | Lista ocorrências salvas |
| `GET` | `/api/criteria/incidents/{incident_id}` | Detalhes, histórico, plano e revalidações ligadas |
| `POST` | `/api/experiments/{experiment_id}/criteria/reconcile` | Lê a avaliação determinística e registra somente `not_met` |
| `POST` | `/api/criteria/incidents/{incident_id}/acknowledge` | Marca ciência da ocorrência; exige `{"note":"..."}` |
| `POST` | `/api/criteria/incidents/{incident_id}/escalate` | Escala a ocorrência; exige `{"note":"..."}` |

A atualização é **idempotente** em relação à mesma evidência. Repetir `reconcile` não acrescenta incidentes ou eventos iguais. Critérios `pending` e `not_evaluable` **não são falhas confirmadas**. Se ainda não existe fechamento, a operação retorna `status=pending`, sem afirmar conformidade.

Os registros são derivados das decisões atuais de `evaluate_snapshot` e **não mudam** `check_contribution`, o parser, os parâmetros, o `Spec`, o corpus, o resultado de exposição ou a amostra.

A reconciliação automática abrange as coletas iniciadas pelo endpoint normal da API. Coletas anteriores, CLI ou outros caminhos podem ser registradas pelo `POST .../reconcile`. A suíte interna `/api/demo` não é coberta pelo gatilho automático desta fatia.

## Estado persistente e proveniência

Dados em `<NORVALD_LAB_DATA_DIR>/observer/criterion_incidents.sqlite3`, **fora** de `experiments/<id>`. O arquivo SQLite recebe permissão `0600` em plataformas POSIX; o diretório é criado com modo solicitado `0700`. Nenhum checksum dos experimentos é atualizado.

Cada incidente identifica `experiment_id`, `criterion_id`, `criterion_version`, `observation_id`, `participant_id` e `run_id`. Preserva `validator_code`, `message`, `evidence`, datas, estado e decisões; ações geram eventos append-only.

`acknowledged` significa apenas **ciente**. `escalated` significa **requer decisão**. Nenhum deles significa que a observação foi corrigida, e não existe opção para declarar um critério original resolvido.

## Diagnóstico e revalidação

Uma observação com `missing_block`, `unclosed_block`, `invalid_json`, `invalid_schema`, `partial` ou outro erro estrutural pode receber o plano `preview_adjustment`, **somente** se a coleta original estiver íntegra, fechada, em modo `live` e com `observation_id` válido. Esse plano é um **rascunho de orientação**, não um envio; mantém `automatic=false` e `requires_approval=true`.

A ação sugerida utiliza o fluxo **já existente** `/api/adjustments/{experiment_id}/preview`. Após aprovação humana, o usuário poderá solicitar um ajuste pelo fluxo existente. A nova chamada não é executada por este motor.

Planos alternativos: `new_collection_review`, `investigate_integrity` ou `review_manually`, quando não é possível corrigir um formato sem alterar a identidade experimental.

A leitura de revalidação mostra por `adjustment_id` o estado da tentativa, vínculo ao hash do selo original, integridade de seu próprio selo, código de validação e `criterion_status` (`met_in_adjustment`, `not_met_in_adjustment`, `not_evaluable`). **Um ajuste que atende a um critério não altera o incidente da observação original**. Um ajuste sem selo ou adulterado não pode ser considerado conforme.

## Controles e limites

- Sem motor de conversa LLM nem novo provider operador nesta fatia.
- Sem aumento de gastos: as operações novas consultam/projetam/registram dados locais e não invocam LLMs.
- Sem troca de participantes/modelos para corrigir falhas, sem reenvio de coleta, sem reparo de RAW.
- A API recebe proteção de origem local coerente com as outras configurações do Lab; **isso não equivale a autenticação remota**. Não expor a porta local na rede.
- As decisões `acknowledge/escalate` são operações da interface local, **não** são oferecidas ao catálogo LLM enquanto faltarem identidade, escopo e aprovação.
- Incidente continua registrado mesmo que uma leitura posterior encontre evidência diferente ou uma tentativa de ajuste válida; alterações da evidência são auditadas, nunca removidas.
- Categorias de conformidade cobrem apenas a projeção determinística implementada; não certificam validade científica global nem inferem efeito causal.

## Como verificar

```bash
python -m pytest -q tests/test_lab_criteria.py tests/test_criterion_incidents.py
python -m pytest -q
```

O workflow de PR verifica Python 3.10 e 3.12 e frontend, além da suíte de regressão de critérios. Um resultado só deve ser declarado aprovado depois de registrado pela CI.

## Próxima etapa possível

Integrar uma UX de incidentes/planos e implementar autorização persistente por operação e limite de custo. Só após isso disponibilizar ao Lab Assistant `recovery.plan` e `adjustment.preview`; a execução do ajuste precisará de consentimento explícito ou política delegada e auditável.
