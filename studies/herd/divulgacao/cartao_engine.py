"""Cartão 'Em destaque' do LinkedIn para a engine documental (15/11/2026).
Número do texto 3 (OSF gzvk5): mudanças de resposta 10,3% em texto corrido × 3,9% estruturado."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig = plt.figure(figsize=(12, 6.27), dpi=100)
fig.patch.set_facecolor("#0F172A")
fig.text(0.05, 0.84, "ENGINE DOCUMENTAL", color="#38BDF8", fontsize=20, weight="bold")
fig.text(0.05, 0.72, "Produto em uso", color="white", fontsize=34, weight="bold")
fig.text(0.05, 0.60, "Informação ao modelo de IA estruturada,\nrastreável e na medida certa.", color="#CBD5E1", fontsize=17, va="top")
fig.text(0.05, 0.36, "Testada e aprovada em 3 ambientes", color="white", fontsize=16, weight="bold")
fig.text(0.05, 0.30, "Huginn  ·  Studio  ·  Lab", color="#38BDF8", fontsize=16)
fig.text(0.05, 0.08, "Eduardo Guedes · Norvald", color="#94A3B8", fontsize=12)

ax = fig.add_axes([0.58, 0.2, 0.37, 0.56])
ax.set_facecolor("#0F172A")
vals = [10.3, 3.9]
bars = ax.bar(["Texto corrido", "Engine\n(estruturado)"], vals, color=["#64748B", "#38BDF8"], width=0.6)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + 0.3, f"{v:.1f}%".replace(".", ","), ha="center", color="white", fontsize=22, weight="bold")
ax.set_ylim(0, 13)
ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)
ax.tick_params(colors="white", labelsize=13, length=0)
fig.text(0.765, 0.86, "Mudanças de resposta do modelo", color="white", fontsize=14, ha="center", weight="bold")
fig.text(0.765, 0.04, "sem perder acerto · pesquisa pré-registrada (OSF)", color="#94A3B8", fontsize=11, ha="center")
fig.savefig("cartao-engine-linkedin.png", facecolor=fig.get_facecolor())
