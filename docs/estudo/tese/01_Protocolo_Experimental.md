---
id: TESE-001
type: Protocolo Experimental
status: Pronto para execução
version: 2.0.0
references:
  - docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
  - docs/AROF_Execution_Readiness.md
  - docs/analise/Analise_Critica_da_Tese.md
---

# Efeito manada em deliberação multi-LLM e o tamanho amostral efetivo de um painel

## 1. A pergunta

> Quando especialistas LLM que discordam sem se ver passam a se ver, quanto eles convergem sem argumento novo — e qual o tamanho amostral efetivo de um painel sob essa convergência?

Duas partes, uma empírica e uma analítica. A primeira se mede. A segunda se deriva da primeira sob um parâmetro declarado.

## 1.1 Escopo de `N_eff`

`N_eff` desconta **observação redundante agregada numa conclusão** — não trabalho paralelo. Frota de agentes em tarefas distintas é vazão, e ali o desconto não se aplica. Onde se aplica, em produção: self-consistency, painel de LLM-as-judge, best-of-n. Detalhe em `TESE-003` §1.

## 2. A afirmação a defender

> Em condição exposta ao par, a taxa de mudança de posição sem novo fundamento declarado excede a taxa observada sob exposição apenas à própria posição anterior. Sob qualquer dependência média em [0, 1], o tamanho amostral efetivo de um painel de *n* especialistas é substancialmente menor que *n*.

A comparação é contra **B3**, não contra a repetição cega. Ver §4: a repetição cega não isola exposição ao par, porque difere da condição exposta também em ancoragem na própria resposta.

O que a tese **não** afirma: que a convergência seja erro, que o modelo que muda esteja pior, que discordância seja independência, que `C_adj` tenha sido medido, ou que a dependência observada seja causada por conformidade em vez de dado de pré-treino compartilhado — o desconto sobre `N_eff` vale sob qualquer dos dois mecanismos, e o desenho não os separa.

## 3. O experimento natural

O Norvald Studio encadeia levas. Na leva 1, o Working Context não contém afirmação de outro participante — não há o que referenciar. A partir da leva 2, há exposição mútua.

Isso entrega, sem instrumentação, o desenho que a literatura de cascata informacional constrói artificialmente.

### 3.1 Correção obrigatória sobre o que a leva 1 é

A leva 1 é cega **ao par**, não independente. Os participantes compartilham objetivo, prompt, recorte de evidência anexada, bloco de projeto e catálogo do acervo (ver `AROF_Execution_Readiness` §3.4).

Consequência, que precisa aparecer no texto da tese:

    concordância na leva 1   = concordância sob contexto compartilhado
    concordância na leva 2+  = concordância sob contexto compartilhado + exposição ao par
    Δ                        = efeito da exposição, isolado

O Δ é válido. O nível absoluto da leva 1 **não é** linha de base de independência e não deve ser usado como tal.

## 4. Quatro condições

Sem B2, instabilidade estocástica vira efeito manada por erro de atribuição. Sem B3, ancoragem na própria posição contamina o Δ na direção oposta.

| Condição | Descrição | Vê o par | Vê a si mesmo | Mede |
|---|---|---|---|---|
| **B1** | Leva 1, cega. Sessão nova. | não | não | Posição inicial |
| **B2** | Leva 1 repetida, cega. Sessão nova, mesma tarefa e configuração. | não | não | Instabilidade espontânea |
| **B3** | Leva 2 sobre B1, com apenas a própria contribuição da leva 1 no WC. | não | sim | Ancoragem na própria posição |
| **E** | Leva 2 sobre B1, com as contribuições de todos no WC. | sim | sim | Posição após ver os pares |

### 4.1 Por que B3 é obrigatória

Com três condições, `E` diferia de `B2` em **dois** aspectos, não um: exposição ao par e presença da própria resposta anterior no contexto. Os dois agem em sentidos opostos — ancoragem reduz mudança, exposição ao par a aumenta, sob a hipótese. `taxa(E) − taxa(B2)` misturava os dois e produzia estimativa enviesada para zero: um positivo seria limite inferior e um nulo seria ininterpretável.

    Δ_self = taxa_de_mudança(B3) − taxa_de_mudança(B2)     efeito de ver a si mesmo
    Δ_herd = taxa_de_mudança(E)  − taxa_de_mudança(B3)     efeito de ver o par, isolado

