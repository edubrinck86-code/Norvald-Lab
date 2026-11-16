"""Cartão 'Em destaque' do LinkedIn para a engine documental (15/11/2026).

Refeito no mesmo dia na paleta clássica da página de produto (pedido do
Eduardo: o azul era "de tech"). Números: texto 3 (OSF gzvk5), 10,3% -> 3,9%
de mudanças de resposta (62% a menos); 10.649 respostas válidas no
laboratório em 15/11/2026.
"""
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "serif"
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

DARK, GOLD, CREAM, SOFT, MUTED = "#2B2724", "#B08D57", "#FBF8F2", "#E6DCCB", "#BDB3A6"

fig = plt.figure(figsize=(12, 6.27), dpi=100)
fig.patch.set_facecolor(DARK)
fig.text(0.05, 0.86, "NORVALD", color=GOLD, fontsize=16, weight="bold")
fig.text(0.05, 0.70, "Engine Documental", color="white", fontsize=36, weight="bold")
fig.text(0.05, 0.60, "Estabilidade comprovada\npara a IA da sua empresa.", color=SOFT, fontsize=19, va="top", linespacing=1.4)
fig.text(0.05, 0.30, "Testada em 30+ modelos de empresas diferentes", color="white", fontsize=14)
fig.text(0.05, 0.24, "3 pesquisas publicadas, com dados abertos", color="white", fontsize=14)
fig.text(0.05, 0.08, "Eduardo Guedes · Norvald", color=MUTED, fontsize=12)

ax = fig.add_axes([0.56, 0.12, 0.40, 0.76])
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
ax.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.04", color=CREAM))
ax.text(0.5, 0.80, "62%", color=GOLD, fontsize=54, weight="bold", ha="center", va="center")
ax.text(0.5, 0.62, "menos mudanças de resposta", color=DARK, fontsize=15, weight="bold", ha="center")
ax.plot([0.15, 0.85], [0.52, 0.52], color="#D9CFBF", lw=1)
ax.text(0.5, 0.33, "10.649+", color=GOLD, fontsize=54, weight="bold", ha="center", va="center")
ax.text(0.5, 0.15, "respostas coletadas", color=DARK, fontsize=15, weight="bold", ha="center")
ax.text(0.5, 0.06, "acerto mantido · pesquisa pré-registrada (OSF)", color="#6E655C", fontsize=10.5, ha="center")
fig.savefig("cartao-engine-linkedin.png", facecolor=fig.get_facecolor())
