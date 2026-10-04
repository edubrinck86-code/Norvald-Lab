---
id: ANALISE-TESE-001
type: Análise Crítica
status: Vigente
version: 1.0.0
date: 2026-09-27
references:
  - docs/tese/01_Protocolo_Experimental.md
  - docs/tese/02_Mapa_de_Teste.md
  - docs/tese/03_Posicionamento_e_Procedencia.md
---

# Análise crítica da tese — benefício, impacto e gaps

Escopo restrito a `TESE-001`, `TESE-002` e `TESE-003`. Não cobre o paper, a anotação de pesquisa nem o caderno.

As correções desta análise foram aplicadas aos três documentos na mesma data. A coluna "estado" da §5 registra o que foi feito e o que permanece como decisão de execução.

## 1. Benefício

Quatro contribuições separáveis, em ordem de robustez. Cada uma sobrevive à queda das seguintes.

**Definições operacionais sem juiz semântico.** A peça mais forte e a menos valorizada no texto original. Todo trabalho concorrente que mede acordo entre LLMs usa um LLM para julgar acordo — introduz um instrumento correlacionado num estudo sobre correlação. Medir posição por identidade de grafo (`decision --selects--> option`) elimina a circularidade. É portável: vale para qualquer medição de concordância entre modelos, independente da tese.

**B2 como controle.** A literatura de debate multiagente compara rodada 1 com rodada N e atribui toda a mudança à exposição. A temperatura 0,7, instabilidade espontânea responde por parcela relevante do efeito ingênuo. B2 converte `Δ_herd` de artefato em estimando.

**Identificação parcial em vez de estimativa pontual.** Não estimar ρ̄ converte a maior fraqueza — `C_adj` inobservável — em escolha declarada com literatura estabelecida atrás. A conclusão passa a ser robusta ao parâmetro desconhecido.

**Falseabilidade pré-declarada.** `TESE-001` §12 registra o critério de fracasso antes da execução. Incomum, e levanta a régua de credibilidade de um trabalho sem instituição atrás.

Benefício não-acadêmico: custo na ordem de um dólar. Muda o perfil de risco — a tese pode ser rodada, falhar e ser refeita. Não é detalhe operacional; é o que torna o trabalho viável sem financiamento.

## 2. Impacto

| Camada | Alcance | Depende de Δ_herd positivo? |
|---|---|---|
| Studio | `C_adj` deixa de ser termo indefensável; composição de painel vira decisão com evidência | não |
| Prática | self-consistency, painel de juízes, best-of-n — linha de custo de inferência | não |
| Método | design effect / ICC entra no vocabulário de avaliação de painel | não |
| Fenômeno | conformidade ao par medida com controle de instabilidade | **sim** |

Três das quatro camadas não dependem do resultado empírico. A metade analítica entrega valor mesmo com `Δ_herd` nulo; a metade empírica é o que faz disso tese em vez de nota metodológica.

**O número mais citável estava implícito.** A tabela de sensibilidade varre ρ̄ para *n* fixo. O resultado forte é o limite:

    N_eff → 1/ρ̄   quando n → ∞

Com ρ̄ = 0,5, nenhum painel de tamanho algum passa de 2 observações efetivas. Incorporado a `TESE-001` §7.3.

**Risco de impacto negativo.** `N_eff` será citado fora de escopo, aplicado a frota de agentes em tarefas distintas. A guarda existe em `TESE-001` §1.1 e `TESE-003` §1, mas precisa estar no abstract, que é o que se lê.

## 3. Gaps

Ordenados por severidade. Os quatro primeiros são substantivos.

### G1 — O ρ̄ medido não é o ρ̄ da fórmula

`N_eff = n/(1+(n−1)ρ̄)` vem de design effect em amostragem por conglomerado, onde ρ é a correlação intraclasse do desfecho dentro do cluster. A tese mede ρ̄ como kappa sobre seleção categórica de opção.

Kappa e ICC coincidem no caso binário com avaliadores permutáveis. Divergem com k>2 opções e marginais desiguais. E acordo comportamental não é correlação de erro — a tese reconhece isso ao criar dois pisos, mas então só `ρ̄_erro` é o insumo correto, e `ρ̄_erro` só existe nas questões com gabarito, que são binárias e de distribuição diferente das contestáveis.

Cadeia original: mede acordo na tarefa A, usa como piso de ρ̄, alimenta fórmula cujo ρ̄ é definido para tarefa B.

**Correção aplicada.** Condição de correspondência declarada (binário com avaliadores permutáveis: kappa de Fleiss é estimador do ICC). A tabela de `N_eff` passa a ser calculada sobre o subconjunto binário com gabarito; o acordo no conjunto contestável vira quantidade descritiva separada.

**Consequência de projeto:** o subconjunto com gabarito deixa de ser complemento e passa a sustentar o número.

### G2 — `novo_fundamento` é declaração, não fato

Na condição exposta as contribuições dos pares estão no Working Context — são objetos citáveis. Um modelo que se conforma pode anexar `derived_from` apontando para o par ao qual se conformou e ser classificado como "mudou com fundamento novo". É o caso que a definição existe para capturar, e ele passava.

