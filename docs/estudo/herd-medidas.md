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
