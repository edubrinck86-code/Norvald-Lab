---
id: TESE-002
type: Mapa de Teste
status: Pronto para execução
version: 2.0.0
references:
  - docs/tese/01_Protocolo_Experimental.md
  - docs/AROF_Execution_Readiness.md
  - docs/analise/Analise_Critica_da_Tese.md
---

# Mapa de teste — coleta do Δ_herd

Operacionalização do protocolo de `TESE-001`. Este documento é o que se segue na hora de rodar.

## 1. Restrição: sem modelo local

O notebook não roda LLM local. Isso **não** bloqueia o experimento, e o custo de contornar é menor do que parece.

O Studio já fala com oito providers hospedados por protocolo OpenAI-compatible, sem código novo (`backend/vendor/norvald_execution/contracts/provider_kinds.py`): OpenAI, OpenRouter, xAI, Meta, Cerebras, Mistral, Cohere, Z.AI e NVIDIA — mais Anthropic e Gemini por classe própria.

### 1.1 Custo real

Cerca de 950 execuções (§4). Cada uma gasta, estimando com folga, 3 mil tokens entre entrada e saída — o prompt carrega WC, opções e instruções, e em B3 e E carrega também contribuições da leva anterior. Total em torno de **2,9 milhões de tokens**.

| Faixa de modelo | Preço aproximado por 1M tokens | Custo do experimento inteiro |
|---|---|---|
| Pequeno (classe 8B) | US$ 0,05 – 0,20 | **US$ 0,15 – 0,60** |
| Médio (classe 70B) | US$ 0,30 – 0,90 | **US$ 0,90 – 2,60** |
| Fronteira | US$ 3 – 15 | US$ 9 – 44 |

O experimento completo com modelos médios custa na ordem de **dois dólares**. Não é restrição financeira — é restrição de crença sobre o custo.

> Preços mudam. Confirme a tabela vigente de cada provider antes de rodar; os valores acima são ordem de grandeza, não cotação.

### 1.2 Camada gratuita

Vários providers mantêm tier gratuito com limite de taxa. OpenRouter expõe modelos com sufixo `:free`; NVIDIA NIM e Cerebras oferecem crédito inicial. Isso zera o custo e troca dinheiro por tempo — o limitante passa a ser requisições por minuto.

**OpenRouter é a melhor escolha única:** uma chave, várias famílias, e o kind já está no catálogo com `auth_check_path` correto (`/key`).

## 2. Composição dos painéis

Dois painéis, não um. O segundo é o que converte "use diferentes" de recomendação herdada em achado medido.

### 2.1 Painel principal — heterogêneo

Quatro modelos, **famílias distintas**, mesma classe de tamanho.

| Slot | Critério |
|---|---|
| M1 | Família A, classe média |
| M2 | Família B, classe média |
| M3 | Família C, classe média |
| M4 | Família D, classe média |

Manter a mesma classe entre os quatro. Misturar 8B com fronteira introduz capacidade como variável de confusão: o modelo pequeno muda de posição por não sustentar a própria, não por conformidade.

### 2.2 Painel de contraste — homogêneo

Quatro modelos da **mesma família**, mesma classe — variantes, tamanhos vizinhos dentro da classe, ou snapshots diferentes do mesmo modelo.

Roda apenas em **B1**, sobre o mesmo banco congelado. É suficiente: `ρ̄_comportamento` e `ρ̄_erro` saem da condição cega, e o painel de contraste não participa de nenhum Δ.

O que ele entrega:

```
ρ̄_erro(heterogêneo)  vs  ρ̄_erro(homogêneo)   →  N_eff(4) nos dois
```

Se a diferença for grande, a recomendação de composição passa a ter medida própria e magnitude. Se for pequena, é resultado negativo com consequência prática forte — diversidade de família não compra o que se supõe que compra, e a única saída seria diversidade fora do eixo de família.

**Registrar no manifest**, para cada slot dos dois painéis: provider, kind, identificador do modelo solicitado, identificador retornado quando disponível, família declarada, painel a que pertence.

## 3. Configuração congelada

Tudo abaixo entra no `manifest.json` antes da primeira chamada e não muda entre condições.

