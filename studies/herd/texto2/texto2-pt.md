# Quantos modelos valem cinco? Correlação de erros e número efetivo de juízes num painel heterogêneo de LLMs, antes e depois da exposição

Eduardo Guedes · Pesquisador independente · ORCID 0009-0003-9960-3337

> Rascunho do Opus, 12/11/2026. **Leitura pendente — proprietário.** Números de `studies/herd/resultados/conf2-*-medidas.md` depois do desvio D7 (Lab PR #25). Nada foi coletado de novo.

## Resumo

Painéis de modelos de linguagem são usados como se cinco modelos fossem cinco opiniões. Se os modelos erram juntos, o painel vale menos. Medimos isso pela correlação média dos erros entre pares de modelos (ρ̄_erro) e pelo número efetivo de juízes, N_eff = n / (1 + (n − 1) ρ̄), com n = 5.

No mesmo experimento pré-registrado do texto 1 (OSF aw9vf e 5dpjr), cinco modelos de cinco empresas responderam 140 perguntas do MMLU-Pro e 52 perguntas com gabarito de um banco novo, em condições pareadas. Respondendo às cegas (B1), o painel do MMLU-Pro teve ρ̄_erro = 0,635 [0,541; 0,721] e N_eff = 1,41 [1,29; 1,58]. Depois de ver as contribuições dos pares (E), ρ̄_erro = 0,826 e N_eff = 1,16: Δ_N_eff = 0,251 [0,153; 0,385]. No banco novo, os erros quase não se correlacionaram (ρ̄_erro = 0,031; N_eff = 4,45) e a exposição não os aproximou (Δ_N_eff = −1,60 [−4,49; −0,73]). Um painel homogêneo de controle, cinco cópias do Gemma, teve ρ̄_erro = 0,848 no MMLU-Pro, próximo do painel misto. Em sete perguntas, os cinco modelos escolheram a mesma opção errada; sem elas (análise exploratória), ρ̄_erro(B1) = 0,572 e N_eff = 1,52. Cruzando com o MMLU-Redux, das 14 perguntas herdadas do MMLU com 3 ou mais modelos na mesma opção errada, 11 convergem num distrator que o MMLU-Pro acrescentou e o Redux não revisou.

## 1. Introdução

O texto 1 mostrou quanto os modelos mudam de resposta quando veem os pares. Este texto trata da outra metade da pergunta do título do texto 1: quantos contribuem. Se dois modelos erram nas mesmas perguntas, o segundo acrescenta pouco ao primeiro, mesmo sem ter visto nada dele.

A hipótese registrada (H3) tem duas partes:
1. o painel heterogêneo vale menos que cinco já às cegas (ρ̄_erro(B1) > 0);
2. a exposição reduz o número efetivo (Δ_N_eff = N_eff(B1) − N_eff(E) > 0).

O registro não prevê teste de significância para Δ_N_eff (344-77): o intervalo bootstrap é a medida.

## 2. Método

O desenho, os modelos, as condições e as perguntas são os do texto 1 (§3). Aqui só o que é próprio do H3.

**Erro.** Para cada modelo, condição e pergunta com gabarito: 1 se a opção escolhida difere da chave, 0 se coincide. Resposta sem posição fica fora (sem imputação).

**ρ̄_erro(c).** Média, sobre os 10 pares de modelos, do coeficiente phi entre os vetores de erro na condição c. Par sem variância de erro fica fora da média e é contado.

**N_eff(c) = n / (1 + (n − 1) ρ̄_erro(c))**, com n = 5 em todas as condições, para que a diferença reflita só o ρ̄.

**Perguntas usadas.** Todas as perguntas com gabarito, inclusive as unânimes em B1 (registro: "on ground-truth items"). O filtro de unânimes vale só para o critério A do texto 1. Até 12/11/2026 o Lab aplicava esse filtro também ao ρ̄; o desvio D7 corrige isso e mostra antes e depois.

**Intervalos.** Bootstrap por pergunta, 20 000 réplicas, seed 20261111, IC 95% percentil, estratificado entre perguntas com gabarito e contestáveis.

**Contraste homogêneo (344-83 item 2).** Cinco cópias de google/gemma-4-31b-it, mesma empresa (Crusoe), só B1. Mede quanto da correlação vem de o painel ser de modelos parecidos em geral, e não de a mesma arquitetura.

**Varredura analítica.** A fórmula do N_eff tabelada para ρ̄ de 0,01 a 1 e n = 4, 5, 8 e ∞. Não é resultado empírico: mostra o teto (1/ρ̄ quando n → ∞) que um painel tem, qualquer que seja o tamanho.

## 3. Resultados

### 3.1 ρ̄_erro e N_eff por condição

| Bloco (perguntas com gabarito) | Condição | ρ̄_erro [IC 95%] | N_eff [IC 95%] |
|---|---|---|---|
| MMLU-Pro (140) | B1 | 0,635 [0,541; 0,721] | 1,413 [1,287; 1,580] |
| | B3 | 0,642 [0,547; 0,729] | 1,401 [1,277; 1,568] |
| | EP | 0,689 [0,600; 0,770] | 1,332 [1,226; 1,471] |
| | E | 0,826 [0,751; 0,894] | 1,162 [1,093; 1,249] |
| Banco (52) | B1 | 0,031 [−0,063; 0,241] | 4,445 [2,548; 6,702] |
| | B3 | 0,022 [−0,076; 0,215] | 4,597 [2,688; 7,190] |
| | EP | 0,080 [−0,054; 0,243] | 3,791 [2,536; 6,367] |
| | E | −0,043 [−0,096; −0,021] | 6,040 [5,465; 8,098] |
| Combinado (192) | B1 | 0,615 [0,520; 0,699] | 1,445 [1,318; 1,624] |
| | E | 0,814 [0,737; 0,879] | 1,175 [1,107; 1,266] |
| h01–h40 (40) | B1 | 0,013 [−0,087; 0,220] | 4,746 [2,660; 7,655] |
| | E | −0,056 [−0,127; −0,028] | 6,456 [5,625; 10,144] |

### 3.2 Δ_N_eff = N_eff(B1) − N_eff(E)

| Bloco | Δ_N_eff [IC 95%] |
|---|---|
| MMLU-Pro | 0,251 [0,153; 0,385] |
| Banco | −1,595 [−4,488; −0,734] |
| Combinado | 0,269 [0,172; 0,404] |
| h01–h40 | −1,710 [−6,021; −0,552] |

No MMLU-Pro e no combinado, o intervalo fica acima de zero: compatível com a parte 2 do H3. No banco, fica abaixo de zero: em E, os erros que restam ficam espalhados entre modelos diferentes (ρ̄ levemente negativo), e o N_eff passa de 5. Um N_eff acima de n só significa erros anticorrelacionados; não é "mais juízes que modelos". O ρ̄ de E no banco vem de muito poucos erros: depois da exposição quase todos convergem para a resposta certa, e o phi com tão poucos erros por modelo é instável. O Δ negativo do banco não deve ser lido como "a exposição torna o painel mais independente".

### 3.3 Correlação por par de modelos (MMLU-Pro, B1)

De 0,471 (Nemotron × Qwen) a 0,789 (Gemma × Qwen). Nenhum par sem correlação definida. A tabela completa está no relatório.

### 3.4 Contraste homogêneo: cinco cópias do Gemma

| Bloco | ρ̄_erro(B1) [IC 95%] | N_eff(B1) [IC 95%] | Painel misto, ρ̄_erro(B1) |
|---|---|---|---|
| MMLU-Pro (140) | 0,848 [0,759; 0,924] | 1,138 [1,065; 1,239] | 0,635 [0,541; 0,721] |
| Banco (52) | indefinido | indefinido | 0,031 |

No banco, os cinco Gemma acertaram as 52 perguntas em B1; sem erro, a correlação de erros não existe. No MMLU-Pro, os dois intervalos não se sobrepõem.

### 3.5 Varredura analítica (n = 5)

| ρ̄ | 0,05 | 0,1 | 0,2 | 0,3 | 0,5 | 0,6 | 0,7 | 0,8 | 0,9 |
|---|---|---|---|---|---|---|---|---|---|
| N_eff (n = 5) | 4,17 | 3,57 | 2,78 | 2,27 | 1,67 | 1,47 | 1,32 | 1,19 | 1,09 |
| N_eff (n = ∞) | 20 | 10 | 5 | 3,33 | 2 | 1,67 | 1,43 | 1,25 | 1,11 |

Com o ρ̄_erro(B1) do MMLU-Pro (0,635), o teto com infinitos modelos seria 1,58; com 8 modelos, 1,47. Acrescentar modelos do mesmo tipo quase não muda o número efetivo.

### 3.6 ρ̄_caminho: os fundamentos se sobrepõem? (exploratório)

Sobreposição de Jaccard entre as palavras de conteúdo dos fundamentos declarados no CONTRIBUTION, por par de modelos e pergunta. Tiramos as palavras da pergunta e das opções, para que repetir o enunciado não conte (`texto2/caminho_dos_fundamentos.py`).

| Bloco, condição | Acerto em comum | Erro em comum (mesma opção) | Opções diferentes | Respostas com fundamento além da decisão |
|---|---|---|---|---|
| MMLU-Pro, B1 | 0,105 (727 pares) | 0,059 (143) | 0,052 (273) | 7,0% |
| MMLU-Pro, E | 0,190 (805) | 0,113 (190) | 0,068 (113) | 1,8% |
| Banco, B1 | 0,072 (389) | 0,000 (2) | 0,024 (42) | 5,4% |
| Banco, E | 0,105 (395) | — | 0,052 (15) | 2,0% |

Leitura, sem adjetivo:
- Em B1, o erro em comum tem sobreposição de fundamentos próxima à de opções diferentes (0,059 contra 0,052), e abaixo da do acerto em comum (0,105).
- Em E, a sobreposição sobe nos três grupos; no acerto em comum, quase dobra (0,105 → 0,190).
- Só 7% das respostas declaram algum fundamento além da decisão; em E, 1,8%. A justificativa costuma estar no texto da própria decisão.
- Limite: palavras em comum não são raciocínio igual. A leitura de 4.1b mostra o mesmo caminho em erros reais que esta medida não separa. Ela só olha o que os pares veem, não o raciocínio interno.

### 3.7 ρ̄_caminho no raciocínio interno (exploratório)

O mesmo Jaccard de 3.6, agora sobre o raciocínio interno de cada modelo. Tiramos as palavras da pergunta, das opções e do vocabulário de formato (JSON, relação, bloco), e separamos os pares por resultado (`texto2/caminho_dos_raciocinios.py`).

| MMLU-Pro | Os dois acertam | Os dois erram na mesma opção | Um certo, um errado | Erros diferentes |
|---|---|---|---|---|
| B1 | 0,129 (838 pares) | 0,130 (159) | 0,132 (203) | 0,124 (96) |
| E | 0,111 (921) | 0,125 (208) | 0,104 (86) | 0,133 (42) |

No banco, em B1: 0,133 quando os dois acertam (463 pares) e 0,118 quando um acerta e o outro erra (47).

- A sobreposição é a mesma nos quatro grupos: por palavras, o raciocínio não separa acerto de erro, nem erro em comum de opções diferentes.
- Ela varia por par de modelos, não por resultado. Em B1, Gemma × Qwen tem 0,178 quando os dois acertam e 0,208 quando erram juntos; Mistral × Muse, 0,096 e 0,090. A medida capta o estilo de escrita de cada modelo.
- O passo que decide a resposta costuma ser uma frase (na m04145, "as concentrações estão perto de 1 M"), e some no meio do raciocínio longo. Medir o caminho pede extrair esse passo, por leitura ou por um modelo juiz.

## 4. Ressalvas

### 4.1 Sete perguntas com os cinco na mesma opção errada

Em sete perguntas, os cinco modelos do painel misto escolheram em B1 a mesma opção, diferente da chave. Lemos as sete e cruzamos as herdadas do MMLU original com o MMLU-Redux 2.0 (`texto2/redux_cruzamento.md`). As chaves não foram editadas (344-79 item 3); só relatamos.

| Pergunta | Origem | Chave | Opção dos cinco | Redux | Leitura |
|---|---|---|---|---|---|
| m07756 | TheoremQA | H | D | fora do Redux | chave errada: a série diverge; a chave "0.0" vem do TheoremQA |
| m07114 | MMLU | G | F | chave ok | distrator acrescentado pelo Pro, não revisado (a nossa leitura o acha também correto) |
| m07045 | MMLU | E | C | chave ok | distrator acrescentado pelo Pro, não revisado (a nossa leitura o acha também correto) |
| m04776 | MMLU | H | C | chave ok | distrator acrescentado pelo Pro, não revisado |
| m05049 | MMLU | G | J | chave ok | distrator acrescentado pelo Pro, não revisado |
| m02530 | MMLU | C | B | ausente do Redux | ambígua (leitura nossa) |
| m07001 | stemez | C | H | fora do Redux | ambígua (leitura nossa) |

Cada uma dessas perguntas conta como erro comum dos cinco e puxa o ρ̄ para cima. **Sensibilidade exploratória** (fora do registro; `texto2/sensibilidade_sete_chaves.py`):

| Bloco | Medida | Todas | Sem as 7 |
|---|---|---|---|
| MMLU-Pro | ρ̄_erro(B1) | 0,635 [0,541; 0,721] (140) | 0,572 [0,460; 0,669] (133) |
| | ρ̄_erro(E) | 0,826 [0,751; 0,894] | 0,789 [0,693; 0,869] |
| | N_eff(B1) | 1,413 | 1,521 [1,360; 1,760] |
| | Δ_N_eff | 0,251 [0,153; 0,385] | 0,318 [0,190; 0,500] |
| Combinado | ρ̄_erro(B1) | 0,615 (192) | 0,548 [0,440; 0,644] (185) |
| | Δ_N_eff | 0,269 [0,172; 0,404] | 0,344 [0,214; 0,528] |
| Contraste Gemma, MMLU-Pro | ρ̄_erro(B1) | 0,848 [0,759; 0,924] | 0,812 [0,701; 0,905] |

O sinal das conclusões de 3.1 a 3.4 não muda sem as sete.

### 4.1b Os outros erros em comum (exploratório)

Nas 140 perguntas do MMLU-Pro, o maior bloco de modelos errando na mesma opção em B1 tem 5 modelos em 7 perguntas (as de 4.1), 4 em 8 e 3 em 9. Lemos os raciocínios e as contribuições das 17 de 3 e 4, e cruzamos com o Redux as que vieram do MMLU original.

| Pergunta | Origem | Chave → opção do bloco (n) | Como chegaram | Redux | Leitura |
|---|---|---|---|---|---|
| m01086 | MMLU | C → H (4) | dolo transferido e Pinkerton; ninguém funde a instigação na conspiração | chave ok; H é original | erro dos modelos, mesmo caminho |
| m05302 | MMLU | I → H (3) | FIV com triagem de embriões | chave ok; H é original | erro dos modelos |
| m05787 | MMLU | G → D (4) | a zona 4 de Burgess | chave ok; D é original | erro dos modelos (nós líamos "numeração ambígua") |
| m02954 | stemez | F → H (3) | (1/4)^n ≈ 2/500 → n = 4, lido como 4 genes e não 4 pares | fora do Redux | erro dos modelos, mesmo atalho (leitura nossa) |
| m04145 | stemez | F → I (3) | "concentrações perto de 1 M", então E ≈ E° = 0,11 V; ignoram o 10⁻⁴ | fora do Redux | erro dos modelos, mesmo atalho (o Qwen fez a conta) |
| m06785 | MMLU | B → H (3) | sintomas digestivos → anorexia; os que acertam passam pela B12 | ausente do Redux | erro dos modelos, mesmo caminho superficial (leitura nossa) |
| m03165 | MMLU | B → D (4) | ΔP = ΔV/C: queda pequena na veia | chave ok | distrator acrescentado pelo Pro, não revisado |
| m04683 | MMLU | D → F (4) | escalada (LBJ) × desescalada (Nixon) | chave ok | distrator acrescentado pelo Pro, não revisado |
| m05018 | MMLU | F → G (4) | as duas primeiras indicadas por grande partido | chave ok | distrator acrescentado pelo Pro, não revisado |
| m05022 | MMLU | B → H (3) | Copérnico é heliocêntrico | chave ok | distrator acrescentado pelo Pro, não revisado |
| m05198 | MMLU | B → I (4) | "dependem dos Estados" | chave ok | distrator acrescentado pelo Pro, não revisado |
| m05220 | MMLU | G → B (3) | fase de vergonha | chave ok | distrator acrescentado pelo Pro, não revisado |
| m09169 | MMLU | F → A (3) | "A é falsa sem interpretação" | chave ok | distrator acrescentado pelo Pro, não revisado |
| m01566 | MMLU | E → D (4) | "o vizinho não tem legitimidade" (fee simple determinable) | ausente do Redux | erro dos modelos ou chave discutível (leitura nossa) |
| m02085 | MMLU | B → A (4) | o MIQ mede valores, não interesses | ausente do Redux | ambígua (leitura nossa) |
| m01935 | MMLU | H → I (3) | "without reserve" obriga a vender | ausente do Redux | ambígua: H e I dizem quase o mesmo (leitura nossa) |
| m07513 | stemez | A → B (3) | bens públicos e estabilização | fora do Redux | ambígua (leitura nossa) |

**As 24 perguntas com 3 ou mais modelos errando juntos (7 + 17), lado a lado:**

| Classe | Perguntas | Base |
|---|---|---|
| Distrator acrescentado pelo MMLU-Pro, chave original ok | 11 | Redux |
| Erro dos modelos, chave ok | 3 | Redux |
| Erro dos modelos | 3 | leitura nossa, fora ou ausente do Redux |
| Chave errada | 1 (m07756) | leitura nossa, TheoremQA |
| Ambígua ou discutível | 6 | leitura nossa |

Nos erros dos modelos que lemos, o bloco chega pelo mesmo caminho ou pelo mesmo atalho. A nossa leitura própria tinha marcado várias das 11 como "chave duvidosa"; o Redux diz que a chave original está certa. O que o Redux não revisou é o distrator que o MMLU-Pro acrescentou, e é nele que os modelos convergem.

### 4.2 Perda do Gemma (D5)

A empresa que serve o Gemma limitou a taxa de pedidos. No painel misto ficaram sem posição 25 respostas do Gemma no banco e 64 no MMLU-Pro. No contraste do MMLU-Pro, 670 de 700 posições em B1 foram obtidas, e 130 das 140 perguntas têm as cinco cópias (na m04776, só uma). A perda vem do fornecedor e não do modelo; ela reduz a amostra de pares e alarga os intervalos do contraste.

### 4.3 Outras

- O ρ̄ é sobre erro com gabarito. Nas perguntas contestáveis não há erro; a concordância de Fleiss (ρ̄_comportamento) só existe no banco e é descritiva.
- n = 5 é fixo; a varredura é analítica, não observada.
- Phi em vetores com poucos erros (banco) tem intervalo largo.

## 5. Discussão

*(a escrever depois da leitura do Eduardo; só os pontos)*
- No MMLU-Pro, cinco modelos de cinco empresas valem cerca de 1,4 às cegas e 1,2 depois de se verem.
- O painel misto fica abaixo do homogêneo (0,635 contra 0,848), mas longe de independente.
- O banco novo dá o quadro oposto: erros quase independentes. Diferença de conteúdo (perguntas novas, fora de dados de treino prováveis) ou de dificuldade? Exploratório (`texto2/novidade_ou_facilidade.py`): no banco, a taxa de erro em B1 é de 5% (MMLU-Pro: 28%) e nenhuma pergunta tem mais de 2 dos 5 errando. O ρ̄ baixo do banco é compatível com facilidade, e o desenho não permite testar a novidade nele. Dentro do MMLU-Pro, as perguntas herdadas do MMLU original têm ρ̄_erro(B1) = 0,68 [0,57; 0,78] e erro de 33% (81 perguntas); as acrescentadas pelo MMLU-Pro, 0,51 [0,33; 0,67] e erro de 20% (59). Os intervalos se sobrepõem, a dificuldade difere e 5 das 16 perguntas originais com os cinco errando estão entre as de §4.1. Novidade e facilidade não se separam com estes dados; separá-las pede perguntas novas e difíceis.
- **Consequência para quem mede painéis com o MMLU-Pro.** Das 24 perguntas com 3 ou mais modelos na mesma opção errada, 11 convergem num distrator que o MMLU-Pro acrescentou às perguntas herdadas do MMLU, e que o Redux não revisou. O Redux confirma a chave original com 4 opções, não as 6 novas. Quem calcula correlação de erros ou N_eff com o MMLU-Pro conta esses casos como erro em comum. Os dados não dizem se o distrator também é correto ou se os modelos caíram juntos num distrator plausível. Nos dois casos, a origem do erro em comum está no conjunto de perguntas, e o ρ̄ mistura a dependência entre modelos com o ruído das opções acrescentadas. A sensibilidade sem as 7 de §4.1 tira só 4 desses distratores; os outros 7, de §4.1b, continuam no cálculo.
- Ligação com o texto 1: a exposição que muda posições (H1, H4) é a mesma que aproxima os erros no MMLU-Pro.

## Apêndice A. Desvio D7

O ρ̄ da análise principal saía só das perguntas sem unanimidade em B1, contra o registro. Antes → depois, ρ̄_erro(B1): banco −0,272 (11 perguntas) → 0,031 (52); MMLU-Pro 0,306 (61) → 0,635 (140); contraste Gemma 0,041 (18) → 0,848 (140). Ver `studies/herd/desvios.md`.
