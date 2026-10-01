import { marked } from "marked";
import markedFootnote from "marked-footnote";
import markedKatex from "marked-katex-extension";
import "katex/dist/katex.min.css";
import type { EvidenceItem } from "./evidence";

type CalloutTone = "note" | "info" | "success" | "warning" | "danger" | "example" | "quote";

const CALLOUT_TYPES: Record<string, { label: string; icon: string; tone: CalloutTone }> = {
  NOTE: { label: "Nota", icon: "✦", tone: "note" },
  ABSTRACT: { label: "Resumo", icon: "≋", tone: "note" },
  SUMMARY: { label: "Resumo", icon: "≋", tone: "note" },
  TLDR: { label: "Em resumo", icon: "≋", tone: "note" },
  INFO: { label: "Informação", icon: "i", tone: "info" },
  TODO: { label: "A fazer", icon: "○", tone: "info" },
  TIP: { label: "Dica", icon: "◇", tone: "success" },
  HINT: { label: "Dica", icon: "◇", tone: "success" },
  IMPORTANT: { label: "Importante", icon: "!", tone: "success" },
  SUCCESS: { label: "Sucesso", icon: "✓", tone: "success" },
  CHECK: { label: "Concluído", icon: "✓", tone: "success" },
  DONE: { label: "Concluído", icon: "✓", tone: "success" },
  QUESTION: { label: "Questão", icon: "?", tone: "warning" },
  HELP: { label: "Ajuda", icon: "?", tone: "warning" },
  FAQ: { label: "FAQ", icon: "?", tone: "warning" },
  WARNING: { label: "Atenção", icon: "!", tone: "warning" },
  CAUTION: { label: "Cuidado", icon: "!", tone: "warning" },
  ATTENTION: { label: "Atenção", icon: "!", tone: "warning" },
  FAILURE: { label: "Falha", icon: "×", tone: "danger" },
  FAIL: { label: "Falha", icon: "×", tone: "danger" },
  MISSING: { label: "Ausente", icon: "×", tone: "danger" },
  DANGER: { label: "Perigo", icon: "!", tone: "danger" },
  ERROR: { label: "Erro", icon: "×", tone: "danger" },
  BUG: { label: "Bug", icon: "⌁", tone: "danger" },
  EXAMPLE: { label: "Exemplo", icon: "◆", tone: "example" },
  QUOTE: { label: "Citação", icon: "”", tone: "quote" },
  CITE: { label: "Citação", icon: "”", tone: "quote" },
};

const renderer = new marked.Renderer();
renderer.blockquote = function ({ tokens }) {
  const inner = this.parser.parse(tokens);
  const match = inner.match(/^<p>\s*\[!(\w+)\]([+-])?(?:\s+([^<\n]*?))?(?:<br\s*\/?>|\n|<\/p>)/i);
  if (!match) return `<blockquote>${inner}</blockquote>`;

  const config = CALLOUT_TYPES[match[1].toUpperCase()];
  if (!config) return `<blockquote>${inner}</blockquote>`;

  const fold = match[2] ?? "";
  const customTitle = (match[3] ?? "").trim();
  const title = customTitle || config.label;
  const markerPattern = /^<p>\s*\[!(\w+)\]([+-])?(?:\s+[^<\n]*?)?(?:<br\s*\/?>|\n|<\/p>)/i;
  let body = inner.replace(markerPattern, "<p>");
  if (body.trim() === "<p>") body = "";

  const titleHtml = `<span class="callout-icon" aria-hidden="true">${config.icon}</span><span>${escapeAttribute(title)}</span>`;
  if (fold) {
    return `<details class="callout callout-${config.tone} callout-collapsible"${fold === "+" ? " open" : ""}><summary class="callout-title">${titleHtml}</summary><div class="callout-body">${body}</div></details>`;
  }
  return `<div class="callout callout-${config.tone}"><div class="callout-title">${titleHtml}</div><div class="callout-body">${body}</div></div>`;
};

renderer.link = function ({ href, title, tokens }) {
  const label = this.parser.parseInline(tokens);
  const safeHref = escapeAttribute(href ?? "");
  const titleAttr = title ? ` title="${escapeAttribute(title)}"` : "";
  const external = /^(https?:)?\/\//i.test(href ?? "");
  const externalAttrs = external ? ' target="_blank" rel="noopener noreferrer"' : "";
  return `<a href="${safeHref}"${titleAttr}${externalAttrs}>${label}</a>`;
};

const MARKDOWN_LANGS = new Set(["markdown", "md"]);

function renderMarkdownBlock(source: string): string {
  const frontMatter = source.match(/^---\n([\s\S]*?)\n---\n?/);
  const corpo = frontMatter ? source.slice(frontMatter[0].length) : source;
  const cabecalho = frontMatter
    ? `<pre class="md-preview-front"><code>${frontMatter[1].replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")}</code></pre>`
    : "";
  return `<div class="md-preview"><span class="md-preview-label">Markdown</span>${cabecalho}<div class="md-preview-body">${marked.parse(corpo, { async: false }) as string}</div></div>`;
}

