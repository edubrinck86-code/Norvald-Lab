"""Gráfico do post de divulgação do texto 2 (15/11/2026).
Números da tabela 3.1 do texto2-pt.md (N_eff, IC 95% bootstrap). O banco novo em E
(6,0) fica fora: vem de pouquíssimos erros e o próprio texto 2 diz para não lê-lo (§3.2);
o post menciona isso em texto."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

barras = [
    ("MMLU-Pro\nàs cegas", 1.413, 1.287, 1.580, "#C2410C"),
    ("MMLU-Pro\nvendo os pares", 1.162, 1.093, 1.249, "#9A3412"),
    ("Perguntas novas\nàs cegas", 4.445, 2.548, 6.702, "#2563EB"),
]
fig, ax = plt.subplots(figsize=(7, 4.5), dpi=200)
for i, (nome, v, lo, hi, cor) in enumerate(barras):
    ax.bar(i, v, 0.6, color=cor, yerr=[[v-lo], [hi-v]], capsize=5, ecolor="#444")
    ax.text(i, 0.2, f"{v:.1f}".replace(".", ","), ha="center", color="white", fontsize=14, weight="bold")
ax.axhline(5, ls="--", color="#666", lw=1)
ax.text(-0.3, 5.15, "se fossem 5 juízes independentes", color="#444", fontsize=9)
ax.set_xticks(range(3)); ax.set_xticklabels([b[0] for b in barras], fontsize=11)
ax.set_ylabel("Juízes que o painel vale (N_eff)", fontsize=11)
ax.set_title("Cinco LLMs de cinco empresas valem quantos juízes?", fontsize=13, weight="bold")
ax.set_ylim(0, 7.2); ax.spines[["top", "right"]].set_visible(False)
fig.text(0.01, 0.01, "Barras: IC 95% bootstrap. N_eff = n/(1+(n−1)ρ̄_erro), n = 5. Pré-registro e dados: OSF gbx5m.", fontsize=7.5, color="#555")
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig("neff-por-condicao.png")
