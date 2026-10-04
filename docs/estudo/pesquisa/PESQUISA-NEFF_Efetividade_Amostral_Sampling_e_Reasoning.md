---
id: PESQUISA-NEFF-SAMPLING
type: Anotação de Pesquisa
status: Linha aberta
version: 1.0.0
date: 2026-09-28
references:
  - docs/tese/01_Protocolo_Experimental.md
  - docs/tese/02_Mapa_de_Teste.md
  - docs/tese/03_Posicionamento_e_Procedencia.md
  - docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
  - docs/pesquisa/PESQUISA-AROF_Observabilidade_do_Raciocinio.md
---

# N_eff, AROF, sampling e efetividade amostral em sistemas LLM

> Anotação consolidada da discussão de 28/09/2026 sobre o potencial científico e prático de N_eff, sua relação com AROF e CC, parâmetros de inferência, desenho experimental, reasoning e inference-time scaling.
>
> Esta nota separa explicitamente três camadas: o que já está sustentado nos documentos do Norvald; o que vem da literatura externa; e o que surgiu como hipótese durante a discussão. Hipóteses novas não são tratadas como resultados.

## 1. Ponto de partida

A discussão começou por uma questão de posicionamento do Norvald Studio: além das capacidades gerais do produto — deliberação multi-modelo, agentes, Working Context, Evidence, Constitution, Repository, artefatos, infraestrutura documental e demais componentes — existe alguma capacidade suficientemente própria para constituir um diferencial metodológico real?

O primeiro candidato foi N_eff.

A hipótese inicial era que o Studio poderia distinguir o número nominal de agentes, respostas ou execuções da quantidade efetiva de observações não redundantes que esse conjunto representa.

A conversa evoluiu da comparação comercial para uma questão mais importante:

> O N_eff pode ser uma contribuição metodológica útil para a comunidade de pesquisa, independentemente de ser ou não responsável por vender o Norvald Studio?

A resposta consolidada continua sendo sim, mas a revisão bibliográfica feita durante a própria consolidação encontrou um precedente direto que altera a reivindicação de novidade específica do uso de Effective Sample Size em painéis de LLMs. Essa correção está registrada na §8 e precisa ser refletida posteriormente em TESE-003.

## 2. Base documental do Norvald usada nesta análise

Foram usados como base os três documentos correntes da tese e o caderno de pesquisa anteriormente chamado ADR-1000.

### 2.1 TESE-001 — Protocolo Experimental

Arquivo: docs/tese/01_Protocolo_Experimental.md

Título: Efeito manada em deliberação multi-LLM e o tamanho amostral efetivo de um painel.

É o documento que estabelece a pergunta principal, as condições B1/B2/B3/E, a separação entre rho_comportamento e rho_erro, o uso do design effect e a aplicação de N_eff.

### 2.2 TESE-002 — Mapa de Teste

Arquivo: docs/tese/02_Mapa_de_Teste.md

Operationaliza a coleta: painéis heterogêneo e homogêneo, banco de perguntas, subconjunto binário com ground truth, pilotos, critérios de descarte, congelamento de parâmetros e execução experimental.

### 2.3 TESE-003 — Posicionamento e Procedência

Arquivo: docs/tese/03_Posicionamento_e_Procedencia.md

Delimita onde N_eff se aplica, sua consequência econômica, literatura adjacente e procedência do CC.

### 2.4 PESQUISA-1000 — antiga ADR-1000

Arquivo: docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md

É o caderno append-only que preserva a evolução da hipótese, autocríticas, reformulações de C_adj, I, efeito manada, AROF-O/AROF-C, variabilidade intra-modelo, saturação estrutural observada, N_sat^obs, K(n) e demais hipóteses abertas.

## 3. O constructo central de N_eff

A formulação utilizada é a clássica do design effect:

    N_eff = n / (1 + (n - 1) * rho_bar)

onde:

- n é o número nominal de observações;
- rho_bar representa a dependência/correlação média relevante;
- N_eff representa o número de observações independentes equivalente ao conjunto correlacionado.

A tese não propõe que a fórmula seja nova.

A contribuição inicialmente pretendida estava na ponte:

    painel de LLMs
        ↓
    correlação / co-falha
        ↓
    rho_erro
        ↓
    design effect
        ↓
    N_eff
        ↓
    quantidade efetiva de observações

A interpretação fundamental é:

    N nominal != N efetivo

Se dez execuções forem fortemente redundantes, não existe justificativa estatística para tratá-las como dez observações independentes apenas porque ocorreram dez chamadas à API.

## 4. O que N_eff não pretende medir

Durante a discussão tornou-se necessário separar grandezas que inicialmente podiam parecer próximas.

N_eff não pretende medir:

- qualidade;
- verdade;
- correção;
- utilidade;
- relevância;
- criatividade;
- profundidade;
- qualidade do reasoning;
- diversidade textual;
- diversidade semântica;
- diversidade estrutural por si só.

Ele caracteriza a efetividade amostral sob dependência para o desfecho que está sendo estudado.

Portanto:

    N_eff alto != respostas melhores

e:

    N_eff baixo != respostas ruins

Essa separação é coerente com o princípio do Norvald:

> Nós não julgamos; apenas analisamos.

O sistema pode informar que determinada configuração produziu maior ou menor efetividade amostral. O julgamento sobre se aquele material é bom, útil, correto ou apropriado continua pertencendo ao pesquisador/usuário.