renderer.code = function (token) {
  const lang = token.lang?.trim().toLowerCase() ?? "";
  if (MARKDOWN_LANGS.has(lang)) return renderMarkdownBlock(token.text);

  const encoded = encodeURIComponent(token.text);
  const label = lang || "código";
  const lineCount = token.text ? token.text.split("\n").length : 0;
  const className = lang ? ` class="language-${escapeAttribute(lang)}"` : "";
  const escaped = token.text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  return `<div class="md-code-block"><div class="md-code-header"><span class="md-code-language">${label}</span><span class="md-code-lines">${lineCount} ${lineCount === 1 ? "linha" : "linhas"}</span><button type="button" class="md-code-copy" data-md-copy="${escapeAttribute(encoded)}">Copiar</button></div><pre><code${className}>${escaped}</code></pre></div>`;
};

marked.setOptions({ gfm: true, breaks: true, renderer });
marked.use(markedFootnote());
marked.use(markedKatex({ throwOnError: false }));

const DATE_MARKER_RE = /@date\((\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2})?)?)\)/g;

function mapOutsideCode(markdown: string, transform: (segment: string) => string): string {
  const segments = markdown.split(/(`{3,}[\s\S]*?`{3,}|~{3,}[\s\S]*?~{3,}|`+[^\n]*?`+)/g);
  return segments.map((segment, index) => index % 2 === 1 ? segment : transform(segment)).join("");
}

function renderDateMarkers(markdown: string): string {
  return mapOutsideCode(markdown, (segment) =>
    segment.replace(DATE_MARKER_RE, (_match, iso: string) => {
      const date = new Date(iso.length === 10 ? `${iso}T00:00:00` : iso);
      if (Number.isNaN(date.getTime())) return _match;
      const label = iso.length === 10
        ? date.toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" })
        : date.toLocaleString("pt-BR", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
      return `<span class="md-date" title="Data registrada no Markdown">📅 ${label}</span>`;
    })
  );
}

const WIKI_LINK_RE = /\[\[([^[\]]+)\]\]/g;
const REFERENCE_RE = /\b([A-Z]{2,6}(?:-\d{1,4})?)\s+(\d{1,3})\.(\d{1,3})\b/g;

function escapeAttribute(value: string): string {
  return value.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function renderWikiLinks(markdown: string): string {
  return mapOutsideCode(markdown, (segment) => segment.replace(WIKI_LINK_RE, (_match, raw: string) => {
    const [targetPart, sectionPart] = raw.split("#", 2).map((s: string) => s.trim());
    const [namespace, ...idParts] = targetPart.split("/");
    const isWorkspaceReference = /^(library|repository|artifact|cloud|note|attachment)$/i.test(namespace ?? "") && idParts.length > 0;
    if (isWorkspaceReference) {
      const source = namespace.toLowerCase();
      const target = idParts.join("/").trim();
      const [id, alias] = target.split("|", 2).map((s) => s.trim());
      const label = alias || id;
      return `<button type="button" class="workspace-reference" aria-label="${escapeAttribute(label)}" data-reference-source="${source}" data-reference-id="${escapeAttribute(id)}" data-reference-section="${escapeAttribute(sectionPart ?? "")}">${escapeAttribute(label)}</button>`;
    }
    const [docPart, alias] = targetPart.split("|", 2).map((s: string) => s.trim());
    const label = alias || (sectionPart ? `${docPart} § ${sectionPart}` : docPart);
    return `<button type="button" class="wiki-link" aria-label="${escapeAttribute(label)}" data-ref="${escapeAttribute(docPart)}" data-section="${escapeAttribute(sectionPart ?? "")}">${escapeAttribute(label)}</button>`;
  }));
}

function renderRawReferences(markdown: string): string {
  return mapOutsideCode(markdown, (segment) =>
    segment.replace(REFERENCE_RE, (match, id: string, chapter: string, section: string) =>
      `<button type="button" class="reference-link" data-identifier="${id}" data-chapter="${chapter}" data-section="${section}">${match}</button>`
    )
  );
}

/** Remove only the stray empty JSX fragment left in generated contributions. */
function stripContributionFragment(markdown: string): string {
  return markdown
    .replace(/(?:^|\r?\n)[ \t]*(?:<>|&lt;\s*&gt;)[ \t]*(?=\r?\n|$)/gi, "\n")
    .replace(/^\s*(?:<>|&lt;\s*&gt;)\s*/i, "")
    .replace(/\s*(?:<>|&lt;\s*&gt;)\s*$/i, "");
}

export function renderNoteMarkdown(markdown: string): string {
  if (!markdown.trim()) return "";
  const sanitized = stripContributionFragment(markdown);
  const withDates = renderDateMarkers(sanitized);
  const withReferences = renderRawReferences(withDates);
  const withWikiLinks = renderWikiLinks(withReferences);
  return marked.parse(withWikiLinks, { async: false }) as string;
}

export function resolveReference(identifier: string, libraryItems: EvidenceItem[]): EvidenceItem | null {
  return libraryItems.find((i) => i.identifier === identifier.trim()) ?? null;
}

export function extractWikiLinks(markdown: string): string[] {
  const matches = [...markdown.matchAll(WIKI_LINK_RE)];
  return Array.from(new Set(matches.map((m) => m[1].trim())));
}

export { resolveWikiLink, countWords } from "./markdownText";