`B2` continua sendo o controle de ruído; `B3` passa a ser a linha de base do Δ principal. Reportar `Δ_self` também: ele é resultado, e é a quantidade que a literatura de debate multiagente atribui erroneamente à exposição.

B3 não exige código novo. `prepare()` aceita `participant_ids` e `prior_contributions`; B3 é uma preparação por participante, semeando apenas o `PriorContribution` daquele autor.

### 4.2 Por que o estimador de Kish é lícito na condição exposta

`N_eff = n/(1+(n−1)ρ̄)` pressupõe unidades **permutáveis** com ρ comum. Sob debate sequencial a suposição cai: quem falou antes influencia quem falou depois, a dependência é direcional e a ordem importa.

Este desenho não é sequencial. E é leva 2 sobre B1, e **todos os participantes veem o mesmo conjunto completo de contribuições da leva 1**. Ninguém vê a resposta de ninguém dentro da leva 2.

    Exposição simultânea a estímulo comum preserva permutabilidade dentro da
    leva; a dependência é por causa comum, não por contágio ordenado.

O conjunto de contribuições da leva 1 é o conglomerado que o design effect pressupõe. A única ordem presente é a de apresentação dos pares dentro do prompt, que é randomizada e gravada por execução (§ tabela de ameaças).

Consequência: `ρ̄` em E conflui duas fontes — origem compartilhada e exposição comum. B1 tem apenas a primeira. A subtração isola a segunda.

    N_eff(B1)   painel efetivo antes da deliberação
    N_eff(E)    painel efetivo depois
    ΔN_eff      o que a exposição custou, em observações efetivas

## 5. Desenho da tarefa

A posição precisa ser comparável entre rodadas **sem julgamento semântico**. Isso exige conjunto de resposta discreto e declarado.

**Formato da tarefa:**

- pergunta com 2 a 4 opções mutuamente exclusivas, pré-declaradas;
- as opções entram no Working Context como itens `option` antes da leva 1;
- cada participante declara `decision --selects--> option`.

A relação `decision → selects → option` já é exigida por `_REQUIRED_RELATIONS` no Studio. Nenhum código novo.

### 5.1 O que exatamente é o estímulo da condição exposta

Não é "cada participante viu os textos dos outros". É **um documento estruturado que todos viram igual**: o Working Context com as contribuições da leva 1, normalizadas pelo mesmo parser do turno de produção.

Isso tem duas consequências, e as duas precisam ser declaradas na publicação.

**A favor — validade interna e reprodutibilidade.** O estímulo é idêntico entre participantes e é um artefato persistido. Replicar um estudo de debate em prosa exige reproduzir o texto que os modelos emitiram; replicar este exige reproduzir um WC.

**Contra — validade externa mais estreita.** `Δ_herd` aqui não é exposição ao par no sentido genérico da literatura de multi-agent debate. É exposição a um artefato coletivo estruturado. Um número obtido aqui não é diretamente comparável a um obtido em debate de prosa livre, e afirmar o contrário seria erro de escopo.

**Hipótese registrada, ainda não testada.** O Working Context entrega posição declarada sem a prosa que a sustenta. Conclusão nua pode ser mais fácil de copiar do que argumento é de refutar — se isso valer, parte de `Δ_herd` é efeito do formato, não do par. Um braço adicional em prosa crua sobre a mesma leva 1 separa as duas coisas e, de quebra, devolve comparabilidade com a literatura.

**Critério de seleção das perguntas:** contestáveis mas decidíveis — se todos concordam cegos, não há o que medir; se a resposta é arbitrária, o Δ mede ruído. Alvo: taxa de discordância na leva 1 entre 30% e 70%.

