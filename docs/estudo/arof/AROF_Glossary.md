---
id: AROF-GLOSSARY
identifier: GLOSSARY
status: Active
tags:
- AROF
- reasoning
- metrics
- notation
- glossary
type: Glossary
version: 1.1.0
---

# AROF — Glossário e Convenção de Notação

> Vocabulário canônico do **Agentic Reasoning Observability Framework (AROF)**.
>
> Este documento existe para impedir que ADRs, código, Intelligence Lab,
> experimentos e textos acadêmicos usem nomes diferentes para o mesmo objeto
> ou o mesmo símbolo para objetos diferentes.

## 1. Regra canônica

Se um termo ou símbolo matemático do AROF aparecer em implementação, ADR,
métrica, experimento ou documentação, ele deve possuir uma definição neste
glossário.

Quando uma definição mudar:

1. o glossário é atualizado primeiro;
2. a versão do glossário é incrementada;
3. artefatos derivados registram a versão usada;
4. dados históricos continuam interpretáveis pela versão anterior.

O glossário define **linguagem**, não resultado científico. Termos marcados como
candidatos ou hipóteses continuam sujeitos a validação experimental.

## 2. Convenção geral de símbolos

| Prefixo/símbolo | Uso canônico |
|---|---|
| P(·) | probabilidade/distribuição |
| F_t | Reasoning Function observada no passo t |
| M | matriz |
| T | trajetória |
| H / h | entropia |
| D | distância/divergência |
| τ | tempo até evento/estado |
| ρ | correlação/dependência |
| N | contagem/tamanho efetivo |
| C | contexto experimental |
| 𝒯 | espaço/distribuição de trajetórias |
| S | distribuição de Reasoning Functions |
| G | estrutura/topologia da trajetória |
| O | orientação dos eventos/funções |

Regra visual:

    H...  → entropia
    D...  → distância/divergência
    P...  → probabilidade
    T...  → trajetória
    M...  → matriz
    τ...  → tempo até evento
    ρ...  → correlação/dependência
    N...  → contagem efetiva

## 3. Objetos de observação

### AROF

**Nome completo:** Agentic Reasoning Observability Framework.

Camada de observação destinada a coletar, normalizar, medir e referenciar a
estrutura observável do reasoning agêntico.

O AROF não afirma acesso ao estado interno completo do modelo e não atribui
qualidade normativa ao padrão observado.

### Reasoning Trace

Reasoning/thinking tal como efetivamente exposto pelo provider.

É o dado bruto de processo.

Não significa:

- chain-of-thought interno completo;
- estado latente verdadeiro;
- representação integral do pensamento do modelo.

### Exposure Mode

Forma pela qual o provider declara ou torna conhecida a exposição do Reasoning
Trace.

Vocabulário inicial:

    raw
    summarized
    filtered
    redacted
    unknown

Quando o provider/interface não declara tecnicamente o modo, o AROF registra
`unknown`. Comprimento, estilo ou concisão do trace não autorizam inferir
automaticamente `summarized`, `filtered` ou `redacted`.

### Reasoning Observation Status

Estado da observação do processo na execução:

    observed
    not_exposed

`not_exposed` significa que nenhum Reasoning Trace foi recebido na fronteira
observada. Não significa ausência de raciocínio interno e não representa uma
Process Trajectory de comprimento zero.

### Exposure Character

Descrição da superfície efetivamente observada, separada do Exposure Mode
declarado. Pode registrar características como uma exposição concisa/estruturada
ou discursiva quando isso for anotado como observação, sem afirmar qual
mecanismo interno do provider a produziu.

O vocabulário de Exposure Character ainda não está congelado. Na ausência de
anotação observacional suficiente, usa-se `unknown`.

### Reasoning Event

Unidade observável extraída do Reasoning Trace.

Exemplo:

    "Essa evidência contradiz a hipótese anterior."

O evento preserva o trecho original, posição/sequência, provider, modelo e
proveniência.

### Reasoning Function

Função semântica normalizada atribuída a um Reasoning Event.

Símbolo: **F_t**, onde t indica a posição do evento na trajetória observada.