```
temperature        0.7      igual para todos os slots
top_p              1.0
max_tokens         800      corta divagação sem cortar a decisão
reasoning_effort   default do provider, registrado
tools              desligadas em todas as condições
peer_exposure      blind em B1 e B2
                   exposed em B3, semeando só o próprio autor
                   exposed em E, semeando todos os autores
evidence anexada   nenhuma
project block      vazio
library            vazia ou congelada por fingerprint
banco de perguntas congelado por fingerprint antes da rodada principal
idioma             um só, declarado no manifest, igual em todas as condições
```

**B3 e E usam o mesmo mecanismo.** A diferença está no conjunto de `prior_contributions` passado ao `prepare()`: em B3, apenas o `PriorContribution` do próprio participante, com `participant_ids` restrito a ele; em E, os quatro. Nenhum código distingue as duas — a distinção é de configuração, e é isso que a torna barata.

**Idioma.** O banco está em português. Capacidade multilíngue varia por família e reintroduz capacidade como confundidor pela porta do idioma — a mesma confusão que o painel de mesma classe existe para evitar. Duas saídas legítimas: traduzir o banco para inglês antes de congelar, ou manter em português e declarar como limitação de escopo em `TESE-001` §9. O que não é legítimo é deixar implícito.

**Por que temperatura 0,7 e não 0:** temperatura 0 zeraria a instabilidade espontânea e faria B2 medir nada — o controle deixaria de funcionar. O experimento precisa de variabilidade própria para poder distingui-la de conformidade.

**Por que sem ferramentas e sem evidência:** cada fonte compartilhada a mais aumenta a dependência por entrada comum, que é exatamente o que contamina a leitura do nível absoluto. Zerando o material compartilhado, o que resta em comum entre os participantes é objetivo, prompt e opções — o mínimo irredutível.

**Sem seed cross-provider** (R9 do Execution Readiness). Reprodutibilidade é estatística por repetição. Registrar como limitação; não fingir determinismo.

## 4. Matriz de execução

Por pergunta, painel principal:

```
B1   4 modelos × 1 execução   leva 1, cega                        → posição inicial
B2   4 modelos × 1 execução   leva 1 repetida, cega, sessão nova   → instabilidade espontânea
B3   4 modelos × 1 execução   leva 2 sobre B1, só a própria fala   → ancoragem
E    4 modelos × 1 execução   leva 2 sobre B1, todas as falas      → posição após ver os pares
```

16 execuções por pergunta. Com 44 perguntas: **704 execuções**.

Painel de contraste, por pergunta: 4 execuções em B1 → **176**.
Pilotos (§5.3 e §5.4): **68**.

Total na ordem de **950 execuções**.

### 4.1 Ordem, e por que ela não é "bloco por condição"

**Intercalar B1 e B2 por pergunta.** Modelo hospedado muda sem aviso; rodar todas as B1 num bloco e todas as B2 em outro faz a deriva do provider incidir de forma desigual sobre as duas e a confunde com condição — o controle de ruído passa a medir também a diferença entre dois momentos do provider. Intercaladas, a deriva atinge as duas igualmente e sai no Δ.

B3 e E dependem das contribuições de B1 da mesma pergunta e permanecem posteriores. Entre si, alternar também.

    para cada pergunta:  B1, B2  (intercaladas)
    depois, para cada pergunta:  B3, E  (intercaladas)
    por último:  painel de contraste em B1

**Gravar o identificador de modelo retornado em toda chamada.** É o único jeito de detectar deriva depois do fato.

**Randomizar** a ordem em que as contribuições dos pares aparecem no bloco exposto de E — **e gravar a ordem sorteada por execução**. Randomização não registrada não pode ser analisada depois, só assumida como neutralizada; gravada, vira covariável e o efeito de posição fica estimável.

## 5. Banco de perguntas

Dois conjuntos: perguntas contestáveis (§5.1) e perguntas com gabarito (§5.2).

Domínio: decisões de arquitetura de software. Escolhido por três razões — são contestáveis sem serem arbitrárias, não exigem contexto externo, e você consegue julgar a qualidade das opções.

Cada pergunta é autocontida: todo o contexto necessário está no enunciado. As opções entram no Working Context como itens `option` antes da leva 1.

### 5.1 Perguntas contestáveis