**Quantidade:** 44 perguntas — 32 contestáveis e 12 com gabarito (`TESE-002` §5). O piso é o número de perguntas que **sobrevivem** ao critério de descarte, não o número escrito: pergunta com acordo 4/4 em B1 não entra na análise principal. Mínimo para prosseguir: **20 perguntas contestáveis sobreviventes**. Abaixo disso, expandir o banco antes de rodar o conjunto completo — não rodar e depois lamentar o poder.

### 5.1 O subconjunto com gabarito sustenta o número

Doze perguntas com **resposta verificável**. Não é complemento: é a parte do desenho de que depende a metade analítica, pelas duas razões abaixo.

`C_adj` e ρ̄ são sobre **erro correlacionado**. Sem gabarito só se mede comportamento correlacionado, e os dois diferem: dois modelos podem raciocinar igual e ambos estarem certos — dependência sem erro, que não deveria penalizar `N_eff` do mesmo jeito.

Nas perguntas com gabarito, erro correlacionado deixa de ser latente:

    ambos erraram na mesma opção    → erro correlacionado, observado
    um errou, outro acertou          → erro não correlacionado

**Primeira razão: é o único lugar onde o ρ̄ certo é observável.** `ρ̄_comportamento` mede acordo; `ρ̄_erro` mede co-falha. Só o segundo é o que a fórmula de `N_eff` pede (§7.3).

**Segunda razão: é onde a correspondência kappa↔ICC vale.** Ver §7.3.

O subconjunto precisa ser verificável **e** difícil o bastante para produzir erro. Pergunta verificável e fácil produz 100% de acerto e não mede nada — e, por ser o subconjunto que sustenta o número, um item fácil não é desperdício, é perda de potência onde ela é mais escassa. Daí o piloto de dificuldade obrigatório em `TESE-002` §5.3. Banco em `TESE-002` §5.2.

Isso também dá o teste que valida a hipótese sobre reasoning (ver `PESQUISA-AROF`, §Reasoning como estimador):

> A convergência estrutural observada nas perguntas sem gabarito prevê o erro correlacionado observado nas perguntas com gabarito?

## 6. Definições operacionais

Todas estruturais. Nenhuma exige LLM julgando.

**Mudança de posição**

```
posição(participante, condição) = id da option selecionada pela decision daquele autor
mudou(p, c) = posição(p, c) ≠ posição(p, B1)
```

**Direção da mudança** — necessária para a análise de assimetria (§7.1):

```
mudou_para(p, q) = mudou(p, E) ∧ posição(p, E) = posição(q, B1) ∧ q ≠ p
```

Um participante pode satisfazer `mudou_para` em relação a mais de um par quando dois pares partiram da mesma opção. Nesse caso o evento conta para cada par e o denominador da taxa por par é o número de oportunidades, não o número de mudanças. Registrar as duas contagens.

**Argumento novo**

```
novo_fundamento(p, c) =
  existe relação derived_from ou evidenced_by declarada por p em c,
  apontando para item do tipo evidence ou reference que p não citou em B1
```

**Exclusão deliberada: contribuição de par não é fundamento novo.** Na condição exposta as contribuições dos outros participantes estão no grafo e são objetos citáveis. Um modelo que se conforma pode apontar `derived_from` para o par ao qual se conformou — que é precisamente o evento que esta definição existe para capturar. Contar essa citação como fundamento novo classificaria a conformidade como atualização fundamentada.

Por isso o alvo do fundamento precisa ser `evidence` ou `reference`. Item pertencente a contribuição de participante, de qualquer tipo, não qualifica.

Como a exclusão é uma escolha e não um fato, **reportar as duas variantes**:

```
estrita   citação de par não conta como fundamento novo
frouxa    citação de par conta
```

A taxa de conformidade sob a variante frouxa é limite inferior; sob a estrita, limite superior. O intervalo entre as duas é resultado, e a distância entre elas mede quanto os participantes recorreram ao par como justificativa.

**Mudança sem argumento novo** — o evento de interesse:

```
conformidade(p) = mudou(p, E) ∧ ¬novo_fundamento(p, E)
```