A função é uma classificação operacional, não uma afirmação sobre mecanismo
cognitivo interno.

### Reasoning Function Assignment

Registro versionado que associa um Reasoning Event a uma Reasoning Function,
subtipo e orientação.

Exemplo conceitual:

    function = CHALLENGE
    subtype = evidence_conflict
    orientation = evidence
    framework_version = v1

Evento e classificação permanecem separados para permitir reprocessamento.

### Support Status

Atributo candidato, ortogonal à Reasoning Function, destinado a registrar o
tipo de suporte/proveniência de uma afirmação observada, por exemplo se ela é
sustentada diretamente por fonte, inferida, hipotética ou incompatível com uma
fonte autoritativa.

O vocabulário ainda está em validação e não é normativo. `support_status`
não cria uma Reasoning Function adicional e não entra automaticamente como
estado da Transition Matrix.

### Reasoning Orientation

Direção/alvo funcional de um evento.

Vocabulário inicial:

    self
    peer
    evidence
    tool
    source

A lista pode crescer de forma versionada.

### Reasoning Transition

Passagem observada entre duas Reasoning Functions:

    F_t → F_(t+1)

Exemplo:

    EVALUATE → REVISE

## 4. Reasoning Functions v1

### FRAME

Delimita problema, hipótese, escopo, premissas ou enquadramento.

### DECOMPOSE

Divide o problema em partes, subtarefas, dimensões ou dependências.

### GENERATE

Produz hipótese, alternativa, explicação, candidato ou possibilidade.

### EVALUATE

Compara, testa, verifica, pondera ou aplica critérios.

Subtipos possíveis:

    compare
    verify
    weigh
    test
    rank

### CHALLENGE

Introduz contradição, contraexemplo, conflito ou ataque a uma premissa.

Subtipos possíveis:

    contradiction
    counterexample
    assumption_attack
    evidence_conflict

### REVISE

Modifica estado anterior do raciocínio.

Subtipos possíveis:

    update
    retract
    narrow
    replace

### INTEGRATE

Combina resultados, evidências, critérios ou subproblemas.

### CONCLUDE

Fecha, seleciona, decide ou sintetiza uma posição.

### UNCERTAINTY

Mantém dúvida, ausência de informação, suspensão ou indeterminação explícita.

## 5. Trajetórias

### Process Trajectory

**Símbolo recomendado:** T_P

Trajetória derivada do Reasoning Trace exposto.

Pode conter Reasoning Events, Reasoning Functions, transitions, branches,
revisions, orientations, eventos de ferramenta e dependências temporais.

### Outcome Trajectory

**Símbolo recomendado:** T_O

Trajetória derivada do comportamento materializado no Studio: primitives,
relations, Working Context, tools, evidências, critérios, inferências, claims e
decisões.

### Agentic Reasoning Observation

**Símbolo recomendado:** A

Objeto que vincula:

    A = (T_P?, T_O, C)

com a proveniência necessária da execução. O ponto de interrogação é
intencional: T_P é opcional porque reasoning pode não ser exposto pelo
provider/interface. T_O permanece observável a partir do comportamento
materializado no Studio quando esse material existe.

É a unidade conceitual que relaciona processo exposto, quando disponível, e
resultado agêntico. O Outcome nunca deve ser usado para preencher
retroativamente transições ausentes de T_P.

### Agentic Trajectory Space

**Símbolo:** 𝒯

Espaço/distribuição das trajetórias agênticas observáveis sob determinado
contexto.

Não significa o espaço completo de estados internos possíveis do modelo.

## 6. Contexto experimental

### Context

**Símbolo:** C

Conjunto de condições sob as quais uma observação foi produzida.

Deve registrar, quando aplicável:

    task/context class
    prompt/orchestration version
    provider
    model
    model version
    reasoning effort
    sampling
    tools disponíveis
    exposure mode
    reasoning observation status
    exposure character quando anotado
    framework version
    Working Context relevante

Toda comparação séria deve deixar explícito o condicionamento em C.

## 7. Function Distribution

**Símbolo:** S

