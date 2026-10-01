
import { useEffect, useId, useMemo, useRef, useState } from "react";
import { Copy, Download, Minus, Plus, RotateCcw } from "lucide-react";

type MermaidRenderResult = {
  svg: string;
  bindFunctions?: (element: Element) => void;
};

let mermaidModulePromise: Promise<typeof import("mermaid")> | null = null;
let mermaidInitializedFor: "dark" | "default" | null = null;
let renderQueue: Promise<void> = Promise.resolve();

function loadMermaid(): Promise<typeof import("mermaid")> {
  mermaidModulePromise ??= import("mermaid");
  return mermaidModulePromise;
}

function currentTheme(): "dark" | "default" {
  return document.documentElement.hasAttribute("data-light-bg") ? "default" : "dark";
}

async function renderMermaid(id: string, source: string): Promise<MermaidRenderResult> {
  let resolveResult!: (value: MermaidRenderResult) => void;
  let rejectResult!: (reason?: unknown) => void;

  const result = new Promise<MermaidRenderResult>((resolve, reject) => {
    resolveResult = resolve;
    rejectResult = reject;
  });

  renderQueue = renderQueue
    .catch(() => undefined)
    .then(async () => {
      try {
        const { default: mermaid } = await loadMermaid();
        const theme = currentTheme();
        if (mermaidInitializedFor !== theme) {
          mermaid.initialize({
            startOnLoad: false,
            theme: "base",
            securityLevel: "strict",
            suppressErrorRendering: true,
            themeVariables: {
              darkMode: theme === "dark",
              background: "#201f1e",
              primaryColor: "#38312a",
              primaryTextColor: "#e7e1d9",
              primaryBorderColor: "#9d7953",
              lineColor: "#aa9b8c",
              secondaryColor: "#293b3d",
              tertiaryColor: "#30312c",
              textColor: "#e7e1d9",
              fontFamily: "Inter, system-ui, sans-serif",
            },
          });
          mermaidInitializedFor = theme;
        }
        resolveResult(await mermaid.render(id, source));
      } catch (error) {
        rejectResult(error);
      }
    });

  return result;
}

async function copyText(value: string): Promise<void> {
  await navigator.clipboard.writeText(value);
}

function downloadSvg(svg: string): void {
  const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "diagrama-mermaid.svg";
  anchor.click();
  URL.revokeObjectURL(url);
}

export function MermaidDiagram({
  source,
  compact = false,
}: {
  source: string;
  compact?: boolean;
}) {
  const reactId = useId();
  const renderId = useMemo(
    () => "norvald-mermaid-" + reactId.replace(/[^a-zA-Z0-9_-]/g, ""),
    [reactId],
  );
  const [svg, setSvg] = useState("");
  const [bindFunctions, setBindFunctions] = useState<((element: Element) => void) | null>(null);
  const [error, setError] = useState("");
  const canvasRef = useRef<HTMLDivElement>(null);
  const [zoom, setZoom] = useState(1);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (compact || !source.trim()) return;

    let active = true;
    setSvg("");
    setBindFunctions(null);
    setError("");
    setZoom(1);

    void renderMermaid(renderId, source.trim())
      .then((result) => {
        if (!active) return;
        setSvg(result.svg);
        setBindFunctions(() => result.bindFunctions ?? null);
      })
      .catch((reason) => {
        if (!active) return;
        setError(reason instanceof Error ? reason.message : "Não foi possível renderizar o diagrama.");
      });

    return () => {
      active = false;
    };
  }, [compact, renderId, source]);

  useEffect(() => {
    if (!svg || !bindFunctions || !canvasRef.current) return;
    bindFunctions(canvasRef.current);
  }, [svg, bindFunctions]);

  if (compact) {
    return (
      <div className="md-mermaid-compact" aria-label="Diagrama Mermaid">
        <span className="md-mermaid-compact-icon">◇</span>
        <span>Diagrama Mermaid</span>
      </div>
    );
  }

  return (
    <section className="md-mermaid" aria-label="Diagrama Mermaid">
      <div className="md-mermaid-toolbar">
        <div className="md-mermaid-label">
          <span className="md-mermaid-status-dot" />
          Mermaid
        </div>
        <div className="md-mermaid-actions">
          <button
            type="button"
            onClick={() => setZoom((value) => Math.max(0.6, Number((value - 0.1).toFixed(1))))}
            aria-label="Diminuir diagrama"
            title="Diminuir"
          >
            <Minus className="h-3.5 w-3.5" />
          </button>
          <span className="md-mermaid-zoom">{Math.round(zoom * 100)}%</span>
          <button
            type="button"
            onClick={() => setZoom((value) => Math.min(2, Number((value + 0.1).toFixed(1))))}
            aria-label="Ampliar diagrama"
            title="Ampliar"
          >
            <Plus className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setZoom(1)}
            aria-label="Restaurar tamanho"
            title="Restaurar tamanho"
          >
            <RotateCcw className="h-3.5 w-3.5" />
          </button>
          <span className="md-mermaid-separator" />
          <button
            type="button"
            onClick={() => {
              void copyText(source).then(() => {
                setCopied(true);
                window.setTimeout(() => setCopied(false), 1400);
              });
            }}
            aria-label="Copiar código Mermaid"
            title={copied ? "Copiado" : "Copiar código"}
          >
            <Copy className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            disabled={!svg}
            onClick={() => svg && downloadSvg(svg)}
            aria-label="Baixar SVG"
            title="Baixar SVG"
          >
            <Download className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div className="md-mermaid-viewport">
        {!svg && !error && (
          <div className="md-mermaid-loading">
            <span className="md-mermaid-loading-dot" />
            Renderizando diagrama…
          </div>
        )}

        {error && (
          <div className="md-mermaid-error">
            <p className="md-mermaid-error-title">Não foi possível renderizar este diagrama.</p>
            <p>{error}</p>
            <details>
              <summary>Ver código Mermaid</summary>
              <pre><code>{source}</code></pre>
            </details>
          </div>
        )}

        {svg && !error && (
          <div
            ref={canvasRef}
            className="md-mermaid-canvas"
            style={{ transform: "scale(" + zoom + ")" }}
            dangerouslySetInnerHTML={{ __html: svg }}
          />
        )}
      </div>
    </section>
  );
}
