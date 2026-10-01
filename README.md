# Norvald Lab

Laboratório independente para observar deliberação entre LLMs. Extraído do AROF do Norvald Studio e integrado ao **Norvald-Execution**. Funciona com o Studio desligado, com configurações e dados próprios.

Inclui uma **bancada visual de observação**, com a identidade fosca do Studio, destaque em cobre e seu renderer de Markdown.

## Comece observando

Para abrir a interface, dentro da pasta do projeto:

```bash
./scripts/start.sh
```

O comando prepara Python e a interface, inicia o laboratório e abre o navegador em `http://127.0.0.1:8766`. Na primeira vez requer internet, Python 3.10+ e Node.js 22.12+. Cadastre sua conexão em **Configurações** e clique em **Novo experimento**. O ambiente inicia sem demonstrações, perguntas ou documentos fictícios.

- **Configurações:** cadastre, substitua ou remova chaves por provedor; consulte a conexão sem gerar resposta e habilite chamadas reais.
- **Preparar:** escreva a pergunta, selecione modelos no catálogo com filtros de preço, tools e reasoning declarados, configure documentos e confira o contrato antes de iniciar.
- **Acompanhar:** veja os participantes em cards horizontais compactos, sem a resposta na página. Clique no card para abrir a Bancada em overlay central de 95% da tela. Respostas, reasoning disponibilizado, eventos e contexto continuam ligados ao registro original.
- **Comparar:** use os cards compactos de **O que mudou?** para abrir uma comparação ampla. **Respostas completas** exibe a base independente e a condição escolhida lado a lado; **Alterações** mostra acréscimos e remoções em toda a largura. Escolha participante, repetição e registro da condição dentro do overlay. Em telas estreitas, as respostas ficam empilhadas.
- **Notes:** anotações rápidas em overlay, com lista à esquerda, título e toolbar no topo, edição/preview, tags e contagem de palavras. O salvamento é automático; copiar e baixar preservam o Markdown.
- **Notebook:** organize suas hipóteses, protocolos e análises em cartões de blocos, seguindo a estrutura do Notebook do Studio. Abra um bloco para escrever com o índice à esquerda, inspector e navegação abertos à direita. Há múltiplos cadernos, busca, duplicação, exclusão e reordenação por arraste ou setas.

Selecione um trecho e use **Fixar trecho**, ou **Marcar momento** na linha do tempo. A nota mantém uma referência à observação original. As notas ficam em `observer/notes/`, fora dos experimentos e dos contextos das LLMs. Alterá-las não modifica o dataset.

No Notebook, **Trazer anotação** cria um bloco com uma cópia do texto, da data e da origem da nota. O inspector permite conferir a cópia original, abrir a nota atual e voltar ao experimento. A cópia permanece mesmo se a nota for alterada ou excluída. Os cadernos ficam em `observer/workbooks/`, também fora do dataset.

**Usar caderno no corpus** (ou **Usar este bloco no corpus**) mostra uma cópia identificada pela revisão e pelo hash do texto. Depois de conferir, **Preparar experimento com esta versão** inclui esse documento na preparação de um novo experimento. Nenhuma LLM é chamada nessa etapa. A versão copiada permanece igual no experimento, mesmo que você continue editando o caderno. As condições derivadas mantêm o corpus da base, como antes.

O editor salva automaticamente e informa falhas. Uma edição atrasada de outra aba é recusada, preservando o rascunho na tela para conferência. Referências `[[título ou ID do bloco]]`, `[bloco](notebook:ID_CADERNO/ID_BLOCO)` e `[anotação capturada](notebook:ID_CADERNO/ID_BLOCO/source)` abrem em overlay; os links web continuam externos.

O replay navega pelos registros gravados; não pausa a coleta. A resposta e o reasoning aparecem quando são capturados, sem simular chegada de tokens. Os destaques comparam texto, sem avaliar qualidade ou atribuir causalidade. Registros ainda sem fechamento são identificados como provisórios; registros fechados alterados têm sua leitura bloqueada.

Para usar modelos reais, abra **Configurações**, salve a chave do provedor e habilite **Chamadas reais**. No **Preparar**, escolha o modo **Modelos reais**. Cada participante permite escolher diretamente entre os provedores cadastrados; trocar o provedor abre seu catálogo. Use **Escolher modelo** para consultar novamente e aplicar filtros. Variáveis e endereços próprios ficam em **Ajustes avançados das conexões**. O catálogo é consultado na API do provedor: preço ou capacidade ausentes aparecem como **não declarados**. Ollama aparece como **local**; isso não é uma declaração de preço zero.