Distribuição marginal das Reasoning Functions observadas:

    S(i) = P(F = i)

Responde:

> com que frequência cada função aparece?

Não deve ser confundida com a matriz condicional de transição.

## 8. Transition Matrix

**Símbolo:** M_T

Matriz condicional:

    M_T[i,j] = P(F_(t+1) = j | F_t = i)

Responde:

> estando em i, como se distribuem os próximos movimentos observados?

A definição canônica do AROF é **condicional**. Não usar M_T para nomear a
distribuição conjunta de pares P(F_t=i, F_(t+1)=j).

## 9. Movimento mais provável

Para estado atual i:

    F̂_(t+1) = argmax_j P(F_(t+1)=j | F_t=i, C)

Interpretação:

> próxima Reasoning Function mais provável segundo a distribuição estimada.

Isso é previsão probabilística de estrutura observada, não previsão de conteúdo
textual nem afirmação sobre estado interno.

## 10. Local Transition Entropy

**Símbolo:** h(i)

    h(i) = - Σ_j P(j|i) log P(j|i)

Responde:

> quão concentrada ou dispersa está a distribuição de próximos movimentos
> quando o processo se encontra em i?

Separação obrigatória:

    P(j|i) → QUAL movimento tende a ocorrer
    h(i)   → QUÃO previsível/concentrada está essa previsão

Entropia maior não significa raciocínio melhor.
Entropia menor não significa raciocínio pior.

## 11. Transition Entropy

**Símbolo:** H_T

Forma agregada ponderada:

    H_T = - Σ_i p(i) Σ_j P(j|i) log P(j|i)

Interpretação:

> variabilidade média observada das transições funcionais.

### Normalized Transition Entropy

**Símbolo recomendado:** H_T^norm

Forma candidata:

    H_T^norm = H_T / log(K)

onde K depende do espaço de estados/transições considerado.

A normalização ainda é objeto de validação experimental.

## 12. Entropy Trajectory

**Símbolo recomendado:** h⃗_T

Para uma trajetória:

    F_1, F_2, ..., F_T

define-se:

    h⃗_T = (h_1, h_2, ..., h_(T-1))

com:

    h_t = H(F_(t+1) | F_t, C)

Responde:

> como a previsibilidade estrutural varia ao longo do processo?

Não confundir com Path Entropy.

## 13. Hitting Time / First-Passage Time

**Símbolo:** τ_R

Para uma função alvo R:

    τ_R = min { t ≥ 0 : F_t = R }

Exemplo:

    E[τ_REVISE | F_0 = FRAME, C]

Interpretação:

> número esperado de movimentos até alcançar REVISE partindo de FRAME sob
> contexto comparável.

Hitting time responde ao **quando**, enquanto Transition Entropy responde à
incerteza da dinâmica local.

## 14. Path Entropy

**Símbolo:** H_path

Para trajetórias completas τ:

    H_path(C) = - Σ_τ P(τ|C) log P(τ|C)

Interpretação:

> dispersão da distribuição de caminhos funcionais completos sob um contexto.

Se quase toda observação percorre a mesma trajetória:

    P(τ*) ≈ 1  →  H_path ≈ 0

## 15. Agentic Entropy

**Símbolo:** H_A

Definição conceitual atual:

    H_A(C) := H(𝒯 | C)

Interpretação:

> incerteza/diversidade do espaço de trajetórias agênticas observáveis
> condicionado ao contexto.

Os seguintes objetos podem descrever ou aproximar aspectos de P(τ|C):

    Transition Entropy
    branching
    revision
    orientation
    recurrence
    trajectory topology
    hitting times
    entropy rate

Eles não são, por definição, parcelas aditivas de H_A.

Não equivalências:

    H_token ≠ H_text ≠ h(i) ≠ H_T ≠ H_path ≠ H_A

## 16. Entropy Rate

**Símbolo:** h_∞

Definição assintótica:

    h_∞ = lim_(T→∞) (1/T) H(F_1, ..., F_T | C)

Interpretação:

> quantidade média de incerteza estrutural nova por passo.

