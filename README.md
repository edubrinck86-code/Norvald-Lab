# Norvald Lab

Laboratório independente para observar deliberação entre LLMs. Extraído do AROF do Norvald Studio e integrado ao **Norvald-Execution**. Funciona com o Studio desligado, com configurações e dados próprios.

Esta primeira entrega é o backend. A interface visual será feita depois.

## Comece observando

No terminal, dentro desta pasta, execute:

```bash
./scripts/lab.sh demo
```

Na primeira vez o comando prepara o ambiente Python e instala as dependências (requer internet). Depois mostra três condições:

1. **B1 — resposta cega:** cada participante responde sem receber respostas dos colegas.
2. **B3 — reconsideração individual:** cada participante recebe apenas sua própria contribuição anterior.
3. **E — exposição aos pares:** cada participante recebe sua contribuição e as dos demais.

Você verá o início, a conclusão de cada participante e a pasta dos registros. A demonstração usa três participantes simulados e produz nove registros. **Não usa LLM, não consome API e não produz evidência sobre a tese.** As escolhas simuladas servem apenas para conferir o instrumento.

Os dados ficam em `~/.norvald/lab/`. Não são gravados nas pastas do Studio. Para escolher outra pasta:

```bash
./scripts/lab.sh --data-dir ./data demo
```

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

A origem precisa ter respostas estruturadas de todos os participantes. O laboratório verifica os arquivos, mantém as repetições pareadas e recusa mudanças de tarefa, participantes, documentos ou ferramentas nessa derivação. B3 e E usam as mesmas instruções de reconsideração; o contexto exposto é diferente.

O perfil de ferramentas é explícito: `off` ou `corpus` (consulta somente aos documentos congelados). O mecanismo vem do Execution. O catálogo externo de Library, Repository, Web e MCP do Studio não está conectado nesta versão.

## Backend para a futura interface

```bash
./scripts/lab.sh serve
```

Escuta apenas em `http://127.0.0.1:8766`; documentação da API em `/docs`. O servidor aceita demonstrações por padrão; `serve --live` habilita configurações reais. Não há autenticação de serviço público nesta entrega.

Endpoints: `GET /health`, `GET/POST /api/experiments`, `GET /api/experiments/{id}` e suas leituras `/manifest`, `/raw`, `/verify`. O POST devolve 202 e a coleta roda em segundo plano. CLI e API usam o mesmo executor.

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
