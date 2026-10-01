import { useEffect, useState } from 'react';
import { Eye, NotebookPen, RefreshCw, Send } from 'lucide-react';
import { api, type ContributionCheck, type RawRecord } from '../api';
import { Modal } from './Modal';
import { NorvaldMarkdown } from '../ui/markdown/NorvaldMarkdown';
import { MarkdownToolbar } from '../ui/MarkdownToolbar';

type Adjustment = { id: string; observation_id: string; instruction: string; parent_id: string | null; created_at: string; max_tokens: number | null; status: string; record?: RawRecord; check?: ContributionCheck; error?: string };
type Preview = { instruction: string; max_tokens: number | null; diagnostic: Pick<ContributionCheck, 'message' | 'code' | 'usable' | 'rejected'> & { details: string[]; execution_error: unknown }; request: { instructions: string; shared_instructions: string; wave_instructions: string; user_message: string } };

export function AdjustResponse({ experimentId, record, invalid, maxTokens }: { experimentId: string; record: RawRecord; invalid: boolean; maxTokens?: number }) {
  const [instruction, setInstruction] = useState(invalid ? 'Corrija o formato da contribuição. Entregue a resposta completa, com knowledge não vazio, JSON válido e o delimitador <<END_CONTRIBUTION>>. Preserve os argumentos que se sustentam no material original.' : '');
  const [limit, setLimit] = useState(maxTokens?.toString() ?? '');
  const [attempts, setAttempts] = useState<Adjustment[]>([]);
  const [parent, setParent] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [preview, setPreview] = useState<Preview | null>(null);
  const [refresh, setRefresh] = useState(0);
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const controller = new AbortController();
    async function read() {
      try {
        const values = await api<Adjustment[]>('/api/adjustments/' + experimentId, { signal: controller.signal });
        if (!active) return;
        const current = values.filter(a => a.observation_id === record.observation_id);
        setAttempts(current);
        if (current.some(a => a.status === 'running')) timer = setTimeout(() => { void read(); }, 1500);
      }
      catch (reason) { if (active) setError(String(reason)); }
    }
    const resume = () => { if (document.visibilityState === 'visible') setRefresh(value => value + 1); };
    window.addEventListener('focus', resume);
    void read();
    return () => { active = false; controller.abort(); clearTimeout(timer); window.removeEventListener('focus', resume); };
  }, [experimentId, record.observation_id, refresh]);
  const running = attempts.some(a => a.status === 'running');
  function payload() { return { observation_id: record.observation_id, instruction, max_tokens: limit === '' ? null : Number(limit), parent_id: parent }; }
  async function inspect() {
    setBusy(true); setError('');
    try { setPreview(await api<Preview>('/api/adjustments/' + experimentId + '/preview', { method: 'POST', body: JSON.stringify(payload()) })); }
    catch (reason) { setError(String(reason)); } finally { setBusy(false); }
  }
  async function send() {
    setBusy(true); setError(''); setMessage('');
    try {
      const accepted = await api<{ id: string }>('/api/adjustments/' + experimentId, { method: 'POST', body: JSON.stringify(payload()) });
      setAttempts(values => [...values, { id: accepted.id, observation_id: record.observation_id, instruction, parent_id: parent, created_at: '', max_tokens: limit === '' ? null : Number(limit), status: 'running' }]);
      setRefresh(value => value + 1);
      setMessage('Ajuste enviado. Você pode fechar a Bancada e voltar depois.');
    } catch (reason) { setError(String(reason)); } finally { setBusy(false); }
  }
  async function saveNote(attempt: Adjustment) {
    setBusy(true); setError('');
    try {
      await api('/api/notes', { method: 'POST', body: JSON.stringify({ title: 'Ajuste · ' + record.participant_name,
        content: '## Resposta ajustada\n\nOrigem: ' + experimentId + '\n\nTentativa: ' + attempt.id + '\n\nOrientação: ' + attempt.instruction + '\n\n' + attempt.record!.result!.content, anchor: null }) });
      setMessage('Resposta ajustada salva nas Notes. Você pode trazê-la para o Notebook.');
    } catch (reason) { setError(String(reason)); } finally { setBusy(false); }
  }
  return <section className="adjustment-panel"><h3>Pedir ajuste à LLM</h3><p>O modelo recebe o material já salvo, esta resposta e sua orientação. O diagnóstico específico do erro e as partes recusadas também são enviados. Só este participante será chamado. A nova tentativa fica registrada separadamente e pode ser levada às Notes.</p><p className="muted">O ajuste não substitui a coleta original nem libera uma comparação controlada que tenha sido bloqueada. É uma nova chamada à API, com consumo próprio.</p>
    <div className="adjustment-form"><label>O que a LLM deve ajustar?<textarea aria-label="Orientação para ajuste" value={instruction} onChange={event => setInstruction(event.target.value)} maxLength={20000} /></label><label>Limite de saída (tokens)<input aria-label="Limite de saída do ajuste" type="number" min="1" max="200000" placeholder="Manter o limite original" value={limit} onChange={event => setLimit(event.target.value)} /></label>{parent ? <p>Continuando a tentativa {parent}. <button className="text-button" onClick={() => setParent(null)}>Voltar à resposta original</button></p> : null}<button className="button secondary" disabled={busy || running || !instruction.trim()} onClick={() => { void inspect(); }}><Eye size={15} />Ver pedido de ajuste</button><button className="button" disabled={busy || running || !instruction.trim()} onClick={() => { void send(); }}><Send size={15} />{busy || running ? 'Ajustando…' : 'Enviar ajuste'}</button></div>
    {error ? <div role="alert" className="error-banner">{error}<button className="button secondary" disabled={busy} onClick={() => { setError(''); setRefresh(value => value + 1); }}><RefreshCw size={15} />Atualizar ajustes</button></div> : null}{message ? <p role="status">{message}</p> : null}
    {attempts.map((attempt, index) => <article className="adjustment-attempt" key={attempt.id}><h4>Tentativa {index + 1} · {attempt.status === 'running' ? 'Em execução' : attempt.status === 'unclosed' ? 'Interrompida / sem fechamento' : attempt.status === 'complete' ? 'Resposta recebida' : 'Falhou'}</h4><small>{attempt.created_at ? new Date(attempt.created_at).toLocaleString('pt-BR') : ''} · {attempt.record?.result?.tokens ?? '—'} tokens</small><p>{attempt.instruction}</p>{attempt.error ? <p className="danger">{attempt.error}</p> : null}{attempt.check ? <p>{attempt.check.usable ? 'Formato estruturado válido nesta tentativa de ajuste.' : attempt.check.message}</p> : null}{attempt.record?.result ? <><NorvaldMarkdown content={attempt.record.result.content} /><MarkdownToolbar markdown={attempt.record.result.content} filename={attempt.id} /><div className="experiment-actions"><button className="button secondary" disabled={busy} onClick={() => { setParent(attempt.id); setLimit(attempt.max_tokens?.toString() ?? ''); setInstruction(''); setMessage('Descreva o próximo ajuste na orientação acima.'); }} >Continuar este ajuste</button><button className="button secondary" disabled={busy} onClick={() => { void saveNote(attempt); }}><NotebookPen size={15} />Salvar nas Notes</button></div></> : null}<details><summary>Registro desta tentativa</summary><pre>{JSON.stringify(attempt, null, 2)}</pre></details></article>)}
    {preview ? <Modal title="Pedido de ajuste para a LLM" onClose={() => setPreview(null)}><div className="modal-scroll"><p className="muted">Esta conferência não chama a LLM. O envio inclui o mesmo objetivo, material original, resposta anterior, diagnóstico e sua orientação.</p><h3>Diagnóstico que será enviado</h3><p>{preview.diagnostic.message}</p>{preview.diagnostic.details.map((detail, index) => <p key={index}>{detail}</p>)}{preview.diagnostic.rejected.length ? <ul>{preview.diagnostic.rejected.map((part, index) => <li key={index}>{part.kind} · {part.identifier || 'Sem identificador'}: {part.reason}</li>)}</ul> : null}{preview.diagnostic.execution_error ? <pre>{JSON.stringify(preview.diagnostic.execution_error, null, 2)}</pre> : null}<h3>Sua orientação</h3><p>{preview.instruction}</p><p>Limite de saída: {preview.max_tokens ?? 'Padrão do provedor'}</p><details open><summary>Pergunta e resposta que serão enviadas</summary><pre>{preview.request.user_message}</pre></details><details><summary>Instruções completas do ajuste</summary><pre>{preview.request.instructions}</pre></details><details><summary>Material e regras compartilhadas</summary><pre>{preview.request.shared_instructions}</pre></details><details><summary>Contexto original completo</summary><pre>{preview.request.wave_instructions}</pre></details></div><footer className="modal-footer"><button className="button secondary" onClick={() => setPreview(null)}>Voltar ao ajuste</button></footer></Modal> : null}
  </section>;
}