Status: **candidato de pesquisa**. Reasoning traces finitos exigem método de
estimação apropriado.

## 17. Estrutura da trajetória

### Topology

**Símbolo:** G

Descrição estrutural da trajetória, potencialmente incluindo:

    depth
    branching
    merging
    recurrence
    backtracking

Revisões não devem ser automaticamente contadas em G e em S como dimensões
independentes de uma métrica composta sem teste de colinearidade.

### Orientation Distribution

**Símbolo:** O

Distribuição das Reasoning Orientations observadas.

A orientação peer deve ser testada contra measure_cross_engagement, porque
pode duplicar informação já representada por R.

## 18. OAD — Observed Agentic Divergence

**Símbolo recomendado:** D_A

Distância estrutural entre trajetórias, perfis ou populações observáveis sob
condições comparáveis.

Representação de trabalho:

    T = (S, M_T, G, O)

Dimensões candidatas:

    D_S, D_M, D_G, D_O

Forma composta candidata:

    OAD(A,B) = w_1 D_M + w_2 D_S + w_3 D_G + w_4 D_O

Os pesos w_k **não estão definidos**.

Nenhum peso deve ser adotado antes de análise de estabilidade, colinearidade,
sensibilidade, validade preditiva e redundância com métricas já existentes.

### Jensen–Shannon Divergence

**Símbolo:** JSD(P,Q)

Candidata para comparar distribuições:

    JSD(P,Q) = 1/2 KL(P||M) + 1/2 KL(Q||M)

com:

    M = 1/2(P+Q)

Status: função candidata, não padrão obrigatório do AROF.

## 19. Observed Reasoning Profile

**Sigla:** ORP

Perfil histórico das distribuições, transições e demais métricas observadas de
uma configuração sob contexto controlado.

Deve ser condicionado pelo menos por provider/model, model version, exposure
mode, task/context class, prompt/orchestration version, sampling, tool grants e
framework version.

Não representa "como o modelo pensa internamente".

## 20. Divergência intra e inter

### Intra-model Divergence

**Símbolo:** D_intra

    D_intra = E[D(T_a,T_b) | model_a = model_b]

Divergência média entre execuções comparáveis do mesmo modelo.

### Inter-model Divergence

**Símbolo:** D_inter

    D_inter = E[D(T_a,T_b) | model_a ≠ model_b]

Divergência média entre execuções de modelos diferentes sob condições
comparáveis.

### Identifiability Hypothesis

Hipótese experimental central:

    D_intra < D_inter

Se sustentada sob controles adequados, indica sinal estrutural associado à
população/modelo além da variabilidade interna.

Não é definição; é hipótese a testar.

## 21. Kernel local

**Símbolo:** P(·|i,C)

Distribuição de próximos estados a partir de i, sob contexto C.

Para dois modelos/populações A e B:

    P_A(·|i,C)
    P_B(·|i,C)

podem ser comparados por divergência.

Interpretação candidata:

    pequena divergência entre kernels
    + baixa entropia local
    → previsão estrutural semelhante mais concentrada naquele estado

A relação precisa ser validada fora da amostra antes de ser chamada de
capacidade preditiva.

## 22. Dependência e tamanho amostral efetivo

### Pairwise Dependency / Correlation

**Símbolo:** ρ_ij

Dependência/correlação estimada entre duas unidades/agentes/trajetórias.

A interpretação estatística concreta depende do estimador adotado.

### Average Dependency / Correlation

**Símbolo:** ρ̄

Correlação/dependência média entre pares:

    ρ̄ = (1/|𝒫|) Σ_(i,j ∈ 𝒫) ρ_ij

A passagem:

    OAD → ρ̂_ij

é uma **hipótese de modelagem ainda não fechada**.

### Effective Sample Size

**Símbolo:** N_eff

Forma registrada no ADR-1000:

    N_eff = n / (1 + (n - 1) ρ̄)

Extremos:

    ρ̄ = 0  →  N_eff = n
    ρ̄ = 1  →  N_eff = 1

Interpretação:

> número efetivo de observações independentes sob a forma de correlação
> adotada.

