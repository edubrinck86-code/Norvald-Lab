# Lab Assistant — etapa 4: planejamento na interface e ferramentas de consulta

**Estado:** implementação em PR rascunho; `main` não foi alterada.  
**Política vigente:** [LAB_ASSISTANT_POLITICA_OPERACIONAL.md](LAB_ASSISTANT_POLITICA_OPERACIONAL.md).  
**Referência:** padrões do catálogo de operações do Norvald-Huginn.

## Planejamento antes da execução

A aba **Lab Assistant** agora contém uma seção de preparação de experimentos:

1. Abrir um novo rascunho ou uma **cópia editável** do experimento selecionado (sem sobrescrever o experimento original).
2. Editar o `Spec` em JSON.
3. Chamar `POST /api/assistant/plans/experiment`. O Lab valida e executa o preflight `ExperimentRunner.prepare`, sem chamada LLM e sem iniciar a coleta.
4. Apresentar objetivo, identificador, condição, ferramentas, participantes/providers/modelos, repetições, total de requests preparados e fingerprint.
5. Só quando o usuário clicar **Executar plano apresentado**, enviar o `plan_id` a `POST /api/assistant/plans/{plan_id}/execute`. O backend verifica novamente a configuração e a integridade e consome o plano uma única vez.
6. Acompanhar o estudo pelo painel já existente da Bancada.

Não há permissão especial por executar operações não destrutivas nem teto adicional de consumo do Assistant. A execução `live` ainda depende de ter as conexões e execução real habilitadas no próprio Lab — isso é um pré-requisito técnico, não aprovação por tarefa.

O sistema de planos e parada emergencial não cancela coletas existentes nem modifica o RAW. O `Spec.budget` (concorrência, timeout e limite de execuções previstos para um desenho experimental) continua sujeito às regras do Runner; ele não é um orçamento do modelo operador.

## Consultas por ferramentas nativas do modelo operador

O `LabAssistant.reply` oferece ao provider os três nomes permitidos:

- `list_operations`: lista o catálogo de consultas habilitadas.
- `describe_operation`: devolve a descrição e o schema JSON de uma operação específica.
- `call_operation`: executa **somente** uma operação já permitida no catálogo tipado.

Operações consultivas disponíveis: `lab.spec.template`, `lab.spec.evaluate`, `lab.experiment.criteria`, `lab.experiments.list`, `lab.experiment.status`, `lab.incidents.list` e `lab.incident.get`.

O modelo não recebe rota arbitrária, shell, filesystem, edição de settings, exclusão, inicialização de coleta ou ajuste por ferramentas. A disponibilização dessas ações fica fora desta fatia. As operações chamam os serviços existentes do Lab e conservam a autoridade do validador.

O laço do modelo pode executar múltiplas consultas legítimas sem quota de chamadas ou tokens própria. O **detector emergencial**, inspirado no Huginn, observa assinaturas de chamadas repetidas (por exemplo, quatro consultas idênticas ou um padrão cíclico reiterado) e interrompe a conversa e **novas ações** com um registro persistente; a interface permite retomada. Não é uma cota para trabalhos distintos.

## Proteções científicas

- `raw/`, `spec.json`, manifests e registros de integridade continuam imutáveis.
- `partial/usable` permanece distinto de `fully_valid`.
- Ajustes são separados, com origem, checksum e histórico; não se tornam amostras independentes.
- O modelo operador é diferente dos participantes e não altera automaticamente os participantes da coleta.
- Planos de execução são persistidos sob `observer/`, não inseridos nos arquivos de experimento.
- O retorno de `call_operation` é informação consultiva, não novo estado científico validado.

## Arquivos principais

- `frontend/src/components/AssistantExperimentPlanner.tsx`: edição do Spec, preparação, visualização e início de coleta.
- `frontend/src/components/LabAssistant.tsx` e `frontend/src/App.tsx`: integração com o painel e navegação.
- `norvald_lab/assistant_tools.py`: definições e despachante de ferramentas de leitura.
- `norvald_lab/lab_operations.py`: contratos Pydantic e whitelist de consultas.
- `norvald_lab/lab_assistant.py`: execução de tool calls, retorno de resultados ao provider e detecção de repetição.
- `norvald_lab/api.py`: vincula o catálogo e o controle emergencial ao Assistant.
- `tests/test_lab_assistant.py`: execução simulada de ferramentas e loop; `tests/test_assistant_plans.py`: planejamento idempotente, bloqueio emergencial e execução de coleta.

## Verificação e limitações

Verificar a CI da PR para as duas versões de Python e para o frontend. Esta etapa não inclui execução manual real com provider nem avaliação de usabilidade em navegador.

**Ainda pendente:** orquestração geral conversacional de tarefas fora de incidentes, planejamento de estudos em linguagem natural (a tela atual edita um `Spec`), autenticação do Assistant pessoal externo, escopos de ações destrutivas e rotinas recorrentes. O modelo operador nesta etapa **não pode acionar experimentos sozinho por tool call**; eles são executados apenas pelo endpoint de plano previamente apresentado.
