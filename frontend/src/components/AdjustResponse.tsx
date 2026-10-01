import { useEffect, useState } from 'react';
import { NotebookPen, Send } from 'lucide-react';
import { api, type ContributionCheck, type RawRecord } from '../api';
import { NorvaldMarkdown } from '../ui/markdown/NorvaldMarkdown';
import { MarkdownToolbar } from '../ui/MarkdownToolbar';

type Adjustment = { id: string; observation_id: string; instruction: string; parent_id: string | null; created_at: string; max_tokens: number | null; status: string; record?: RawRecord; check?: ContributionCheck; error?: string };

export function AdjustResponse({ experimentId, record, invalid, maxTokens }: { experimentId: string; record: RawRecord; invalid: boolean; maxTokens?: number }) {
  const [instruction, setInstruction] = useState(invalid ? 'Corrija o formato da contribuição. Entregue a resposta completa, com knowledge não vazio, JSON válido e o delimitador <<END_CONTRIBUTION>>. Preserve os argumentos que se sustentam no material original.' : '');
  const [limit, setLimit] = useState(maxTokens?.toString() ?? '');
  const [attempts, setAttempts] = useState<Adjustment[]>([]);
  const [parent, setParent] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    async function read() {
      try { const values = await api<Adjustment[]>('/api/adjustments/' + experimentId, { signal: controller.signal }); if (active) setAttempts(values.filter(a => a.observation_id === record.observation_id)); }
      catch (reason) { if (active) setError(String(reason)); }
    }
    void read(); const timer = setInterval(() => { void read(); }, 1500);
    return () => { active = false; controller.abort(); clearInterval(timer); };
  }, [experimentId, record.observation_id]);
  const running = attempts.some(a => a.status === 'running');
  async function send() {
    setBusy(true); setError(''); setMessage('');
    try {
      await api('/api/adjustments/' + experimentId, { method: 'POST', body: JSON.stringify({ observation_id: record.observation_id, instruction, max_tokens: limit === '' ? null : Number(limit), parent_id: parent }) });
      setAttempts((await api<Adjustment[]>('/api/adjustments/' + experimentId)).filter(a => a.observation_id === record.observation_id));
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
  return <section className="adjustment-panel"><h3>Pedir ajuste à LLM</h3><p>O modelo recebe o material já salvo, esta resposta e sua orientação. Só este participante será chamado. A nova tentativa fica registrada separadamente e pode ser levada às Notes.</p><p className="muted">O ajuste não substitui a coleta original nem libera uma comparação controlada que tenha sido bloqueada. É uma nova chamada à API, com consumo próprio.</p>
    <div className="adjustment-form"><label>O que a LLM deve ajustar?<textarea aria-label="Orientação para ajuste" value={instruction} onChange={event => setInstruction(event.target.value)} maxLength={20000} /></label><label>Limite de saída (tokens)<input aria-label="Limite de saída do ajuste" type="number" min="1" max="200000" placeholder="Manter o limite original" value={limit} onChange={event => setLimit(event.target.value)} /></label>{parent ? <p>Continuando a tentativa {parent}. <button className="text-button" onClick={() => setParent(null)}>Voltar à resposta original</button></p> : null}<button className="button" disabled={busy || running || !instruction.trim()} onClick={() => { void send(); }}><Send size={15} />{busy || running ? 'Ajustando…' : 'Enviar ajuste'}</button></div>
    {error ? <div role="alert" className="error-banner">{error}</div> : null}{message ? <p role="status">{message}</p> : null}
    {attempts.map((attempt, index) => <article className="adjustment-attempt" key={attempt.id}><h4>Tentativa {index + 1} · {attempt.status === 'running' ? 'Em execução' : attempt.status === 'unclosed' ? 'Interrompida / sem fechamento' : attempt.status === 'complete' ? 'Resposta recebida' : 'Falhou'}</h4><small>{attempt.created_at ? new Date(attempt.created_at).toLocaleString('pt-BR') : ''} · {attempt.record?.result?.tokens ?? '—'} tokens</small><p>{attempt.instruction}</p>{attempt.error ? <p className="danger">{attempt.error}</p> : null}{attempt.check ? <p>{attempt.check.usable ? 'Formato estruturado válido nesta tentativa de ajuste.' : attempt.check.message}</p> : null}{attempt.record?.result ? <><NorvaldMarkdown content={attempt.record.result.content} /><MarkdownToolbar markdown={attempt.record.result.content} filename={attempt.id} /><div className="experiment-actions"><button className="button secondary" disabled={busy} onClick={() => { setParent(attempt.id); setInstruction(''); setMessage('Descreva o próximo ajuste na orientação acima.'); }} >Continuar este ajuste</button><button className="button secondary" disabled={busy} onClick={() => { void saveNote(attempt); }}><NotebookPen size={15} />Salvar nas Notes</button></div></> : null}<details><summary>Registro desta tentativa</summary><pre>{JSON.stringify(attempt, null, 2)}</pre></details></article>)}
  </section>;
}
