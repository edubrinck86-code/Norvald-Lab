export type Exposure = 'blind' | 'self' | 'exposed';
export type Connection = { kind: string; credential_env: string; base_url: string; has_key: boolean; saved_key: boolean; credential_source: 'environment' | 'local' | 'none' };
export type LabSettings = { live_enabled: boolean; connections: Connection[] };
export type CatalogModel = { id: string; name: string; tools: boolean | null; reasoning: boolean | null; free: boolean | null; local: boolean; context_length: number | null; pricing: Record<string, string>; dynamic_router: boolean };
export type Catalog = { kind: string; fetched_at: string; models: CatalogModel[] };
export type Participant = { id: string; name: string; role: string; provider: string; model: string; reasoning_effort: string; sampling: { temperature?: number; top_p?: number; max_tokens?: number } };
export type DocumentItem = { id: string; title: string; text: string; source: string };
export type Spec = {
  schema_version: string; experiment_id: string; mode: 'demo' | 'live';
  task: { id: string; objective: string; instructions: string };
  participants: Participant[]; providers: Record<string, { kind: string; credential_env?: string; base_url?: string }>;
  documents: DocumentItem[]; working_context: Record<string, unknown>; repetitions: number;
  condition: { id: string; exposure: Exposure; prior_experiment?: string; tools: 'off' | 'corpus'; max_tool_calls?: number; max_tool_iterations?: number };
  budget: { max_concurrency: number; max_concurrency_per_provider: number; timeout_seconds: number; max_logical_executions: number };
};
export type ExperimentItem = { experiment_id: string; status: string; task: string; exposure: Exposure; source_experiment_id?: string; synthetic: boolean };
export type RecordedEvent = { at: string; event: string; data: Record<string, unknown> };
export type PreparedRequest = { agent_id: string; instructions: string; shared_instructions: string; wave_instructions: string; user_message: string; reasoning_effort: string; context: { working_context: string; metadata: { run_id: string; repetition_index: number; execution_id: string; source_observation_ids: string[] } } };
export type RawRecord = {
  observation_id: string; logical_execution_id: string; participant_id: string; participant_name: string;
  run_id: string; started_at: string; captured_at: string; reasoning_exposure_mode: string;
  requested_model: string; request: Record<string, unknown>;
  result: { content: string; reasoning: string | null; tokens: number; duration_seconds: number; metadata: Record<string, unknown> } | null;
  error: { message: string; type: string } | null;
};
export type Snapshot = { experiment_id: string; status: string; provisional: boolean; integrity: { valid: boolean; issues: string[] } | null; spec: Spec; requests: PreparedRequest[]; events: RecordedEvent[]; records: RawRecord[] };
export type Anchor = { experiment_id: string; observation_id?: string; excerpt?: string; event_index?: number };
export type Note = { id: string; title: string; content: string; anchor: Anchor | null; created_at: string; updated_at: string };
export type WorkBlock = { id: string; title: string; content: string; type: string; source_note: (Note & { captured_at: string }) | null };
export type Workbook = { id: string; title: string; blocks: WorkBlock[]; revision: number; created_at: string; updated_at: string };
export type CorpusCapture = { workbook_id: string; revision: number; block_ids: string[]; sha256: string; document: DocumentItem };

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } });
  if (response.status === 204) return undefined as T;
  const value = await response.json();
  if (!response.ok) throw new ApiError(typeof value.detail === 'string' ? value.detail : JSON.stringify(value.detail ?? value), response.status);
  return value as T;
}
export const conditions: Record<Exposure, { title: string; description: string }> = {
  blind: { title: 'Resposta independente', description: 'Pergunta e documentos, sem respostas dos participantes.' },
  self: { title: 'Reconsideração individual', description: 'Mesmo material e a própria resposta anterior.' },
  exposed: { title: 'Exposição aos colegas', description: 'Mesmo material, a própria resposta anterior e as respostas dos colegas previstas no experimento.' },
};
export function statusLabel(status: string): string {
  return ({ running: 'Em execução', complete: 'Concluído', incomplete: 'Com falhas', aborted: 'Interrompido', unclosed: 'Sem fechamento', failed: 'Falhou', accepted: 'Aguardando início' } as Record<string, string>)[status] ?? status;
}