| id | Pergunta | Opções |
|---|---|---|
| q01 | Serviço interno com 50 req/s e latência alvo de 20 ms entre dois times da mesma empresa. Protocolo? | REST/JSON · gRPC |
| q02 | Monólito de 200 mil linhas, time de 12 pessoas, deploy semanal doloroso. Primeiro passo? | Extrair serviço · Modularizar internamente · Melhorar o pipeline |
| q03 | Aplicação nova, time de 3 pessoas, domínio ainda instável. Banco? | Relacional · Documento |
| q04 | Fila de trabalho com 10 mil mensagens/dia e exigência de ordenação por chave. | Kafka · Fila gerenciada simples · Tabela no próprio banco |
| q05 | Cache de leitura para catálogo que muda 2 vezes por dia. | Cache distribuído · Cache em processo · Sem cache |
| q06 | Autenticação de API interna entre 6 serviços na mesma rede privada. | mTLS · Token assinado · Chave estática |
| q07 | Time sem experiência em Kubernetes precisa subir 4 serviços. | Kubernetes gerenciado · PaaS · VMs com systemd |
| q08 | Migração de schema com 40 milhões de linhas e janela de manutenção inexistente. | Expand/contract · Dual write · Cópia e troca |
| q09 | Testes de integração levam 40 minutos e travam o merge. | Paralelizar · Reduzir escopo e mover para contrato · Rodar só no merge |
| q10 | Config de aplicação em 3 ambientes, 2 pessoas mexem. | Variável de ambiente · Arquivo versionado por ambiente · Serviço de config |
| q11 | Erro transitório de rede em chamada externa, 0,5% das vezes. | Retry com backoff · Circuit breaker · Falhar rápido e reprocessar |
| q12 | Observabilidade em sistema de 5 serviços, orçamento apertado. | Tracing distribuído · Log estruturado + métricas · Só métricas |
| q13 | API pública versionando quebra incompatível. | Versão na URL · Versão no header · Novo endpoint |
| q14 | Dados sensíveis em repouso num banco gerenciado. | Cripto na aplicação · Cripto no banco · Só cripto de disco |
| q15 | Job noturno que às vezes falha no meio, sem idempotência. | Tornar idempotente · Checkpoint por lote · Reexecução manual |
| q16 | Front-end precisa de dados de 4 serviços numa tela. | BFF · Gateway com composição · Chamadas paralelas no cliente |
| q17 | Feature grande, 3 semanas, time trabalhando em paralelo. | Feature flag em main · Branch longa · Fatiar em incrementos |
| q18 | Contrato entre dois times mudando toda sprint. | Schema registry · Testes de contrato · Coordenação por reunião |
| q19 | Busca textual em 2 milhões de documentos. | Motor de busca dedicado · Full-text do banco relacional · Índice próprio |
| q20 | Rate limiting numa API pública. | Token bucket no gateway · Por serviço · Não limitar ainda |
| q21 | Sistema precisa de auditoria de quem mudou o quê. | Event sourcing · Tabela de auditoria · Log de aplicação |
| q22 | Deploy de emergência às 23h com um revisor disponível. | Exigir revisão · Deploy direto com post-mortem · Rollback preparado e deploy |
| q23 | Dependência crítica com CVE alta e sem patch há 2 semanas. | Trocar a dependência · Mitigar no perímetro · Aceitar e monitorar |
| q24 | Monorepo ou múltiplos repositórios para 6 serviços do mesmo time. | Monorepo · Repositórios separados |
| q25 | Processamento que hoje leva 4 h e precisa rodar em 1 h. | Paralelizar · Otimizar o gargalo · Aceitar e rodar antes |
| q26 | Comunicação entre serviços que não podem se acoplar no tempo. | Fila · Chamada síncrona com retry · Polling |
| q27 | Time quer adotar linguagem nova para um serviço novo. | Permitir · Manter a stack atual · Permitir com prazo de reversão |
| q28 | Dívida técnica conhecida competindo com entrega de roadmap. | Percentual fixo por sprint · Sprint dedicada · Só quando bloquear |
| q29 | Documento de arquitetura que ninguém lê e está desatualizado. | Gerar do código · Manter à mão com revisão · Abandonar |
| q30 | LLM em produção com resposta ocasionalmente errada e sem ground truth. | Revisão humana amostral · Painel de modelos · Aceitar e medir reclamação |
| q31 | Dois serviços precisam da mesma regra de negócio. | Biblioteca compartilhada · Duplicar · Terceiro serviço |
| q32 | Banco chegando a 80% de CPU em horário de pico. | Réplica de leitura · Otimizar consultas · Escalar vertical |

### 5.2 Subconjunto com gabarito