Para publicação, é mais seguro falar em "quantidade efetiva de observações" ou "evidência não redundante segundo o desfecho definido" do que usar "quantidade de conhecimento" sem definição, porque conhecimento pode ser interpretado como conhecimento verdadeiro ou validado.

## 5. N_eff não é equivalente a diversidade semântica

No início da análise foi feita uma aproximação excessiva entre N_eff e métricas como Vendi Score. Essa aproximação foi rejeitada após a leitura integral da tese.

Chen et al., em Diversity Collapse in Multi-Agent LLM Systems, estudam diversidade efetiva, colapso de diversidade e convergência em sistemas multiagente. O objeto é a diversidade/estrutura das saídas, não o Kish ESS de erro correlacionado.

Referência: https://aclanthology.org/2026.findings-acl.13/

A pergunta de uma métrica de diversidade efetiva é aproximadamente:

    Quantos modos semanticamente distintos
    existem no conjunto?

O N_eff da tese responde outra pergunta:

    Quantas observações independentes equivalentes
    existem neste conjunto sob a dependência
    observada para o desfecho?

Consequentemente, pode haver:

    diversidade semântica alta
    rho_erro alto
    N_eff baixo

ou, em outro desenho:

    diversidade semântica baixa
    rho_erro baixo
    N_eff relativamente alto

A relação é empírica e dependente do desfecho; não há identidade definicional.

Esse ponto é central para não confundir diferença aparente entre respostas com independência estatística de erro.

## 6. Comportamento não é erro

A tese distingue explicitamente:

    rho_comportamento

de:

    rho_erro

Isso evita um erro conceitual importante.

Dois modelos podem concordar porque ambos estão corretos. Nesse caso existe concordância comportamental, mas não necessariamente co-falha.

Logo:

    agreement != error correlation

A versão anterior do protocolo chegou a considerar a concordância observada como possível piso de rho. Essa inferência foi posteriormente retraída.

O contraexemplo é direto:

- perguntas fáceis podem gerar forte acordo;
- o acordo pode ser produzido por acerto legítimo;
- esse acordo não deveria ser interpretado como erro correlacionado;
- portanto rho_comportamento não pode ser automaticamente usado como piso de rho_erro.

Essa retratação melhora o trabalho.

Ela também explica por que o subconjunto que sustenta numericamente N_eff é deliberadamente mais restrito:

    questões binárias
    + ground truth
    + erro observável
    + estrutura adequada à correspondência estatística utilizada

O restante do banco sustenta os experimentos comportamentais e Delta_herd, não necessariamente a tabela de N_eff.

## 7. B1/B2/B3/E e a decomposição da conformidade

A tese não reduz efeito manada a simples mudança de resposta.

As quatro condições são:

    B1
    primeira resposta, sem ver pares nem resposta anterior

    B2
    nova execução cega
    → estima instabilidade espontânea

    B3
    vê apenas a própria resposta anterior
    → estima self-anchoring

    E
    vê própria resposta + respostas dos pares
    → inclui peer exposure

Isso permite:

    Delta_self = mudança(B3) - mudança(B2)

e:

    Delta_herd = mudança(E) - mudança(B3)

A presença de B3 é importante porque E e uma repetição cega diferem em mais de uma variável.

Sem B3 seria possível confundir:

- instabilidade estocástica;
- ancoragem na própria resposta;
- exposição aos pares.

A literatura recente também trata decomposição de mudanças de posição. Not All Flips Are Conformity separa instabilidade espontânea, conformidade e persuasão em debate multiagente.

Referência: https://arxiv.org/abs/2606.00820

Portanto, decompor conformidade não é exclusividade do Norvald. A contribuição específica precisa permanecer na combinação entre desenho experimental, estrutura/proveniência do Working Context e sua relação com a dependência que depois interessa ao N_eff.

## 8. Correção bibliográfica crítica: existe precedente direto de Kish ESS em painéis LLM

Durante a preparação desta anotação foi localizado um trabalho que não havia aparecido na busca anterior e que altera o posicionamento corrente da tese.

Guneet Kohli publicou em 28/05/2026:

Nine Judges, Two Effective Votes: Correlated Errors Undermine LLM Evaluation Panels

Referência: https://arxiv.org/abs/2605.29800

O trabalho testa nove LLMs de sete famílias em tarefas de NLI e conclui que o painel fornece aproximadamente o equivalente a apenas duas observações/votos independentes.

Mais importante: o paper usa explicitamente Kish effective sample size:

    n_eff = k / (1 + (k - 1) * phi_bar)

onde phi_bar é a correlação média entre vetores binários de erro dos juízes.

O trabalho relata que nove juízes fornecem cerca de 2.18 votos independentes equivalentes. Também testa a robustez do déficit sob variações de prompt, temperatura, chain-of-thought reasoning e uma tarefa de preferência pareada.

Consequência direta:

A afirmação de TESE-003:

    ESS para painel de LLMs correlacionados → não encontrado

não pode permanecer como está.

Existe pelo menos um precedente direto.

Isso não significa que todo o programa da tese perdeu novidade.

Significa que a seguinte reivindicação não é mais sustentável:

> Aplicar effective sample size a um painel de LLMs com erros correlacionados é, em si, a contribuição inédita.

Kohli já faz isso explicitamente.

### 8.1 O que continua diferente no programa Norvald