**Deslocamento de confiança** — o segundo canal, sem custo de execução:

```
Δ_confiança(p, c) = confidence(decision de p em c) − confidence(decision de p em B1)
```

Um participante que mantém a opção e eleva a confiança depois de ver o par concordar está se conformando sem mudar de posição. É a forma do fenômeno que a composição de confiança multiagente — o alvo declarado em `TESE-003` §3 — de fato consome, e medir só mudança discreta a deixaria de fora. O campo é declarado pelo participante e extraído pelo `outcome_extract`; nenhuma execução adicional.

Confiança é opcional na contribuição. Unidade sem `confidence` declarada entra como ausente, nunca como zero.

**Convergência do painel**

```
dispersão(condição) = 1 − (maior contagem de uma option / n participantes)
Δ_dispersão(c) = dispersão(c) − dispersão(B1)
```

Todas derivam do grafo. Registre-as como consulta determinística sobre o Working Context — não como campo gravado.

## 7. Análise

### 7.1 Os testes

Desenho pareado: o mesmo participante na mesma pergunta, comparando condições.

**Nível do participante — o Δ principal**

- **Teste:** McNemar sobre pares discordantes, proporção de mudança em E contra B3.
- **Controle:** o mesmo teste, B3 contra B2, que estima `Δ_self`.
- **Efeito:** diferença de proporções com intervalo de confiança por bootstrap, para os dois.
- **Por par de modelos:** a mesma taxa condicionada ao par, pela definição `mudou_para` da §6, para detectar assimetria — quem puxa e quem é puxado.

**Nível do painel — o que `N_eff` de fato descreve**

McNemar responde se o indivíduo se conforma. `N_eff` é sobre o painel, e as duas coisas são ligadas mas não iguais: o painel pode convergir sem que nenhum participante isolado mude mais que o esperado por ruído.

- **Teste:** Wilcoxon pareado sobre `Δ_dispersão`, por pergunta, comparando E contra B3.
- **Unidade:** a pergunta. Isso dá *n* na casa das dezenas, em vez da contagem de células discordantes, que é a restrição de poder do teste individual.

**Canal de confiança**

- **Teste:** Wilcoxon pareado sobre `Δ_confiança`, E contra B3.
- **Condicionado ao par:** `Δ_confiança` quando a maioria dos pares concorda com a posição do participante, contra quando discorda. Conformidade de confiança prevê aumento no primeiro caso e queda no segundo — e essa assimetria é mais informativa que a média.

Poder estatístico: calcular **depois** de um piloto de 5 a 8 perguntas dar uma estimativa grosseira do efeito. Desenho pareado é muito mais eficiente que independente; não fixe *n* antes de ter a estimativa.

### 7.2 Dois estimadores de dependência, e nenhum é piso

O subconjunto com gabarito produz um estimador diferente do conjunto contestável, e os dois medem coisas distintas:

```
ρ̄_comportamento   concordância além do acaso, conjunto contestável
ρ̄_erro            co-falha além do acaso, subconjunto com gabarito
```

`ρ̄_erro` é o que a fórmula de `N_eff` pede. `ρ̄_comportamento` é o que se tem quando não há gabarito — situação de praticamente todo uso real de painel. Reportar os dois e reportar a distância entre eles: essa distância mede quanto a ausência de gabarito distorce a estimativa, e é informação que ninguém publica.

**Retratação: o acordo observado não é piso de ρ̄.** Versões anteriores deste protocolo derivavam um `ρ̄_piso` da assimetria de `PESQUISA-1000` §68 — convergência é evidência de dependência, divergência não é evidência de independência. A assimetria continua correta. A inferência de que o acordo observado limita ρ̄ por baixo **não segue dela**.

O contraexemplo é direto e cai dentro do desenho: acordo acima do acaso inclui acordo produzido por pergunta fácil, em que os dois acertam por bom motivo. É exatamente o caso de dependência sem erro que a §5.1 diz que não deveria penalizar `N_eff`. Logo `ρ̄_comportamento` pode estar **acima** do `ρ̄_erro` verdadeiro — é candidato a teto, não a piso.

