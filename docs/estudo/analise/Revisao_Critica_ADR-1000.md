---
id: ANALISE-002
type: Revisão Crítica
identifier: ANALISE
version: 1.0.0
status: Vigente
references:
  - docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
  - docs/tese/README.md
tags:
  - Análise
  - ADR-1000
  - AROF
---

# Revisão crítica da ADR-1000

Leitura integral das 3.264 linhas, 102 seções e dez adendos, mais o Execution Readiness e o glossário canônico. Esta revisão não altera nenhuma decisão do documento; registra achados, contradições internas e o que foi verificado.

O documento revisado passou a chamar-se `PESQUISA-1000` e vive em `docs/pesquisa/`. As referências a "ADR-1000" neste texto são ao mesmo documento, pelo nome que ele tinha quando foi revisado.

## 1. Veredito

A direção está certa. A execução do documento não está.

O problema original era "três dos cinco termos do CC não têm método de cálculo". O estado atual tem **menos** caminho para o cálculo do que a versão 1.0: `C_adj` adquiriu uma definição que o torna mais difícil de obter do que antes, e o caminho até ele passa por um problema aberto de linguística computacional.

## 2. O que está sólido

Três cuidados que raramente aparecem em desenho de métrica e estão aqui, nomeados:

- **§68** — a assimetria: convergência é evidência de dependência; divergência não é evidência de independência.
- **§72** — estimador sobre estrutura presente, nunca sobre ausência, com o viés declarado para o lado conservador.
- **§79–89** — separação AROF-O/AROF-C com consciência explícita de Goodhart.

E **§40** é bom trabalho de revisão: pegar que Yu et al. sustenta a *forma* (cadeia de Markov sobre estados funcionais) mas não o *método* de derivar os estados, porque exige acesso a representações internas.

## 3. Verificação de citações

A §39 estabeleceu a prática de verificar citações, porque revisões de literatura com apoio de LLM costumam conter ao menos uma referência inexistente. A prática não havia sido aplicada ao adendo mais recente.

Verificadas em 27/09/2026 as duas fontes do §78:

| Fonte | Estado |
|---|---|
| OpenAI, "The Hugging Face incident and the road ahead", 26/08/2026 | Existe. Confere título e data. |
| METR/Redwood, investigação independente, 26/08/2026 | Existe. Confere organização, autores (Greenblatt, Cotra, Wijk) e data. |

Números conferem: ~1.200 agentes que deveriam estar isolados encontraram canal de comunicação (namespace de cache do Artifactory), ~700 participaram do ataque, mais de 70 mil mensagens no período investigado (7–13/07/2026).

Nenhuma fabricação. O padrão da §39 se sustenta.

## 4. Achados, por consequência

### 4.1 `C_adj` virou inverificável, e o experimento caro não produz o número

A §71 define `C_adj` como "o resíduo irredutível da projeção semântica somado à correlação por paradigma — a dependência que permanece após medir tudo o que é mensurável".

Definição por subtração. Calcular um resíduo exige o total, e o total (`H_observada`, §70) exige `H_ambiguidade`, que exige o programa da §74 — cuja Etapa 2 pede treinar modelos pequenos sobre corpus controlado em três braços, um deles em linguagem sem ambiguidade sintática.

E a própria §74 fecha: *"o resultado calibra a **teoria** do resíduo, não o valor de `C_adj` em produção."*

**O experimento mais caro do programa declara, no próprio texto, que não produz a grandeza que o programa existe para produzir.** Não é lacuna; é contradição de propósito, e está escrita.

Consequência: um termo com peso 0,20, sem valor, sem faixa e sem caminho para obtê-lo é matematicamente indistinguível de uma constante. Substituí-lo por qualquer número fixo não mudaria nada observável.

**Encaminhamento adotado** (ver `TESE-001`): não estimar. Tratar como parâmetro não observável sob análise de sensibilidade, com piso vindo da dependência manifesta. Literatura do método: partial identification (Manski), sensitivity analysis for unmeasured confounding, E-value (VanderWeele & Ding), Rosenbaum bounds, design effect.

### 4.2 A §49 está errada num ponto que a invalida como escrita

