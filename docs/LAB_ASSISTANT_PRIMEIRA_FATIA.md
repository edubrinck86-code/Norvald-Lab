# Lab Assistant — primeira fatia: critérios e catálogo interno

**Estado:** implementação em branch de desenvolvimento, para revisão/testes; **não integra ainda o Assistant LLM**.  
**Branch:** `feature/lab-assistant-criteria-operations`.  
**Concepção:** [LAB_ASSISTANT_HUGINN_PROPOSTA.md](LAB_ASSISTANT_HUGINN_PROPOSTA.md).  
**Mapeamento:** [LAB_ASSISTANT_HUGINN_MAPEAMENTO_CODIGO.md](LAB_ASSISTANT_HUGINN_MAPEAMENTO_CODIGO.md).

## Escopo entregue nesta branch

- `norvald_lab/criteria.py`: projeções determinísticas `evaluate_spec(runner, spec)` e `evaluate_snapshot(snapshot)`. Reutilizam as decisões existentes de `validate_spec`, `runner.prepare` e `observer.snapshot/contribution_checks`.
- `norvald_lab/lab_operations.py`: catálogo **interno** e exclusivamente consultivo. Schema Pydantic, nomes/descrições de operações e whitelist:
  - `lab.spec.template`
  - `lab.spec.evaluate`
  - `lab.experiment.criteria`
- `norvald_lab/api.py`: `POST /api/criteria/spec` (regras de configuração/preparação) e `GET /api/experiments/{experiment_id}/criteria` (observações após leitura de integridade); ambos com verificação de origem local e `Cache-Control: no-store`.
- `tests/test_lab_criteria.py`: testes de projeção, distinção `usable` vs `fully_valid`, recusa de histórico alterado, catálogo whitelist, contrato HTTP, proteção de origem e não alteração do RAW.

O catálogo fica em `app.state.lab_operations` para consumo por um serviço de Assistant futuro, sem despachante genérico sobre HTTP. A presença desse objeto no backend não permite execução remota.

## Exemplos

```http
POST /api/criteria/spec
Content-Type: application/json

{ ...Spec do Norvald Lab... }
```

Sucesso ou recusa do validador retorna avaliação estruturada (JSON) com `schema_version=norvald.lab.criteria.v1`, `subject`, `overall`, `evaluations[]`, e `fingerprint` quando a preparação passou. Uma recusa do framework é reportada como `not_met`, não como uma falsa execução.

```http
GET /api/experiments/experimento-123/criteria
```

A resposta contempla:
- `lab.dataset.integrity`
- `lab.experiment.complete`
- `arof.contribution.coverage`
- `arof.contribution.usable` e `arof.contribution.fully_valid` para cada `observation_id` verificável.

Estados dos critérios: `met`, `not_met`, `pending`, `not_evaluable`. Os códigos reais de `check_contribution` permanecem em `code` e `evidence.validator_code`. Critérios e evidências têm identificação versionada simples.

**Atenção:** `overall` é apenas um agregado das verificações **implementadas nesta fatia**; **não é certificação global do protocolo, resultado científico ou aprovação de exposição**. Para exposição, a autoridade permanece `ExperimentRunner.prepare`, e `usable` pode ser verdadeiro mesmo com `fully_valid` falso. A aceitação parcial não deve ser invalidada retroativamente por um critério posterior de conformidade integral.

Se `integrity.json` não existe ou falha, a avaliação não afirma conformidade de contribuições. Nenhuma LLM é chamada por esses endpoints.

## Limites intencionais

- Nenhum campo, registro RAW, manifesto, outcome, script de coleta ou validador existente é modificado por essas novas leituras.
- Nenhum Assistant em operação, nenhum incidente persistido, nenhuma correção automática, nenhum scheduler, nenhuma exportação para outra plataforma.
- Nenhum novo endpoint de `call_operation` aberto; a autenticação/autorização de agentes externos continua a ser projetada.
- A API local não é adequada para exposição pública na rede.
- Não há estimativa ou autorização de custos de execução nesta fatia.

## Verificação

Com ambiente e dependências do Lab instalados, executar:

```bash
python -m pytest tests/test_lab_criteria.py
python -m pytest tests/test_contribution_check.py tests/test_adjustments.py tests/test_lab.py tests/test_observer.py
```

Não marcar testes como passados sem execução comprovada. Revisar a compatibilidade da versão Pydantic instalada antes da integração.

## Próxima fatia sugerida

Adotar esquema persistente de incidentes por `criterion_id`/`observation_id`, histórico de aprovações e a primeira política **não destrutiva** de `recovery.plan` (propor, explicar, pré-visualizar; sem disparar ajustes por conta própria). Após testes, ligar catálogo e diagnósticos ao Assistant nativo.
