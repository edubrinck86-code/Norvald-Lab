/** Utilitários de texto do Markdown — sem dependência de renderização.
 *
 * Viviam em `lib/markdown.ts`, que importa `marked` e o CSS do `katex`
 * no topo. Qualquer módulo que só quisesse contar palavras ou resolver
 * referências arrastava ~250 KB de KaTeX para o chunk inicial. Aqui não há
 * nenhuma dependência: quem renderiza continua em `markdown.ts`.
 */
import type { EvidenceItem } from "./evidence";

/**
 * Resolve um `[[Documento]]` contra a Library real — por
 * identificador (ADR-UX-007, ex: "ADR-016"), por reference (nome de
 * arquivo/URL) ou por nome, nessa ordem. `null` se não achar nada (link
 * "quebrado", igual ao Obsidian trata).
 */
export function resolveWikiLink(ref: string, libraryItems: EvidenceItem[]): EvidenceItem | null {
  const clean = ref.trim();
  // A inserção grava `item.identifier || item.id` (BlockEditorOverlay).
  // Quando o item não tem identifier, o que fica no wikilink é o id —
  // então a resolução precisa tentar por id também, senão a referência
  // aponta para um caminho que "não existe" mesmo com o item na Library.
  const byId = libraryItems.find((i) => i.id === clean);
  if (byId) return byId;
  const byIdentifier = libraryItems.find((i) => i.identifier === clean);
  if (byIdentifier) return byIdentifier;
  const byReference = libraryItems.find((i) => i.reference === clean);
  if (byReference) return byReference;
  const lower = clean.toLowerCase();
  const byName = libraryItems.find((i) => i.name.toLowerCase() === lower);
  return byName ?? null;
}

export function countWords(text: string): number {
  const trimmed = text.trim();
  return trimmed ? trimmed.split(/\s+/).length : 0;
}