O trabalho de Kohli concentra-se em LLM-as-a-judge, erro correlacionado e confiabilidade de votação.

O programa Norvald possui escopo mais amplo:

    dependência
    +
    herd effect
    +
    self-anchoring
    +
    deliberação exposta
    +
    estrutura/proveniência
    +
    AROF
    +
    operação futura sem ground truth
    +
    relação futura com CC

Além disso, o programa Norvald pretende investigar a questão em estruturas como:

- self-consistency;
- painéis LLM-as-judge;
- best-of-n;
- ensembles;
- deliberação multi-modelo;
- repeated reasoning / inference-time sampling.

A possível contribuição precisa, portanto, ser reposicionada.

Não:

> introdução de N_eff para painéis de LLMs.

Mas potencialmente:

> caracterização mais geral da efetividade amostral de sistemas LLM correlacionados, sua relação com exposição e conformidade, seu uso como instrumento experimental e sua eventual estimação em ambientes sem ground truth.

Essa diferença precisa ser demonstrada experimentalmente, não apenas declarada.

## 9. Effective channels: um vizinho conceitual importante

Yang et al., em Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity, mostram forte retorno decrescente na expansão de sistemas homogêneos e ganhos maiores com heterogeneidade.

Referência: https://arxiv.org/abs/2602.03794

O paper propõe que o desempenho depende menos da quantidade bruta de chamadas e mais do número de effective channels que introduzem evidência complementar. Introduz K*, um effective channel count label-free.

Conceitualmente:

    K*
    ≈ canais/direções não redundantes observáveis
    sem ground truth

enquanto:

    N_eff baseado em erro
    ≈ observações independentes equivalentes
    para um desfecho com erro observável

São vizinhos, não equivalentes.

Isso sugere um experimento especialmente interessante:

    K*
    vs.
    AROF observables
    vs.
    rho_erro real
    vs.
    N_eff

em tarefas nas quais ground truth esteja disponível.

Esse desenho permitiria verificar quais proxies carregam informação real sobre dependência de erro.

## 10. Erros correlacionados são um problema real

Kim et al., em Correlated Errors in Large Language Models, estudaram centenas de modelos e encontraram correlação substancial de erros.

Referência: https://proceedings.mlr.press/v267/kim25e.html

Isso sustenta a premissa central:

    modelos diferentes != erros independentes

A tese não precisa criar esse fenômeno.

O fenômeno está sendo empiricamente documentado.

O trabalho de N_eff precisa demonstrar o que acrescenta depois que essa premissa é aceita.

## 11. Diversidade não é suficiente

Donghwan Kim, em Are Diversity Metrics Measuring Diversity?, auditou 31.900 subconjuntos de LLMs e mostrou que algumas métricas de diversidade são fortemente confundidas com capacidade; após controle, permanece uma associação residual entre co-falha e ganho do ensemble.

Referência: https://arxiv.org/abs/2607.20768

Esse trabalho reforça a necessidade de separar:

    diversidade

de:

    dependência de erro

e dá suporte ao cuidado da tese em não usar diversidade semântica como substituto automático de rho_erro.

## 12. Aplicação econômica: desperdício computacional

Uma das primeiras consequências práticas discutidas foi simples:

> Por que testar 20 agentes se a passagem de 10 para 20 quase não aumenta a quantidade efetiva de observações?

A lógica não é:

    mais agentes não ajudam

mas:

    mais agentes
        ↓
    podem ajudar

    porém

    Delta N_eff
    pode ficar muito menor que
    Delta N nominal

A informação passa a ser:

    ganho nominal
    vs.
    ganho efetivo

Isso permite observar:

    N
    N_eff
    N_eff / N
    Delta N_eff / Delta N

e caracterizar quanto compute adicional realmente acrescenta observação efetiva.

N_eff não precisa concluir "pare de executar".

Ele apenas informa que o ganho efetivo daquela expansão foi pequeno ou grande.

A decisão continua com o pesquisador.

## 13. A conclusão econômica não é simplesmente "use menos"

A formulação "use menos agentes" é inadequada.

Um N_eff baixo pode levar o pesquisador a:

- reduzir chamadas;
- trocar modelo;
- trocar provider;
- diversificar prompt;
- variar sampling;
- alterar ferramentas;
- coletar evidência externa adicional;
- aceitar a redundância porque o domínio exige;
- continuar escalando mesmo com pequeno ganho marginal.

A métrica informa a estrutura.

Ela não prescreve a política.

Uma formulação mais adequada é:

> Não compre repetidamente a mesma evidência sem saber que está fazendo isso.

## 14. Temperature e top-p como variáveis experimentais

A discussão passou então a um ponto com potencial metodológico maior do que a simples economia de chamadas.

Temperature e top-p são parâmetros de sampling que alteram a distribuição das realizações produzidas pelo modelo.

Conceitualmente:

    temperature / top_p
            ↓
    distribuição de sampling
            ↓
    trajetórias / respostas observadas
            ↓
    dependência entre realizações
            ↓
    rho
            ↓
    N_eff

Isso sugere que N_eff pode ser utilizado para caracterizar empiricamente regimes de sampling.

Não para decidir se uma resposta é boa.

Não para declarar uma temperatura universalmente melhor.

Mas para responder:

> Sob este modelo, tarefa, contexto e configuração, como a efetividade amostral muda quando alteramos temperature ou top-p?