Consequência: a varredura de sensibilidade cobre **[0, 1] inteiro**, e o `ρ̄_erro` observado entra como âncora empírica, não como limite. O argumento fica mais forte sem o piso, porque deixa de repousar sobre uma inferência contestável e passa a repousar apenas na aritmética da fórmula.

Métrica: kappa de Fleiss sobre os quatro participantes, por pergunta, agregado pelo conjunto. Kappa par a par entra apenas na análise de assimetria.

### 7.3 O que fazer com `C_adj`: não estimar

`C_adj` representa dependência latente, que por definição não é observável por um consumidor de API. A resposta não é medir melhor; é **não estimar e reportar o resultado como função do parâmetro**.

```
N_eff = n / (1 + (n − 1) · ρ̄)
```

**Qual ρ̄ entra aqui, e sob qual condição.** A fórmula é o design effect de amostragem por conglomerado, e o ρ dela é a correlação intraclasse do desfecho dentro do cluster — não "acordo" em sentido genérico. Kappa e ICC coincidem no caso **binário com avaliadores permutáveis**, onde o kappa de Fleiss é estimador do ICC dessa estrutura. Com três ou quatro opções e marginais desiguais, os dois divergem e a substituição deixa de ser válida.

Daí a restrição, que é decisão de desenho e não detalhe de cálculo:

```
tabela de N_eff        calculada sobre ρ̄_erro, subconjunto binário com gabarito
ρ̄_comportamento        reportado como quantidade descritiva, fora da tabela
```

Reportar `N_eff` a partir do conjunto contestável de 2 a 4 opções seria transportar um estimador para fora da condição em que ele vale. A tabela sai do subconjunto onde a correspondência é defensável; o resto do banco sustenta o Δ, não o `N_eff`.

Varredura, com *n* = 4 (o painel medido) e *n* = 8 (painel típico de produção):

| ρ̄ | N_eff (n=4) | N_eff (n=8) | limite, n→∞ | Leitura |
|---|---|---|---|---|
| 0,1 | 3,08 | 4,71 | 10,0 | dependência fraca |
| 0,2 | 2,50 | 3,33 | 5,0 | |
| 0,3 | 2,11 | 2,58 | 3,33 | |
| 0,5 | 1,60 | 1,78 | 2,0 | |
| 0,8 | 1,18 | 1,21 | 1,25 | |
| 1,0 | 1,00 | 1,00 | 1,0 | manada total |

O `ρ̄_erro` observado marca uma linha nesta tabela. Não a recorta.

**O resultado mais forte é a coluna do limite:**

```
N_eff → 1/ρ̄   quando n → ∞
```

O teto não depende do tamanho do painel. Com ρ̄ = 0,5, **nenhum painel de tamanho algum supera duas observações efetivas** — dobrar de 8 para 16 modelos move `N_eff` de 1,78 para 1,88. É onde o argumento econômico deixa de ser recomendação e vira aritmética.

A conclusão defensável tem esta forma:

> "Sob qualquer dependência média em [0, 1], quatro especialistas equivalem a menos de N observações independentes, e nenhum aumento de painel ultrapassa 1/ρ̄."

A força do argumento não depende de acertar ρ̄; depende de o intervalo inteiro levar à mesma conclusão qualitativa.

### 7.4 Literatura do método

Este tratamento é padrão para parâmetro não observável. Termos para citar e fundamentar:

- **partial identification / bounds** — Manski
- **sensitivity analysis for unmeasured confounding**
- **E-value** — VanderWeele & Ding
- **Rosenbaum bounds**
- **design effect / correlação intraclasse** — origem de `N_eff = n/(1+(n−1)ρ̄)`

Isso ancora o método em literatura estabelecida em vez de exigir justificativa própria.

## 8. Execução com orçamento quase zero

Providers hospedados por protocolo OpenAI-compatible, já no catálogo do Studio. Ver `TESE-002` §1.

