---
id: ADR-020
type: ADR
identifier: ADR
version: 1.0.0
status: Proposed
references:
  - ADR-016
  - ADR-019
  - TESE-001
tags:
  - ADR
  - Arquitetura
  - Telemetria
  - Privacidade
---

# ADR-020 — Fronteira entre comercial e pesquisa, e telemetria declarada

| Campo | Valor |
|--------|-------|
| O que é | Separa o produto da pesquisa, tira o AROF experimental do Studio e define o que o produto coleta e exporta. |
| Problema | AROF mora dentro do que observa, e a captura grava o material do cliente — o que impede tanto a separação quanto a coleta declarável. |
| Finalidade | Permitir coleta comum de produto sem conteúdo do cliente, e manter aberta a decisão sobre qual é o produto. |
| Quando utilizar | Ao mexer em captura, exportação ou em qualquer coisa que atravesse a fronteira produto ↔ pesquisa. |
| Quando NÃO utilizar | Para decidir o modelo de negócio, o preço ou o que se vende — esta ADR adia isso de propósito. |

---

# 1. Contexto & Problema

## 1.1 A dependência aponta para os dois lados

`backend/application/arof` e `backend/infrastructure/arof` somam 18 arquivos e 4.030 linhas. A medição da direção de importação:

```
AROF importa do Studio          22 módulos, quase todos uma única vez
Studio importa de AROF           5 pontos
```

Vinte e dois módulos importados uma vez cada não é consumo de interface — é acesso direto ao que estava ao alcance. Dos 22, treze são `domain.*` (tipos, custo baixo) e nove são `application.*`: `round_execution`, `specialist_execution_service`, `context_assembler`, `round_prompt`, `evidence_projection`, `project_context`, `research_scope_builder`, `library_tools`, `assistant.singleton`. Esses nove são uma capacidade só — preparar contexto congelado e executar uma rodada.

Dos 5 pontos em que o Studio alcança o AROF, dois estão no caminho quente (`round_execution`, `specialist_execution_agent`) e ambos são sink de observação, com `arof_observation_sink=None` já como parâmetro. O AROF observa; não participa.

## 1.2 A captura grava o material do cliente

`raw_observation.py` monta dois blocos:

```
linha 224  request_snapshot   instructions · user_message · objective · working_context
linha 254  result_snapshot    content · reasoning · tool_calls · metadata
```

`working_context` é o acervo do cliente serializado. `objective` é o que ele está decidindo. `content` e `reasoning` são a deliberação em texto.

Enquanto a captura for isso, ela não é exportável sob declaração nenhuma — e a fronteira entre produto e pesquisa não fecha, porque o canal de pesquisa carregaria conteúdo do cliente.

## 1.3 A lista de campos permitidos já existe, e já vaza

`_METADATA_KEYS` (linha 20) é uma tupla de chaves permitidas para `studio_metadata` — o mecanismo certo, no nível errado. Duas entradas dela são rótulo livre, não identificador:

```
participant_name   configurado pelo usuário, pode ser qualquer texto
task_label         livre fora do desenho experimental
```

O mecanismo existe e é bom. Falta subi-lo um nível e dar-lhe uma régua.

## 1.4 O que ainda não está decidido

Qual é o produto comercial — o Studio, as bibliotecas, ou o Studio agora e as bibliotecas depois — continua em aberto, por decisão. Esta ADR precisa servir às três saídas sem retrabalho.

---

# 2. Decisão

## 2.1 Três anéis, uma direção

```
núcleo      norvald_kernel · documental_engine · norvald_execution
            bibliotecas; não sabem que o Studio existe

produto     Studio: deliberação, WC, CDD, Library, Repository,
            licensing, telemetria operacional e declarada

pesquisa    experimento, dataset, replay, análise, tese
            repositório próprio
```

**Regra:** `pesquisa → produto → núcleo`. Nunca ao contrário.

Isto é o que adia a decisão de produto a custo zero: se o núcleo nunca souber do Studio, vender as bibliotecas depois é publicar o que já está isolado, e vender o Studio deixa o núcleo como implementação. A mesma estrutura serve às três saídas.

Hoje `vendor/` já obedece — os três pacotes importam zero coisas do Studio. A regra passa a ser verificada por teste, não por disciplina.

