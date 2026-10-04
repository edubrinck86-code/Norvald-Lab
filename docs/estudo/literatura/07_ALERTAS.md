---
id: DESK-ALERTAS
tipo: Achados que alteram posicionamento
data: 2026-10-04
prioridade: ler antes dos demais
---

# Alertas — o que muda em relação ao que está registrado

Seis achados posteriores ao pré-registro de 29/09/2026 (osf.io/5vy6e) que alteram
o que a tese e o CC podem reivindicar. Todos conferidos na fonte, dois deles por
checagem dupla.

---

## 1. A fórmula de N_eff não é só do Kohli — RoPoLL tem a mesma

**Acharya, Pan & Verkhovsky (2026) — ROPOLL: Robust Panel of LLM Judges**
[arXiv:2606.30931](https://arxiv.org/abs/2606.30931) · conferido no HTML completo

Corollary 1, Seção 3.5, enunciado literal:

> "Defining the effective jury size N_eff ≜ N/(1+(N−1)γ), the MSE rate is tr(Σ)/N_eff."

É a identidade algébrica idêntica, aplicada ao mesmo objeto — painel de juízes LLM —
derivada de forma independente. Correlações empíricas: γ̄ ∈ [0,49–0,71] em HelpSteer-2
e UltraFeedback; γ̄_W ∈ [0,45–0,53] (Tabela 3). Sob γ ∈ [0,3–0,5] o tamanho efetivo do
júri satura em **N_eff ≈ 2–3**, e é por isso que eles usam comitês de três.

**Não citam Kish** — derivam do próprio modelo de júri equicorrelacionado.

### Consequência
TESE-003 e TESE-004 tratam Kohli como "o precedente direto", no singular. São dois,
chegando pelo mesmo resultado por caminhos diferentes no mesmo ano. Citar só Kohli e
ser apresentado ao RoPoLL em revisão é pior do que citar os dois agora.

---

## 2. O efeito da exposição já foi documentado — mas não em N_eff

**Shu (2026) — Unanimity Without Persuasion: A Single Round of Debate Erases the
Disagreement That Verification Needs**
[arXiv:2609.26145](https://arxiv.org/abs/2609.26145) · conferido na fonte

Painel heterogêneo de 7 juízes, 7 provedores, uma rodada cega seguida de três rodadas
de debate, 600 candidatos de correção de código com gabarito executável.

```
unanimidade      39,5%  →  95,2%   na rodada 1
                          98,6%   rodada 2
                          99,3%   rodada 3
acurácia                  move menos de 1 ponto
inversões de veredito     96,3% seguem a maioria dos pares exibida
rodada 3                  toda decisão errada é unânime
```

Controles de coorte idêntica: reconsideração sem pares reproduz 79,6% do colapso;
rótulos reais sem raciocínio reproduzem 91,5%; o debate completo acrescenta apenas
4,3 p.p. sobre rótulos-só (IC 95% clusterizado [0,7–8,1]).

### Consequência, e ela é dupla

**Ruim:** o fenômeno que a tese ia descobrir já está documentado, com desenho melhor
(7 juízes, gabarito executável, controles de coorte) e com números fortes.

**Bom, e verificado por grep no texto completo:** o paper **não usa** "effective sample
size", "n_eff", "Kish", "design effect" nem "intraclass correlation" em lugar nenhum.
Mede unanimidade, taxa de pivô e flips.

A contribuição da tese deixa de ser *descobrir que a exposição destrói independência*
e passa a ser *quantificar isso no numerário de N_eff e mostrar que esse é o número
certo de reportar*. É contribuição de instrumentação, não de descoberta. Isso precisa
estar escrito assim, ou é rejeitada como redundante.

---

## 3. Ninguém mediu N_eff POR RODADA de exposição

Confirmado nas seis frentes: nenhum trabalho encontrado computa N_eff antes e depois
da exposição, nem reporta a trajetória N_eff(t).

Como o colapso é concentrado na primeira rodada — Shu: 93,1% do colapso total na
rodada 1; Li, Liu & Yuen ([2609.35279](https://arxiv.org/abs/2609.35279)): 58,9% dos
colapsos na rodada 1 — a curva de decaimento de N_eff deve ter forma característica.
Caracterizá-la é o que resta de aberto, e é estreito.

---

## 4. Elahi et al. v2 já desconta por dependência — a descrição em TESE-003 ficou errada

**Elahi, Curry & Di Eugenio (2026), v2 de 21/09/2026**
[arXiv:2606.13591](https://arxiv.org/abs/2606.13591) · conferido no HTML da v2

TESE-003 §3 diz que eles "assumem independência condicional e registram que a
suposição é violada nos próprios resultados, seguindo adiante mesmo assim". **Isso era
verdade na v1. A v2 propõe a correção.**

Introduz um *shared dependence discount* `w ∈ (0,1]`:

```
concordância:   c = σ(w(ℓ₁+ℓ₂))
discordância:   c = σ(w|ℓ₁−ℓ₂|)
```

`w` ajustado em validação. Resultados: `w* < 1` em **118 de 120 configurações**,
**mediana w* = 0,65** — a evidência fundida vale cerca de dois terços do que a
independência implicaria. ECE cai de 0,100 → 0,055 e de 0,112 → 0,063. Escopo: 5
benchmarks, 30 pares de modelos.

E mostram que o desconto é **matematicamente equivalente a temperature scaling com
T = 1/w**, concluindo que o custo principal da independência violada é um erro de
escala de um único escalar.

### Consequência
É o precedente direto do C_adj, e calibrado em dados em vez de elicitado. O argumento
de que 0,20 do índice precisa ir para um termo de dependência fica difícil de sustentar
contra "um escalar ajustado em validação resolve".

---

## 5. A forma do CC tem derivação ótima publicada

**Balasubramanian, Podkopaev & Kasiviswanathan (2026) — Dependence-Aware Label
Aggregation for LLM-as-a-Judge via Ising Models** · ICML 2026
[arXiv:2601.22336](https://arxiv.org/abs/2601.22336) · conferido na fonte

Para acoplamentos *class-independent*, o log-odds de Bayes **se reduz a um voto linear
ponderado com parâmetros ajustados por correlação**. Provam resultados de separação:
preditores que assumem independência condicional permanecem estritamente subótimos
mesmo com K → ∞.

Acurácia (Tabela 1, média de 20 trials):

```
                Ising class-dep / class-indep    CI-WMV / CI-UMV
Relevance              0,90 / 0,88                 0,82 / 0,80
Toxicity               0,79 / 0,77                 0,72 / 0,69
Summarization          0,68 / 0,64                 0,61 / 0,60
```

Frase deles: *"se os juízes compartilham um modo de falha, a concordância deveria ser
descontada em vez de contada múltiplas vezes."*

### Consequência
Bom: a forma linear do CC não é arbitrária, tem derivação ótima. Ruim: a derivação é
deles.

---

## 6. A objeção "C_adj não é mensurável por consumidor de API" caiu

Três caminhos independentes para estimar dependência sem o que você dizia faltar:

- **CAPA** (Goel et al., ICML 2025, [2502.04313](https://arxiv.org/abs/2502.04313)) —
  similaridade por sobreposição de **erros**, ajustada por acaso. Computável de
  respostas num conjunto rotulado.
- **CARE** ([2603.00039](https://arxiv.org/abs/2603.00039)) — recupera confundidores
  latentes **sem ground truth**, da própria matriz de scores. Reduz erro em até 26,8%
  em 12 benchmarks.
- **Elahi v2** — ajusta `w` em validação.

### Consequência
PESQUISA-1000 e o ADR-1000 argumentam que C_adj dependia de informação indisponível e
por isso virou âncora. Essa premissa não se sustenta mais. O que não quer dizer que a
conclusão esteja errada — o AROF continua valendo — mas o **motivo** precisa mudar.

---

## 7. Risco separado: os pesos do CC

**Paruolo, Saltelli & Saisana (2013, JRSS-A)** ·
[arXiv:1104.3009](https://arxiv.org/abs/1104.3009) · conferido nos metadados
**Becker, Saisana, Paruolo & Vandecasteele (2017), Ecological Indicators** ·
[PMC5473177](https://pmc.ncbi.nlm.nih.gov/articles/PMC5473177) · conferido no texto

Quando os componentes de um índice composto são correlacionados — e os do CC são, por
construção: C_adj e I medem lados da mesma coisa — **o peso nominal não corresponde à
importância efetiva**, e frequentemente é impossível obter a importância declarada
mesmo reotimizando os pesos no simplex.

Caso documentado: peso nominal 0,4 produziu razão de correlação normalizada de 0,303
contra alvo de 0,400.

### Consequência
`0.30·E + 0.25·R + 0.20·C_adj + 0.15·I + 0.10·H` não significa que E tem 30% da
importância. Becker et al. dão o método para medir o gap e reotimizar. Se os pesos
elicitados vão ser defendidos, isso precisa ser rodado.

---

## Resumo acionável

| # | Ação | Onde |
|---|---|---|
| 1 | Acrescentar RoPoLL como co-precedente | `03_Posicionamento`, `04_Confronto` |
| 2 | Reescrever a contribuição como instrumentação, não descoberta | `01_Protocolo` §2, `04_Confronto` §3 |
| 3 | Acrescentar N_eff(t) por rodada ao desenho | decisão sua — ver nota abaixo |
| 4 | Corrigir a descrição de Elahi et al. (v2) | `03_Posicionamento` §3 |
| 5 | Posicionar o CC contra Balasubramanian et al. | ADR-1000 / PESQUISA-1000 |
| 6 | Reescrever o motivo pelo qual C_adj virou âncora | PESQUISA-1000 |
| 7 | Rodar a análise de importância efetiva dos pesos | ADR-1000 |

**Sobre a ação 3 e o pré-registro:** o desenho registrado tem duas levas, não uma
trajetória. Acrescentar rodadas agora seria mudar o desenho depois de registrar, o que
é exatamente o que o registro existe para impedir. O caminho limpo é registrar o
estudo da trajetória como um **segundo** pré-registro, e manter o primeiro como está.
