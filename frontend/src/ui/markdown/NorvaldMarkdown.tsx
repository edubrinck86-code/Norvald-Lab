
import { useMemo, type MouseEvent } from "react";
import remend from "remend";
import { useResourceReferences } from "../references/ResourceReferenceContext";
import { resourceFromHref, type ResourceReference, type ResourceSource } from "../references/resourceReference";
import { API_BASE } from "../../services/apiBase";
import { renderNoteMarkdown } from "../../lib/markdown";
import { cn } from "../../lib/utils";
import { MermaidDiagram } from "./MermaidDiagram";

export type NorvaldMarkdownMode = "document" | "compact" | "streaming";

type MermaidSegment =
  | { kind: "markdown"; source: string }
  | { kind: "mermaid"; source: string; complete: boolean };

export interface NorvaldMarkdownProps {
  content: string;
  mode?: NorvaldMarkdownMode;
  className?: string;
  onWikiLinkClick?(ref: string, section?: string): void;
  onWorkspaceReferenceClick?(
    source: "library" | "repository",
    id: string,
    section?: string,
  ): void;
  onReferenceClick?(identifier: string, chapter?: string, section?: string): void;
  resourceScope?: Pick<ResourceReference, "workspaceId" | "sessionId" | "conversationId" | "taskId">;
}

