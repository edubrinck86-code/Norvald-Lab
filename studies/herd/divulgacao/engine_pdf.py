"""Uma página de produto da Engine Documental Norvald (A4, PDF), 15/11/2026.
Números: texto 3 (OSF gzvk5) e registros do Lab; ver engine-uma-pagina.md."""
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["font.family"] = "serif"
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

NAVY, CYAN, GREY, LIGHT, INK = "#2B2724", "#B08D57", "#6E655C", "#F3EEE4", "#2B2724"  # 15/11: clássico (grafite quente, dourado envelhecido, creme), pedido dele
fig = plt.figure(figsize=(8.27, 11.69), facecolor="#FBF8F2")
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 141.4); ax.axis("off")

def t(x, y, s, **k): ax.text(x, y, s, va="top", **k)

# Cabeçalho
ax.add_patch(Rectangle((0, 112), 100, 29.4, color=NAVY))
t(7, 136, "NORVALD", color=CYAN, fontsize=11, weight="bold")
t(7, 131, "Engine Documental", color="white", fontsize=30, weight="bold")
t(7, 122.5, "Estabilidade comprovada para a IA da sua empresa.", color="#E6DCCB", fontsize=14)

# Dor
t(7, 107, "Sua IA muda de resposta sem motivo?", color=INK, fontsize=16, weight="bold")
t(7, 101.5, "Você pede para ela revisar e ela troca uma resposta certa por outra. Ou responde\n"
            "diferente à mesma pergunta. Cada mudança à toa é retrabalho e perda de confiança.\n"
            "Quase sempre o problema não é o modelo: é a informação chegando solta e sem ordem.",
  color=GREY, fontsize=10.5, linespacing=1.5)

# Dois números em destaque (15/11, pedido dele): resultado e volume de prova
ax.add_patch(FancyBboxPatch((7, 64), 86, 22, boxstyle="round,pad=0,rounding_size=2", color=LIGHT))
ax.plot([50, 50], [67, 83], color="#D9CFBF", lw=1)
t(11, 83, "62%", color=CYAN, fontsize=42, weight="bold")
t(11, 71.5, "menos mudanças de resposta", color=INK, fontsize=12, weight="bold")
t(11, 67.8, "de 1 a cada 10 revisões para 1 a cada 25", color=GREY, fontsize=9)
t(54, 83, "10.649+", color=CYAN, fontsize=42, weight="bold")
t(54, 71.5, "respostas coletadas", color=INK, fontsize=12, weight="bold")
t(54, 67.8, "acerto mantido · ainda ~7% mais barato", color=GREY, fontsize=9)

# Como funciona
t(7, 58, "Como funciona", color=INK, fontsize=14, weight="bold")
t(7, 53, "A engine organiza a informação antes de entregá-la à IA: cada dado no lugar certo,\n"
         "na medida certa e com origem rastreável. O modelo não precisa adivinhar o que importa.",
  color=GREY, fontsize=10.5, linespacing=1.5)

# Provas em 3 colunas
cols = [("30+", "modelos de IA testados,\nde empresas diferentes"),
        ("3", "sistemas da Norvald\nusando a engine"),
        ("3", "pesquisas publicadas,\ncom dados abertos")]
for i, (big, small) in enumerate(cols):
    x = 7 + i * 29.5
    ax.add_patch(FancyBboxPatch((x, 27), 26.5, 16, boxstyle="round,pad=0,rounding_size=1.5", color=NAVY))
    t(x + 3, 41, big, color=CYAN, fontsize=22, weight="bold")
    t(x + 3, 34, small, color="white", fontsize=9, linespacing=1.4)

# Para quem
t(7, 22, "Para quem serve", color=INK, fontsize=12, weight="bold")
t(7, 18, "Sistemas em que a IA trabalha em etapas ou revisa o próprio trabalho: atendimento,\n"
         "análise de documentos e contratos, produção de conteúdo, agentes que decidem.",
  color=GREY, fontsize=10, linespacing=1.5)

# Rodapé
ax.add_patch(Rectangle((0, 0), 100, 9, color=NAVY))
t(7, 6.2, "Comece com um diagnóstico: onde sua IA oscila e quanto isso custa.", color="white", fontsize=10, weight="bold")
t(7, 2.8, "Eduardo Guedes · Norvald   ·   contato@norvald.com.br", color=CYAN, fontsize=9.5)

fig.savefig("engine-documental-norvald.pdf", facecolor=fig.get_facecolor())
fig.savefig("engine-documental-norvald.png", dpi=110, facecolor=fig.get_facecolor())
