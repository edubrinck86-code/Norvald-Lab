import { diffWordsWithSpace } from 'diff';
import type { RecordedEvent, Snapshot } from '../api';

/** Projeção legível. O Markdown/RAW de origem continua intocado. */
export function responseProjection(content: string): { markdown: string; structured: string | null } {
  const start = content.indexOf('<<CONTRIBUTION>>');
  const end = content.indexOf('<<END_CONTRIBUTION>>', start);
  if (start < 0 || end < 0) return { markdown: content, structured: null };
  const structured = content.slice(start + '<<CONTRIBUTION>>'.length, end).trim();
  try {
    const block = JSON.parse(structured);
    if (!Array.isArray(block.knowledge)) return { markdown: content, structured: null };
    const texts = block.knowledge.filter((item: { content?: unknown }) => typeof item.content === 'string').map((item: { content: string }) => item.content);
    const before = content.slice(0, start).trim();
    const after = content.slice(end + '<<END_CONTRIBUTION>>'.length).trim();
    return { markdown: [before, ...texts, after].filter(Boolean).join('\n\n'), structured };
  } catch { return { markdown: content, structured: null }; }
}

export function compareWords(before: string, after: string) {
  // Texto literal, sem inferência semântica. Evita custo quadrático de textos enormes.
  if (before.length + after.length > 100_000) return null;
  return diffWordsWithSpace(before, after);
}
export function eventParticipant(event: RecordedEvent, snapshot: Snapshot): string | undefined {
  if (typeof event.data.participant_id === 'string') return event.data.participant_id;
  return snapshot.requests.find(request => request.context.metadata.execution_id === event.data.execution_id)?.agent_id;
}
export function eventRun(event: RecordedEvent, snapshot: Snapshot): string | undefined {
  if (typeof event.data.run_id === 'string') return event.data.run_id;
  return snapshot.requests.find(request => request.context.metadata.execution_id === event.data.execution_id)?.context.metadata.run_id;
}
export function eventLabel(event: RecordedEvent): string {
  const names: Record<string, string> = {
    'experiment.started': 'Experimento iniciado', 'experiment.completed': 'Experimento fechado',
    'execution.started': 'Execução iniciada', 'execution.completed': 'Resposta registrada',
    'execution.failed': 'Falha registrada', 'tool.started': 'Ferramenta iniciada',
    'tool.completed': 'Ferramenta concluída', 'tool.failed': 'Falha na ferramenta',
    'provider.request.started': 'Solicitação enviada ao provedor',
    'provider.request.completed': 'Retorno do provedor',
    'provider.request.failed': 'Falha no provedor',
  };
  const name = typeof event.data.tool_name === 'string' ? ' · ' + event.data.tool_name : '';
  return (names[event.event] ?? event.event) + name;
}
export function elapsed(at: string, origin: string): string {
  const milliseconds = Math.max(0, Date.parse(at) - Date.parse(origin));
  if (!Number.isFinite(milliseconds)) return '—';
  if (milliseconds < 1000) return milliseconds + ' ms';
  const total = Math.floor(milliseconds / 1000);
  return Math.floor(total / 60).toString().padStart(2, '0') + ':' + (total % 60).toString().padStart(2, '0');
}
export function familyId(item: { experiment_id: string; source_experiment_id?: string }): string {
  return item.source_experiment_id || item.experiment_id;
}