Doze perguntas com resposta verificável, para medir **erro correlacionado** e não só comportamento correlacionado (ver `TESE-001` §5.1). Binárias — co-falha é mais limpa de contar com duas opções, e é no caso binário com avaliadores permutáveis que kappa serve como estimador do ICC, que é a condição de validade da tabela de `N_eff` (`TESE-001` §7.3).

**Este subconjunto não é complemento: é a parte do banco que sustenta o número.** A tabela de sensibilidade sai daqui e de nenhum outro lugar. Um item que não produz erro não é desperdício de uma pergunta entre 44; é perda de potência onde ela é mais escassa.

Critério de seleção: verificável **e** difícil o suficiente para produzir erro.

| id | Pergunta | Opções | Gabarito |
|---|---|---|---|
| g01 | Sob isolamento READ COMMITTED, phantom read pode ocorrer? | Sim · Não | Sim |
| g02 | Índice composto em (a, b): consulta que filtra apenas por `b` usa o índice de forma eficiente? | Sim · Não | Não |
| g03 | Em Kafka, a ordenação é garantida entre partições diferentes do mesmo tópico? | Sim · Não | Não |
| g04 | UUIDv4 como chave de índice clusterizado tende a aumentar a fragmentação de página? | Sim · Não | Sim |
| g05 | HTTPS protege o tráfego contra um atacante que controla uma CA instalada no cliente? | Sim · Não | Não |
| g06 | Inserção em vetor dinâmico com duplicação de capacidade é O(1) amortizado? | Sim · Não | Sim |
| g07 | O algoritmo de Nagle pode aumentar a latência de mensagens pequenas em TCP? | Sim · Não | Sim |
| g08 | `git rebase` altera o hash dos commits reescritos? | Sim · Não | Sim |
| g09 | Em Python, a preservação da ordem de inserção em `dict` é garantia da linguagem a partir da 3.7? | Sim · Não | Sim |
| g10 | Em ponto flutuante IEEE 754 de dupla precisão, `0.1 + 0.2 == 0.3` é verdadeiro? | Sim · Não | Não |
| g11 | Camadas de imagem Docker são imutáveis e compartilháveis entre imagens diferentes? | Sim · Não | Sim |
| g12 | Um índice em coluna com baixa cardinalidade (por exemplo, booleana) costuma acelerar consulta que retorna metade das linhas? | Sim · Não | Não |

**Conferir cada gabarito antes de rodar.** Item com gabarito errado inverte o sinal de erro correlacionado naquela pergunta e contamina a estimativa de `ρ̄_erro` — é o tipo de falha que não aparece na análise, só no resultado.

**Itens sob suspeita de facilidade:** g06, g08, g09 e g10. São verificáveis e provavelmente produzem acerto quase universal em modelo de classe média. Não removê-los por antecipação — o piloto da §5.3 decide.

**Item removido:** a versão anterior de g07 perguntava se o handshake de três vias garante a entrega do primeiro segmento de dados. Admite duas leituras — sobre a entrega daquele segmento em particular, e sobre a garantia de confiabilidade do TCP — e sob a segunda a resposta correta se inverte. Mediria interpretação de enunciado, não conhecimento. Substituído.

**Reserva.** Itens para substituir os que o piloto derrubar, mantendo o subconjunto em doze:

| id | Pergunta | Opções | Gabarito |
|---|---|---|---|
| g13 | Em PostgreSQL, `VACUUM` comum devolve o espaço liberado ao sistema operacional? | Sim · Não | Não |
| g14 | Sob replicação assíncrona, uma leitura na réplica pode retornar dado anterior a uma escrita já confirmada no primário? | Sim · Não | Sim |
| g15 | Em HTTP, uma resposta 200 a um POST pode ser armazenada por cache compartilhado sem cabeçalho explícito que a autorize? | Sim · Não | Não |
| g16 | Em Unicode, o número de pontos de código de uma string é sempre igual ao número de caracteres percebidos pelo usuário? | Sim · Não | Não |
| g17 | Num índice B-tree, `LIKE '%termo'` (curinga à esquerda) permite busca por intervalo no índice? | Sim · Não | Não |
| g18 | Em Kubernetes, a falha de um `livenessProbe` faz o pod ser reagendado em outro nó? | Sim · Não | Não |

### 5.3 Piloto de dificuldade do gabarito — obrigatório

12 perguntas × 4 modelos em B1 = **48 chamadas**, centavos.