## 15. Correção de uma interpretação surgida durante a conversa: N_eff não julga qualidade

Em determinado momento foi sugerido:

    maximizar N_eff
    sujeito a um piso de qualidade

Essa formulação foi rejeitada porque introduz uma variável normativa que não pertence ao papel de N_eff nem ao princípio arquitetural do Norvald.

A formulação corrigida é:

> Caracterizar como os parâmetros de inferência alteram N_eff e disponibilizar esse dado para que o pesquisador escolha a configuração apropriada ao seu objetivo.

A separação fica:

    GERAÇÃO
    model / provider / temperature / top_p / prompt / n
                       ↓

    OBSERVAÇÃO
    correlação / redundância / N_eff / AROF
                       ↓

    JULGAMENTO
    relevância / correção / utilidade / qualidade
                       ↑
                     usuário

Isso mantém:

    observar != julgar

## 16. Ruído não invalida automaticamente a métrica

Foi levantada a objeção:

> Se eu aumentar muito a temperatura, posso gerar ruído, diminuir correlação e aumentar N_eff. Então a métrica estaria sendo enganada.

A resposta consolidada é: não necessariamente.

Se a dependência realmente caiu para o desfecho medido, N_eff deve registrar que as observações estão menos correlacionadas.

O erro só aparece se alguém concluir:

    menos correlação = maior qualidade

N_eff não faz essa afirmação.

Logo:

    independência alta != qualidade alta

da mesma maneira que:

    diversidade estrutural alta != independência epistemológica

Essa distinção precisa ficar explícita em qualquer publicação para evitar que N_eff seja interpretado como métrica de "melhor resposta".

## 17. Calibração experimental de sampling

Uma aplicação potencialmente relevante para engenharia experimental é usar N_eff para caracterizar configurações de inferência.

Primeiro:

    mesmo modelo
    mesmo prompt
    mesma tarefa
    mesmo contexto

    temperature variável
    top_p fixo

Depois:

    temperature fixa
    top_p variável

E somente então:

    temperature × top_p

observando, conforme o estágio da pesquisa:

    rho
    N_eff
    D_intra
    K(n)
    N_sat^obs
    custo

A razão para variar um parâmetro por vez inicialmente é experimental: se temperature e top-p forem alterados simultaneamente, a origem do efeito fica confundida.

A etapa posterior pode mapear:

    N_eff =
    f(modelo,
      provider,
      versão,
      tarefa,
      contexto,
      prompt,
      temperature,
      top_p,
      n,
      demais parâmetros)

O resultado não seria uma "temperatura ideal universal".

Seria um método de calibração contextual.

## 18. Por que isso pode melhorar a montagem de testes

Considere dois experimentos nominalmente balanceados:

    Modelo A
    30 execuções

    Modelo B
    30 execuções

O desenho parece simétrico.

Mas pode ocorrer:

    A → N_eff muito maior
    B → N_eff muito menor

Nesse caso:

    mesmo N nominal != mesma quantidade efetiva de observação

Isso pode ser metodologicamente importante.

Pesquisadores podem acreditar que deram o mesmo volume amostral a dois braços experimentais quando, sob dependência, a quantidade efetiva de observação é bastante diferente.

N_eff torna essa assimetria visível.

## 19. Saturação e ganho marginal

Outra consequência é acompanhar a curva:

    N
    ↓
    N_eff(N)

O interesse não é apenas o valor final.

É também o ganho marginal:

    Delta N_eff / Delta N

Se novas execuções continuam sendo adicionadas mas N_eff praticamente deixa de crescer, existe um dado objetivo de saturação efetiva para aquele constructo.

Isso pode informar — mas não determinar automaticamente — um critério de parada:

    mais amostras
        ↓
    recalcular N_eff
        ↓
    Delta N_eff pequeno por várias etapas
        ↓
    pesquisador é informado

O sistema não precisa decidir que o experimento "já é suficiente".

Essa conclusão é externa à métrica.

## 20. Relação com inference-time scaling

Muita pesquisa contemporânea escala:

    1 trajetória
    4 trajetórias
    8 trajetórias
    16 trajetórias
    32 trajetórias
    64 trajetórias

e mede accuracy, pass@k, majority vote, consistência, tokens e custo.

N_eff acrescenta outra dimensão:

> Quanto dessa expansão nominal realmente aumenta a amostra efetiva?

Um experimento poderia reportar:

    nominal samples: 64
    effective samples: X
    sampling configuration: ...

Isso ajuda a distinguir:

    compute scaling

de:

    effective observation scaling

## 21. Relação com redução de reasoning redundante

Efficient Test-Time Scaling via Temporal Reasoning Aggregation propõe detectar convergência ao longo de uma trajetória de reasoning e reporta redução de aproximadamente 25–30% de tokens, mantendo desempenho próximo ao reasoning completo.

Referência: https://aclanthology.org/2026.findings-acl.651/

Esse trabalho trata redundância dentro de uma trajetória temporal.

N_eff pode tratar uma questão complementar:

    redundância entre múltiplas amostras

Logo:

    reasoning interno
    → quando uma trajetória já convergiu?

    sampling externo
    → quando novas trajetórias deixam de
      acrescentar muita observação efetiva?

São níveis distintos de eficiência.

## 22. Relação com pesquisa estrutural de reasoning

TRACE: A Framework for Analyzing and Enhancing Stepwise Reasoning in Vision-Language Models investiga passos intermediários e consistência ao longo do reasoning.

