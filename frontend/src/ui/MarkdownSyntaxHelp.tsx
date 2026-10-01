import { useMemo, useRef } from "react";
import { X, BookOpen } from "lucide-react";
import { dispensarAoClicarFora } from "../lib/dispensarAoClicarFora";
import { MarkdownIndexSidebar } from "./markdown/MarkdownIndexSidebar";

interface SyntaxGroup {
  title: string;
  items: { syntax: string; description: string }[];
}

// Cobre exatamente o que o renderer do Studio suporta de verdade (ver
// lib/markdown.ts) — nunca lista sintaxe que não funciona aqui.
const GROUPS: SyntaxGroup[] = [
  {
    title: "Estrutura",
    items: [
      { syntax: "# Título\n## Subtítulo", description: "Cabeçalhos (Capítulo/Seção — ADR-UX-007 usa \"N. Título\")" },
      { syntax: "**negrito**", description: "Texto em negrito" },
      { syntax: "*itálico*", description: "Texto em itálico" },
      { syntax: "==destaque==", description: "Highlight no estilo Obsidian, sem alterar o source" },
      { syntax: "- item\n- item", description: "Lista com marcadores" },
      { syntax: "1. item\n2. item", description: "Lista numerada" },
      { syntax: "- [ ] pendente\n- [x] feito", description: "Lista de tarefas (checkbox)" },
      { syntax: "> citação", description: "Bloco de citação" },
      { syntax: "| A | B |\n|---|---|\n| 1 | 2 |", description: "Tabela (GFM)" },
    ],
  },
  {
    title: "Referências",
    items: [
      { syntax: "[texto](url)", description: "Link comum" },
      { syntax: "[[Documento]]", description: "Wikilink — resolve contra a Library de verdade, navega ao clicar" },
      { syntax: "[[Documento#Seção]]", description: "Wikilink apontando pra uma seção específica" },
      { syntax: "[[Library/ADR-016|Arquitetura]]", description: "Referência explícita à Library com alias" },
      { syntax: "[[Repository/doc-id|Especificação]]", description: "Referência explícita ao Repository" },
      { syntax: "Texto com nota[^1]\n\n[^1]: A nota em si", description: "Nota de rodapé" },
    ],
  },
  {
    title: "Callouts",
    items: [
      { syntax: "> [!NOTE] Contexto\n> Texto da nota", description: "Callout com título customizado" },
      { syntax: "> [!TIP]\n> Texto da dica", description: "Dica / hint" },
      { syntax: "> [!WARNING]\n> Texto de atenção", description: "Warning / caution / attention" },
      { syntax: "> [!SUCCESS]\n> Texto de sucesso", description: "Success / check / done" },
      { syntax: "> [!DANGER]\n> Texto crítico", description: "Danger / error / bug / failure" },
      { syntax: "> [!QUESTION]\n> Questão em aberto", description: "Question / help / FAQ" },
      { syntax: "> [!EXAMPLE]\n> Exemplo", description: "Exemplo destacado" },
      { syntax: "> [!QUOTE]\n> Citação", description: "Citação semântica" },
      { syntax: "> [!NOTE]- Detalhes\n> Começa recolhido", description: "Callout recolhível; use + para começar aberto" },
    ],
  },
  {
    title: "Código e diagramas",
    items: [
      { syntax: "`código inline`", description: "Código inline" },
      { syntax: "```python\ncódigo\n```", description: "Bloco de código com linguagem, contagem de linhas e cópia" },
      { syntax: "```mermaid\ngraph TD\n  A --> B\n```", description: "Mermaid em SVG com zoom, cópia do source e download do SVG" },
      { syntax: "```markdown\n# Template\n- item\n```", description: "Preview de um documento Markdown dentro do documento" },
    ],
  },
  {
    title: "Combinações úteis",
    items: [
      { syntax: `# Decisão\n\n> [!NOTE]\n> Contexto importante`, description: "Combine títulos e callouts para estruturar decisões." },
      { syntax: `- [ ] Validar [[ADR-016]]\n- [x] Revisar texto`, description: "Tarefas podem apontar diretamente para documentos da Library." },
      { syntax: `## Evidência\n\n\`status=valid\`\n\n[[CON-001#2.3]]`, description: "Misture subtítulos, código inline e referências documentais." },
      { syntax: "**Conclusão:** [ver documento](https://example.com)", description: "Destaque uma conclusão e associe uma fonte externa." },
    ],
  },
  {
    title: "Datas e auditoria",
    items: [
      { syntax: "@date(2026-08-14)", description: "Data semântica — exibida de forma legível e preservada no Markdown." },
      { syntax: "@date(2026-08-14T15:30:00)", description: "Data e hora — útil para registros, marcos e auditoria." },
    ],
  },
  {
    title: "Matemática (KaTeX)",
    items: [
      { syntax: "$E = mc^2$", description: "Fórmula inline" },
      { syntax: "$$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$", description: "Fórmula em bloco, centralizada" },
    ],
  },
];

export function MarkdownSyntaxHelp({ onClose }: { onClose(): void }) {
  const contentRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const indexMarkdown = useMemo(
    () => GROUPS.map((group) => `## ${group.title}`).join("\n\n"),
    [],
  );

  return (
    <div
      className="overlay-scrim overlay-blur-notebook fixed inset-0 z-toast flex items-center justify-center p-4 sm:p-6"
      style={{ animation: "fade-in 180ms ease-out" }}
      {...dispensarAoClicarFora(onClose)}
    >
      <div
        className="glass-panel flex h-[80vh] w-[80vw] max-w-none flex-col overflow-hidden rounded-overlay border border-line shadow-panel"
        style={{ animation: "fade-in 180ms ease-out" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-4 border-b border-line px-4 py-4 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-panel bg-primary/15 text-primary">
              <BookOpen className="h-4.5 w-4.5" />
            </span>
            <div className="min-w-0">
              <h2 className="text-base font-semibold text-foreground">Sintaxe do Markdown</h2>
              <p className="truncate text-xs text-muted-foreground">Renderer do Studio · referências ao corpus e caderno locais</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-card text-muted-foreground transition-colors hover:bg-layer-raised hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex min-h-0 flex-1 overflow-hidden">
          <MarkdownIndexSidebar
            title="Sintaxe do Markdown"
            markdown={indexMarkdown}
            contentRef={contentRef}
            scrollRef={scrollRef}
          />
          <div ref={scrollRef} className="min-w-0 flex-1 overflow-y-auto">
            <div ref={contentRef} className="flex w-full flex-col gap-6 px-6 py-6">
              {GROUPS.map((group) => (
                <section key={group.title} className="w-full">
                  <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-subtle">
                    {group.title}
                  </h3>
                  <div className="card-depth flex w-full flex-col gap-px overflow-hidden rounded-panel border border-line bg-layer-panel">
                    {group.items.map((item, i) => (
                      <div key={i} className="grid grid-cols-1 items-center gap-3 bg-layer-panel px-3 py-3 sm:gap-5 sm:px-4 md:grid-cols-[minmax(220px,1fr)_1.2fr]">
                        <pre className="min-w-0 overflow-x-auto whitespace-pre-wrap break-words rounded-card bg-layer-raised-veil px-2.5 py-2 font-mono text-xs text-foreground/90">
                          {item.syntax}
                        </pre>
                        <p className="self-center text-xs text-muted-foreground">{item.description}</p>
                      </div>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
