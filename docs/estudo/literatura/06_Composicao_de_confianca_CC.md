---
id: DESK-06
tema: Composição de confiança — agregação, quantificação de incerteza e índices compostos
data: 2026-10-04
---

# Composição de confiança (CC)

O CC é um índice composto: combina componentes elicitados num escalar
(`0.30·E + 0.25·R + 0.20·C_adj + 0.15·I + 0.10·H`). Três literaturas distintas tocam
nisso e nenhuma delas conversa com as outras:

1. **agregação de opinião / fusão de evidência** — como combinar julgamentos dependentes;
2. **UQ em LLM** — se a confiança declarada por um modelo é calibrada o bastante para entrar
   numa soma ponderada;
3. **teoria de indicadores compostos** — o que um peso nominal significa quando os
   componentes são correlacionados.

**Resumo em uma linha:** a *forma* do CC tem derivação ótima publicada (não é arbitrária,
mas também não é sua), o *termo de dependência* tem precedente calibrado em dados, e os
*pesos* têm um problema metodológico conhecido que ainda não foi endereçado.

---

## 1. O precedente direto do C_adj

### Elahi, Curry & Di Eugenio (2026), v2 — shared dependence discount
- [arXiv:2606.13591](https://arxiv.org/abs/2606.13591) · conferido no HTML da **v2** (21/09/2026)
- Fusão de duas fontes de evidência com desconto escalar `w ∈ (0,1]`:

```
concordância:   c = σ(w(ℓ₁ + ℓ₂))
discordância:   c = σ(w|ℓ₁ − ℓ₂|)
```

- `w` ajustado em validação. **`w* < 1` em 118 de 120 configurações; mediana `w* = 0,65`.**
  ECE: 0,100 → 0,055 e 0,112 → 0,063. Escopo: 5 benchmarks, 30 pares de modelos
- Mostram que o desconto é **equivalente a temperature scaling com `T = 1/w`**: o custo
  principal da independência violada é erro de escala de um único escalar
- **É o concorrente direto do C_adj, e vence no argumento de parcimônia.** Um escalar
  ajustado em dados contra um componente de peso 0,20 elicitado. Ver `07_ALERTAS.md` §4 —
  a descrição em TESE-003 §3 está factualmente errada e descreve a v1

---

## 2. A forma linear do CC tem derivação ótima — de outra pessoa

### Balasubramanian, Podkopaev & Kasiviswanathan (2026) — Ising Models · ICML 2026
- [arXiv:2601.22336](https://arxiv.org/abs/2601.22336) · conferido na fonte
- Modela os juízes como um campo de Ising com acoplamentos par-a-par. Para acoplamentos
  *class-independent*, o log-odds de Bayes **se reduz a um voto linear ponderado com
  parâmetros ajustados por correlação**
- **Resultado de separação:** preditores que assumem independência condicional permanecem
  estritamente subótimos mesmo com K → ∞. Não é questão de amostra pequena
- Acurácia (Tabela 1, média de 20 trials):

```
                Ising class-dep / class-indep    CI-WMV / CI-UMV
Relevance              0,90 / 0,88                 0,82 / 0,80
Toxicity               0,79 / 0,77                 0,72 / 0,69
Summarization          0,68 / 0,64                 0,61 / 0,60
```

- *"se os juízes compartilham um modo de falha, a concordância deveria ser descontada em vez
  de contada múltiplas vezes"*
- **Apoia a forma, ameaça a autoria.** O CC não pode mais ser apresentado como "uma proposta
  de combinação linear": precisa ser apresentado como *instanciação operacional* dessa forma
  com componentes auditáveis, ou ser reconhecido como subconjunto

### Clemen & Winkler (1985) — Limits for the Precision and Value of Information from
### Dependent Sources · Operations Research 33(2)
- Clássico, pré-LLM. Fontes de probabilidade correlacionadas têm um **teto de informação**:
  acima de certa correlação, acrescentar fontes não melhora a precisão da combinação
- É o antecedente teórico tanto do N_eff quanto do C_adj, e nenhum dos papers de 2026 o cita
- **Vale citar.** Ancora a tese numa linhagem de 40 anos em vez de parecer reação a 2026

---

## 3. Estimar dependência sem gabarito — a objeção que caiu

### Goel et al. (2025) — CAPA · ICML 2025
- [arXiv:2502.04313](https://arxiv.org/abs/2502.04313) · conferido
- Similaridade por **sobreposição de erros**, ajustada por acaso (kappa sobre o vetor de
  acertos). Computável só de respostas num conjunto rotulado
- Detalhado em `02_Erro_correlacionado.md` e `03_Diversidade_e_capacidade.md`

### CARE (2026) — confundidores latentes sem ground truth
- [arXiv:2603.00039](https://arxiv.org/abs/2603.00039) · conferido
- Recupera estrutura de dependência **da própria matriz de scores**, sem rótulo. Redução de
  erro de até **26,8%** em 12 benchmarks
- **Este é o achado que derruba a premissa do ADR-1000.** O argumento de que C_adj virou
  âncora porque dependia de informação indisponível ao consumidor de API não se sustenta:
  há três caminhos (CAPA com rótulo, CARE sem, Elahi v2 por validação)

### Liu, N. (2026) — LLMs as a Jury: Cross-Model Consensus Can Outperform Process Reward Models
- [arXiv:2607.10139](https://arxiv.org/abs/2607.10139) · conferido no HTML · pesquisador independente
- **Correção de 04/10:** a lei **consome** ρ, não estima. Entradas `(a, ρ, s)` = acurácia média
  do membro, correlação média de erro par-a-par, taxa de equívoco compartilhado. Prediz
  acurácia de consenso, MAE 0,028; piso de erro compartilhado, erro 0,009
- A lei é paramétrica-livre (nada é ajustado), mas **as três entradas exigem gabarito**
- **Não serve como estimador de `C_adj`.** Serve para predizer o resultado do painel uma vez
  que a dependência já foi medida

---

## 4. Os componentes elicitados — a confiança declarada é usável?

Isto importa porque `E` e `I` dependem de o modelo (ou o avaliador) declarar um número.

### Xiong et al. — Can LLMs Express Their Uncertainty?
- [arXiv:2306.13063](https://arxiv.org/abs/2306.13063) · conferido
- LLMs são **sistematicamente overconfident** ao verbalizar confiança, com modas em números
  redondos (80%, 90%). Estratégias de agregação de amostras reduzem, não eliminam
- **Ameaça direta a qualquer componente elicitado do CC sem calibração posterior**

### Yang, Tsai & Yamada — verbalized confidence e calibração pós-hoc
- [arXiv:2405.02917](https://arxiv.org/abs/2405.02917) · conferido
- Confiança verbalizada é fraca cru, mas **melhora substancialmente com calibração pós-hoc**
  (temperature / isotonic sobre um conjunto de validação)
- **Combinado com Elahi v2:** ambos convergem para "o problema é escala, e escala se
  conserta com um escalar ajustado". Se o CC vai usar números elicitados, a calibração
  pós-hoc não é refinamento, é requisito

### Lin et al. (2026) — TC-ECE
- Argumentam que **um escore composto único é grosseiro demais** para capturar calibração
  condicional por tarefa: o mesmo ECE agregado esconde regimes com comportamentos opostos.
  Propõem decomposição por tipo de tarefa
- ⚠️ **Não consegui abrir a fonte primária.** Citado por terceiros. **Verificar antes de usar**
- **Ameaça de princípio ao CC**, se confirmado: é o argumento de que colapsar cinco
  componentes num escalar destrói justamente a informação que distingue os casos

---

## 5. O problema dos pesos — o mais concreto e o menos endereçado

### Paruolo, Saltelli & Saisana (2013) — Ratings and Rankings: Voodoo or Science?
### JRSS-A 176(3)
- [arXiv:1104.3009](https://arxiv.org/abs/1104.3009) · conferido nos metadados
- Quando os componentes de um índice composto são correlacionados, **o peso nominal não
  corresponde à importância efetiva**. Propõem medir importância pela razão de correlação
  (medida de sensibilidade de primeira ordem), não pelo coeficiente declarado

### Becker, Saisana, Paruolo & Vandecasteele (2017) — Ecological Indicators 80
- [PMC5473177](https://pmc.ncbi.nlm.nih.gov/articles/PMC5473177) · conferido no texto
- Dão o método para medir o gap e reotimizar os pesos para aproximar a importância desejada.
  Mostram que **frequentemente é impossível** atingir a importância declarada reotimizando no
  simplex — a correlação entre componentes impõe um limite
- Caso documentado: peso nominal 0,4 → razão de correlação normalizada **0,303** contra alvo
  de 0,400

### Consequência para o CC, explicitamente
`C_adj` e `I` medem lados da mesma coisa (dependência e independência informacional), logo
são correlacionados **por construção**. Portanto:

- `0.30·E + 0.25·R + 0.20·C_adj + 0.15·I + 0.10·H` **não significa** que E carrega 30% da
  importância do índice
- Qualquer defesa dos pesos elicitados precisa reportar a importância *efetiva* medida, não a
  nominal. É uma análise rodável com os dados que o Studio já produz
- Esta é a crítica mais difícil de responder sem rodar a análise, e a mais fácil de antecipar
  em revisão — é literatura de política pública consolidada, não especulação

---

## 6. Contexto de normalização

### Turkmen et al. (2026) — survey de agregação multi-LLM
- Mapeia o campo: votação, ponderação por confiança, fusão aprendida. Útil para situar o CC
  no espaço de desenhos existentes e evitar reivindicar novidade onde há família conhecida
- Aparece também em `01`, `02`, `03`, `05`

### OCDE/JRC — Handbook on Constructing Composite Indicators (2008)
- O manual de referência: normalização, imputação, ponderação, análise de incerteza e
  sensibilidade. É o padrão contra o qual um índice composto é avaliado fora de ML
- **Usar o checklist dele para o CC** é o caminho mais barato para blindar o índice: boa parte
  das objeções previsíveis já está catalogada ali

---

## Saldo para o CC

| Camada | Estado | Risco |
|---|---|---|
| Forma linear ponderada | derivação ótima publicada (Balasubramanian) | autoria, não validade |
| Termo de dependência `C_adj` | precedente calibrado (Elahi v2, `w*`=0,65) | parcimônia: 1 escalar vs 1 componente |
| Mensurabilidade de dependência | CAPA e Elahi exigem rótulo; CARE exige 11–20 juízes | **interseção vazia para painel de 4 sem gabarito** |
| Componentes elicitados `E`, `I` | overconfidence documentada; calibrável pós-hoc | requisito, não refinamento |
| Colapso em escalar único | contestado (Lin et al., **não conferido**) | de princípio, se confirmado |
| Pesos nominais | gap importância nominal × efetiva | **o mais concreto e ainda aberto** |

**O que fazer com isso:** três das seis linhas pedem reescrita de justificativa, não de
desenho. A única que pede trabalho novo é a última, e é uma análise de sensibilidade sobre
dados existentes.