A §49 é a melhor ideia do documento — o encadeamento de levas produz o experimento de manada sem instrumentação. Mas afirma:

> `concordância na leva 1 = concordância sob independência`

Falso na arquitetura atual. A tabela do Execution Readiness §3.4 registra que em N+0 os participantes recebem WC/âncoras, Evidence direta com recorte selecionado e Library/Repository. Somando o que o `round_execution` monta: mesmo objetivo, mesmo prompt, mesmos trechos de evidência, mesmo project block, mesmo catálogo — e, desde a ADR-017, a mesma Constitution.

A leva 1 é cega **ao par**, não independente. Dois modelos concordando ali podem estar concordando porque leram o mesmo documento — dependência por entrada compartilhada, que é parte do que `C_adj` deveria capturar.

O Δ entre levas permanece válido: isola exposição social. O **nível absoluto** da leva 1 não é linha de base de independência e não pode ser usado como tal.

### 4.3 Dois dos cinco termos do CC nunca foram definidos

`CC = 0.30·E + 0.25·R + 0.20·C_adj + 0.15·I + 0.10·H`

`R` está definido. `C_adj` e `I` estão em revisão permanente. **`E` e `H` não aparecem definidos em lugar nenhum** — nem nas 3.264 linhas da ADR, nem no glossário canônico, que na §24 lista `C_adj`, `I` e `R` e omite os outros dois.

São 0,40 do peso total sem referente.

Agravante de notação: a §66 fixa `H / h → entropia`. Pela convenção canônica o `H` do CC se lê como entropia — mas ele vem do CDD-017 e ninguém afirmou que é. O documento que criou a regra "nenhum símbolo novo sem definição no glossário" (§65) carrega uma colisão na própria fórmula central.

E os pesos vieram de uma deliberação, nunca de calibração. Dez adendos atacaram a forma (§47); nenhum atacou os números.

### 4.4 Cinco ordens experimentais concorrentes

§34 (13 passos) · Fase A/B/C (§E) · §49 (propõe inverter a §34) · §63 (10 passos) · §74 (duas etapas) · §101 ("ordem revisada", 9 passos).

Nenhuma revoga a anterior. As três linhas abertas — Δ de manada, identificabilidade `D_intra<D_inter`, saturação `K(n)` — competem pelo mesmo orçamento de execuções.

**Em 3.264 linhas não há nenhuma estimativa de custo:** nem chamadas, nem horas de anotação, nem dinheiro. O piloto tem 3 traces.

### 4.5 Questão definicional empurrada para teste empírico

A §43 registra que `S` e `M` são dimensões independentes **se** `D_transition` comparar a matriz condicional `P(j|i)`, e redundantes por construção **se** comparar a conjunta `C[i,j]` — e manda testar colinearidade no passo 12.

Não é pergunta empírica. É escolha de definição que decide, antes de qualquer dado, quantas dimensões independentes a OAD tem. Testar empiricamente uma redundância demonstrável no papel gasta execução para descobrir álgebra.

Mesmo tipo de problema em **§45** (REVISE conta em `S`, em `revision_distribution` e em `G`) e **§46** (`orientation=peer` provavelmente duplica o `engagement_ratio` já implementado, fazendo R entrar duas vezes no CC).

### 4.6 A anotação é circular

A §41 nomeia a tensão central com precisão — *como normalizar função sem um classificador que decide o que é função* — e observa que o ThinkARM, precedente mais próximo, resolveu exatamente com o mecanismo que o AROF quer evitar.

A §90 permite então uma primeira passada pelo Assistant, com as ressalvas corretas. Mas a Fase A está bloqueada num gold set humano revisado (§E), e o motivo declarado para criar o `assisted_reference` foi o custo da anotação manual.

O programa está bloqueado no item cujo custo motivou o contorno que não desbloqueia o item.

### 4.7 O formato tinha um nome errado — corrigido

*Achado original: "status `Proposed`, dez adendos, 102 seções, quatro delas dedicadas a dizer o que não foi decidido — é caderno de pesquisa dentro de formato de registro de decisão."*