As chaves ficam em `private/settings.json` dentro da pasta de dados, fora dos experimentos e do Git, com permissões de acesso do usuário (diretório `0700`, arquivo `0600`). A interface não recupera a chave após salvar. A execução real começa apenas no botão **Iniciar experimento**, após a conferência. Variáveis de ambiente e configurações JSON existentes continuam aceitas.

Use `NORVALD_LAB_DATA_DIR` para escolher a pasta de dados da bancada. Quem já compilou a interface pode iniciar apenas o servidor com `./scripts/lab.sh serve --open`.

### Gerenciar e ajustar

Em **Experimentos**, use **Selecionar**, marque um registro e escolha **Editar** ou **Excluir**. Editar abre uma cópia da configuração em Preparar, com um novo ID e como nova coleta independente; os registros anteriores permanecem intactos. Excluir retira da lista sem apagar as referências existentes. **Mostrar excluídos → Restaurar** desfaz a exclusão.

No overlay de um participante, **Pedir ajuste à LLM** permite escrever uma orientação e ajustar o limite de saída. Só a resposta escolhida é reenviada, com seu contexto e material originais. O pedido inclui automaticamente o diagnóstico dessa resposta, partes recusadas pelo validador e limites de saída anterior e atual. Ao continuar, o diagnóstico corresponde à tentativa escolhida, não à resposta original. **Ver pedido de ajuste** mostra essas informações, a resposta anterior e as instruções completas antes do envio, sem chamadas à LLM nem gravação de uma tentativa. Cada tentativa registra instrução, pedido, resposta, consumo, diagnóstico e ligação à origem em `observer/adjustments/`, com fechamento de integridade separado. Você pode fechar o overlay, voltar depois, continuar uma tentativa ou salvar sua resposta nas Notes para trazê-la ao Notebook.

Um ajuste assistido tem protocolo próprio e **não é uma nova amostra independente**. Ele não altera o RAW original nem substitui uma base B1 em comparações pareadas. Uma contribuição inválida na coleta original continua bloqueando a exposição controlada. Não há loop automático de correção; cada nova tentativa exige clicar em Enviar ajuste e pode consumir a API. Um erro de transporte também é preservado e pode ser tentado novamente sem chamar os demais participantes.

O editor de blocos do Notebook ocupa 95% da largura e da altura disponíveis, com índice, inspector e navegação. O documento central usa toda a largura adicional.

Os dados ficam em `~/.norvald/lab/`, separados do Studio.

## O que olhar nos resultados

Cada experimento tem uma pasta em `experiments/<id>/`:

| Arquivo | O que você pode observar |
|---|---|
| `spec.json` | A tarefa, os participantes, documentos e condição declarados |
| `manifest.json` | O desenho registrado antes das chamadas |
| `requests.json` | O contexto e as instruções preparados para cada participante |
| `raw/r0001/observations.jsonl` | As entradas, respostas, reasoning disponibilizado, erros e consumo |
| `seed_audits.json` | Quais contribuições anteriores chegaram à condição seguinte e efeitos da inserção no grafo |
| `events.jsonl` | A sequência operacional da execução |
| `outcomes.csv` | Uma linha por execução lógica: posição declarada, confiança e relações |
| `capacity.json` | Medidas operacionais da máquina |
| `completion.json` | Fechamento e contagens da coleta |
| `result.json` | Resumo operacional, sem substituir os registros brutos |
| `integrity.json` | Impressões dos arquivos para detectar alterações posteriores |

Uma falha continua sendo um registro. Ausência de resposta ou confiança não vira zero. Chamadas adicionais de ferramentas não contam como novos participantes.

`complete` significa que as chamadas planejadas retornaram sem erro de execução; não certifica a qualidade das respostas ou a validade científica da hipótese. `incomplete` indica falhas de execução. `aborted` indica interrupção tratada. Uma pasta sem fechamento é uma coleta não certificada.

## Conferir e consultar

```bash
./scripts/lab.sh list
./scripts/lab.sh inspect ID_DO_EXPERIMENTO
./scripts/lab.sh verify ID_DO_EXPERIMENTO
```

Os comandos `inspect` e `verify` não chamam modelos. A exportação CSV é produzida automaticamente. Não edite os arquivos fechados: copie-os para outra pasta se quiser trabalhar sobre eles.

## Usar modelos reais

O exemplo `examples/live.template.json` mostra o formato. Escolha os modelos, provider e tarefa. A configuração guarda **o nome** da variável que contém a chave; nunca coloque a chave no JSON ou no Git.

```bash
# Defina LAB_PROVIDER_KEY no ambiente de forma privada.
./scripts/lab.sh prepare examples/live.template.json
./scripts/lab.sh run examples/live.template.json --live
```

