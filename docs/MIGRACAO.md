# Migração inicial do backend

## Decisão

Norvald Lab é um programa independente. Reutiliza a infraestrutura de execução e a instrumentação AROF já existentes. Não chama o servidor do Studio e não modifica seus repositórios, sessões, credenciais ou dados.

Origens fixadas em 2026-10-01:

| Origem | Commit |
|---|---|
| `edubrinck86-code/Norvald-teste-codex` | `f0d640779324bdde8c1f76e83b1a1869602af089` |
| `edubrinck86-code/Norvald-Execution` | `c903aa42af8a959c7868c6d8be3b744c9677ac16` |

O namespace público deste projeto é `norvald_lab`. Não existe alias global `backend` ou `src` que permita importar silenciosamente o aplicativo de origem.

## Reaproveitado

- Execution: contratos, providers, suporte HTTP, retries, limites, orquestração e laço de ferramentas. Cópia fixada, somente imports reescritos.
- AROF: RAW v4, manifesto e fechamento v1, replay, integridade dos RAW, captura de capacidade, normalização de referências, extração de outcomes e auditoria de semeadura.
- Domínio: CONTRIBUTION, parser, validação, Working Context, relações, atualização e diff estrutural necessários à exposição controlada.
- Instruções estruturadas do Studio, preservadas na função de origem; o adaptador Lab acrescenta a declaração explícita do seu perfil de corpus e ferramentas.
- Testes correspondentes dos dois repositórios.

`SOURCES.json` mapeia cada arquivo copiado. `source_git_blob_sha` identifica o blob remoto; `source_sha256` refere-se à representação textual baixada. `destination_sha256` registra o conteúdo na entrega. Arquivos novos são a composição independente, CLI, API, configuração, verificação adicional, testes de integração e documentação.

## Adaptado

1. O executor deixou de depender de SessionStore, DeliberationSetupStore, factories do Studio, políticas de conta e montagem de contexto ligada ao workspace. Recebe uma especificação portátil por valor.
2. Toda a condição é preparada antes da primeira chamada. As requisições preparadas são strings imutáveis, e os snapshots completos são gravados antes de executar.
3. Cada repetição usa apenas as contribuições da mesma repetição cega. E entrega o mesmo snapshot de contexto a todos na leva. B3 entrega apenas a contribuição própria.
4. A condição derivada exige origem completa e íntegra. As configurações comparáveis são conferidas. IDs não podem ser reutilizados; reserva de diretório exclusiva impede dois processos de iniciar a mesma coleta.
5. O caminho de dados é `NORVALD_LAB_DATA_DIR` ou `~/.norvald/lab`. Foram retirados os imports e chamadas de espelhamento Drive do Studio. O runner sempre captura RAW; o opt-in legado continua isolado em `NORVALD_LAB_CAPTURE` para os consumidores opcionais desse helper.
6. O catálogo local de ferramentas lê apenas documentos incluídos no snapshot. Não lê caminhos arbitrários, não modifica arquivos e não acessa a biblioteca viva do Studio.
7. O laço do Execution fixado ainda chama `context_scan_pending()` sem checar a presença do gancho. `LabToolRuntime` responde `False` porque a projeção do contexto é integral. O pacote vendorizado não foi editado para corrigir essa dívida de origem.
8. O RAW mantém o formato v4 e os campos legados, inclusive `studio_metadata`, para compatibilidade. A fronteira é declarada como `norvald_lab_execution`; metadados adicionam repetição, tipo de exposição e IDs exatos das observações de origem. `self` tem `peer_exposure_mode=blind` e `lab_exposure_mode=self`: há memória própria, mas não há exposição a pares.
9. A captura de capacidade resolve `/proc/self` quando o ambiente Linux apresenta PIDs em namespaces diferentes. Isso preserva a medição do próprio processo. Nenhuma medição de outra máquina foi usada como substituto.
10. O fechamento adicional `integrity.json` inclui manifesto, snapshots, resultados e eventos. É detecção de alteração, não assinatura criptográfica contra um agente que reescreva também o arquivo de integridade.

## Diferenças experimentais explícitas

O perfil desta entrega é `lab-controlled-structured-v1`, registrado no manifesto. Não se apresenta como execução idêntica à UI do Studio.