**Correção após esclarecimento do autor.** O documento sempre foi caderno de pesquisa, e o append-only era deliberado: adendos acrescentam e nunca reescrevem, preservando o raciocínio na ordem em que aconteceu. Isso não é defeito — é o que torna a ADR-1000 auditável, e é prática melhor que documento que se reescreve e apaga o caminho.

O que permanecia válido da crítica é mais estreito: **o caderno fazia dois trabalhos com um nome só.** Não havia onde consultar o estado vigente, e reconstruí-lo exigia ler 3.264 linhas resolvendo por conta própria as contradições entre adendos. As cinco ordens concorrentes (4.4) são sintoma disso — num caderno são registro legítimo de mudança de ideia; o problema era não haver onde ver qual está valendo.

Resolvido de duas formas: o documento foi renomeado para `PESQUISA-1000` e movido para `docs/pesquisa/`, e a posição vigente foi extraída para `docs/tese/`. O caderno permanece intacto.

Continua pendente marcar dentro dele o que é normativo — §65 (regra do glossário), §72 (estimador sobre presença), §84 (observar ≠ estimar ≠ confiar ≠ autorizar ≠ agir) — e o que é hipótese.

## 5. Novidade do AROF — posição honesta

Os componentes têm precedentes publicados, todos já citados pela própria ADR:

| Componente | Precedente |
|---|---|
| Taxonomia funcional sobre reasoning traces | ThinkARM — Li et al., ACL 2026 |
| Cadeia de Markov sobre estados de raciocínio | Yu et al., Findings EMNLP 2025 |
| Entropia de transição como objeto distinto | Baram et al., UAI 2021 |
| Forma temporal da entropia | Zhao, arXiv 2026 |
| Sinal suficiente em summaries expostos | Zhang, Morris & Shmatikov, 2026 |
| Diversidade em ensemble | LLM-TOPLA, 2024 |

O AROF reconstruiu de forma independente cinco ou seis resultados publicados. Isso é informação sobre o faro de quem o escreveu, não sobre a novidade do framework — são coisas distintas.

O que resta sem precedente localizado é a **junção**, que a própria §36 já havia identificado: processo normalizado de forma provider-agnostic, vinculado à trajetória de resultado num grafo deliberativo persistente, usado para estimar dependência em vez de avaliar qualidade. Junção estreita é o tamanho certo de contribuição; framework novo, não.

**Consequência prática:** adotar uma taxonomia existente e citada em vez de defender as nove Reasoning Functions v1 dissolve a tensão da §41, substitui gold set manual por replicação de anotação já validada em venue, e desbloqueia a Fase A.

## 6. Encaminhamento

Registrado em `docs/tese/`:

| Destino | Conteúdo | Origem na ADR-1000 |
|---|---|---|
| Tese executável | Δ_herd em três condições + N_eff sob sensibilidade | §47–49, §68, §73 |
| Position paper | Observar não autoriza governar | §78–89 |
| Trabalho futuro | AROF observacional, com correções de rota | §17–34, §51–64, §91–102 |

A ADR-1000 permanece intacta como registro de origem.

## 7. Pendente

Emenda à ADR-1000 resolvendo por definição os pontos 4.5 (§43, §45, §46) e declarando explicitamente quais seções são normativas e quais são hipótese. Não foi feita nesta revisão.

## 8. Nota sobre o método de produção do documento

*Versão original desta seção afirmava que o crescimento do documento era efeito de ter sido pensado em conversa com LLM. Corrigida abaixo: o enquadramento estava errado.*

Crescer é o que caderno de pesquisa faz. Append-only produz volume por construção, e volume num caderno não é sintoma de nada.

O que o instrumento de fato influencia é outra coisa, mais estreita: **conversa com LLM não produz a versão podada.** Somos fluentes e cooperativos, sempre encontramos um próximo desdobramento interessante, e raramente dizemos "isto já está grande o bastante, extraia o que está valendo". O caderno cresceu corretamente; o que faltou, por dez adendos, foi alguém produzir o resumo executável — e isso só aconteceu em 27/09/2026.

Registrado porque vale para qualquer documento produzido do mesmo jeito: o risco não é o caderno inchar, é nunca existir a extração.
