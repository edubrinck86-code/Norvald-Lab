---
id: DESK-INDICE
tipo: Índice de literatura
data: 2026-10-04
escopo: N_eff, AROF, CC e temas diretamente relacionados
---

# Índice — literatura verificada

Levantamento de 04/10/2026. **Toda entrada marcada "conferido na fonte" teve a página
aberta e título, autores, ano e achado lidos no texto.** O que não foi possível abrir
está marcado como tal. Nenhum número foi reconstruído de memória.

## Arquivos

| Arquivo | Tema | Entradas |
|---|---|---|
| `01_ESS_e_dependencia.md` | N_eff, design effect, Kish, saturação de painel | 17 |
| `02_Erro_correlacionado.md` | a premissa: LLMs não erram independentemente | 22 |
| `03_Diversidade_e_capacidade.md` | por que diversidade ≠ independência | 19 |
| `04_Conformidade_e_exposicao.md` | Δ_herd, debate, ancoragem, efeito manada | 16 |
| `05_Reasoning_observavel_AROF.md` | traço como observável; predizer erro pelo processo | 15 |
| `06_Composicao_de_confianca_CC.md` | agregação de confiança, UQ, índices compostos | 15 |
| `07_ALERTAS.md` | **o que muda o posicionamento — ler primeiro** | 6 |

## Os trabalhos que mais importam, em uma linha cada

| Ref | Por quê |
|---|---|
| Kohli 2026 (2605.29800) | Kish ESS em painel de 9 juízes isolados: n_eff = 2,18 |
| **RoPoLL (2606.30931)** | **Corollary 1 tem a fórmula idêntica. Co-precedente de Kohli.** |
| **Shu 2026 (2609.26145)** | **1 rodada de debate: unanimidade 39,5% → 95,2%, acurácia parada** |
| Elahi et al. v2 (2606.13591) | já propõe desconto de dependência calibrado, w* ≈ 0,65 |
| Balasubramanian et al. ICML 2026 (2601.22336) | forma linear com pesos ajustados por correlação, derivada como ótimo de Bayes |
| Kim, E. et al. ICML 2025 (2506.07962) | 350+ modelos; concordam 60% das vezes quando ambos erram |
| Goel et al. ICML 2025 (2502.04313) | CAPA; erros ficam MAIS parecidos conforme a capacidade sobe |
| ReasonOps (2605.29192) | traço identifica o modelo com AUC 0,987 e prediz erro com WP-AUC 0,701 |
| Liu 2026 (2607.10139) | lei que **consome** ρ e prediz acurácia de consenso (MAE 0,028) — não estima dependência |
| CARE (2603.00039) | estima dependência **sem gabarito** — mas exige 11–20 juízes; não serve a painel de 4 |

## Cruzamento por autor

| Autor | Aparece em |
|---|---|
| Kohli, G. | 01, 02, 03, 05, 07 |
| Goel et al. | 01, 02, 05, 06 |
| Kim, E. M. et al. | 01, 02, 03, 05 |
| Kim, D. | 03 |
| Yang, Y. et al. (K*) | 01, 03 |
| Hao, X. et al. | 04 |
| Elahi et al. | 06, 07 |
| Balasubramanian et al. | 06, 07 |
| Clemen & Winkler (1985) | 06 |
| Paruolo / Becker et al. | 06, 07 |
| Xiong et al. | 06 |
| Yang, Tsai & Yamada | 06 |
| Liu | 01, 06 |
| Shu | 01, 04, 07 |
| Acharya et al. (RoPoLL) | 01, 07 |
| Bay & Yearick | 01 |
| Xin | 01 |
| Turkmen et al. | 01, 02, 03, 05, 06 |
| Bommasani et al. | 02 |
| Kish (1965) | 01 |
| Fleiss & Cohen (1973) | 01 |
