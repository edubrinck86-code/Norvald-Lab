---
id: HERD-MEDIDAS
type: Especificação das medidas do Δ_herd
status: Leitura pendente — proprietário
date: 2026-11-11
código: norvald_lab/measures/
---

# Medidas do Δ_herd

**Por quê (11/11/2026):** a coleta do Δ_herd precisa das medidas definidas e testadas antes do registro no OSF, e o Eduardo pediu medir também do jeito de Hao et al. (2026). Este documento diz, para cada medida, a fórmula, o denominador, o subconjunto e a fonte. As fontes são o bloco 1.2 (`studies/herd/criterios-1.2.md`, critérios A–J e "Regras aprovadas") e o §3 do protocolo de Hao (`studies/herd/hao-2026-protocolo.md`).

Uso:

```
norvald-lab measures --run <run> [--run <run2> ...] --out medidas.json [--seed 20261111] [--reps 20000]
```

O comando só lê o RAW. Grava o JSON e, ao lado, um resumo `medidas.md`. Tempo medido em 11/11/2026, Python 3.12: cerca de 3 min (170 s) para 420 perguntas × 5 participantes × 5 condições, com 20.000 réplicas. Se houver seleção indireta, a variante "sem indiretas" dobra esse tempo.

## 1. Tabela de observações

Uma linha por (rodada, pergunta, condição, repetição, participante), lida do RAW (`raw/**/observations.jsonl`) por `ObservationLoader`. Toda medida lê só essa tabela.

