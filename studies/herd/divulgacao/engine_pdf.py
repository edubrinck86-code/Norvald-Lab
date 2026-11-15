"""Uma página de produto da Engine Documental Norvald (A4, PDF), 15/11/2026.
Números: texto 3 (OSF gzvk5) e registros do Lab; ver engine-uma-pagina.md."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

NAVY, CYAN, GREY, LIGHT, INK = "#0F172A", "#38BDF8", "#64748B", "#F1F5F9", "#1E293B"
fig = plt.figure(figsize=(8.27, 11.69))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 100); ax.set_ylim(0, 141.4); ax.axis("off")

def t(x, y, s, **k): ax.text(x, y, s, va="top", **k)

# Cabeçalho
ax.add_patch(Rectangle((0, 112), 100, 29.4, color=NAVY))
t(7, 136, "NORVALD", color=CYAN, fontsize=11, weight="bold")
t(7, 131, "Engine Documental", color="white", fontsize=30, weight="bold")
t(7, 122.5, "Sua IA estável, previsível e rastreável.", color="#CBD5E1", fontsize=14)

# Dor
t(7, 107, "Sua IA muda de resposta sem motivo?", color=INK, fontsize=16, weight="bold")
t(7, 101.5, "Você pede para ela revisar e ela troca uma resposta certa por outra. Ou responde\n"
            "diferente à mesma pergunta. Cada mudança à toa é retrabalho e perda de confiança.\n"
            "Quase sempre o problema não é o modelo: é a informação chegando solta e sem ordem.",
  color=GREY, fontsize=10.5, linespacing=1.5)

# Número grande
ax.add_patch(FancyBboxPatch((7, 64), 86, 22, boxstyle="round,pad=0,rounding_size=2", color=LIGHT))
t(11, 83, "62%", color=CYAN, fontsize=54, weight="bold")
t(11, 69.5, "menos mudanças de resposta", color=INK, fontsize=12, weight="bold")
# barras 1 em 10 x 1 em 25
for i, (lab, v, c) in enumerate([("Sem a engine: 1 a cada 10 revisões", 10.3, "#94A3B8"),
                                 ("Com a engine: 1 a cada 25", 3.9, CYAN)]):
    y = 82.5 - i * 7.5
    t(50, y, lab, color=INK, fontsize=9.5)
    ax.add_patch(Rectangle((50, y - 5), 40 * v / 10.3, 2.6, color=c))
t(50, 67.5, "Acerto mantido · ainda ~7% mais barato", color=GREY, fontsize=9)

# Como funciona
t(7, 58, "Como funciona", color=INK, fontsize=14, weight="bold")
t(7, 53, "A engine organiza a informação antes de entregá-la à IA: cada dado no lugar certo,\n"
         "na medida certa e com origem rastreável. O modelo não precisa adivinhar o que importa.",
  color=GREY, fontsize=10.5, linespacing=1.5)

# Provas em 3 colunas
cols = [("30+", "modelos de IA testados,\nde empresas diferentes"),
        ("~10 mil", "respostas registradas\nno laboratório"),
        ("3", "sistemas em produção\ne 3 pesquisas publicadas")]
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
t(7, 2.8, "Eduardo Guedes · Norvald   [contato]", color=CYAN, fontsize=9.5)

fig.savefig("engine-documental-norvald.pdf")
fig.savefig("engine-documental-norvald.png", dpi=110)