Referência: https://aclanthology.org/2026.eacl-long.166/

Esse tipo de pesquisa aproxima-se do território conceitual do AROF: observar estrutura/processo em vez de apenas resultado.

A conexão potencial é:

    reasoning trace
          ↓
    representação estrutural
          ↓
    AROF
          ↓
    D_intra / D_inter
    K(n)
    N_sat^obs

comparado com:

    desfecho observável
          ↓
    co-falha
          ↓
    rho_erro
          ↓
    N_eff

A pergunta científica importante é:

> Certos padrões estruturais observáveis de reasoning predizem dependência de erro?

Essa relação precisa ser testada.

Não pode ser presumida.

## 23. Variabilidade intra-modelo, K(n) e N_sat^obs

A PESQUISA-1000 registra que uma mesma configuração pode produzir múltiplas trajetórias:

    T_r ~ P(T | M, C)

e que uma única execução não representa adequadamente todo o repertório observável de uma configuração.

Foram introduzidos:

    K(n)

como curva de descoberta estrutural, e:

    N_sat^obs

como saturação da novidade estrutural observada.

Isso se conecta diretamente aos parâmetros de sampling.

Uma expansão conceitual natural é:

    T_r ~ P(T | M, C, theta)

onde theta representa parâmetros de inferência/sampling.

Então é possível investigar:

    theta
      ↓
    D_intra
    K(n)
    N_sat^obs
    rho_erro
    N_eff

sem concluir automaticamente que qualquer configuração é melhor.

## 24. Diversidade estrutural e N_eff devem permanecer separados

A PESQUISA-1000 já contém uma salvaguarda importante:

    diversidade estrutural observada
    !=
    independência epistemológica

O mesmo vale para:

    N_sat^obs != N_eff

e:

    K(n) != N_eff

Um modelo pode produzir muitas formas distintas de reasoning que acabam cometendo os mesmos erros.

Ou pode produzir reasoning estruturalmente semelhante com erros pouco correlacionados em determinado desfecho.

A relação entre essas grandezas é objeto experimental.

Não identidade definicional.

## 25. Experimento forte: semantic diversity vs. effective independence

Single-Agent Generation Surpasses Multi-Agent Systems in Semantic Diversity encontrou, sob condições controladas, maior diversidade semântica em configurações single-agent do que em certas configurações multi-agent; a estratégia Multi-Output apresentou a maior diversidade entre as comparadas.

Referência: https://aclanthology.org/2026.findings-acl.1894/

Isso abre uma comparação:

                       Semantic diversity     N_eff

    single × N                  ?               ?
    multi-agent × N             ?               ?
    multi-output                ?               ?

A pergunta passa a ser:

> A configuração que produz maior diversidade semântica também produz menor correlação de erro?

Talvez sim.

Talvez não.

Qualquer resultado é informativo.

Essa é uma forma clara de demonstrar empiricamente que diversidade e independência não são sinônimos.

## 26. K*, AROF e ground truth

O trabalho de Yang et al. oferece uma oportunidade experimental importante.

A pesquisa Norvald pode confrontar:

    K*
    AROF
    Vendi Score
    outras medidas de diversidade

contra:

    rho_erro observado
    N_eff baseado em ground truth

O ground truth serviria como ambiente de calibração.

Depois seria possível investigar quais proxies mantêm informação útil quando o ground truth desaparece.

Essa direção é mais forte para AROF do que declarar antecipadamente que estrutura de reasoning equivale a independência.

## 27. AROF como possível ponte para ambientes sem ground truth

A principal limitação de N_eff forte baseado em erro é simples:

    para observar erro
    é necessário saber o que seria correto

Mas muitos usos reais de painéis LLM acontecem justamente porque não existe ground truth acessível.

AROF explora outra superfície:

    Reasoning Trace
          ↓
    observação
          ↓
    normalização
          ↓
    estrutura
          ↓
    redundância / complementaridade observável

A hipótese importante passa a ser:

> Essa estrutura observável contém informação suficiente para estimar ou predizer dependência relevante para N_eff?

O protocolo já contém uma pergunta diretamente relacionada:

> A convergência estrutural observada nas perguntas sem gabarito prevê o erro correlacionado observado nas perguntas com gabarito?

Se a resposta for positiva e generalizar:

    ambiente com ground truth
            ↓
    rho_erro real
            ↓
    N_eff observável
            ↑
            │ calibração
            │
    AROF observables
            ↓
    ambiente sem ground truth
            ↓
    estimativa de dependência

Isso tem potencial consideravelmente maior do que simplesmente aplicar o design effect.

## 28. AROF-O e AROF-C

A PESQUISA-1000 separa:

AROF-O:

    execução
    → observação
    → normalização
    → métricas
    → análise

AROF-C:

    execução
    → observação
    → métricas
    → decisão automática
    → alteração da população/orquestração
    → nova execução
    ↺

Validar AROF-O não valida automaticamente AROF-C.

Isso é importante especialmente se N_eff algum dia for utilizado para:

- interromper chamadas;
- convocar novos agentes;
- mudar modelo;
- mudar provider;
- mudar sampling;
- reorganizar ensemble;
- redistribuir orçamento.

A métrica informar a política é diferente da métrica possuir autoridade para executá-la.

A invariância permanece:

    observar
    !=
    estimar
    !=
    confiar
    !=
    autorizar
    !=
    agir