- Corpus integral e constante entre B1, B3 e E.
- Grafo inicial limpo de contribuições de especialistas.
- B1 não recebe respostas anteriores; B3 e E partem da mesma condição cega.
- CONTRIBUTION é analisada pelo parser e pelas regras de origem; a auditoria de semeadura preserva contagens de colisões e possíveis fusões. Validação estrutural não é avaliação de verdade.
- Os pedidos não recebem respostas que terminaram antes na mesma leva. Resultados não são aplicados durante a execução da leva.
- Uma tentativa no limite do agente por execução lógica. Retries de transporte e followups de ferramentas continuam sob a política do Execution, com eventos operacionais; não viram novas unidades amostrais.
- Timeout é limite da execução completa, incluindo ferramentas/retries. Limites de chamadas e iterações de ferramentas são opcionais e registrados quando presentes.
- Amostragem solicitada é preservada na especificação; a resolvida e suas notas são preservadas no pedido/RAW. O Lab não certifica que o provider cumpriu um parâmetro apenas porque ele foi solicitado.
- O manifesto fixa commits do instrumento; aliases de modelos, versões internas e raciocínio não exposto pelo provider continuam sendo limites de observação.

## Não migrado nesta entrega

Frontend, editor, gestão de contas/licenciamento, credenciais do Studio, biblioteca viva, sincronização Drive, catálogo Web/MCP, políticas operacionais do Builder e assistente global do Studio. O normalizador determinístico AROF foi copiado; o assistente interpretativo que usa o singleton do Studio não foi conectado. Não existe summarizer intermediário novo.

Importar arquivos de resultados antigos é diferente de certificar uma nova condição Lab: o replay legado continua disponível como biblioteca, mas uma origem para `derive` precisa ter snapshot e fechamento Lab verificáveis. A migração não transforma retroativamente dados do Studio em dados coletados neste perfil.

## Validação da entrega

- 115 testes aprovados no ambiente de preparação.
- Demonstração completa B1/B3/E, três participantes, nove registros, sem Studio e sem rede de LLM.
- Adapter OpenAI-compatible real com `httpx.MockTransport`: reasoning, amostragem, uso e ausência da chave nos arquivos.
- Laço de ferramentas real do Execution com provider de teste e corpus local.
- API FastAPI com POST assíncrono, consulta, RAW, verificação, conflito de ID e bloqueio de chamadas reais quando não habilitadas.
- Cancelamento, falha de participante, limitação concorrente, origem adulterada, corpus incompatível, cópias imutáveis e pareamento entre repetições.
- Análise de imports impede dependência do pacote `backend` do Studio.

Duas verificações herdadas foram adaptadas: a assinatura de `prepare` foi substituída pelo teste de recusa de exposição sem origem; a propriedade de apresentação `display_reasoning` do Studio foi substituída pela verificação de preservação do reasoning bruto e dos metadados separados. A variável do helper opt-in foi renomeada nos testes correspondentes.

Não foram realizadas chamadas pagas nem validação empírica da tese. A suíte emitiu uma advertência de depreciação da integração de testes Starlette/httpx, sem falha funcional.

## Divergências intencionais do Studio — 2026-10-04

Até esta data, parser, validador e extrator eram cópia do Studio no commit `f0d6407`, com reescrita de namespace. A partir daqui o Lab diverge nos pontos abaixo. O Studio **não** foi alterado, e a divergência é intencional: nada aqui deve ser lido como "igual à origem".

`RUNNER_VERSION` passou de `norvald.lab.runner.v1` para `norvald.lab.runner.v2`. O valor é gravado no manifesto e entra no fingerprint da condição; é por ele que se distingue uma coleta anterior de uma posterior a esta mudança. `STUDIO_REVISION` continua apontando para o commit de origem da cópia.

### Arquivos

| Arquivo | Estado | O que mudou |
|---|---|---|
| `norvald_lab/domain/deliberation/malformed_contribution_part.py` | novo | Registro de uma parte do bloco que o parser não leu: tipo, posição, identificador, motivo |
| `norvald_lab/domain/deliberation/contribution.py` | cópia alterada | Leitura por parte em `Contribution.parse`; campo `malformed` |
| `norvald_lab/domain/deliberation/contribution_validation.py` | cópia alterada | Partes não lidas entram em `rejected`; campo `local_ids` em `ValidatedContribution` |
| `norvald_lab/application/arof/outcome_validation.py` | novo | Leitura do validador para uma execução, a partir do RAW |
| `norvald_lab/application/arof/outcome_extract.py` | cópia alterada | Oito colunas novas ao fim de `OutcomeRow` |
| `norvald_lab/contribution_check.py` | próprio do Lab, alterado | `declared_items` e `declared_relations` contam também as partes não lidas |
| `norvald_lab/runner.py` | próprio do Lab, alterado | `RUNNER_VERSION` v2 |
| `tests/test_part_tolerant_parsing.py`, `tests/test_outcome_validation.py` | novos | Testes das duas mudanças |

`destination_sha256` das três cópias alteradas foi atualizado em `SOURCES.json`; `source_sha256` e `source_git_blob_sha` continuam sendo os da origem.