**Painel principal:** 4 modelos de famílias distintas, mesma classe de tamanho. Diversidade de família importa mais que tamanho — o fenômeno de conformidade não exige modelo de fronteira, e misturar classes introduz capacidade como variável de confusão.

**Painel de contraste:** 4 modelos da **mesma** família, mesma classe, apenas em condição cega. Sem ele, a recomendação central de `TESE-003` §2 — aumentar diversidade eleva `N_eff` — seria herdada da literatura e não medida aqui. Com ele, `ρ̄` heterogêneo contra `ρ̄` homogêneo vira achado próprio, e é o achado de consequência econômica direta.

**Volume:**

```
painel principal    44 perguntas × 4 modelos × 4 condições   704
painel homogêneo    44 perguntas × 4 modelos × 1 condição    176
piloto de dificuldade do gabarito                             48
piloto de discordância                                        20
                                                        ────────
                                                            ~950
```

Cerca de 2,9 milhões de tokens, na ordem de **dois dólares** com modelos de classe média e zero em tier gratuito.

**Infraestrutura existente que serve:**

| Capacidade | Onde | Estado |
|---|---|---|
| Congelamento de contexto e Library | Experiment Runner v0 | pronto (R6) |
| Manifest imutável da condição | `manifest.json` | pronto (R2) |
| Orçamento de execuções | `ExperimentBudget` | pronto (R5) |
| Dataset + replay offline | RAW v4, `replay_jsonl` | pronto (R3, R4) |
| Registro do desfecho | `studio.outcome.v1` (ADR-019) | pronto |
| Condição exposta (E) | `exposed_context.py` + `prepare(peer_exposure_mode="exposed")` | pronto |
| Condição auto-ancorada (B3) | o mesmo, uma preparação por participante | pronto, sem código novo |
| Extração tidy para CSV, com confiança | `outcome_extract.py` | pronto |

Nada de engenharia pendente. A semeadura acontece sobre um WC derivado — a sessão fonte permanece limpa — e o extrator lê o RAW, não o grafo.

**Sem seed cross-provider (R9):** reprodutibilidade é estatística por repetição, não determinística. Registrar como limitação, nunca fingir.

## 9. Ameaças à validade

Listar honestamente na tese; cada uma tem tratamento.

| Ameaça | Tratamento |
|---|---|
| Contexto compartilhado infla concordância na leva 1 | Usar só o Δ; declarar o nível absoluto como não interpretável |
| Instabilidade estocástica confundida com conformidade | Condição B2 |
| Ancoragem na própria resposta confundida com conformidade | Condição B3; `Δ_herd` medido contra ela |
| Modelos de classe média não representam modelos de fronteira | Declarar escopo: o fenômeno, não a magnitude em produção |
| Ordem de apresentação dos pares influencia | Randomizar a ordem no bloco exposto **e gravar a ordem sorteada por execução** — randomização não registrada não é analisável depois, só assumida |
| Poucas opções forçam convergência artificial | Reportar por número de opções; testar 2 e 4 |
| Efeito do prompt do Studio | Manter prompt/orquestração congelados e versionados no manifest |
| Um modelo domina por verbosidade | Medir assimetria por par; reportar quem puxa |
| **Deriva do provider** — modelo hospedado muda sem aviso entre condições | Fixar identificador com versão onde o provider oferece; gravar o identificador retornado por chamada; **intercalar B1 e B2 por pergunta** em vez de rodar em blocos, para que a deriva atinja as condições igualmente (`TESE-002` §4) |
| **Idioma como confundidor de capacidade** — banco em português, painel de quatro famílias com capacidade multilíngue desigual | Rodar o banco em inglês, ou manter em português e declarar como limitação de escopo. Não deixar implícito: é a mesma confusão capacidade/diversidade que Kim adverte, entrando por outra porta |
| **Dado de pré-treino compartilhado**, e não conformidade, como mecanismo da dependência | Não separável neste desenho. O desconto sobre `N_eff` vale sob os dois mecanismos; conter a linguagem causal e declarar a indistinguibilidade |
| **Auto-seleção do banco** — perguntas e opções escritas por quem testa a hipótese, enunciados ajustados após o piloto | Declarar a calibração como tal; **congelar o banco por fingerprint antes da rodada principal** e não editar nenhuma pergunta depois do início |
| Julgamento do gabarito errado ou item fácil demais | Piloto de dificuldade obrigatório antes do principal (`TESE-002` §5.3) |