## 2.2 O que sai para repositório próprio

Sai o **AROF experimental**: `experiment_runner`, `exposed_context`, `corpus`, `capacity`, `dataset`, `replay`, extração e análise de desfecho, mais `docs/tese`, `docs/paper`, `docs/pesquisa` e `docs/AROF_*`.

Não sai a **captura**. Ela deixa de ser instrumentação de pesquisa e passa a ser telemetria de produto, sob as regras de §2.3 a §2.6.

Consequência para a tese: o repositório de pesquisa consome dado exportado, não módulo do Studio. Para os experimentos próprios — em que o operador é dono dos dois lados — vale o modo de §2.7.

## 2.3 O produto não exporta conteúdo

O Studio já consome o conteúdo internamente: é o que ele faz. O que ele **exporta** é telemetria.

```
conteúdo    permanece no ambiente do cliente, nunca cruza a fronteira
telemetria  estrutura da execução, exportável sob declaração
```

Os campos `request`, `result` e `error` deixam de existir no registro exportável. O que hoje se obtém lendo o texto depois passa a ser computado no instante da captura, e o texto é descartado ali.

## 2.4 A régua: identificador e enumeração, nunca rótulo

Um campo só entra na telemetria se for uma destas três coisas:

```
identificador   opaco fora da sessão          opt-3 · ev-17 · sess-9f2
enumeração      valor de um conjunto fechado  ok · no_decision · failed
medida          número ou instante            tokens · duração · timestamp
```

Fica de fora, sempre:

```
rótulo    texto escolhido por pessoa     nome de participante, título de tarefa
prosa     qualquer texto livre           instrução, mensagem, resposta, raciocínio
```

A régua é verificável em teste, e é ela que sustenta a declaração — "coletamos identificador, enumeração e medida" é auditável; "não coletamos nada sensível" não é.

`participant_name` e `task_label` saem da lista atual por esta régua. Em seu lugar, `participant_id` e `task_id`, que já existem.

## 2.5 Manifesto de campos

A lista do que se coleta vira objeto no código, em arquivo próprio, e é a **única** fonte:

- o registro de telemetria é construído a partir dela;
- a tela que mostra ao usuário o que é coletado é gerada dela;
- um teste falha se o registro emitir campo que não esteja nela.

Sem o teste, o terceiro campo novo entra sem passar pela lista e a declaração vira mentira sem ninguém perceber. É o mesmo raciocínio da ADR-019 sobre lacuna: o que não tem consequência estrutural não se sustenta por intenção.

## 2.6 Consentimento por workspace

Hoje a captura é ligada por `NORVALD_AROF_CAPTURE`, variável de ambiente — decisão de quem opera o servidor, não de quem é dono do dado.

Passa a ser chave por workspace, desligável pelo cliente, com o manifesto de §2.5 visível na mesma tela. Coleta declarada sem desligamento ao alcance de quem declara não é declaração.

Desligada, nada é gravado — não é filtro na exportação, é ausência de registro.

## 2.7 Modo de pesquisa própria

Para os experimentos do próprio operador, sobre material próprio, existe um modo separado que grava o RAW completo, incluindo conteúdo.

Três condições, cumulativas:

1. ligado explicitamente por workspace, nunca por padrão;
2. gravação local, fora de qualquer canal de exportação;
3. marcado no registro, para que dado de pesquisa e telemetria de produto não se misturem em nenhuma análise.

Cliente e pesquisa deixam de compartilhar canal. É isso que torna as duas coisas declaráveis separadamente.

---

# 3. Mapa de arquivos

## 3.1 Arquivos novos