Direção do viés: conservadora, subestima `Δ_herd`. Um efeito detectado sobrevive. Um resultado nulo fica ininterpretável — pode ser conformidade disciplinadamente citada.

**Correção aplicada.** Exclusão explícita: alvo pertencente a contribuição de participante não conta como fundamento novo. As duas variantes — estrita e frouxa — passam a ser reportadas como intervalo.

### G3 — B2 controla duas coisas ao mesmo tempo

B1→E e B1→B2 diferem em dois aspectos, não um:

| | vê os pares | vê a própria posição da leva 1 |
|---|---|---|
| B2 | não | não |
| E | sim | **sim** |

A condição exposta tem ancoragem na própria posição, que reduz mudança, somada à exposição ao par, que a aumenta. `Δ_herd = taxa(E) − taxa(B2)` mistura os dois com sinais opostos: estimativa enviesada para zero, positivo vira limite inferior, nulo vira inconclusivo.

**Correção aplicada.** Quarta condição **B3**: rodada 2 da sessão de B1 com o WC contendo apenas a contribuição do próprio participante.

    Δ_self = taxa(B3) − taxa(B2)     efeito de ver a si mesmo
    Δ_herd = taxa(E)  − taxa(B3)     efeito de ver o par, limpo

Custo de engenharia: zero. `prepare()` já aceita `participant_ids` e `prior_contributions`; B3 é uma chamada por participante com o próprio `PriorContribution`.

### G4 — `ρ̄_piso` não é piso

A derivação original apoiava o piso na assimetria de `PESQUISA-1000` §68: convergência é evidência de dependência, divergência não é evidência de independência. A assimetria está correta; a conclusão de que o acordo observado é limite inferior de ρ̄ não segue dela.

Acordo acima do acaso inclui acordo produzido por pergunta fácil — ambos certos por bom motivo. É exatamente o caso "dependência sem erro" que a própria tese diz que não deveria penalizar `N_eff`. Logo `ρ̄_comportamento` pode estar acima do `ρ̄_erro` verdadeiro: candidato a teto, não a piso.

**Correção aplicada.** O piso foi removido. A varredura cobre [0, 1] e o `ρ̄_erro` observado entra como âncora empírica, não como limite. A força retórica — todo o intervalo leva à mesma conclusão qualitativa — não precisava do piso e fica maior sem ele, porque deixa de repousar sobre inferência contestável. Correção por subtração.

### G5 — Confiança não era medida

Participante que mantém a opção e move a confiança de 0,4 para 0,9 depois de ver três pares concordarem está se conformando. É a forma mais pura do fenômeno — contágio sem mudança de comportamento — e o desenho original pontuava como "não mudou".

Grave por posicionamento: o alvo declarado da tese compõe **confiança**. O desenho media tudo menos o canal do alvo.

**Correção aplicada.** `confidence` passa a ser extraído no `OutcomeRow`. Zero execuções adicionais. Ganho secundário: desfecho contínuo, onde ICC é propriamente definido — resolve parcialmente G1.

### G6 — "Use diferentes" era herdado, não medido

`TESE-003` §2 é a conclusão prática central, e o desenho original usava uma única composição de painel. Nada variava diversidade: a recomendação vinha de Kim (2607.20768) e da teoria.

**Correção aplicada.** Braço de contraste com quatro modelos da mesma família, mesma classe, apenas em condição cega — suficiente para `ρ̄_comportamento` e `ρ̄_erro` homogêneos. Converte a recomendação econômica de citação em achado próprio.

### G7 — Aritmética amostral não fechava

- Protocolo pedia 25–40 perguntas e "um terço com gabarito"; o banco tem 32 + 12 = 44, e 12/44 = 27%.
- Volume declarado era 30 perguntas e 360 execuções; o banco implica outro número.
- A tabela de sensibilidade usava n=5; o painel tem 4.
- O critério de descarte remove perguntas com acordo 4/4 em cega. Com alvo de discordância de 30–70%, o descarte pode atingir a maioria. McNemar opera sobre pares discordantes, e não havia mínimo de perguntas sobreviventes nem regra de aborto.
- 12 perguntas × 4 modelos = 48 unidades para `ρ̄_erro` — fino para razão de contagens pequenas, e é a quantidade que sustenta o número.

**Correção aplicada.** Números reconciliados em torno de 44 perguntas, tabela em n=4, mínimo de perguntas sobreviventes declarado, e o banco com gabarito marcado para expansão se o piloto de dificuldade derrubar itens.

### G8 — Gabarito com risco de item fácil e item ambíguo

O risco maior não é gabarito errado, é item fácil demais. Quatro itens do banco devem produzir acerto quase universal em modelos competentes; se não produzem erro, `ρ̄_erro` repousa na metade restante.

Um item mede leitura em vez de conhecimento: a pergunta sobre o handshake TCP admite leitura em que a resposta correta se inverte, porque TCP garante entrega confiável ou notificação de falha.

