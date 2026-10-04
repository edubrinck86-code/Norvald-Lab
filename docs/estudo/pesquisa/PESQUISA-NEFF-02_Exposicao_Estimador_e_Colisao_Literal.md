---
id: PESQUISA-NEFF-02
type: Registro de Decisão de Pesquisa
status: Acordado, pendente de aplicação
version: 1.0.0
date: 2026-09-28
references:
  - docs/pesquisa/PESQUISA-NEFF_Efetividade_Amostral_Sampling_e_Reasoning.md
  - docs/tese/01_Protocolo_Experimental.md
  - docs/tese/03_Posicionamento_e_Procedencia.md
  - docs/analise/Analise_Critica_da_Tese.md
  - docs/adr/Processando/ADR-020_Fronteira_Comercial_e_Telemetria_Declarada.md
---

# Exposição, estimador e colisão literal

> Decisões fechadas na sessão de 28/09/2026, posteriores a PESQUISA-NEFF.
> Esta nota registra o que foi **acordado**, não o que foi cogitado. Onde
> a decisão exige alteração em outro documento ou no código, a ação está
> nomeada com o arquivo e a linha.

## 1. Verificação bibliográfica

Cinco referências centrais de PESQUISA-NEFF foram conferidas na fonte.

| Referência | Estado |
|---|---|
| Kohli, [arXiv 2605.29800](https://arxiv.org/abs/2605.29800), 28/05/2026 | confere |
| Yang et al., [arXiv 2602.03794](https://arxiv.org/abs/2602.03794) | confere — introduz effective channels e K* |
| Kim, E. et al., [PMLR v267](https://proceedings.mlr.press/v267/kim25e.html) | confere — 350+ modelos |
| Kim, D., [arXiv 2607.20768](https://arxiv.org/abs/2607.20768) | registro existe; corpo não extraído |
| Hao et al., [arXiv 2606.00820](https://arxiv.org/abs/2606.00820) | confere — decomposição em três fontes |

A retratação da §8 de PESQUISA-NEFF está apoiada em trabalho real.

### 1.1 Método do Kohli, conferido no corpo do paper

- `e_j,i = 1` se o juiz *j* discorda do rótulo majoritário da ChaosNLI no item *i*. **Vetores binários de erro.** φ̄ é a média sobre os 36 pares.
- Temperatura, variação de prompt e ordenação de rótulo são **condições sistemáticas com n_eff por condição** (Tabela 4), não checagens de robustez. n_eff de 1,94 a 2,18.
- Chain-of-thought **aumenta** a correlação: φ̄ = 0,456, n_eff = 1,94.
- **Os nove juízes não se veem.** Temperatura 0.0, prompt padronizado, sem comunicação nem refinamento iterativo. Não há condição de exposição.

## 2. Reposicionamento perante Kohli

### 2.1 O que cai

Cai mais do que a §44 de PESQUISA-NEFF registrou. A ação documental não é só a linha da tabela.

**Ação — `docs/tese/03_Posicionamento_e_Procedencia.md:99`**, remover ou reformular:

```
ESS para painel de LLMs correlacionados          não encontrado
```

**Ação — mesmo arquivo, parágrafo imediatamente seguinte.** Este é o trecho que Kohli de fato invalida, e deixá-lo em pé com a tabela corrigida produz contradição na mesma página:

> A contribuição não é medir efeito manada — isso tem literatura. É a **ponte**: converter dependência observada em desconto sobre o tamanho amostral de um painel, que é o que falta em quem hoje compõe confiança.

Cai também, por consequência, a caracterização de N_eff sob temperature e sob reasoning como diferencial: Kohli reporta n_eff por condição para ambas.

### 2.2 O que permanece

Uma coisa só, e é suficiente: **exposição**.

O n_eff do Kohli é propriedade estática de um painel que nunca interage. B1/B2/B3/E mede o que acontece com a dependência **quando os participantes passam a se ver**. Isso é N_eff como efeito de tratamento, não como descrição.

Hao decompõe conformidade mas não calcula ESS. A interseção — conformidade expressa como perda de tamanho amostral efetivo — está vaga.

### 2.3 Enquadramento aceito

Rejeitado: "mais abrangente". Kohli cobre o caso dominante (juízes independentes: self-consistency, best-of-n, LLM-as-judge, ensemble). Exposição é subconjunto, e menor.

Aceito:

> Kohli estabelece o piso em painéis isolados; este trabalho mede o que a exposição faz a esse piso.

### 2.4 Confronto obrigatório antes da publicação

A §8.1 de PESQUISA-NEFF declara diferença sem demonstrá-la. **Ação:** tabela linha a linha contra Kohli — tarefa, painel, agregação, estimador de ρ, condições testadas, desfecho. Sem ela, "vamos além" é declaração, que é a objeção que a própria §8.1 levanta.

## 3. Permutabilidade na condição exposta — resolvida

Objeção levantada: Kish pressupõe unidades permutáveis com ρ comum; sob exposição a dependência seria direcional e a ordem importaria.

**A objeção cai contra o protocolo.** `01_Protocolo_Experimental.md` §4: E é leva 2 sobre B1, com as contribuições de **todos** no WC. Ninguém vê a resposta de ninguém na leva 2.

- Dentro da leva 2 as unidades **são** permutáveis: todas viram o mesmo estímulo.
- A dependência é por **causa comum** — o WC da leva 1 — que é a estrutura de conglomerado que Kish pressupõe.
- Não há direcionalidade entre respondentes. Não é "A influenciou B", é "A e B viram a mesma coisa".

Debate sequencial, que é o que Hao e a maior parte da literatura fazem, teria quebrado o estimador.

**Ação — `docs/tese/01_Protocolo_Experimental.md`, §4.** Registrar explicitamente, porque quem conhece design effect vai levantar exatamente esta objeção:

> Exposição simultânea a estímulo comum preserva permutabilidade dentro da leva; a dependência é por causa comum, não por contágio ordenado.

## 4. O estimando

```
N_eff(B1)   painel efetivo antes da deliberação
N_eff(E)    painel efetivo depois
ΔN_eff      o que a exposição custou, em observações
```

ρ̄ em E conflui duas fontes: origem compartilhada e exposição comum. B1 tem só a primeira. A subtração isola a segunda.

## 5. Dois ρ, dois N_eff

A fórmula não conhece o conteúdo de ρ. Aceita qualquer dependência estimável.

```
ρ sobre vetores de erro            →  N_eff de observações efetivas para o erro
ρ sobre sobreposição de conteúdo   →  N_eff de observações efetivas para contribuição
```

Os dois são legítimos e não intercambiáveis. A §37.6 de PESQUISA-NEFF já sustenta isto: N_eff depende do desfecho.

**Consequência — temperatura volta ao escopo.** O nulo do Kohli (1,94 a 2,18) é sobre ρ de erro. Sobre ρ de conteúdo a expectativa é oposta, porque temperatura é o parâmetro que espalha a distribuição de saída. Resultado esperado, se confirmado:

> A amostragem expande a amostra efetiva de conteúdo sem expandir a amostra efetiva de erro.

Isso usa o Kohli em vez de competir com ele. Cuidado obrigatório: N_eff de conteúdo é vizinho de K* (Yang) e precisa ser diferenciado — provavelmente por ser comparável na mesma escala que o de erro, no mesmo painel.

### 5.1 Vocabulário

Rejeitado em texto de publicação: "falta de conhecimento novo". A objeção não é de julgamento — redundância é dado —, é de instrumento: aponta para ρ de conteúdo enquanto a medida usa ρ de erro.

Aceito: **"redundância observacional para o desfecho medido"**.

Registrar o limite conhecido: nos itens em que o painel acerta, conformidade não produz co-falha e ρ_erro não a registra. Δ_herd e N_eff não são intercambiáveis.

## 6. Inference-time scaling

Frase aceita como enquadramento principal:

> N_eff pode ajudar pesquisadores a saber quanto de seu inference-time scaling realmente está aumentando a amostra efetiva, e quanto está apenas repetindo variações correlacionadas.

Escapa de Kohli porque o ρ dele é **entre modelos**; inference-time scaling é **dentro do mesmo modelo, entre amostras**. Nenhuma referência da lista calcula ESS sobre k trajetórias de um único modelo.

Objeção esperada: "já se sabe que self-consistency satura perto de k=20". Resposta: a literatura observa saturação **no desfecho**; esta medida quantifica a causa, em unidade de amostra, por configuração.

O que transforma descrição em ferramenta: se φ̄ for estimável com k pequeno, N_eff **prevê** onde vai saturar antes do gasto.

**Pré-condição, e é o primeiro teste:** φ̄ entre amostras do mesmo modelo é estimável com precisão suficiente em k pequeno? Teste de simulação, sem rodar modelo — gerar vetores binários com ρ conhecido, amostrar k = 4, 8, 16, medir o erro da estimativa. Se só fechar em k = 32, a previsão chega depois do gasto e o valor prático cai.

## 7. AROF-C — o invariante e o estimador

A métrica não julga. **A ação importa uma valência que a métrica não tem.** Enquanto o pesquisador age, a valência é dele; com o laço fechado, ela passa a estar embutida no sistema.

Aceito que o erro está em **antecipar a troca**, não em trocar. Com janela de medição fechada antes da intervenção, o desenho deixa de ser continuamente adaptativo e vira batelada sequencial: medições válidas, não uma contaminada.

**Três regras, acordadas:**

1. Janela de medição declarada antes; intervenção só depois que ela fecha.
2. Número de rodadas declarado antes. Parada por inspeção enviesa ρ̄ para cima — para-se numa flutuação na direção que motiva agir.
3. Nenhuma afirmação de ganho sem braço de controle. "O laço melhorou N_eff de 2,1 para 3,4" nasce contaminada por regressão à média, porque a intervenção foi disparada por leitura baixa.

### 7.1 Controles, a partir de família e reprocessamento

Resolve a regra 3 sem braço nulo adicional:

```
reprocessar (mesmo modelo, nova execução)  →  nenhuma mudança real; é o braço nulo
trocar dentro da família                   →  mudança nominal, ganho esperado pequeno
trocar entre famílias                      →  o tratamento
```

Reprocessar é essencialmente B2. Se N_eff sobe só por reprocessar, isso é regressão à média mais variância estocástica, medida diretamente. Resposta monotônica nos três degraus indica efeito real; ganho concentrado no reprocessamento indica que o laço mede o próprio ruído.

**Limitação a declarar:** família não é variável limpa. Provider não é família; família não é linhagem de treino. Há derivados da mesma base servidos por providers distintos, destilados, fine-tunes, e fechados de procedência desconhecida. O fator exige critério escrito e terá casos indeterminados.

## 8. Família como proxy dispensável

Família nunca foi o objeto — é proxy de "esses dois vão errar juntos". Havendo observável que prediz co-falha diretamente, o proxy é dispensável, e o problema do modelo fechado desaparece.

**Armadilha:** definir parentesco por semelhança de raciocínio e usar parentesco para explicar correlação de erro é circular — co-comportamento explicando co-falha é redescrição.

**Saída:** predição fora da amostra. Estrutura medida no conjunto A precisa predizer correlação de erro no conjunto B. A §40 de PESQUISA-NEFF já exige isso.

**Escada de linhas de base que AROF precisa superar:**

```
metadado declarado (provider, nome)          baseline fraco
artefato de superfície                       baseline barato
estrutura de raciocínio (AROF)               tem que ganhar dos dois
                        ↓
        predizer rho_erro em itens held-out
```

Se artefato de superfície predisser co-falha tão bem quanto estrutura de raciocínio, AROF não acrescentou. É a primeira pergunta que um revisor faz.

## 9. Defeito verificado: fusão entre autores no WC exposto

### 9.1 O caminho

```
backend/application/arof/exposed_context.py       seed_peer_contributions
  → backend/domain/deliberation/contribution_validation.py   validate_and_convert
  → backend/application/execution/working_context_commit_service.py   apply
  → backend/application/deliberation/working_context_updater.py       _find_duplicate
```

### 9.2 O critério

`working_context_updater.py`, `_find_duplicate`:

```python
existing.type == item.type
and existing.content.strip().casefold() == normalized
and existing.source_id == item.source_id
```

A terceira condição existe para impedir fusão entre autores diferentes. No caminho da deliberação ela funciona — `application/deliberation/specialist_execution_service.py` passa `source_id=agent_id`.

**No caminho do experimento ela não funciona.** `validate_and_convert` cria o `ContextItem` sem `source_id`, só com `author_id`. A comparação vira `None == None` e a guarda é sempre verdadeira.

### 9.3 O efeito

Dois participantes que declararem a mesma afirmação, byte a byte após `strip` e `casefold`, viram **uma unidade** no WC exposto. `_merge_provenance` mantém o `author_id` do primeiro; o segundo sobrevive apenas como entrada de proveniência.

O estímulo da condição E é o sinal de maioria. A fusão apaga a repetição **exatamente onde a concordância era máxima**, e a probabilidade de colisão literal cresce nas perguntas em que os modelos concordam — ou seja, a taxa de colisão é maior onde o efeito manada é maior.

Direção do viés: **subestima o estímulo, e portanto Δ_herd.**

Agravante de registro: em `exposed_context.py`, `autores.append(autor)` roda sempre, depois do `apply`. A lista de semeados declara que os dois entraram; um foi absorvido.

O comportamento atual é inconsistente: posições distintas sem contagem para texto idêntico, asserções separadas para o resto — e a inconsistência correlaciona com concordância.

### 9.4 Decisão

**Conserto.** A fusão entre autores é defeito, não escolha de produto: a guarda foi escrita para impedi-la. Corrigir restaura o comportamento pretendido — cada asserção aparece, sem contagem, uniformemente. Nada novo chega ao agente.

**Instrumentação.** A mesma comparação que hoje funde passa a registrar em vez de agir. Mesmo código, consumidor diferente.

**Fronteira.** O dado não é repassado ao agente. Isso preserva o modelo comercial e mantém ADR-020: identificador, enumeração ou medida, nunca rótulo nem prosa.

```
registrar   par de autores + contagem de colisões por leva
não registrar   o texto da afirmação que colidiu
```

A taxa é o que interessa; o conteúdo é do usuário.

**Decisão cancelada por esta:** a escolha entre exibir asserções separadas, posições com contagem, ou posições sem contagem. O conserto restaura a primeira; a contagem vive fora da vista do agente.

### 9.5 Subproduto

Colisão literal entre autores é a **linha de base de artefato de superfície da §8** — a mais barata que existe, determinística, sem embedding nem juiz semântico. Se ela predisser co-falha tão bem quanto estrutura de raciocínio, AROF não acrescentou.

O baseline que a hipótese AROF precisa enfrentar nasce dentro do próprio experimento.

## 10. Auditoria de normalização

Pergunta: o que o WC descarta é redundância?

Critério mecânico, sem juiz semântico, viabilizado pela exigência de conjunto de resposta discreto e declarado (`01_Protocolo_Experimental.md` §5):

```
fusão legítima    ⟺  unidades fundidas tinham a MESMA posição declarada
fusão destrutiva  ⟺  posições declaradas diferentes
```

Por leva cega, comparar o conjunto de posições distintas nas contribuições cruas com o conjunto no WC. Como o normalizador é determinístico e idempotente, isso é auditoria, não experimento.

Se der zero fusões destrutivas, o braço E-prosa vira opcional — mantido só por validade externa, não por controle. Se der diferente de zero, há achado: o framework de deliberação reduz divergência **antes** de qualquer modelo deliberar, o que a literatura de multi-agent não consegue medir porque seus sistemas não têm WC estruturado.

## 11. Escopo do estímulo

O estímulo da condição E não é "cada um viu os textos dos outros" — é *todos viram o mesmo documento estruturado*. Causa comum perfeita, e reproduzível: replicar Hao exige reproduzir a prosa emitida; replicar este desenho exige reproduzir um WC.

Contrapartida, que é escopo e não defeito: Δ_herd aqui não é exposição ao par no sentido genérico da literatura. Validade interna alta, externa mais estreita. **Ação:** declarar, para que não pareça que se mediu a mesma coisa que Hao e se obteve outro número.

Hipótese registrada, derivada de achado anterior do próprio Studio (o WC entrega conclusão sem o argumento que a sustenta): conclusão nua é mais fácil de copiar do que argumento é de refutar. Se valer, parte de Δ_herd é efeito de formato. O braço E-prosa sobre a mesma leva 1 separa as duas coisas e devolve comparabilidade com a literatura.

## 12. Ordem de publicação

Não é escolha entre AROF e N_eff. A §40 exige calibração com gabarito antes de
qualquer estimativa sem gabarito, e essa calibração é produzida pelo próprio
experimento de N_eff. AROF é a jusante.

```
experimento B1/B2/B3/E
        ↓
rho_erro no subconjunto binário com gabarito
        ↓
   ├── N_eff / ΔN_eff            →  publicação 1
   └── alvo de predição do AROF  →  publicação 2
```

**Decidido: a primeira publicação é ΔN_eff sob exposição.** Kohli fornece método
e ponto de comparação; esta tese fornece a condição que ele não tem.

Risco declarado: Δ_herd nulo implica N_eff(E) ≈ N_eff(B1). O protocolo já trata
o caso (`01_Protocolo_Experimental.md`, sobre Δ_self grande com Δ_herd nulo) —
é achado, mas é publicação diferente e menor.

### 12.1 Linha guardada: inference-time scaling

Guardada deliberadamente para depois da publicação 1, para não repetir a
dispersão de PESQUISA-NEFF. Registrada aqui para não se perder.

Um modelo, k amostras, vetores binários de erro entre amostras, ESS sobre
trajetórias. Sem painel, sem multi-provider, sem Studio. Território aberto
porque o ρ do Kohli é **entre modelos** e este é **dentro do mesmo modelo**.

Pré-condição, testável por simulação antes de qualquer execução: φ̄ entre
amostras do mesmo modelo é estimável com precisão suficiente em k pequeno?
Se só fechar em k alto, a previsão de saturação chega depois do gasto e o
valor prático cai. Ver §6.

## 13. Ações pendentes

| # | Ação | Arquivo | Estado |
|---|---|---|---|
| 1 | Remover/reformular a linha `não encontrado` | `docs/tese/03_Posicionamento_e_Procedencia.md` §3 | **feito** |
| 2 | Remover o parágrafo da "ponte" | `docs/tese/03_Posicionamento_e_Procedencia.md` §3 | **feito** |
| 3 | Registrar a justificativa de permutabilidade | `docs/tese/01_Protocolo_Experimental.md` §4.2 | **feito** |
| 4 | Declarar o escopo do estímulo (WC estruturado) | `docs/tese/01_Protocolo_Experimental.md` §5.1 | **feito** |
| 5 | Tabela de confronto linha a linha com Kohli | `docs/tese/04_Confronto_com_Kohli_2026.md` | **feito** |
| 6 | Corrigir a guarda de fusão entre autores | `contribution_validation.py` ou `working_context_updater.py` | pendente |
| 7 | Instrumentar colisão literal como telemetria | a definir | pendente |
| 8 | Teste de simulação: φ̄ estimável em k pequeno? | novo | pendente |
| 9 | Auditoria de normalização por leva | novo | pendente |
| 10 | Pré-registro datado externo | fora do repositório | pendente |

Ações 1 a 5 aplicadas em 28/09/2026, antes do pré-registro — para que o artefato congelado no OSF não contenha reivindicação já sabida falsa. As demais dependem de dado, de código ou de ação externa.
