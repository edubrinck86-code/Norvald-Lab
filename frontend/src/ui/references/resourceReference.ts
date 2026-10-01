export type ResourceSource = "auto" | "library" | "repository" | "artifact" | "assistant_artifact" | "cloud" | "attachment" | "note" | "notebook";
export interface ResourceReference {
  source: ResourceSource;
  id: string;
  workspaceId?: string;
  sessionId?: string;
  section?: string;
  conversationId?: string;
  taskId?: string;
}
/** Only recognized Studio resources are intercepted. Web links remain external. */
export function resourceFromHref(href: string, origin: string, apiOrigin = origin): ResourceReference | null {
  if (!href || href.startsWith("#")) return null;
  let url: URL;
  try { url = new URL(href, origin + "/"); } catch { return null; }
  const custom = /^(library|repository|artifact|cloud|note|notebook|attachment):(?:\/\/)?(.+)$/i.exec(href);
  if (custom) {
    try { const [id, section] = custom[2].split("#", 2); return { source: custom[1].toLowerCase() as ResourceSource, id: decodeURIComponent(id), section: section ? decodeURIComponent(section) : undefined }; } catch { return null; }
  }
  if (![origin, apiOrigin].includes(url.origin)) return null;
  const path = url.pathname.replace(/^\/api(?=\/)/, "");
  let section: string | undefined;
  try { section = url.hash ? decodeURIComponent(url.hash.slice(1)) : undefined; } catch { return null; }
  const matchers: Array<[RegExp, (match: RegExpMatchArray) => ResourceReference]> = [
    [/^\/(?:evidence-library|library)\/([^/]+)\/?$/, m => ({ source: "library", id: m[1] })],
    [/^\/workspaces\/repository-documents\/([^/]+)(?:\/(?:content|download))?\/?$/, m => ({ source: "repository", id: m[1] })],
    [/^\/repository\/([^/]+)\/?$/, m => ({ source: "repository", id: m[1] })],
    [/^\/workspaces\/([^/]+)\/attachments\/([^/]+)(?:\/(?:content|download))?\/?$/, m => ({ source: "attachment", workspaceId: m[1], id: m[2] })],
    [/^\/workspaces\/notes\/([^/]+)\/?$/, m => ({ source: "note", id: m[1] })],
    [/^\/deliberations\/([^/]+)\/artifacts\/([^/]+)(?:\/(?:content|download))?\/?$/, m => ({ source: "artifact", sessionId: m[1], id: m[2] })],
    [/^\/artifacts?\/([^/]+)\/?$/, m => ({ source: "artifact", id: m[1] })],
    [/^\/cloud\/items\/([^/]+)(?:\/(?:content|text))?\/?$/, m => ({ source: "cloud", id: m[1] })],
    [/^\/assistant\/artifacts\/([^/]+)(?:\/content)?\/?$/, m => ({ source: "assistant_artifact", id: m[1], conversationId: url.searchParams.get("conversation_id") ?? undefined, taskId: url.searchParams.get("task_id") ?? undefined })],
  ];
  for (const [pattern, resolve] of matchers) {
    const match = path.match(pattern);
    if (match) {
      const reference = resolve(match);
      try { return { ...reference, id: decodeURIComponent(reference.id), workspaceId: reference.workspaceId ? decodeURIComponent(reference.workspaceId) : undefined, sessionId: reference.sessionId ? decodeURIComponent(reference.sessionId) : undefined, section }; } catch { return null; }
    }
  }
  if (!/^[a-z][a-z\d+.-]*:/i.test(href) && /\.(?:md|txt|pdf|csv|json|docx?|xlsx?|png|jpe?g|svg|zip)(?:#.*)?$/i.test(href)) {
    try { return { source: "auto", id: decodeURIComponent(path.split("/").at(-1) ?? href), section }; } catch { return null; }
  }
  return null;
}


function objectRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value)
    ? value as Record<string, unknown>
    : {};
}

function stringValue(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

/**
 * Propaga a procedência de um item da Library para referências abertas
 * dentro dele. CDD consolidado preserva a sessão em `reference`; itens
 * promovidos mais novos também carregam `knowledge_provenance`.
 */
export function resourceScopeFromEvidence(item: {
  kind?: string;
  reference?: string;
  metadata?: Record<string, unknown>;
}): Pick<ResourceReference, "workspaceId" | "sessionId"> {
  const metadata = objectRecord(item.metadata);
  const provenance = objectRecord(metadata.knowledge_provenance);
  const semantic = objectRecord(metadata.semantic);
  const semanticMetadata = objectRecord(semantic.metadata);

  const workspaceId =
    stringValue(provenance.origin_workspace_id)
    ?? stringValue(semanticMetadata.workspace_id)
    ?? stringValue(metadata.workspace_id);

  const sessionId =
    stringValue(provenance.origin_session_id)
    ?? stringValue(semanticMetadata.session_id)
    ?? stringValue(metadata.session_id)
    ?? (item.kind === "documento_consolidado" ? stringValue(item.reference) : undefined);

  return { workspaceId, sessionId };
}