`prepare` confere e prepara os pedidos sem chamar modelos. `--live` habilita a execução real, sujeita ao consumo da conta do provider. IDs de experimentos são exclusivos: uma nova coleta recebe outro ID.

Depois de uma condição cega completa e íntegra:

```bash
./scripts/lab.sh derive ID_CEGO novo-b3 --exposure self --output b3.json
./scripts/lab.sh run b3.json --live
./scripts/lab.sh derive ID_CEGO novo-e --exposure exposed --output e.json
./scripts/lab.sh run e.json --live
```

A origem precisa ter respostas estruturadas de todos os participantes. Quando um bloco CONTRIBUTION estiver ausente, inválido ou sem fechamento, a bancada mostra **Ver diagnóstico e resposta original**, com participante, modelo e repetição. Essa conferência não modifica o RAW e não avalia qualidade. Aumentar limite de saída ou ajustar instruções exige uma nova coleta base; a anterior permanece preservada. O laboratório verifica os arquivos, mantém as repetições pareadas e recusa mudanças de tarefa, participantes, documentos ou ferramentas nessa derivação. B3 e E usam as mesmas instruções de reconsideração; o contexto exposto é diferente.

O perfil de ferramentas é explícito: `off` ou `corpus` (consulta somente aos documentos congelados). O mecanismo vem do Execution. O catálogo externo de Library, Repository, Web e MCP do Studio não está conectado nesta versão.

## Servidor local e API

```bash
./scripts/lab.sh serve
```

Escuta apenas em `http://127.0.0.1:8766`; documentação da API em `/docs`. O servidor inicia com chamadas reais desabilitadas se ainda não houver preferência salva. Habilite chamadas reais em Configurações; essa preferência persiste entre reinicializações. `serve --live` continua disponível como alternativa. Não há autenticação de serviço público nesta entrega.

Endpoints: `GET /health`, `GET/POST /api/experiments`, `GET /api/experiments/{id}` e suas leituras `/manifest`, `/raw`, `/verify`, `/observe`. `POST /api/prepare` confere sem executar; `POST /api/derive` prepara outra condição; `GET /api/experiment-template` oferece uma configuração vazia para modelos reais. `GET /api/experiments/{id}/editable-copy` prepara uma cópia editável; `DELETE /api/experiments/{id}` exclui da lista e `POST /api/experiments/{id}/restore` restaura. `GET/POST /api/adjustments/{id}` lê ou solicita ajustes separados da coleta. As anotações usam `/api/notes`; os cadernos, `GET/POST /api/workbooks`, `GET/PUT /api/workbooks/{id}` e `POST` nas ações `/capture-note` e `/corpus`. Escritas e capturas de caderno exigem a revisão atual. Conexões e execução usam `/api/settings`; `POST /api/models` consulta o catálogo sem gerar respostas. Essas rotas recusam origens web diferentes e retornam `Cache-Control: no-store`. A coleta roda em segundo plano. CLI e API usam o mesmo executor.

## Limites científicos e da migração

- O reasoning registrado é somente o disponibilizado pelo provider. Ausência permanece ausência; não é reconstruído a partir da resposta final.
- `outcomes.csv` conserva o extrator do AROF. `new_evidence_cited` sinaliza uma relação de fundamento declarada; **não prova novidade factual, validade da fonte ou independência**. Os IDs dos alvos ficam disponíveis para análise posterior.
- Esta versão não calcula automaticamente efeito manada, qualidade, causalidade, correlação ou tamanho efetivo de amostra.
- O perfil `lab-controlled-structured-v1` usa o formato CONTRIBUTION e o parser do Studio, mas entrega corpus integral em todas as condições e não faz replanejamento automático. Não é uma reprodução integral do perfil nativo do Studio.
- Repetir a leitura do RAW é possível sem API. Repetir a chamada à LLM não garante a mesma resposta; aliases de modelos e detalhes dos providers podem mudar.
- Interrupção normal deixa fechamento `aborted`; queda abrupta de energia/processo pode deixar a coleta sem fechamento. Não há retomada automática que reenvie chamadas potencialmente cobradas.

Detalhes de origem, alterações e verificação estão em [docs/MIGRACAO.md](docs/MIGRACAO.md). O mapa por arquivo está em [docs/SOURCES.json](docs/SOURCES.json).

## Testes

```bash
./scripts/lab.sh --help
.venv/bin/python -m pytest -q
```

Os testes incluem os módulos migrados, execução independente, isolamento entre condições/repetições, concorrência, falhas, cancelamento, integridade, ferramentas e API. A integração com um adapter real é testada com transporte HTTP simulado, sem chamadas pagas.