## 23. Conformidade / herd effect

### Blind Condition

Condição em que especialistas ainda não foram expostos às posições dos pares.

No desenho atual do Norvald, corresponde conceitualmente à primeira leva quando
não há afirmações alheias disponíveis no Working Context.

### Exposed Condition

Condição em que especialistas já recebem posições/contribuições anteriores de
outros participantes.

### Herd/Conformity Delta

**Símbolo recomendado:** Δ_herd

    Δ_herd = Convergence_exposed - Convergence_blind

É candidato a variável observável para validar métricas derivadas do AROF.

## 24. Relação com o CC

Fórmula histórica registrada:

    CC = 0.30 E + 0.25 R + 0.20 C_adj + 0.15 I + 0.10 H

Este glossário não redefine os componentes históricos.

### C_adj

Componente histórico ligado à correlação/dependência estimada entre
especialistas.

Sua interpretação futura permanece em revisão no ADR-1000.

### I

Componente histórico ligado à independência.

Sua interpretação futura permanece em revisão no ADR-1000.

### R

Componente de consistência/cruzamento estrutural entre análises.

measure_cross_engagement é parte da instrumentação já implementada.

### Caminho candidato em estudo

    OAD
      → ρ̄ estimado
      → N_eff
      → CC

Status: **proposta de reformulação**, não fórmula final do CC.

## 25. Relações que não podem ser assumidas

As seguintes equivalências são proibidas sem evidência empírica:

    texto diferente = raciocínio diferente
    concordância = dependência
    discordância = independência
    mais entropia = melhor reasoning
    menos entropia = pior reasoning
    mais agentes = mais evidência independente
    providers diferentes = independência
    mesmo provider = dependência total
    mesmo H_T = mesma trajetória
    OAD alta = qualidade alta
    reasoning trace = pensamento interno completo
    reasoning não exposto = trajetória de comprimento zero
    resposta final = reconstrução válida do Process Trajectory
    web search = verdade

## 26. Status das definições

### Definido

Objeto com significado operacional suficientemente especificado para
implementação.

    Reasoning Trace
    Reasoning Event
    Reasoning Function
    Reasoning Transition
    M_T
    h(i)
    H_T
    T_P
    T_O

### Definido conceitualmente, estimação aberta

Objeto matemático claro cuja estimação prática ainda precisa ser validada.

    H_path
    H_A
    h_∞

### Candidato de modelagem

Objeto cuja forma/composição ainda depende de dados.

    OAD composta
    pesos w_k
    OAD → ρ
    normalização H_T^norm

### Hipótese experimental

Relação a ser confirmada ou rejeitada.

    D_intra < D_inter
    OAD prediz Δ_herd
    kernels semelhantes predizem movimentos semelhantes

## 27. Cadeia canônica resumida

    Reasoning Trace
          ↓
    Reasoning Event
          ↓
    Reasoning Function F_t
          ↓
    Reasoning Transition
          ↓
    Transition Matrix M_T
          ├──→ próximo movimento P(j|i,C)
          ├──→ Local Transition Entropy h(i)
          ├──→ Transition Entropy H_T
          ├──→ Entropy Trajectory
          └──→ Hitting Time τ

    sequências completas
          ↓
    Process Trajectory T_P
          ↓
    P(τ|C)
          ↓
    Path Entropy H_path
          ↓
    Agentic Entropy H_A(C)=H(𝒯|C)

    Working Context + tools + primitives + relations
          ↓
    Outcome Trajectory T_O

    T_P? ↔ T_O
           ↓
    Agentic Reasoning Observation

    comparação de trajetórias/populações
          ↓
    OAD / D_A
          ↓
    hipótese: ρ̂
          ↓
    N_eff
          ↓
    relação futura com CC

## 28. Regra de interpretação

O AROF segue a cadeia:

    observação
      ↓
    representação
      ↓
    métrica
      ↓
    experimento
      ↓
    estatística
      ↓
    interpretação limitada ao que os dados sustentam

Nunca:

    padrão observado
      ↓
    juízo de qualidade

O Studio coleta, estrutura, mede e referencia.