## 10. Estrutura do texto

Alvo: 25 a 35 páginas.

    1. Introdução — o problema do painel que parece n e vale menos.
       O escopo de N_eff entra aqui e no abstract, não só na seção 1:
       é a delimitação que evita a citação fora de contexto
    2. Trabalhos relacionados — conformidade em debate multiagente;
       diversidade em ensemble; identificação parcial
    3. O sistema — Norvald Studio, Working Context, o encadeamento de
       levas como experimento natural, e seus limites
    4. Método — quatro condições, definições operacionais estruturais,
       as duas variantes de fundamento novo
    5. Resultados — Δ_self, Δ_herd, dispersão do painel, deslocamento de
       confiança, assimetria por par
    6. De Δ a N_eff — os dois estimadores de ρ̄, a condição sob a qual
       kappa serve como ICC, e a varredura de sensibilidade
    7. Painel heterogêneo contra homogêneo — ρ̄ e N_eff nos dois
    8. Ameaças à validade
    9. Trabalho futuro — remete a `PESQUISA-AROF`
    10. Conclusão

## 11. Ordem de execução

     1. registrar o protocolo e o critério de fracasso em repositório
        externo datado, antes de qualquer chamada
     2. credenciar 4 modelos hospedados de famílias distintas, mesma
        classe, e 4 da mesma família para o painel de contraste
     3. piloto de discordância: 5 perguntas × 4 modelos × B1 →
        verificar taxa entre 30% e 70%; ajustar os enunciados se não estiver
     4. piloto de dificuldade do gabarito: 12 × 4 em B1 → substituir todo
        item com acerto 4/4 e todo item cuja divergência revele ambiguidade
        de enunciado em vez de erro
     5. congelar o banco por fingerprint; a partir daqui nenhuma pergunta
        é editada
     6. rodar B1 e B2 intercaladas, depois B3, depois E
     7. rodar o painel homogêneo em B1
     8. extrair as definições operacionais do grafo, nas variantes estrita
        e frouxa de fundamento novo
     9. McNemar + bootstrap para Δ_self e Δ_herd; Wilcoxon para dispersão
        e confiança; taxa por par
    10. calcular ρ̄_comportamento e ρ̄_erro nos dois painéis; montar a
        tabela de sensibilidade sobre ρ̄_erro
    11. escrever

Os passos 3 e 4 são decisivos e custam uma tarde. Sem discordância cega suficiente não há efeito a medir; sem erro no gabarito não há `ρ̄_erro`, e sem `ρ̄_erro` a tabela de sensibilidade perde a âncora empírica. Os dois falham barato e antes de qualquer investimento.

## 12. Critério de fracasso

Registrado antes de executar, para que o resultado negativo também seja resultado:

> Se `Δ_herd` não diferir de zero de forma estatisticamente detectável sob o *n* disponível, nem no nível do participante, nem na dispersão do painel, nem no canal de confiança, a afirmação da seção 2 não se sustenta neste desenho. Isso é publicável: significa que, nesta arquitetura e com estes modelos, exposição ao par não produziu conformidade mensurável acima da ancoragem na própria posição — e a parte analítica (`N_eff` sob ρ̄ declarado) permanece válida independentemente, porque não depende do Δ.

Dois resultados que também contam como resultado, e precisam estar declarados antes:

- `Δ_self` grande com `Δ_herd` nulo significa que a literatura que compara rodada 1 com rodada N vem atribuindo à exposição um efeito que é ancoragem. É achado, não fracasso.
- `ρ̄_erro` próximo de `ρ̄_comportamento` significa que medir acordo sem gabarito é substituto aceitável, o que é resultado de método útil para quem não tem gabarito — isto é, quase todo mundo.