**Correção aplicada.** Piloto de dificuldade do gabarito tornado obrigatório e anterior ao principal — 48 chamadas, centavos. Item ambíguo reescrito. Regra de substituição para qualquer item com acerto 4/4.

### G9 — Texto defasado pelo pivô de LLM local

| Local | Texto original | Contradizia |
|---|---|---|
| §11 passo 2 | "instalar 4 modelos locais" | §8 e `TESE-002` §1 |
| §11 passo 4 | "implementar a condição E (única lacuna de engenharia)" | §8 "Nada de engenharia pendente" |
| §9 | "Modelos locais não representam fronteira" | idem |
| §6 | definia `Δ_dispersão` | §7 nunca usava |
| §7.1 | "A muda em direção a B" | §6 não definia direção de mudança |

Todos corrigidos.

### G10 — Δ_dispersão órfão e nível de painel nunca testado

McNemar individual responde "o indivíduo se conforma". `N_eff` é sobre o painel. São ligados, não iguais.

**Correção aplicada.** Teste de nível de painel: Wilcoxon pareado sobre `Δ_dispersão` por pergunta. Unidade é a pergunta, o que dá n na casa das dezenas em vez de contagem de células discordantes.

## 4. Ameaças não listadas que um revisor levanta

**Não-estacionariedade do provider.** Modelos hospedados mudam sem aviso. A ordem original — todas as B1, depois todas as B2, depois todas as E — maximizava a exposição à deriva e a confundia com condição. Corrigido: B1 e B2 intercaladas por pergunta. E depende de B1 e permanece posterior.

**Idioma como confundidor de capacidade.** Perguntas em português, painel de quatro famílias, capacidade multilíngue variando por família. Reintroduz capacidade pela porta do idioma — precisamente o que Kim adverte. Registrado na tabela de ameaças com os dois caminhos: rodar o banco em inglês, ou manter em português e declarar como limitação de escopo.

**Dado de pré-treino compartilhado como mecanismo.** O desenho mede dependência mas não atribui causa. Para o argumento de `N_eff` é indiferente — o desconto vale de qualquer modo — mas a linguagem causal precisa ser contida. Registrado.

**Auto-seleção do banco.** Perguntas escritas por quem testa a hipótese, opções escolhidas por ele, enunciados ajustados após o piloto até cair na faixa de discordância. Calibração legítima, que precisa ser declarada como tal e seguida de congelamento do banco antes da rodada principal. Registrado.

**Randomização não registrada.** Se a ordem sorteada dos pares não for gravada por execução, o efeito de posição não pode ser analisado depois — só assumido como neutralizado. Registrado no checklist.

**Ausência de pré-registro externo.** O critério de fracasso está dentro de um repositório mutável de autoria própria. Para primeira tese sem instituição, a pergunta de credibilidade é se a análise foi decidida depois de ver o dado. Registro datado externo custa zero e converte a declaração em artefato.

## 5. Recomendações e estado

| # | Ação | Custo | Estado |
|---|---|---|---|
| 1 | Condição B3 (auto-ancoragem) | ~US$ 0,30 · zero código | aplicado ao protocolo e ao mapa |
| 2 | Abandonar o piso de ρ̄; varrer [0,1] | zero | aplicado |
| 3 | Extrair `confidence` no `OutcomeRow` | ~10 linhas | implementado |
| 4 | Braço homogêneo, só condição cega | ~US$ 0,50 · zero código | aplicado ao mapa |
| 5 | Piloto de dificuldade do gabarito | centavos | aplicado ao mapa e ao checklist |
| 6 | Intercalar B1/B2 | zero | aplicado ao mapa |
| 7 | Reportar a assíntota 1/ρ̄ | zero | aplicado |
| 8 | Declarar condição kappa↔ICC; N_eff no subconjunto binário | zero | aplicado |
| 9 | Citação de par não conta como fundamento novo | zero | aplicado |
| 10 | Wilcoxon sobre `Δ_dispersão` | zero | aplicado |
| 11 | Texto defasado e aritmética amostral | zero | aplicado |
| 12 | Pré-registro externo datado | zero | decisão de execução, fora do repositório |

Os itens 1 a 6 somam menos de um dólar sobre o orçamento anterior e, com exceção do 3, não exigem engenharia.

## 6. Avaliação de conjunto

A tese é executável e o desenho é mais cuidadoso que a média do que se publica sobre debate multiagente — B2 sozinho já a coloca acima de boa parte da literatura de conformidade em LLM.

Os defeitos que importavam eram G1 (estimando trocado), G3 (controle que controla duas coisas) e G4 (piso que não é piso). Os três tinham correção barata, e G4 se corrigiu removendo material.

O ponto de fragilidade estrutural é outro e não estava escrito em lugar nenhum: **o subconjunto com gabarito é a parte que sustenta o número e era tratado como complemento** — doze itens, alguns fáceis demais, um ambíguo, sem piloto de dificuldade previsto. Se `ρ̄_erro` não sair estimável, a tabela de sensibilidade perde a âncora empírica e a metade analítica vira exercício algébrico. Inverter a prioridade entre os dois bancos foi a decisão de projeto mais consequente desta revisão.