## 29. Relação com CC

O CC surgiu em CDD-017 como:

    CC = 0.30 E + 0.25 R + 0.20 C_adj + 0.15 I + 0.10 H

A documentação corrente reconhece que:

- a forma é um índice composto genérico;
- a decomposição é própria;
- os pesos foram elicitados, não calibrados;
- C_adj e I dependiam de informação sobre dependência entre modelos que o consumidor de API normalmente não possui.

A PESQUISA-1000 inicialmente explorou proxies como:

- família;
- provider;
- composição pública de treinamento;
- comportamento histórico;
- taxa de contestação.

Com AROF surge a possibilidade de observar externamente aspectos estruturais do reasoning.

Mas o caminho:

    AROF
    → dependência
    → CC

ainda é hipótese.

Ele precisa passar por:

    AROF observable
    vs.
    dependência realmente observada

antes de CC poder incorporar essas estimativas de maneira defensável.

## 30. Potencial científico após o precedente de Kohli

A descoberta de Nine Judges, Two Effective Votes reduz uma reivindicação de novidade, mas não destrói o programa.

O potencial científico deixa de ser:

> Ninguém aplicou Effective Sample Size a LLMs correlacionados.

Isso é falso.

O potencial passa a estar em perguntas mais profundas.

### 30.1 Generalidade

N_eff pode funcionar como medida experimental em:

- LLM-as-judge;
- self-consistency;
- best-of-n;
- repeated reasoning;
- multi-model ensemble;
- deliberação;
- multi-agent debate.

Ou o comportamento muda radicalmente conforme o regime?

### 30.2 Interação social

Como a exposição entre modelos altera a dependência?

    blind
    vs.
    self-anchored
    vs.
    peer-exposed

### 30.3 Sampling

Como temperature e top-p alteram a efetividade amostral?

### 30.4 Composição

Como modelo, família, provider, prompt, persona e tools alteram rho e N_eff?

### 30.5 Scaling

Como cresce:

    N_eff(N)

e onde aparecem retornos marginais pequenos?

### 30.6 Reasoning

A estrutura do reasoning permite antecipar correlação de erro?

### 30.7 Sem ground truth

É possível estimar dependência útil através de AROF ou outras medidas label-free?

### 30.8 Comparação com proxies existentes

Qual é a relação entre:

    Vendi Score
    K*
    embedding diversity
    AROF
    rho_erro
    N_eff

?

Esse programa continua rico mesmo sem exclusividade sobre a fórmula ou sobre a primeira aplicação de Kish ESS a painéis LLM.

## 31. Temperature já aparece no precedente direto — mas a pergunta pode ser diferente

Kohli relata que o déficit de independência permanece através de variações de temperatura.

Referência: https://arxiv.org/abs/2605.29800

Isso é particularmente relevante para a nova hipótese.

Não devemos assumir:

    temperature ↑
    → N_eff ↑

A relação precisa ser observada.

O resultado pode ser:

    temperature muda muito
    N_eff muda pouco

ou:

    existe uma região em que
    temperature altera fortemente N_eff

Ambos seriam informativos.

A diferença entre o precedente e a direção discutida aqui é de pergunta experimental:

- Kohli testa robustez do déficit a diferentes temperaturas;
- a hipótese emergente desta conversa propõe caracterizar a própria curva N_eff(temperature) e, posteriormente, superfícies envolvendo temperature, top_p, n, model, provider e contexto.

Não foi verificado nesta consolidação se Kohli faz exploração equivalente para top_p. Isso não deve ser afirmado sem leitura específica.

## 32. Por que isso pode importar ainda mais para pesquisadores com grande compute

Inicialmente N_eff parecia principalmente uma ferramenta de economia.

Mas pode ser mais importante justamente para quem possui muito compute.

Um laboratório capaz de gerar:

    1.000
    10.000
    100.000

inferências enfrenta uma pergunta que orçamento por si só não responde:

> Quantas observações efetivas adicionais essas chamadas realmente produziram?

Se N cresce rapidamente, mas N_eff cresce lentamente, o compute está aumentando volume nominal mais rápido do que observação independente equivalente.

Esse dado pode ajudar pesquisadores a realocar esforço experimental.

Não porque N_eff manda reduzir compute.

Mas porque torna visível o retorno informacional marginal sob dependência.

## 33. Aplicação a planejamento e relato de amostragem

Um uso possível é abandonar parcialmente escolhas arbitrárias como:

    vamos usar 100 amostras

e começar a documentar:

    n nominal
    N_eff observado
    configuração de sampling

Isso permite comparar coletas que nominalmente têm o mesmo tamanho, mas dependências distintas.

Eventualmente, artigos poderiam reportar:

    nominal n = 64
    effective n = 17.3

A importância científica disso não depende de N_eff alterar o modelo.

Ele melhora a descrição do experimento.

## 34. Impacto plausível para a comunidade

O cenário de impacto não precisa ser:

> N_eff revolucionou IA.

Um impacto mais plausível e ainda relevante seria:

> pesquisadores deixam de reportar apenas quantas execuções fizeram e passam também a considerar quanto de independência efetiva existia nessas execuções.

Isso mudaria a linguagem metodológica de:

    usamos 32 agentes

para algo mais informativo:

    usamos 32 agentes
    com efetividade amostral estimada de X

