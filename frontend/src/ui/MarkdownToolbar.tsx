import { useState } from "react";
import { createPortal } from "react-dom";
import { Check, Copy, Download, Share2, BookOpen } from "lucide-react";
import { cn } from "../lib/utils";
import { MarkdownSyntaxHelp } from "./MarkdownSyntaxHelp";

interface MarkdownToolbarProps {
  /** Markdown original, cru — Copiar preserva a estrutura, sem HTML renderizado. */
  markdown: string;
  className?: string;
  /** Nome do arquivo sem extensão. */
  filename?: string;
  downloadUrl?: string;
  /** Botão de referência de sintaxe. */
  showSyntaxHelp?: boolean;
}

/**
 * ADR-UX-002 §11 — Toolbar padrão para documentos renderizados em Markdown.
 * O overlay de sintaxe é montado via portal para não interferir em overlays
 * ou containers que hospedem a toolbar.
 */
export function MarkdownToolbar({ markdown, className, filename = "documento", downloadUrl, showSyntaxHelp }: MarkdownToolbarProps) {
  const [copied, setCopied] = useState(false);
  const [syntaxHelpOpen, setSyntaxHelpOpen] = useState(false);

  function handleDownload() {
    const safeFilename = filename.replace(/[^a-z0-9_-]+/gi, "-").replace(/^-+|-+$/g, "") || "documento";
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = downloadUrl ?? URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = downloadUrl ? filename : `${safeFilename}.md`;
    anchor.style.display = "none";
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    if (!downloadUrl) window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(markdown);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // Clipboard indisponível (ex: contexto não seguro) — falha silenciosa.
    }
  }

  function openSyntaxHelp(event: React.MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
    setSyntaxHelpOpen(true);
  }

  function keepSyntaxHelpClickInside(event: React.MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
  }

  return (
    <div className={cn("flex items-center gap-1", className)}>
      <button type="button" onClick={handleCopy} aria-label="Copiar Markdown" title="Copiar Markdown" className="flex h-8 w-8 items-center justify-center rounded-card text-muted-foreground transition-colors hover:bg-layer-raised hover:text-foreground">
        {copied ? <Check className="h-4 w-4 text-ok" /> : <Copy className="h-4 w-4" />}
      </button>
      <button type="button" disabled aria-label="Compartilhar (em breve)" title="Compartilhar (em breve)" className="flex h-8 w-8 items-center justify-center rounded-card text-muted-foreground transition-colors hover:bg-layer-raised hover:text-foreground">
        <Share2 className="h-4 w-4" />
      </button>
      <button type="button" onClick={handleDownload} aria-label={downloadUrl ? "Baixar arquivo original" : "Baixar Markdown"} title={downloadUrl ? "Baixar arquivo original" : "Baixar Markdown"} className="flex h-8 w-8 items-center justify-center rounded-card text-muted-foreground transition-colors hover:bg-layer-raised hover:text-foreground">
        <Download className="h-4 w-4" />
      </button>
      {showSyntaxHelp && (
        <button
          type="button"
          onMouseDown={keepSyntaxHelpClickInside}
          onClick={openSyntaxHelp}
          title="Sintaxe do Markdown"
          aria-label="Abrir sintaxe do Markdown"
          className="flex h-8 w-8 items-center justify-center rounded-card text-muted-foreground transition-colors hover:bg-layer-raised hover:text-foreground"
        >
          <BookOpen className="h-4 w-4" />
        </button>
      )}
      {syntaxHelpOpen && createPortal(
        <MarkdownSyntaxHelp onClose={() => setSyntaxHelpOpen(false)} />,
        document.body
      )}
    </div>
  );
}
