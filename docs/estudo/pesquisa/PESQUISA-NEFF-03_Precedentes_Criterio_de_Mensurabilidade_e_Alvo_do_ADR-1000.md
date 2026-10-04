---
id: PESQUISA-NEFF-03
type: Registro de pesquisa e decisão
status: Achados conferidos na fonte; pendências operacionais listadas em §9
version: 1.0.0
date: 2026-10-04
references:
  - docs/tese/01_Protocolo_Experimental.md
  - docs/tese/03_Posicionamento_e_Procedencia.md
  - docs/tese/04_Confronto_com_Kohli_2026.md
  - docs/tese/05_Adendo_Escopo_Descritivo_e_Alteracao_Sob_Exposicao.md
  - docs/pesquisa/PESQUISA-NEFF-02_Exposicao_Estimador_e_Colisao_Literal.md
  - docs/pesquisa/PESQUISA-1000_Correlacao_Entre_Especialistas_e_Efeito_Manada.md
---

# Precedentes, critério de mensurabilidade e redefinição do alvo do ADR-1000

Registro da sessão de 04/10/2026. Levantamento de literatura com seis frentes de busca,
seguido de verificação direta na fonte dos itens que alteram decisão. Os sete arquivos de
apoio (`00_INDICE` a `07_ALERTAS`) estão no Desk do autor, fora do repositório.

---

## 1. Precedentes, depois da triagem

| Trabalho | Estado após verificação |
| --- | --- |
| Kohli (2605.29800) | **Sobrevive inteiro.** Único precedente forte |
| RoPoLL (2606.30931) | Co-precedente da **fórmula**; o valor de γ fica enfraquecido |
| Shu (2609.26145) | Não refutado — mede outro objeto; dimensiona Δ_herd |
| Balasubramanian et al. (2601.22336) | Não cai; ocupa a forma ótima do CC |
| Elahi et al. v2 (2606.13591) | Não cai; concorrente de parcimônia do `C_adj` |
| CARE (2603.00039) | Eliminado **por escopo**: exige 11–20 juízes |
| Liu (2607.10139) | Eliminado: **consome** ρ, não estima |

### 1.1 Kohli é o precedente que resiste

- 9 juízes, **7 famílias**, voto cego sem comunicação.
- Robustez testada: T=0,5, três variantes de prompt (reformulação, ordem de rótulos
  invertida), CoT, quatro tipos de tarefa → **n_eff estável entre 1,94 e 2,18**.
- Referência: voto majoritário de **100 anotadores humanos** (ChaosNLI), não um modelo.
- Sem método próprio a vender.

Consequência favorável ao desenho: se o piso cego é estável sob configuração, um Δ medido
sob exposição não é ruído de configuração.

### 1.2 RoPoLL — a fórmula vale, o número não

Corollary 1, §3.5, literal: *"Defining the effective jury size N_eff ≜ N/(1+(N−1)γ), the MSE
rate is tr(Σ)/N_eff."* Derivação independente, **não cita Kish**. Painel de 13 juízes
open-weight, 4B–675B (DeepSeek-V3.1, Qwen3-235B/32B, Mistral-Large-3, Nemotron-30B/9B,
Gemma-27B/12B/4B, Magistral-Small, Ministral-14B/8B). γ̄ ∈ [0,3–0,7]; γ̄_W ∈ [0,45–0,53].
Satura em N_eff ≈ 2–3.

Quatro ressalvas conferidas no HTML completo:

