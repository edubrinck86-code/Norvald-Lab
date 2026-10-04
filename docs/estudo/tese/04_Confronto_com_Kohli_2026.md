---
id: TESE-004
type: Confronto Bibliográfico
status: Ativo
version: 1.0.0
date: 2026-09-28
references:
  - docs/tese/01_Protocolo_Experimental.md
  - docs/tese/03_Posicionamento_e_Procedencia.md
  - docs/pesquisa/PESQUISA-NEFF-02_Exposicao_Estimador_e_Colisao_Literal.md
---

# Confronto com Kohli (2026)

> *Nine Judges, Two Effective Votes: Correlated Errors Undermine LLM Evaluation Panels*
> Guneet Kohli · [arXiv 2605.29800](https://arxiv.org/abs/2605.29800) · 28/05/2026

É o trabalho mais próximo que existe. Este documento existe para que a tese o enfrente de frente, linha a linha, em vez de ser surpreendida por ele em revisão.

Tudo que consta na coluna **Kohli** foi conferido no corpo do paper, não no resumo.

## 1. Comparação

| | Kohli 2026 | Esta tese |
|---|---|---|
| **Tarefa** | NLI sobre ChaosNLI, 1.000 itens | Banco congelado, 2 a 4 opções mutuamente exclusivas, declaradas |
| **Painel** | 9 LLMs, 7 famílias | 4 modelos, classe de tamanho controlada |
| **Papel do modelo** | juiz avaliando um item | participante declarando posição |
| **Interação** | **nenhuma** — juízes isolados, temperatura 0.0, prompt padronizado, sem comunicação nem refinamento | **é a variável** — B1 cega, E exposta ao WC da leva 1 |
| **Estimador de ρ** | φ̄ sobre vetores binários de erro (`e_j,i = 1` se discorda do rótulo majoritário), média sobre 36 pares | mesmo estimador, subconjunto binário com gabarito |
| **ESS** | Kish, `n_eff = k/(1+(k−1)φ̄)` | idem |
| **Resultado central** | 9 juízes ≈ 2,18 votos independentes | `ΔN_eff = N_eff(B1) − N_eff(E)` |
| **Natureza da grandeza** | propriedade **estática** de um painel | efeito de **tratamento** sobre essa propriedade |
| **Temperatura** | condição sistemática, n_eff por condição: 1,94 a 2,18 | sobre ρ de erro, esperado replicar; aberto sobre ρ de conteúdo |
| **Reasoning** | CoT como condição: φ̄ = 0,456, n_eff = 1,94 — **aumenta** a correlação | fora do escopo desta publicação |
| **Agregação** | voto, modelo nulo de Condorcet, algoritmos alternativos | não agrega — mede posição declarada |
| **Ancoragem na própria resposta** | não medida | B3, e `Δ_self` é resultado reportado |

## 2. O que a tese não pode mais reivindicar

1. **Aplicar ESS a painel de LLM correlacionado.** Feito, com número.
2. **Caracterizar N_eff sob temperatura.** Feito, com tabela por condição.
3. **Caracterizar N_eff sob reasoning.** Feito para chain-of-thought.
4. **Decompor conformidade.** Hao et al. ([arXiv 2606.00820](https://arxiv.org/abs/2606.00820)) separam instabilidade espontânea, conformidade e persuasão por condições contrafactuais controladas — sem calcular ESS, mas a decomposição não é inédita.

## 3. O que permanece aberto

Uma coisa, e é a interseção de 1 com 4:

> **conformidade expressa como perda de tamanho amostral efetivo.**

Kohli tem o estimador e não tem exposição. Hao tem exposição e não tem estimador. Ninguém mede o que a exposição faz com N_eff.

    Kohli estabelece o piso em painéis isolados.
    Esta tese mede o que a exposição faz a esse piso.

## 4. Onde Kohli ajuda esta tese

**Dá o ponto de comparação.** Um resultado desta tese lido isolado é um número sem escala. Lido contra 2,18, vira frase: *nove juízes que nunca se falam valem 2,18; depois de uma rodada de exposição, valem X.*

**Valida a correção do estimador.** O φ̄ do Kohli é sobre vetores binários de erro. É exatamente a correção que `Analise_Critica_da_Tese.md` (G1) impôs — tirar `N_eff` do kappa sobre seleção categórica e calculá-lo no subconjunto binário com gabarito. O precedente confirma que a correção era obrigatória.

**Delimita o escopo honestamente.** Painel isolado é o caso dominante da prática. Exposição é subconjunto. A tese é mais estreita que o precedente, e é isso que a torna defensável.

## 5. O que o revisor vai perguntar

| Pergunta | Onde está a resposta |
|---|---|
| "Kohli já fez isso." | §1 e §3 deste documento. O painel dele não interage. |
| "ESS pressupõe unidades permutáveis; sob exposição isso não vale." | `01_Protocolo_Experimental.md` §4.2 — exposição simultânea a estímulo comum. |
| "Seu Δ é comparável ao debate em prosa da literatura?" | `01_Protocolo_Experimental.md` §5.1 — não é, e está declarado. |
| "Temperatura você não testou, e Kohli testou." | Fora do escopo desta publicação; a linha sobre ρ de conteúdo está registrada em `PESQUISA-NEFF-02` §5. |
| "Por que 4 modelos e não 9?" | Controle de capacidade (Kim, D.), declarado em `03_Posicionamento_e_Procedencia.md` §3. |