Mesmo que o método depois evolua ou seja substituído por estimadores melhores, introduzir essa preocupação metodológica já seria uma contribuição.

## 35. O que isso muda na avaliação do Norvald Studio

Sem essa linha de pesquisa, o Studio pode ser comparado principalmente por features:

- multi-model;
- agentes;
- RAG;
- documentos;
- artefatos;
- local-first;
- deliberação;
- ferramentas.

Essas categorias possuem concorrentes fortes.

Com pesquisa incorporada, a comparação muda.

O diferencial não é simplesmente:

    Studio tem N_eff

porque Kish ESS já está sendo usado por outros pesquisadores em LLM panels.

O diferencial potencial passa a ser:

    Norvald Studio
        │
        ├─ executa deliberações
        ├─ controla exposição
        ├─ preserva proveniência
        ├─ registra estrutura
        ├─ permite múltiplos providers/modelos
        │
        └─ funciona como infraestrutura experimental
                │
                ├─ N_eff
                ├─ AROF
                └─ futuramente CC

Ou seja:

> O produto pode funcionar como ambiente operacional onde uma linha de pesquisa sobre dependência, pluralidade efetiva e estrutura de reasoning é executável.

Isso é mais difícil de copiar do que uma única feature.

## 36. O que permanece forte mesmo sem exclusividade de N_eff

O precedente de Kohli não remove:

- integração com uma deliberação real;
- B1/B2/B3/E;
- provenance estrutural;
- exposição controlada;
- Working Context;
- comparação de providers/modelos;
- painel homogêneo vs. heterogêneo;
- AROF;
- relação futura com reasoning traces;
- eventual integração com CC;
- capacidade de tornar a pesquisa operacional em um produto.

Se existir defensibilidade de longo prazo, ela provavelmente virá de:

    método
    +
    instrumentação
    +
    dados experimentais
    +
    implementação
    +
    integração

e não de:

    uma fórmula exclusiva

## 37. Pontos críticos que não devem ser escondidos

### 37.1 N_eff não é novo como fórmula

É estatística clássica.

### 37.2 Seu uso direto em painéis correlacionados de LLM já possui precedente

Kohli 2026 precisa entrar na revisão.

### 37.3 Diversidade e independência são constructos diferentes

Vendi Score, K*, embeddings e AROF não podem ser tratados automaticamente como equivalentes de rho_erro.

### 37.4 Sampling pode alterar dependência, mas o sentido não é conhecido a priori

Temperature e top-p precisam ser experimentalmente caracterizados.

### 37.5 N_eff maior não significa output melhor

A métrica não julga qualidade.

### 37.6 N_eff depende do desfecho

Não existe necessariamente um único N_eff universal de um modelo.

### 37.7 Configuração importa

Modelo, provider, versão, domínio, prompt, contexto e parâmetros de inference podem alterar a dependência.

### 37.8 Relações AROF → rho → N_eff ainda são hipóteses

Precisam ser validadas.

### 37.9 CC é posterior

AROF funcionar não implica automaticamente que CC esteja validado.

## 38. Hipótese consolidada sobre temperature e top-p

A hipótese emergente desta conversa pode ser registrada assim:

> Parâmetros de amostragem podem alterar a dependência entre realizações de uma mesma configuração ou conjunto de configurações. Portanto, N_eff pode ser utilizado como variável observacional para caracterizar o efeito de temperature, top-p e outros parâmetros sobre a efetividade amostral de um painel ou conjunto de inferências. Essa caracterização não implica julgamento da qualidade, correção ou utilidade das realizações produzidas.

Uma formulação experimental possível:

    N_eff = f(M, P, V, C, Pi, theta, n)

onde:

- M = modelo;
- P = provider;
- V = versão/snapshot;
- C = contexto;
- Pi = prompt/protocolo/orquestração;
- theta = parâmetros de sampling;
- n = quantidade nominal de amostras.

E:

    theta = {
      temperature,
      top_p,
      ...
    }

## 39. Hipótese consolidada sobre reasoning

Outra hipótese derivada:

> Em experimentos de repeated reasoning ou inference-time scaling, N_eff pode caracterizar quanto o crescimento nominal do número de trajetórias corresponde a crescimento efetivo de observação não redundante para o desfecho analisado.

Isso pode ser comparado com:

- semantic diversity;
- structural diversity;
- K*;
- AROF;
- accuracy;
- pass@k;
- token budget;

sem reduzir qualquer uma dessas grandezas às outras.

## 40. Hipótese consolidada sobre AROF

A formulação mais importante é:

> Observáveis estruturais de reasoning podem conter informação sobre dependência entre realizações; essa relação deve ser estimada em tarefas com ground truth antes que esses observáveis possam ser utilizados para estimar dependência em tarefas sem ground truth.

Pipeline experimental:

    GROUND TRUTH
         ↓
    rho_erro observado
         ↓
    N_eff observado
         ↑
         │ validação
         │
    AROF observables
    K*
    semantic metrics

Somente se existir capacidade preditiva fora da amostra:

    sem ground truth
          ↓
    AROF
          ↓
    estimativa de dependência
          ↓
    N_eff estimado

## 41. Síntese crítica final

A pergunta original era:

> N_eff realmente tem potencial?

A resposta continua sendo sim, mas ficou mais precisa depois da revisão bibliográfica.

Não há base para dizer hoje:

> Ninguém fez N_eff para LLMs.