function splitMermaidSegments(markdown: string): MermaidSegment[] {
  if (!markdown) return [];

  const lines = markdown.match(/[^\n]*\n|[^\n]+$/g) ?? [];
  const segments: MermaidSegment[] = [];
  let markdownBuffer = "";
  let mermaidBuffer = "";
  let fenceChar: "`" | "~" | null = null;
  let fenceLength = 0;

  const flushMarkdown = () => {
    if (!markdownBuffer) return;
    segments.push({ kind: "markdown", source: markdownBuffer });
    markdownBuffer = "";
  };

  for (const line of lines) {
    if (!fenceChar) {
      const opening = line.match(/^\s{0,3}(`{3,}|~{3,})\s*mermaid(?:\s+[^\n]*)?\s*(?:\n|$)/i);
      if (!opening) {
        markdownBuffer += line;
        continue;
      }

      flushMarkdown();
      fenceChar = opening[1][0] as "`" | "~";
      fenceLength = opening[1].length;
      mermaidBuffer = "";
      continue;
    }

    const closing = new RegExp(
      "^\\s{0,3}" + (fenceChar === "`" ? "`" : "~") + "{" + fenceLength + ",}\\s*(?:\\n|$)",
    );
    if (closing.test(line)) {
      segments.push({ kind: "mermaid", source: mermaidBuffer.trim(), complete: true });
      fenceChar = null;
      fenceLength = 0;
      mermaidBuffer = "";
      continue;
    }

    mermaidBuffer += line;
  }

  if (fenceChar) {
    segments.push({ kind: "mermaid", source: mermaidBuffer.trim(), complete: false });
  }

  flushMarkdown();
  return segments;
}

function mapOutsideCode(markdown: string, transform: (value: string) => string): string {
  const parts = markdown.split(/(`{3,}[\s\S]*?`{3,}|~{3,}[\s\S]*?~{3,}|`+[^\n]*?`+)/g);
  return parts.map((part, index) => index % 2 === 1 ? part : transform(part)).join("");
}

function applyHighlights(markdown: string): string {
  return mapOutsideCode(
    markdown,
    (segment) => segment.replace(
      /==([^=\n](?:[\s\S]*?[^=\n])?)==/g,
      (_match, value: string) => "<mark>" + value + "</mark>",
    ),
  );
}

function isSafeUrl(value: string): boolean {
  const trimmed = value.trim().toLowerCase();
  if (!trimmed) return true;
  if (
    trimmed.startsWith("#") ||
    trimmed.startsWith("/") ||
    trimmed.startsWith("./") ||
    trimmed.startsWith("../")
  ) return true;
  return /^(https?:|mailto:|tel:|data:image\/|library:|repository:|artifact:|cloud:|note:|notebook:|attachment:)/i.test(trimmed) || /^[^:]+\.(?:md|txt|pdf|csv|json|docx?|xlsx?|png|jpe?g|svg|zip)(?:#.*)?$/i.test(trimmed);
}

function sanitizeRenderedHtml(html: string): string {
  if (typeof DOMParser === "undefined") return html;

  const doc = new DOMParser().parseFromString("<div id=\"norvald-md-root\">" + html + "</div>", "text/html");
  const root = doc.getElementById("norvald-md-root");
  if (!root) return "";

  root.querySelectorAll("script, style, iframe, object, embed, form, meta, link, base").forEach((node) => node.remove());

  root.querySelectorAll<HTMLElement>("*").forEach((element) => {
    for (const attribute of Array.from(element.attributes)) {
      const name = attribute.name.toLowerCase();
      const value = attribute.value;

      if (name.startsWith("on") || name === "srcdoc") {
        element.removeAttribute(attribute.name);
        continue;
      }

      if ((name === "href" || name === "src" || name === "xlink:href") && !isSafeUrl(value)) {
        element.removeAttribute(attribute.name);
        continue;
      }

      if (name === "style" && /(?:expression\s*\(|url\s*\()/i.test(value)) {
        element.removeAttribute(attribute.name);
      }
    }
  });

  const walker = doc.createTreeWalker(root, 4);
  const nodes: Text[] = [];
  while (walker.nextNode()) nodes.push(walker.currentNode as Text);
  const pattern = /\b(?:[A-Z]{2,8}-\d{1,6}(?:\s+\d{1,3}\.\d{1,3})?|[\wÀ-ÿ-]+\.(?:md|txt|pdf|csv|json|docx?|xlsx?|png|jpe?g|svg|zip)|[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12})\b/g;
  for (const node of nodes) {
    if (node.parentElement?.closest("a,button,pre,code,.wiki-link,.reference-link,.workspace-reference")) continue;
    const value = node.textContent ?? "";
    const matches = [...value.matchAll(pattern)];
    if (!matches.length) continue;
    const fragment = doc.createDocumentFragment(); let offset = 0;
    for (const match of matches) {
      fragment.append(doc.createTextNode(value.slice(offset, match.index)));
      const button = doc.createElement("button"); button.type = "button"; button.className = "wiki-link";
      const parts = match[0].match(/^([A-Z]{2,8}-\d{1,6})\s+(\d{1,3}\.\d{1,3})$/);
      button.dataset.ref = parts?.[1] ?? match[0]; if (parts) button.dataset.section = parts[2];
      button.textContent = match[0]; fragment.append(button); offset = (match.index ?? 0) + match[0].length;
    }
    fragment.append(doc.createTextNode(value.slice(offset))); node.replaceWith(fragment);
  }
  return root.innerHTML;
}

function renderStaticChunk(source: string): string {
  if (!source.trim()) return "";
  const html = renderNoteMarkdown(applyHighlights(source));
  return sanitizeRenderedHtml(html);
}

export function NorvaldMarkdown({
  content,
  mode = "document",
  className,
  onWikiLinkClick,
  onWorkspaceReferenceClick,
  onReferenceClick,
  resourceScope,
}: NorvaldMarkdownProps) {
  const resources = useResourceReferences();
  const scopedReference = (reference: ResourceReference): ResourceReference => ({
    ...reference,
    workspaceId: reference.workspaceId ?? resourceScope?.workspaceId,
    sessionId: reference.sessionId ?? resourceScope?.sessionId,
    conversationId: reference.conversationId ?? resourceScope?.conversationId,
    taskId: reference.taskId ?? resourceScope?.taskId,
  });
  // Markdown chega token a token durante streaming e pode terminar um frame
  // no meio de **negrito**, _itálico_, `código` ou [links](...). Remend
  // completa somente a projeção usada para renderização; `content` permanece
  // intocado e continua sendo a fonte persistida/canônica.
  const displayContent = useMemo(
    () => mode === "streaming"
      ? remend(content, { inlineKatex: false })
      : content,
    [content, mode],
  );
  const segments = useMemo(() => splitMermaidSegments(displayContent), [displayContent]);
  const rendered = useMemo(
    () => segments.map((segment) =>
      segment.kind === "markdown" ? renderStaticChunk(segment.source) : null
    ),
    [segments],
  );

  function handleClick(event: MouseEvent<HTMLDivElement>) {
    const target = event.target as HTMLElement;

    const workspaceReference = target.closest<HTMLElement>(".workspace-reference");
    if (workspaceReference) {
      const source = workspaceReference.dataset.referenceSource;
      const id = workspaceReference.dataset.referenceId ?? "";
      const section = workspaceReference.dataset.referenceSection || undefined;
      if (source && id) {
        event.preventDefault();
        if (onWorkspaceReferenceClick && (source === "library" || source === "repository")) onWorkspaceReferenceClick(source, id, section);
        else resources?.open(scopedReference({ source: source as ResourceSource, id, section }));
      }
      return;
    }

    const wikiLink = target.closest<HTMLElement>(".wiki-link");
    if (wikiLink) {
      const ref = wikiLink.dataset.ref ?? "";
      const section = wikiLink.dataset.section || undefined;
      if (ref) {
        event.preventDefault();
        if (onWikiLinkClick) onWikiLinkClick(ref, section);
        else resources?.open(scopedReference({ source: "auto", id: ref, section }));
      }
      return;
    }

    const reference = target.closest<HTMLElement>(".reference-link");
    if (reference) {
      const identifier = reference.dataset.identifier ?? "";
      if (identifier) {
        event.preventDefault();
        if (onReferenceClick) onReferenceClick(identifier, reference.dataset.chapter || undefined, reference.dataset.section || undefined);
        else resources?.open(scopedReference({ source: "auto", id: identifier, section: [reference.dataset.chapter, reference.dataset.section].filter(Boolean).join(".") || undefined }));
      }
      return;
    }

    const anchor = target.closest<HTMLAnchorElement>("a[href]");
    if (anchor && resources) {
      const apiOrigin = new URL(API_BASE || "/", window.location.origin).origin;
      const resource = resourceFromHref(anchor.getAttribute("href") ?? "", window.location.origin, apiOrigin);
      if (resource) { event.preventDefault(); resources.open(scopedReference(resource)); return; }
    }
    const copyButton = target.closest<HTMLButtonElement>("[data-md-copy]");
    if (copyButton?.dataset.mdCopy) {
      event.preventDefault();
      const encoded = copyButton.dataset.mdCopy;
      try {
        void navigator.clipboard.writeText(decodeURIComponent(encoded));
        const previous = copyButton.textContent;
        copyButton.textContent = "Copiado";
        window.setTimeout(() => {
          copyButton.textContent = previous || "Copiar";
        }, 1200);
      } catch {
        // Falha de clipboard não interfere na leitura do documento.
      }
    }
  }

  return (
    <div
      className={cn(
        "note-markdown",
        mode === "compact" && "note-markdown-compact",
        mode === "streaming" && "note-markdown-streaming",
        className,
      )}
      data-markdown-mode={mode}
      onClick={handleClick}
    >
      {segments.map((segment, index) => {
        if (segment.kind === "markdown") {
          const html = rendered[index] ?? "";
          if (!html) return null;
          return (
            <div
              key={"markdown-" + index}
              className="md-static-chunk"
              dangerouslySetInnerHTML={{ __html: html }}
            />
          );
        }

        if (mode === "compact") {
          return <MermaidDiagram key={"mermaid-" + index} source={segment.source} compact />;
        }

        if (!segment.complete) {
          return (
            <div key={"mermaid-" + index} className="md-mermaid-building">
              <span className="md-mermaid-loading-dot" />
              {mode === "streaming" ? "Diagrama em construção…" : "Bloco Mermaid incompleto."}
            </div>
          );
        }

        return <MermaidDiagram key={"mermaid-" + index} source={segment.source} />;
      })}
    </div>
  );
}
