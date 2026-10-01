import { useMemo, type RefObject } from "react";
import { ListTree } from "lucide-react";
import { cn } from "../../lib/utils";

export interface MarkdownIndexEntry {
  level: number;
  text: string;
  index: number;
}

export function extractMarkdownIndex(markdown: string): MarkdownIndexEntry[] {
  const headings: MarkdownIndexEntry[] = [];
  let fenced = false;

  for (const rawLine of markdown.replace(/^\uFEFF?---\s*\n[\s\S]*?\n---\s*\n?/, "").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (/^(```|~~~)/.test(line)) {
      fenced = !fenced;
      continue;
    }
    if (fenced) continue;

    const atx = /^(#{1,6})\s+(.+?)\s*#*\s*$/.exec(line);
    if (!atx) continue;
    const text = atx[2]
      .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
      .replace(/[*_~`]/g, "")
      .trim();
    if (!text) continue;
    headings.push({ level: atx[1].length, text, index: headings.length });
  }

  return headings;
}

export function scrollMarkdownHeading(
  contentRoot: HTMLElement | null,
  scrollRoot: HTMLElement | null,
  index: number,
) {
  if (!scrollRoot) return;
  if (index < 0) {
    scrollRoot.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }
  if (!contentRoot) return;
  const heading = contentRoot.querySelectorAll<HTMLElement>("h1,h2,h3,h4,h5,h6")[index];
  if (!heading) return;
  const top =
    heading.getBoundingClientRect().top
    - scrollRoot.getBoundingClientRect().top
    + scrollRoot.scrollTop
    - 24;
  scrollRoot.scrollTo({ top, behavior: "smooth" });
}

export function MarkdownIndexSidebar({
  title,
  markdown,
  contentRef,
  scrollRef,
  onNavigate,
  className,
}: {
  title: string;
  markdown: string;
  contentRef?: RefObject<HTMLElement | null>;
  scrollRef?: RefObject<HTMLElement | null>;
  onNavigate?: (index: number) => void;
  className?: string;
}) {
  const entries = useMemo(() => extractMarkdownIndex(markdown), [markdown]);

  function navigate(index: number) {
    if (onNavigate) {
      onNavigate(index);
      return;
    }
    scrollMarkdownHeading(contentRef?.current ?? null, scrollRef?.current ?? null, index);
  }

  return (
    <aside className={cn("flex w-[230px] shrink-0 flex-col border-r border-line-soft bg-layer-sunken-veil", className)}>
      <div className="shrink-0 border-b border-line-soft px-4 py-4">
        <div className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
          <ListTree className="h-3.5 w-3.5" />
          Índice
        </div>
        <button
          type="button"
          onClick={() => navigate(-1)}
          title={title}
          className="mt-3 block w-full truncate text-left text-xs font-semibold text-foreground transition hover:text-primary"
        >
          {title}
        </button>
      </div>
      <nav className="min-h-0 flex-1 overflow-y-auto px-2.5 py-3">
        {entries.length ? (
          <div className="space-y-0.5">
            {entries.map((entry) => (
              <button
                key={`${entry.index}-${entry.text}`}
                type="button"
                onClick={() => navigate(entry.index)}
                title={entry.text}
                className="block w-full truncate rounded-control py-1.5 pr-2 text-left text-[11px] leading-4 text-muted-foreground transition-colors hover:bg-layer-panel hover:text-foreground"
                style={{ paddingLeft: `${8 + Math.max(0, entry.level - 1) * 10}px` }}
              >
                {entry.text}
              </button>
            ))}
          </div>
        ) : (
          <p className="px-2 py-2 text-[11px] leading-5 text-subtle">
            Nenhum título encontrado neste Markdown.
          </p>
        )}
      </nav>
    </aside>
  );
}