### 1. Parser: recusa por parte

**Origem.** Uma unidade sem `local_id` ou `type`, uma relação sem `relation_type`, `source` ou `target`, uma parte que não fosse objeto JSON ou um `metadata` inválido descartavam o bloco inteiro. Resultado: zero unidades, participante não semeado, derivação de B3/E recusada.

**Lab.** A parte ilegível é registrada em `Contribution.malformed` e aparece entre as recusas do validador, com o motivo. As demais partes seguem para a validação normal. Identificador da recusa: o `local_id` quando existe; senão a posição, `knowledge[i]` ou `relations[i]`, contada a partir de zero.

**O que não mudou.** Nenhum campo é preenchido, inferido ou corrigido. Bloco sem delimitador de fechamento, JSON inválido e `knowledge`/`relations` que não sejam listas continuam descartando o bloco inteiro. A tabela de relações permitidas, os tipos declaráveis e as demais regras do validador são os da origem.

**Consequências para a coleta.**

- Um participante cujo bloco tem uma parte ilegível passa a ser semeado em B3/E com as partes aceitas. O estímulo exposto, para esses casos, é diferente do que a versão anterior produziria (que era recusar a derivação).
- Em `outcomes.csv`, `status`, `option_selected`, `confidence`, `new_evidence_cited`, `grounding_targets` e `relations_out` desses casos passam a ser lidos das partes que sobraram. Antes saíam como `no_decision` e vazios. Para blocos sem parte ilegível, essas colunas não mudam.
- Uma relação que aponta para uma unidade recusada é recusada pelo validador como `source ou target inexistente`.
- Condições de um mesmo estudo devem ser coletadas sob a mesma `RUNNER_VERSION`. `derive` não compara essa versão entre origem e derivada.
- Experimentos já fechados não são reprocessados: o `outcomes.csv` deles foi gerado pelo parser anterior e está sob o fechamento de integridade. O RAW é o mesmo nas duas versões.

### 2. `outcomes.csv`: leitura do validador ao lado da leitura declarada

**Origem.** O extrator lê o bloco declarado sem validar. O contexto exposto de B3/E é montado com o que o validador aceita. As duas leituras divergem sem que a tabela mostre: uma relação recusada conta na tabela e não chega aos pares.

**Lab.** Oito colunas novas, ao fim, sem alterar nome, ordem ou definição das anteriores:

| Coluna | Conteúdo | De onde vem |
|---|---|---|
| `validation_code` | Código do diagnóstico da bancada (`usable`, `partial`, `missing_block`, `unclosed_block`, `invalid_json`, `invalid_schema`, `empty_knowledge`, `rejected_knowledge`, `empty_response`, `execution_failed`) | `check_contribution` |
| `items_declared` | Unidades declaradas no bloco, incluídas as não lidas | contagem |
| `items_accepted` | Unidades aceitas pelo validador | contagem |
| `relations_declared` | Relações declaradas no bloco, incluídas as não lidas | contagem |
| `relations_accepted` | Relações aceitas pelo validador | contagem |
| `option_accepted` | Alvo da primeira relação `selects` aceita que parte de uma `decision` | `validate_and_convert` |
| `grounding_targets_accepted` | Alvos das relações `derived_from`, `evidenced_by` e `documents` aceitas, ordenados, separados por `;` | `validate_and_convert` |
| `rejected_reasons` | Motivo de cada parte recusada, uma entrada por parte, na ordem do validador, separados por barra vertical entre espaços | `validate_and_convert` |

A validação usa o Working Context que a execução recebeu, gravado no próprio RAW em `request.context.working_context`. Quando o registro não traz esse contexto, as oito colunas saem vazias: vazio é ausência de leitura, não zero.

Alvos e opções aparecem como foram declarados: `local_id` quando a unidade é da própria contribuição, id do Working Context quando já existia. O UUID que o validador atribui a cada unidade é sorteado a cada validação e não é gravado na tabela.

**O que não foi decidido aqui.** Qual das duas leituras é a medida. `01_Protocolo_Experimental.md` §6 define as consultas sobre o grafo e §8 diz que o extrator lê o RAW; as colunas tornam a diferença observável por execução e não resolvem a escolha. A tabela de relações permitidas e a definição de `novo_fundamento` também permanecem como estavam.

## Atualização futura

Mudanças no motor Execution devem ser feitas no repositório de origem e depois incorporadas com novo commit registrado. Não editar sua cópia local para alterar comportamento. Mudanças nas adaptações AROF pertencem ao Lab e precisam manter origem, versão de schema e diferenças experimentais explícitas.