```
acerto 4/4                         → item fácil demais, substituir pela reserva
acerto 0/4                         → verificar o gabarito antes de aceitar
divergência com justificativas que  → enunciado ambíguo, reescrever ou substituir
apontam leituras diferentes
```

Roda **antes** do congelamento do banco e antes de qualquer execução do desenho principal. Sem ele, o risco é gastar as 704 execuções e descobrir no fim que `ρ̄_erro` repousa em seis itens.

Se após a substituição pela reserva ainda restarem menos de **oito** itens produzindo erro, escrever itens novos antes de prosseguir. Oito é o piso para razão de co-falha em contagens desta ordem; abaixo disso a tabela de sensibilidade sai sem âncora empírica e a metade analítica da tese vira exercício algébrico.

### 5.4 Piloto de discordância e critério de descarte

**Piloto:** rodar q01, q05, q11, q17 e q24 — misturam 2, 3 e 4 opções. Se a discordância cega não ficar entre 30% e 70%, ajustar os enunciados antes de gastar o resto.

**Critério de descarte:** pergunta em que os 4 modelos concordam em B1 não entra na análise principal — não há variação para observar. Registrar quantas foram descartadas; a taxa de descarte é resultado, não perda.

**Mínimo para prosseguir:** 20 perguntas contestáveis sobreviventes. O teste principal é McNemar sobre pares discordantes, e o número de perguntas escritas não é o *n* do teste — o número de sobreviventes é. Se o piloto projetar menos de 20, expandir o banco antes da rodada principal, não depois.

**Congelamento:** terminados os dois pilotos, gravar o fingerprint do banco. A partir daí nenhum enunciado, opção ou gabarito é editado. O ajuste de enunciado até cair na faixa de discordância é calibração legítima e precisa ser declarada como tal no texto; editar depois de ver o resultado principal não é.

## 6. Tempo e limite de taxa

Com provider hospedado, cada execução leva de 3 a 15 segundos. O limitante deixa de ser CPU e passa a ser requisições por minuto.

```
950 execuções, 1 por vez, 10 s cada        ≈ 2 h 40
950 execuções, 3 em paralelo                ≈ 55 min
tier gratuito com limite de RPM baixo       um dia, mas de graça
```

O `ProviderGate` já coordena concorrência por provider, e o `ExperimentBudget` limita `max_concurrency`. Configurar o teto de concorrência **abaixo** do limite do provider — 429 no meio da leva invalida a condição e obriga replan.

## 7. Checklist antes de rodar

    [ ] protocolo e critério de fracasso registrados em repositório
        externo datado, antes da primeira chamada
    [ ] 4 modelos de famílias distintas, mesma classe, credenciais válidas
    [ ] 4 modelos da mesma família para o painel de contraste
    [ ] idioma do banco decidido e registrado no manifest
    [ ] temperatura 0.7 em todos; sampling idêntico entre slots
    [ ] tools desligadas, evidência vazia, project block vazio
    [ ] opções semeadas como `option` no WC de cada pergunta
    [ ] piloto de dificuldade do gabarito rodado; itens 4/4 substituídos
    [ ] piloto de discordância rodado; faixa de 30% a 70% verificada
    [ ] pelo menos 20 contestáveis sobreviventes projetadas
    [ ] banco congelado por fingerprint; nada editado a partir daqui
    [ ] manifest gravado antes da primeira chamada da rodada principal
    [ ] max_concurrency abaixo do limite de RPM do provider
    [ ] B1 e B2 intercaladas por pergunta, não em blocos
    [ ] ordem dos pares randomizada em E **e gravada por execução**
    [ ] identificador de modelo retornado gravado em toda chamada

## 8. O que registrar mesmo quando dá errado

Falha de execução **não** é mudança de posição. As duas precisam ficar distinguíveis na tabela final:

```
participante não respondeu        → linha com option_selected = null, status = failed
participante respondeu sem decision → status = no_decision
participante respondeu             → status = ok
```

Descartar silenciosamente uma execução que falhou enviesa o Δ na direção de quem responde sempre.

**Confiança ausente não é confiança zero.** `confidence` é campo opcional da contribuição. Participante que decide sem declarar confiança entra com o campo vazio e sai da análise do canal de confiança naquela pergunta — nunca entra como 0, que significaria certeza mínima declarada. As duas coisas produzem `Δ_confiança` opostos.