| Arquivo | Conteúdo |
|---|---|
| `backend/domain/telemetry/field_manifest.py` | `FIELD_MANIFEST` — a lista única, com nome, tipo (identificador/enumeração/medida) e descrição |
| `backend/domain/telemetry/field_kind.py` | `FieldKind` — o enum da régua de §2.4 |
| `backend/domain/telemetry/execution_telemetry.py` | `ExecutionTelemetry` — o registro exportável, sem conteúdo |
| `backend/application/telemetry/telemetry_projection.py` | Projeta `ExecutionRequest`/`ExecutionResult` em `ExecutionTelemetry`, descartando texto |
| `backend/application/telemetry/outcome_projection.py` | Deriva posição, confiança, relações e alvos de fundamento no instante da captura |
| `backend/application/observation/observation_sink.py` | `ObservationSink` — protocolo declarado pelo produto, com no-op padrão |
| `backend/application/telemetry/collection_consent.py` | Chave por workspace de §2.6 |
| `backend/api/collection_routes.py` | `GET /api/workspaces/{id}/collection` — manifesto e estado; `PUT` para ligar e desligar |
| `backend/tests/test_direcao_de_importacao.py` | `vendor/` não importa `backend.*`; `application/` não importa `arof` |
| `backend/tests/test_manifesto_de_campos.py` | Nenhum campo emitido fora do manifesto; nenhum rótulo ou prosa no manifesto |
| `backend/tests/test_projecao_de_telemetria.py` | Conteúdo não sobrevive à projeção |
| `frontend/src/features/settings/components/CollectionPanel.tsx` | A tela de §2.6, gerada do manifesto |

## 3.2 Arquivos alterados

| Arquivo | Alteração |
|---|---|
| `backend/application/deliberation/round_execution.py` | Importa `ObservationSink` do produto, não de `infrastructure.arof` |
| `backend/application/execution/specialist_execution_agent.py` | `_capture_arof_attempt` passa a emitir `ExecutionTelemetry` |
| `backend/main.py` | Remove `arof_router`; monta `collection_router` |
| `backend/api/telemetry_routes.py` | Deixa de importar símbolos de `arof` |
| `backend/api/deliberation_routes.py` | `build_outcome_observation_sink` vem do produto |

## 3.3 Arquivos que saem do repositório

```
backend/application/arof/          exceto o que virar projeção de telemetria
backend/infrastructure/arof/
backend/api/arof_routes.py
backend/tests/test_arof_*.py
docs/tese/ · docs/paper/ · docs/pesquisa/ · docs/AROF_*
frontend/src/features/deliberation/components/environments/ArofEnvironment.tsx
```

---

# 4. Ordem de execução

Cada passo entrega o Studio verde. Só o passo 6 é ruptura, e é mecânica.

```
1  teste de direção de importação          invariante antes de mexer
2  manifesto de campos + régua             a lista existe e é verificada
3  ExecutionTelemetry + projeção           o registro sem conteúdo nasce ao lado do RAW
4  projeção de desfecho na borda           o que se lia do texto passa a ser computado
5  inversão dos sinks                      produto declara, AROF implementa
6  AROF experimental sai                   agora é mover, não refatorar
7  consentimento por workspace + tela      a coleta vira declarada de fato
8  módulos tools/ e knowledge/             a raiz solta de application/ some
```

O passo 3 roda em paralelo ao RAW atual de propósito: enquanto os dois coexistem, dá para comparar se a telemetria responde às mesmas perguntas sem o texto. O RAW só é removido quando essa comparação fechar.

---

# 5. Consequências

**A decisão de produto continua aberta.** A regra de direção serve às três saídas. Nenhuma delas exige retrabalho estrutural.

**A tese perde acesso ao texto e não sente.** O que ela mede — posição, mudança, fundamento, confiança — é estrutura, e passa a ser computado na borda. O que ela perderia é a reanálise do texto com critério novo, que deixa de ser possível sobre dado de cliente e continua possível sob §2.7.

**A coleta fica pequena e defensável.** Identificador, enumeração e medida é uma frase auditável. Cobre o que operação precisa — custo, latência, erro, truncamento, terminação — e não cobre nada do que o cliente delibera.

**A raiz de `application/` continua solta até o passo 8.** Sete arquivos `*_tools.py` e quatro de conhecimento sem módulo são o defeito estrutural que motivou este redesenho, e ficam por último porque não bloqueiam a fronteira.

**A vendorização permanece.** Transformar `vendor/` em dependência publicada tem custo de release sem retorno enquanto o produto for indefinido. Vendorização mais teste de direção entrega o mesmo isolamento.

---

# 6. O que esta ADR não decide

- Qual é o produto comercial.
- Preço, empacotamento ou o que entra em cada plano.
- Se o núcleo vira pacote publicado, e quando.
- O destino das 65 falhas de teste pré-existentes.
- A reorganização do frontend, cuja feature `deliberation` tem 114 arquivos e 15.819 linhas.