Há base para dizer:

> A comunidade está convergindo para o problema da redundância, correlação e saturação em ensembles e sistemas multiagente. Já existem trabalhos de effective channels, effective diversity, correlated errors e, crucialmente, pelo menos um trabalho aplicando Kish effective sample size diretamente a painéis de LLM-as-a-judge.

A oportunidade do programa Norvald está em ir além dessa aplicação isolada:

    effective sampling
    +
    exposição / herd effect
    +
    self-anchoring
    +
    sampling parameters
    +
    multi-provider composition
    +
    reasoning structure
    +
    AROF
    +
    ambientes sem ground truth
    +
    eventual CC

A observação sobre temperature/top-p é especialmente promissora porque transforma N_eff de simples descrição retrospectiva de redundância em possível instrumento de caracterização de desenho experimental.

Não para escolher a "melhor" temperatura.

Mas para permitir que pesquisadores saibam:

> Quanto cada regime de inferência realmente expande a amostra efetiva que eles estão coletando?

A aplicação a reasoning/inference-time scaling segue a mesma lógica:

> Quanto do compute adicional está produzindo novas observações efetivas e quanto está produzindo realizações correlacionadas?

Essa informação pode ajudar pesquisas existentes sem substituir seus métodos.

O objetivo não precisa ser mudar completamente a forma como IA é utilizada. É suficiente oferecer uma ferramenta conceitual e experimental que ajude pesquisadores a medir melhor o que já estão fazendo, reduzir desperdício informacional, montar experimentos de forma mais consciente e distinguir escala nominal de escala efetiva.

## 42. Referências internas — Norvald

- TESE-001 — docs/tese/01_Protocolo_Experimental.md
- TESE-002 — docs/tese/02_Mapa_de_Teste.md
- TESE-003 — docs/tese/03_Posicionamento_e_Procedencia.md
- PESQUISA-1000 / antiga ADR-1000 — docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
- PESQUISA-AROF — docs/pesquisa/PESQUISA-AROF_Observabilidade_do_Raciocinio.md

## 43. Referências externas centrais

### Kohli, G. (2026)

Nine Judges, Two Effective Votes: Correlated Errors Undermine LLM Evaluation Panels.

https://arxiv.org/abs/2605.29800

Precedente direto para Kish effective sample size aplicado a painéis LLM correlacionados.

### Yang, Y. et al. (2026)

Understanding Agent Scaling in LLM-Based Multi-Agent Systems via Diversity.

https://arxiv.org/abs/2602.03794

Introduz effective channels e K*; mostra retorno decrescente em scaling homogêneo e ganhos de heterogeneidade.

### Chen, N. et al. (2026)

Diversity Collapse in Multi-Agent LLM Systems: Structural Coupling and Collective Failure in Open-Ended Idea Generation.

Findings of ACL 2026.

https://aclanthology.org/2026.findings-acl.13/

### Kim, E. M.; Garg, A.; Peng, K.; Garg, N. (2025)

Correlated Errors in Large Language Models.

ICML 2025 / PMLR 267.

https://proceedings.mlr.press/v267/kim25e.html

### Kim, D. (2026)

Are Diversity Metrics Measuring Diversity? A Capability-Controlled Audit of Majority-Vote Gain in LLM Ensembles.

https://arxiv.org/abs/2607.20768

### Hao, X. et al. (2026)

Not All Flips Are Conformity: Decomposing Stance Convergence in Multi-Agent LLM Debate.

https://arxiv.org/abs/2606.00820

### Encheng, C. et al. (2026)

Single-Agent Generation Surpasses Multi-Agent Systems in Semantic Diversity.

Findings of ACL 2026.

https://aclanthology.org/2026.findings-acl.1894/

### Elahi, A.; Curry, M. J.; Di Eugenio, B. (2026)

Confidence Composition for Multiagent Language Model Systems.

https://arxiv.org/abs/2606.13591

### Huang, C.; Wu, Y.; Wang, K. (2026)

How Many Human Survey Respondents is a Large Language Model Worth? An Uncertainty Quantification Perspective.

https://arxiv.org/abs/2502.17773

Relacionado no enquadramento, mas não equivalente ao problema de co-falha entre membros de painel LLM.

### Imani, S. et al. (2026)

TRACE: A Framework for Analyzing and Enhancing Stepwise Reasoning in Vision-Language Models.

EACL 2026.

https://aclanthology.org/2026.eacl-long.166/

### Li, J. et al. (2026)

Efficient Test-Time Scaling via Temporal Reasoning Aggregation.

Findings of ACL 2026.

https://aclanthology.org/2026.findings-acl.651/

## 44. Ação documental necessária

A descoberta de Kohli exige atualização posterior de TESE-003.

A linha:

    ESS para painel de LLMs correlacionados
    → não encontrado

deve ser retirada ou reformulada.

Uma formulação mais defensável passa a ser:

    ESS para painel LLM correlacionado
    → existe precedente direto em LLM-as-a-judge

    lacuna investigada pelo Norvald
    → generalização para outros regimes de agregação,
      interação/exposição, sampling e eventual estimação
      sem ground truth através de observáveis estruturais

Isso não deve ser tratado como detalhe bibliográfico.

É uma mudança de posicionamento da contribuição e deve ser incorporada antes da publicação, para que a tese enfrente diretamente o trabalho mais próximo em vez de ser surpreendida por ele em revisão.