1. **Rubrica estruturada compartilhada** por todos os 13 juízes (Definition 5: *"sharing a
   common rubric ρ and parser φ but employing distinct backbones"*). Causa comum: parte do γ
   é a rubrica, não os modelos. Não separam.
2. **Nenhuma análise de sensibilidade.** γ é apresentado como observação fixa de uma
   configuração única.
3. Em UltraFeedback a referência é **GPT-4 como anotador** — julgamento de IA contra
   julgamento de IA.
4. Autores: Anish Acharya, Kris W. Pan, Brian Verkhovsky — **todos Amazon Web Services**. O
   paper preserva o painel e substitui o agregador (mediana geométrica). Mesma álgebra do
   Kohli, recomendação operacional inversa.

**Como citar:** como co-precedente da identidade algébrica; o valor de γ como *reportado por*,
nunca como estabelecido.

### 1.3 Correção ao registro anterior — Liu

`06_Composicao_de_confianca_CC.md` e o índice do Desk descrevem Liu (2607.10139) como lei que
**estima** dependência a partir de respostas finais. Está errado.

*"LLMs as a Jury: Cross-Model Consensus Can Outperform Process Reward Models for LLM
Reasoning"*, Ning Liu (pesquisador independente). A lei é paramétrica-livre mas **consome**
`(a, ρ, s)` — acurácia média do membro, correlação média de erro par-a-par, taxa de equívoco
compartilhado — e prediz acurácia de consenso (MAE 0,028). As três entradas exigem gabarito.
Não serve como estimador de `C_adj`.

### 1.4 Afiliação não é argumento

Dois dos papers são da AWS (RoPoLL; e Balasubramanian, Podkopaev & Kasiviswanathan, este com
afiliação conjunta UC Davis). Ambos diagnosticam dependência e propõem o agregador que a
corrige. O padrão é registrável; a inferência de que o incentivo produziu o número **não tem
evidência** e não é usada aqui. A fragilidade do γ do RoPoLL é metodológica e valeria igual
vindo de qualquer instituição.

---

## 2. Temperatura zero — o que ela faz com ρ

Kohli e RoPoLL rodam a **T=0**. Consequências, nenhuma delas endereçada por nenhum dos dois:

**T=0 não reduz incerteza; reporta incerteza zero.** A distribuição `p(y|x)` não muda com a
temperatura — temperatura é regra de amostragem. Observa-se o argmax e descarta-se o resto de
`p`. A entropia verdadeira permanece; a observada é 0.

**ρ fica sendo correlação de argmax, não de crença.** Dois juízes em `p = [0,51 , 0,49]` que
caem no mesmo rótulo contam igual a dois juízes em `p = [0,99 , 0,01]`. Estados epistêmicos
opostos, contribuição idêntica para ρ̄. O primeiro caso é justamente onde a exposição ao par
mais deveria mover.

**Decomposição da variância.** Em `ρ = σ²_comum / (σ²_comum + σ²_idiossincrática)`, zerar a
parcela idiossincrática **infla ρ por construção**. γ̄ ≈ 0,5 é medido no regime que maximiza a
correlação aparente.

### 2.1 Duas rotas para recuperar `p`

| Rota | Exigência | Estado |
| --- | --- | --- |
| Logprobs do token da resposta | provedor expor logprobs | **conferir por provedor nos 4 modelos** |
| Repetição a T>0 | N amostras por juiz por pergunta | runner suporta; rota trava em `le=1` |

A segunda reposiciona a repetição no protocolo: deixa de ser controle de ruído e passa a ser
**o instrumento que recupera a distribuição que T=0 esconde**. Muda o dimensionamento.

Observação sobre a condição B2: hoje mede "a opção selecionada mudou?", que é o argmax de
novo. Duas respostas de prosa inteiramente diferente e mesma opção registram variância zero.

### 2.2 Assimetria nos dados do próprio Kohli

A referência dele é o ChaosNLI, que traz **100 anotadores por item**, isto é, entropia humana
por item. Ele compara estimativas pontuais dos juízes contra uma distribuição humana. Ter os
dois lados em distribuição e comparar entropia de painel contra entropia humana é medida que
os dados dele permitem e que ele não faz.

---

## 3. Composição dos painéis — os dois são heterogêneos

| | Painel | Resultado |
| --- | --- | --- |
| Kohli | 9 juízes, 7 famílias | n_eff ≈ 2,18 |
| RoPoLL | 13 juízes, múltiplas famílias | γ̄ ≈ 0,5; N_eff ≈ 2–3 |

Diversidade de fornecedor já está **dentro** da medida, e não foi suficiente. γ̄ ≈ 0,5 é o
número de um painel multi-família.

**Nenhum dos dois decompõe γ por família.** Verificado no HTML completo do RoPoLL: todos os γ̄
reportados são sobre o painel misto, sem recorte, e não há frase comparando pares
intra-família com pares cross-família. É exatamente o que o painel de contraste do protocolo
(§8, 4 modelos da mesma família) mede.

Expectativa calibrada pela literatura: o Δ entre painéis deve ser **positivo e modesto**.
Nogueira et al. (2607.02808) — famílias diferentes realizam 0,43–0,44 do ganho de
independência, contra <0,3 no mesmo modelo: heterogeneidade compra menos da metade, não tudo.
ReasonOps (2605.29192) — na identificação do modelo pelo traço (macro-AUC 0,987) os piores
casos one-vs-rest se concentram em pares intra-família.

---

## 4. Enunciado da contribuição

O que existe, separado:

```
N_eff(cego)                      Kohli, RoPoLL     ~2, γ̄ ≈ 0,5
colapso sob exposição            Shu               39,5% → 95,2%, sem N_eff
N_eff(exposto) − N_eff(cego)     ninguém
```

Kohli e RoPoLL medem a condição B1 — dependência **estrutural**, de corpora sobrepostos, sem
comunicação. É o piso, não o efeito. Shu mede a condição exposta mas no numerário errado:
conferido por busca no texto completo, **não usa** "effective sample size", "Kish", "design
effect" nem "intraclass correlation".

> A dependência estrutural entre juízes LLM cegos já está quantificada. O colapso de desacordo
> sob exposição também está documentado. O que não existe é a mesma quantidade medida nas duas
> condições, no mesmo instrumento — quanto da perda de independência é estrutural e quanto é
> adquirida na exposição.

A base vem pronta e não precisa ser repetida. Isso não é perda de prioridade: é redução de
escopo de execução.

---

## 5. Critério de mensurabilidade

Critério declarado pelo autor em 04/10/2026: **uma variável só entra se tiver condição de
verdade externa ao julgamento.** Não se mede qualidade, mérito ou valor; mede-se dado.

### 5.1 Variáveis com condição de verdade

| Variável | Condição de verdade |
| --- | --- |
| erro contra gabarito | chave declarada; certo ou errado |
| mudança de posição B3→E | ID da opção selecionada; mudou ou não |
| colisão literal entre autores | conteúdo normalizado idêntico; colidiu ou não |
| presença de referência nova no esquema | nó existe ou não existe |

### 5.2 Variáveis dependentes de convenção

| Variável | Do que depende |
| --- | --- |
| ρ̄_comportamento | escolha de representação |
| dispersão do painel | escolha de métrica de distância |
| N_eff | transformação de ρ̄; herda o que ρ̄ for |
| confiança declarada | autorrelato; overconfidence documentada (Xiong et al.) |

### 5.3 Três consequências

1. **Uma só das quatro variáveis verificáveis alimenta N_eff** — erro contra gabarito. As
   outras três medem comportamento, não erro. Pelo critério do autor, N_eff sem o braço de
   gabarito é índice sobre convenção.
2. **"Referência nova no esquema" é binária como medida e não como construto.** O registro é
   verificável; a ausência de registro não prova ausência de inferência nova. É o que o
   `TESE-005` §7 já afirma. Manter, declarada assim.
3. **Dependência não é observável em n=1.** É propriedade de uma distribuição sobre itens.
   Nenhuma observação isolada é binária a respeito dela. Por isso todo estimador existente
   exige ou muitos itens rotulados, ou muitos juízes.

---

## 6. Redefinição do alvo do ADR-1000

Objetivo declarado do ADR-1000: substituto maior e melhor para o `C_adj`, **acessível a
consumidor de API**.

| Candidato | Sem gabarito | Painel estreito (3–5) |
| --- | --- | --- |
| CAPA (2502.04313) | não | sim |
| Elahi `w` (2606.13591) | não | sim |
| Liu (2607.10139) | não (ρ é entrada) | sim |
| CARE (2603.00039) | **sim** | **não** |

CARE — *Confounder-Aware Aggregation for Reliable LLM Evaluation*, Zhao, Shin, Huang, Namburi
& Sala (UW–Madison) — é o único genuinamente sem rótulo: entrada é só a matriz de scores
n×p; recupera qualidade latente Q e confundidores compartilhados C; 17,37% de melhora relativa
sobre média, 12,75% sobre voto majoritário, até 26,8%, em 12 benchmarks. Mas a decomposição
esparsa-mais-baixo-posto exige diversidade de juízes suficiente: demonstram com **11–20
juízes** e centenas a milhares de itens. Com p=4 não se separa Q de C.

**A interseção é vazia.** O buraco do ADR-1000, enunciado em uma linha:

> Estimar dependência entre 3–5 modelos, por item, sem gabarito.

### 6.1 Consequência: a tarefa é validação, não busca

A premissa do AROF é a única forma candidata que quebra a restrição de n=1: se a similaridade
**estrutural** do traço prediz co-falha, há sinal de dependência por item, de painel estreito,
sem rótulo — porque o traço é observável a cada chamada.

É o cruzamento que o ReasonOps deixa aberto: prova que o traço identifica o modelo (macro-AUC
0,987) e que prediz correção pelo processo (WP-AUC 0,701 cross-dataset), e nunca pergunta se a
similaridade estrutural entre traços de modelos diferentes prediz erro **no mesmo item**.

As restrições impostas pelo próprio ADR-1000 eliminam todos os candidatos menos um, e esse um
é não-validado. O experimento em curso é o desenho que valida: as 12 perguntas com gabarito
dão a co-falha real, o traço dá a similaridade estrutural, e a pergunta é se a segunda prediz
a primeira — exatamente a formulação do `01_Protocolo_Experimental.md` §5.1.

### 6.2 O motivo da âncora muda

`PESQUISA-1000` justifica o `C_adj` como âncora por indisponibilidade de informação ao
consumidor de API. Essa premissa caiu: CAPA, CARE e Elahi `w` são três caminhos distintos. O
motivo que **não** cai é o critério de §5: não se compõe índice sobre componentes sem condição
de verdade — e dos cinco componentes do CC, nenhum tem. A decisão se mantém; a justificativa
precisa ser substituída.

Risco separado e ainda aberto: Paruolo et al. (2013) e Becker et al. (2017) — com componentes
correlacionados, peso nominal ≠ importância efetiva. `C_adj` e `I` são correlacionados por
construção. A análise de importância efetiva não foi rodada.

---

## 7. Variável nova — cruzamento de duas medidas binárias

Por par de autores, por item, por condição, duas variáveis binárias já disponíveis no
instrumento:

- mesma opção selecionada? (ID da opção)
- colisão literal? (`colisoes_literais`, em `backend/application/arof/seed_observation.py`)

Cruzadas, quatro contagens:

```
opção igual     × colidiu
opção igual     × não colidiu
opção diferente × colidiu
opção diferente × não colidiu
```

Painel estreito, sem gabarito, por item. Não é estimador de dependência — é decomposição dela.
É a única construção levantada nesta sessão que satisfaz as duas restrições do ADR-1000 e roda
com o que já está implementado. **Não está no protocolo.**

A quarta célula só existe porque as unidades `decision` foram excluídas da contagem de colisão
(`PESQUISA-NEFF-02` §6).

### 7.1 Limitação do detector de colisão, a registrar onde o número aparecer

Colisão literal mede **identidade literal, não concordância**. Erra nas duas direções:

- paráfrase da mesma proposição → não colide, e é dependência;
- expressão idêntica com sentido diferente no contexto → colide, e não é.

Nenhuma das duas taxas está quantificada. O número é **piso** de dependência de conteúdo.

---

## 8. Conflitos com o TESE-005

| Ponto | Conflito |
| --- | --- |
| §5 — braço com gabarito como "complementar" | Contraria `01_Protocolo` §5.1 (*"não é complemento"*) e §7 (*"ρ̄_erro é o que a fórmula de N_eff pede"*) |
| §6 — `Δ_pares` | Duplica `Δ_herd`, já definido em `01_Protocolo` linha 66 com o mesmo contraste e sinal |
| §3 — proibição de implicações | Correta; mas deixa a pergunta "por que importa" sem resposta |

### 8.1 Três argumentos independentes de que o braço com gabarito é obrigatório

1. **Precedente:** Kohli e RoPoLL definem N_eff sobre erro relativo a referência. Dependência
   de posições não entra na fórmula sem derivação nova.
2. **Desenho:** Δ(N_eff) exige a mesma quantidade nas duas condições. Se a quantidade não
   estiver ancorada em erro, não é comparável com o piso que a literatura fornece.
3. **Critério do autor (§5):** é a única variável do desenho cuja condição de verdade não é um
   julgamento.

### 8.2 Sobre §3 — separar escopo de implicação

O resultado permanece descritivo. A implicação normativa pode ser **citada**, não produzida:
Shu mede acurácia contra gabarito executável e mostra que ela não se move enquanto a
unanimidade vai de 39,5% a 95,2%. Importar o achado, atribuído, preserva §3 intacto.

### 8.3 Sobre §8 — a ressalva de sensibilidade pode ser empírica

"ρ=0 produz N_eff=n" é formalmente correto e fraco na prática. O intervalo medido para este
objeto é γ̄_W ∈ [0,45–0,53] e γ̄ ∈ [0,3–0,7] (RoPoLL), n_eff 1,94–2,18 em 9 juízes (Kohli).
Citar o intervalo empírico em vez do limite teórico.

---

## 9. Pendências

| # | Item | Onde |
| --- | --- | --- |
| 1 | Acrescentar RoPoLL como co-precedente da fórmula, com as quatro ressalvas | `03_Posicionamento`, `04_Confronto` |
| 2 | Reescrever a contribuição como medida conjunta nas duas condições | `01_Protocolo` §2, `04_Confronto` §3 |
| 3 | Corrigir a descrição de Elahi et al. (descreve a v1) | `03_Posicionamento` §3 |
| 4 | Resolver o conflito do §5 — o braço com gabarito é obrigatório | `05_Adendo` |
| 5 | Substituir `Δ_pares` por `Δ_herd` | `05_Adendo` §6 |
| 6 | Substituir a justificativa da âncora do `C_adj` pelo critério de §5 | `PESQUISA-1000` |
| 7 | Redimensionar o *n* pelo tamanho de efeito que o Shu implica | `01_Protocolo` §6 |
| 8 | Conferir disponibilidade de logprobs nos quatro provedores | — |
| 9 | Destravar `repetitions` (`RunExperimentDTO`, hoje `ge=1, le=1`) | `backend/api/arof_routes.py` |
| 10 | Acrescentar o cruzamento de §7 ao protocolo | `01_Protocolo`, `02_Mapa_de_Teste` |
| 11 | Rodar análise de importância efetiva dos pesos do CC | `ADR-1000` |
| 12 | Registrar N_eff por rodada como **segundo** pré-registro | — |

Ordem: o piloto de discordância precede tudo. Sem 30–70% de desacordo na leva cega não há Δ a
medir, e nenhum argumento desta sessão sobrevive a isso.

---

## 10. Invariante

> A literatura fornece o piso cego e documenta o colapso sob exposição, em numerários
> diferentes. O que o estudo produz é a mesma quantidade nas duas condições, no mesmo
> instrumento. Nenhuma variável entra sem condição de verdade declarada, e nenhuma medida
> recebe interpretação normativa por definição.