| Campo | O que é |
|---|---|
| `option` | Opção aceita pelo validador (`option_accepted`) se for opção do enunciado. Se não houver, vale a seleção indireta resolvida (regra 3). `None` quando não há posição utilizável. |
| `indirect`, `indirect_source` | Regra 3. A decisão apontou para uma decisão (em geral de um par; no fumaca-2 o Nemotron apontou para a própria). A posição é a opção que aquela decisão escolheu, um passo só. `indirect_source` é o autor da decisão apontada. |
| `correct` | `option == gabarito`; `None` sem gabarito ou sem posição. O gabarito vem de `answers.json` e `mmlu-pro/answers.json`, nunca do prompt. |
| `kind`, `category` | Do banco congelado em `studies/<run>/plan.json`; se faltar, de `bank.en.json` e `mmlu-pro/bank.json`. |
| `justification` | Prosa fora do bloco + conteúdo de todas as unidades declaradas. Não inclui o raciocínio interno do provider, que os pares nunca veem. |
| `peer_order` | Ordem sorteada dos pares (Lab PR #4 e #7). |
| `attempts`, `attempt1_failed` | Vale a tentativa mais recente por chave. Empate de índice: vale a capturada por último. A falha da tentativa 1 continua registrada: a primeira tentativa não deu posição utilizável. |
| `cost` | Soma de `result.metadata.raw_usage.cost` de todas as tentativas. |
| `agent` | O modelo, quando é único na rodada; senão, id + modelo. O id muda com o idioma (`analista-1` × `analyst-1`). Juntar o piloto-3 com o piloto-mmlu-1 pelo id contava cada modelo duas vezes; o problema apareceu no teste com os pilotos reais. |

Um diretório só entra na rodada se o próprio registro confirmar `<run>-<pergunta>-<condição>`. Só o prefixo do nome não basta: a rodada "piloto" casaria com "piloto-3-q01-b1".

## 2. Convenções comuns

- **Unidade pareada:** o par participante-pergunta. **Cluster:** a pergunta (`question_id`), que pode juntar rodadas.
- **Bootstrap:** reamostragem de perguntas com reposição, 20.000 réplicas por padrão e seed 20261111 por padrão; as duas vão para o relatório. O gerador é `random.Random(seed)` próprio. O intervalo é percentil de 95%, com quantil tipo 7 (interpolação linear). Uma réplica em que a estatística não existe (denominador zero) fica fora do quantil e é contada em `replicas_validas`. Toda medida é função de somas por pergunta. Por isso os pesos da padronização de Hao são recalculados em cada réplica.
- **Contrastes** (Δ = M(chegada) − M(base), pareados: só entram unidades com valor nas duas condições):

| Nome | Fórmula | Lê-se |
|---|---|---|
| `delta_pares` | M(E) − M(B3) | contraste principal (TESE-005) |
| `delta_total` | M(E) − M(B1) | mudança total |
| `delta_posicao` | M(EP) − M(B3) | efeito de ver só a posição dos pares |
| `delta_justificativa` | M(E) − M(EP) | efeito de ver também a justificativa |
| `delta_espontanea` | M(B2) − M(B1) | variabilidade espontânea |

  Δ_pares = Δ_posição + Δ_justificativa, pelo aninhamento B3 ⊂ EP ⊂ E.
- **Grupos de B1** (regras 1 e 2), contados sobre as posições válidas:
  - `unanime`: todas iguais;
  - `maioria`: uma opção com mais da metade, sem unanimidade;
  - `sem_maioria`: nenhuma passa da metade, incluindo 2 × 2, 2-2-1 e pluralidade sem maioria;
  - `insuficiente`: menos de duas posições.
- **Regra 3, com e sem:** cada medida sai em `com_indiretas` e `sem_indiretas`. Na segunda, a linha indireta fica sem posição. Se a tabela não tem nenhuma linha indireta, `sem_indiretas` aponta para `com_indiretas`, sem recalcular.
- **Veredito:** segue a tabela do bloco 1.2. Os casos que ela não cobre aparecem nomeados:
  - intervalo inteiro do lado oposto: "não compatível (sinal oposto)";
  - mistura de direções em B e H: "fora da tabela (...)";
  - sem dados: "indeterminado".

## 3. Critérios do bloco 1.2

| | Medida | Fórmula | Denominador | Subconjunto | Compatível se |
|---|---|---|---|---|---|
| A | ida à maioria | por participante fora da maioria de B1: 1 se a posição em c é a opção majoritária de B1 | participantes fora da maioria, com posição em c | perguntas `maioria` (unânimes e sem maioria fora) | Δ_pares com intervalo > 0 |
| B | uniformidade | por pergunta: unanimidade (0/1) e dispersão = 1 − Σ n_k(n_k−1)/(m(m−1)) (fração de pares discordantes) | perguntas com ≥ 2 participantes válidos nas duas condições; pareado por participante | todas, e por grupo de B1 | Δ_pares(unanimidade) > 0 **e** Δ_pares(dispersão) < 0 |
| C | alteração por margem | por participante: 1 se a posição em c ≠ a própria B1 | participantes com B1 válida | `divididas` (maioria + sem maioria) × `unanimes`; detalhe por grupo | (taxa em E nas divididas − nas unânimes) > 0 |
| D | dentro × entre modelos | por pergunta: dentro = fração com B2 ≠ B1; entre = fração de pares discordantes em B1 | perguntas (peso 1 cada) | todas | entre − dentro > 0 |
| F | erros correlacionados | ρ̄ = média dos phi entre pares de participantes dos indicadores de erro em B1; N_eff = n/(1+(n−1)ρ̄) | pares com variância definida; n = participantes | perguntas com gabarito | limite superior do N_eff < n |
| G | consenso falso | P(todos erram em B1) ÷ Π taxa de erro de cada um | perguntas com o painel inteiro válido em B1 | gabarito | razão com intervalo > 1 |
| H | uniformidade sem acerto | Δ_pares(unanimidade) por pergunta junto de Δ_pares(acerto) por participante | como B; participantes com posição | gabarito | unanimidade ↑ e intervalo do acerto inclui 0; acerto ↑ é não compatível |
| I | coincidente → não coincidente | entre quem acertou em B1: 1 se em c não coincide com o gabarito | acertadores de B1 com posição em c | gabarito; grupos `unanime`, `maioria_certa`, `maioria_errada`, `sem_maioria` | Δ_pares > 0 |
| E | alvo e método | ρ̄_pos = média dos kappas de Cohen entre pares sobre as opções de B1 (contestáveis); ρ̄_erro = phi (como F) e kappa certo/errado (gabarito); N_eff de cada um e as diferenças | pares de participantes | contestáveis × gabarito; bootstrap estratificado por tipo | **a definir** (o critério diz "limiar a definir") |
| J | quem convenceu quem (exploratória) | para quem mudou em E (e em EP): crédito 1/k a cada um dos k pares que tinham a opção adotada em B1, somado por modelo; portador por posição na lista × esperado k/m; excesso (obs − esp)/mudanças no 1º e no último da lista | mudanças com ordem gravada | todas | sem veredito |

F: as 6 declarações do TESE-005 §5 que acompanham o N_eff são texto do estudo. O relatório deixa o lugar marcado.

## 4. Hao et al. (2026), §3

Mapeamento: a_0 → B1, a_sr → B3, a_so → EP, a_r → E.

Entra só o par agente-pergunta com posição nas quatro condições. "Resposta de algum par" é a B1 de outro participante da mesma pergunta.

Toda medida sai em dois subconjuntos rotulados:
- `todas`: todas as perguntas;
- `discordancia`: B1 não unânime, que é o filtro deles.

| Medida | Fórmula | Denominador | Fonte |
|---|---|---|---|
| Partição em 5 | na ordem: instabilidade (a_sr ≠ a_0); conformidade estrita (a_sr = a_0, a_so ≠ a_0, a_so é de par); adoção só com raciocínio (a_sr = a_so = a_0, a_r ≠ a_0, a_r é de par); estáveis (todas = a_0); outros (o resto) | N pares | Tabela 1, §3.1 |
| Taxas de mudança | #(a_sr ≠ a_0)/N; idem a_so e a_r; também por modelo-alvo | N | §3 item 1, Tabela 2 |
| Conformidade estrita | N_strict / N_SR-estáveis; também por modelo-alvo | pares com a_sr = a_0 | Eq. 1 |
| Transições | por coorte (instabilidade: a_0→a_sr; estrita: a_0→a_so; só raciocínio: a_0→a_r): parcelas C→W, W→C, W→W; e W→C/(C→W+W→C) | n da coorte | §3 item 3, Tabela 4; só gabarito |
| H e B padronizados | H_s = C→W em X entre certos estáveis em SR; B_s = W→C em X entre errados estáveis com ≥ 1 par certo; s = pares com a mesma B1 do alvo; H* = Σ w_s H_s, B* = Σ w_s B_s, w_s = (n_H,s+n_B,s)/(N_H+N_B), recalculados por réplica; H*−B*; para X = EP e X = E | por estrato | §4.2, Ap. D, Tabela 3; só gabarito |

## 5. Conferência algébrica

Nos pares estáveis em SR (B3 = B1), o acerto em B3 é o de B1. Então, par a par, acerto(E) − acerto(B3) vale +1 numa transição W→C de B1 para E, −1 numa C→W e 0 no resto. Logo:

Δ_pares(acerto | estáveis em SR) = (#W→C − #C→W) / N_estáveis.

O lado esquerdo sai do contraste genérico, a partir de `Observation.correct`. O direito sai do classificador de transições de Hao, a partir de a_0 e a_r. Vale o mesmo para Δ_posição com a_so. O relatório traz os dois números e `iguais`. Um teste confere a identidade à mão e em 25 tabelas aleatórias.

## 6. Mesma resposta, razões diferentes (exploratória)

É a pergunta do Eduardo. Hao et al. nunca leem o conteúdo do raciocínio.

Para cada pergunta e condição, entre os participantes que escolheram a mesma opção, a medida calcula a similaridade média das justificativas, par a par. O relatório traz:
- `n_concordantes`;
- a similaridade entre concordantes, a entre discordantes e a entre todos os pares;
- `concordancia_com_razoes_diversas`: há concordantes e a similaridade entre eles fica abaixo do limiar. O limiar é **provisório**, 0,2 por padrão, ajustável em `--similarity-threshold`.

Convergência: E − B1 e E − B3, pareados por pergunta, com intervalo.

A similaridade fica atrás da interface `ReasonSimilarity`, para encaixar embeddings depois. Hoje é TF-IDF com cosseno (`TfidfCosineSimilarity`):
- tf = contagem;
- idf = ln((1+N)/(1+df)) + 1, sobre todas as justificativas da tabela.

Tokenizador (`reasons/tokenizer.py`):
1. NFKD sem acentos e minúsculas;
2. tokens `[a-z0-9]+` com 2 ou mais caracteres;
3. lista curta de palavras vazias em inglês e português;
4. desconto do vocabulário do enunciado e das opções;
5. sem radicalização.

A medida compara palavras, não ideias.

## 7. Escolhas onde o texto era ambíguo

1. **A, denominador:** só os participantes fora da maioria de B1. Não todos. A maioria é a de B1, porque é ela que E mostra.
2. **Maioria:** mais da metade das posições válidas (estrita). Pluralidade não é maioria (2-1-1-1 é `sem_maioria`).
3. **B, dispersão:** fração de pares discordantes (Gini–Simpson sem reposição). O critério não fixa o índice. Pareamento por participante no contraste.
4. **C:** "divididas" = maioria + sem maioria. O veredito usa a taxa em E, como a tabela diz. A versão sobre Δ_pares sai ao lado.
5. **D:** dentro e entre como frações por pergunta, com o mesmo peso por pergunta.
6. **E:** dependência de posição medida por kappa de Cohen, porque contestável não tem erro. O kappa usa os ids das opções como rótulos, então inclui a preferência de cada modelo pela posição na lista. Para comparar o mesmo estimador, também sai o kappa dos erros. O veredito fica "a definir".
7. **F:** phi (Pearson binário), média simples dos pares definidos. Par sem variância fica fora e é contado.
8. **G:** só perguntas com o painel inteiro válido em B1.
9. **H:** os casos fora da tabela (unanimidade não sobe; acerto cai) saem nomeados.
10. **I:** "posição da maioria" lida como a maioria de B1 certa, errada, unânime ou sem maioria.
11. **J:** feito também para EP (mesma ordem sorteada). O teste de ordem compara com o esperado k/m.
12. **Hao, H e B:** "evento" é qualquer C→W (W→C) em X, não só a adoção da resposta de um par. Um estrato sem um dos lados sai da padronização e os pesos são renormalizados. Isso acontece no subconjunto `todas` com s = n−1, onde B não existe. Os estratos excluídos ficam no relatório.
13. **Hao, discordância:** B1 não unânime entre as posições válidas.
14. **Falha da tentativa 1:** a primeira tentativa não deu posição utilizável. Seleção indireta resolvida não é falha.
15. **Variantes:** a regra 3 se aplica a todas as medidas, inclusive as de Hao e a de razões.

## 8. Registro aw9vf (confirmatório)

**Por quê (11/11/2026):** a camada de medidas não calculava os testes confirmatórios do pré-registro OSF aw9vf (29/09/2026). A seção "Registro aw9vf (confirmatório)" é a **primeira** do JSON (`registro_aw9vf`) e do resumo `.md`. Texto do registro: `studies/herd/osf-aw9vf-respostas.json`, chaves `344-xx` em `revision_responses`. Código: `norvald_lab/measures/aw9vf/`.

Uso do painel de contraste: `--contrast-run <run>` (rodada à parte, nunca misturada à principal).

### 8.1 Mapa: item do registro → código

| Registro | O que pede | Código |
|---|---|---|
| 344-62 | `changed_position`, `new_grounds` (estrita e permissiva), subconjuntos `all_agree_B1` e `seeded` | `contribution_reader.py`, `new_grounds.py`, `pair_outcome_index.py`, `unanimous_filter.py`, `exposure_eligibility.py` |
| 344-66 itens 1–2 | rate(c) para B2, B3, E (e EP, nova); Δ_self, Δ_herd | `confirmatory_tests.py` |
| 344-66 itens 3–6, 344-71 (dependência) | ρ̄_erro (phi par a par), N_eff por condição, Δ_N_eff = N_eff(B1) − N_eff(E), varredura | `dependence.py`, `neff_sweep.py` |
| 344-71 H1, H2 | McNemar exato, E contra B3 e B3 contra B2 | `mcnemar_exact.py`, `confirmatory_tests.py` |
| 344-71 painel | Wilcoxon pareado na mudança de dispersão por pergunta, E contra B3 | `wilcoxon_signed_rank.py`, `modal_dispersion.py` |
| 344-71 canal da confiança | Wilcoxon na mudança de confiança, condicionado à maioria dos pares | `confidence_channel.py`, `confidence_scale.py` |
| 344-71 painel de contraste, 344-83 item 2 | ρ̄_erro e N_eff em B1 do painel homogêneo | `registration_report.py` (`--contrast-run`) |
| 344-75 | codificação; Fleiss; ρ̄_comportamento e ρ̄_erro; distância entre os dois | `fleiss_agreement.py`, `dependence.py`, `confidence_scale.py` |
| 344-77 | alfa 0,05 bilateral; Holm sobre os três; p bruto e corrigido; tamanhos de efeito com IC | `holm_bonferroni.py`, `confirmatory_tests.py`; IC: `bootstrap.py` |
| 344-79 | unânimes em B1 fora; sem contribuição estruturada fora da exposição, por pergunta | `unanimous_filter.py`, `exposure_eligibility.py`, `missingness.py` |
| 344-81 | ausência sem imputação; confiança pareada; taxa de rejeição por condição | `missingness.py`, `confidence_channel.py` |
| 344-83 item 1 | distância ρ̄_comportamento − ρ̄_erro | `dependence.py` (`distancia_comportamento_menos_erro`) |
| 344-83 item 3 | assimetria por par ordenado de modelos | `pair_asymmetry.py` |
| 344-83 item 5 | colisão literal, por par de autores, nunca o texto | `literal_collision.py` |
| 344-83 itens 4 e 6 | efeito da posição na lista; auditoria de normalização | **não implementados aqui**; a ordem sorteada já está em `Observation.peer_order` e o critério J mede o efeito de ordem |

Fora de escopo e não implementado: a verificação de que nenhuma entrada de segunda onda continha a saída de segunda onda de outro participante (344-71, "Assumption check"). A simultaneidade vale pelo desenho do runner; o relatório não a confere.

### 8.2 Regra dos fundamentos (`new_grounds`)

- **Fundamento** = alvo de uma relação `derived_from`, `evidenced_by` ou `documents` (as mesmas do extrator da tabela tidy) **declarada** no bloco da contribuição, aceita ou não pelo validador. Em dados reais (11/11/2026, 501 linhas de B1) 19 contribuições declararam fundamento e o validador aceitou 0: a regra de tipos admite, por exemplo, inferência → afirmação, e recusa decisão → opção ou decisão → evidência. Medir só o aceito tornaria `new_grounds` sempre falso.
- O alvo é classificado, sem juízo semântico, contra o Working Context da execução e a própria contribuição:
  - `base`: item do contexto sem autor (opção, evidência), ou id que não existe em lugar nenhum (conta como declarado); chave = id;
  - `local`: outra unidade da própria contribuição que não a decisão; chave = conteúdo normalizado (minúsculas, espaços colapsados), porque `k1` é reutilizado em toda contribuição;
  - `own`: contribuição anterior do próprio participante (aparece em B3, EP e E);
  - `peer`: contribuição de outro participante;
  - alvo que é a decisão que seleciona a opção não é fundamento (é a posição).
- Fundamento **novo** = presente na segunda onda e ausente entre os da própria B1 (mesma classe, mesma chave).
  - **Estrita:** só `base` e `local` contam. `peer` não conta.
  - **Permissiva:** `base`, `local` e `peer` contam.
  - `own` nunca conta, nas duas.
- O resultado sai como **intervalo entre as duas leituras**, e cada estatística sai nas duas (a estrita é a que o registro nomeia).
- Limite conhecido: citar como fundamento a opção que se acaba de escolher (`derived_from option-b`) é fundamento `base` novo, lido ao pé da letra. Reduz rate(c) onde isso acontece.

### 8.3 Estatísticas

- **rate(c)** = `changed_position` E NÃO `new_grounds`, sobre os pares participante-pergunta válidos em c. Para B2, "mudou" = opção de B2 ≠ opção de B1, com os fundamentos de B2 comparados aos de B1. Par válido: elegível em B1 (posição válida e contribuição estruturada) e com posição válida em c.
- **Δ_self** = rate(B3) − rate(B2); **Δ_herd** = rate(E) − rate(B3). Calculados sobre os pares válidos **nas duas** condições (o mesmo conjunto do McNemar). Com dados faltando, podem diferir da subtração das taxas marginais, que saem sobre os pares de cada condição.
- **McNemar exato bilateral:** b e c são os pares discordantes; p = min(1, 2 · P(Bin(b+c, ½) ≤ min(b, c))); sem discordantes, p = 1.
- **Dispersão** de uma pergunta = 1 − fração das posições na opção modal (o registro não fixa o índice; é diferente da dispersão do critério B). Medida em B3 e em E sobre os participantes elegíveis com posição válida nas duas, mínimo 2.
- **Wilcoxon** pareado bilateral sobre a mudança de dispersão (E − B3) por pergunta. Zeros saem. Empates recebem postos médios. Exato (permutação dos sinais, condicionada aos postos, com os postos dobrados para ficarem inteiros) até 50 diferenças não nulas; acima disso, aproximação normal com correção de empates na variância e continuidade de 0,5. O método sai no relatório.
- **Holm–Bonferroni** sobre os três testes confirmatórios, separadamente em cada leitura de `new_grounds`; p bruto e p corrigido lado a lado.
- **Tamanhos de efeito:** diferença de proporções (Δ) e diferença média da dispersão, com IC bootstrap percentil por pergunta (`ClusteredBootstrap`); para os Wilcoxon, também a correlação bisserial por postos (W+ − W−)/(W+ + W−) e a mediana da mudança.
- **Canal da confiança** (exploratório, sem correção): confiança → posto (baixa 1, média 2, alta 3); mudança = posto em E − posto em B3, só onde está declarada nas duas condições e há posição válida nas duas; ausência nunca vira zero e a contagem dos excluídos sai. Grupos pela relação da maioria dos pares com a própria B1 do participante: `maioria_concorda`, `maioria_discorda` e `sem_maioria` (nenhuma opção com mais da metade dos pares); `todos` ao lado. Os pares são os outros participantes elegíveis, com a posição de B1 (é o que E mostra).
- **ρ̄_erro** por condição (B1, B3, EP, E): média dos phi par a par entre os vetores de erro, nas perguntas com gabarito; par sem variância sai da média e é contado. **N_eff(c)** = n/(1 + (n−1)ρ̄_erro(c)) com n = participantes distintos do painel (o mesmo n em todas as condições). **Δ_N_eff** = N_eff(B1) − N_eff(E), IC bootstrap. Sem teste de significância.
- **Varredura analítica:** N_eff para ρ̄ de 0,01 a 1 e n em {4, 5, 8, ∞} (∞ dá 1/ρ̄), mais o n do painel se for outro; os ρ̄ observados entram como âncoras, não como limite. Rotulada como analítica.
- **ρ̄_comportamento:** kappa de Fleiss de B1 nas contestáveis. Por pergunta, P_i = fração de pares do painel que concordam; κ = (P̄ − P_e)/(1 − P_e), com P_e das frequências de opção pooled. Descritivo, fora da tabela de N_eff. **Distância** = ρ̄_comportamento − ρ̄_erro(B1), com IC. O bootstrap dessa seção reamostra dentro de dois estratos (gabarito e contestável).
- **Assimetria:** por par ordenado (puxa j → puxado i), entre os casos em que i e j discordavam em B1, a fração em que i termina na posição de j sem fundamento novo, em E e (linha de base) em B3. Descritiva, sem inferência.
- **Colisão literal:** strings byte a byte idênticas entre as afirmações declaradas de dois participantes na mesma pergunta, em B1 e em B2 (as ondas cegas). Contagens por par de autores (agentes); nunca o texto. `colisoes_em_decisoes` separa as que são conteúdo de uma `decision` nos dois.

### 8.4 Variantes de exclusão

- **Principal (registrada):** pergunta unânime em B1 (todas as posições válidas iguais, mínimo duas) sai de toda a análise desta seção, inclusive da dependência. A taxa de descarte é resultado (`descarte_de_unanimes_em_b1`).
- **Alternativa (desvio aprovado em 11/11/2026):** unânimes mantidas.
- As duas saem lado a lado, e cada uma nas variantes da regra 3 (`com_indiretas`, `sem_indiretas`).
- **Sem contribuição estruturada:** o participante sem unidade aceita pelo validador em B1 sai da análise de exposição naquela pergunta, e a saída fica listada por pergunta (`ausencia`). Na prática o participante também fica sem posição, então já sai pela posição inválida.
- As duas variantes valem também para o painel homogêneo de contraste. Atenção: um painel de uma só instância tende a ser unânime, então a variante principal pode deixá-lo com poucas perguntas ou nenhuma (ρ̄ indefinido); a alternativa é a que o descreve como referência de dependência máxima.
