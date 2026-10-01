import { useState } from 'react';
import { Eye, NotebookPen, RefreshCw, Send } from 'lucide-react';
import { api, type Adjustment, type ContributionCheck, type RawRecord } from '../api';
import { contributionSummary, latestAdjustment, usableAdjustment, validAdjustment } from '../lib/adjustments';
import { Modal } from './Modal';
import { responseProjection } from '../lib/observation';
import { NorvaldMarkdown } from '../ui/markdown/NorvaldMarkdown';
import { MarkdownToolbar } from '../ui/MarkdownToolbar';

type Preview = { instruction: string; max_tokens: number | null; diagnostic: Pick<ContributionCheck, 'message' | 'code' | 'usable' | 'rejected'> & { details: string[]; execution_error: unknown }; request: { instructions: string; shared_instructions: string; wave_instructions: string; user_message: string } };

export function AdjustResponse({ experimentId, record, invalid, maxTokens, attempts, historyError, onRefresh, onAccepted }: {
  experimentId: string; record: RawRecord; invalid: boolean; maxTokens?: number; attempts: Adjustment[]; historyError: string;
  onRefresh(): void; onAccepted(attempt: Adjustment): void;
}) {
  const [instruction, setInstruction] = useState(invalid ? 'Corrija o formato e as partes recusadas apontadas no diagnóstico. Entregue a resposta completa, com knowledge não vazio, JSON válido e o delimitador <<END_CONTRIBUTION>>. Preserve os argumentos que se sustentam no material original.' : '');
  const [limit, setLimit] = useState(maxTokens?.toString() ?? '');
  const [parent, setParent] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [preview, setPreview] = useState<Preview | null>(null);
  const latest = latestAdjustment(attempts, record.observation_id);
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
      onAccepted({ id: accepted.id, observation_id: record.observation_id, instruction, parent_id: parent, created_at: new Date().toISOString(), max_tokens: limit === '' ? null : Number(limit), status: 'running' });
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
  function continueAttempt(attempt: Adjustment, correctRejected = false) {
    setParent(attempt.id); setLimit(attempt.max_tokens?.toString() ?? '');
    setInstruction(correctRejected ? 'Corrija as partes recusadas desta tentativa, conforme o diagnóstico específico. Preserve as unidades aceitas que se sustentam no material. Reenvie a resposta completa e o bloco CONTRIBUTION. Não invente relações nem altere tipos apenas para passar pela validação.' : '');
    setMessage(correctRejected ? 'Pedido preparado a partir desta tentativa. Confira antes de enviar.' : 'Descreva o próximo ajuste na orientação acima.');
    document.getElementById('response-adjustments')?.scrollIntoView({ block: 'start' });
  }
  return <section className="adjustment-panel" id="response-adjustments"><h3>Pedir ajuste à LLM</h3>{validAdjustment(latest) ? <div className="adjustment-success" role="status"><strong>O último ajuste está válido, sem partes recusadas.</strong><p>O formato passou na validação. O diagnóstico acima continua sendo o da resposta original. Você pode salvar esta resposta nas Notes; outra correção de formato não é necessária nesta tentativa.</p></div> : usableAdjustment(latest) ? <div className="adjustment-partial" role="status"><strong>O último ajuste foi aceito parcialmente.</strong><p>{contributionSummary(latest!.check!)} As recusas estão discriminadas nesta tentativa. Use Corrigir partes recusadas para preparar um pedido específico, sem enviar automaticamente.</p></div> : null}<p>O modelo recebe o material já salvo, esta resposta e sua orientação. O diagnóstico específico do erro e as partes recusadas também são enviados. Só este participante será chamado. A nova tentativa fica registrada separadamente e pode ser levada às Notes.</p><p className="muted">O ajuste não substitui a coleta original nem libera uma comparação controlada que tenha sido bloqueada. É uma nova chamada à API, com consumo próprio.</p>
    <div className="adjustment-form"><label>O que a LLM deve ajustar?<textarea aria-label="Orientação para ajuste" value={instruction} onChange={event => setInstruction(event.target.value)} maxLength={20000} /></label><label>Limite de saída (tokens)<input aria-label="Limite de saída do ajuste" type="number" min="1" max="200000" placeholder="Manter o limite original" value={limit} onChange={event => setLimit(event.target.value)} /></label>{parent ? <p>Continuando a tentativa {parent}. <button className="text-button" onClick={() => setParent(null)}>Voltar à resposta original</button></p> : null}<button className="button secondary" disabled={busy || running || !instruction.trim()} onClick={() => { void inspect(); }}><Eye size={15} />Ver pedido de ajuste</button><button className="button" disabled={busy || running || !instruction.trim()} onClick={() => { void send(); }}><Send size={15} />{busy || running ? 'Ajustando…' : 'Enviar ajuste'}</button></div>
    {error || historyError ? <div role="alert" className="error-banner">{error || historyError}<button className="button secondary" disabled={busy} onClick={() => { setError(''); onRefresh(); }}><RefreshCw size={15} />Atualizar ajustes</button></div> : null}{message ? <p role="status">{message}</p> : null}
    {attempts.map((attempt, index) => <article className="adjustment-attempt" key={attempt.id}><h4>Tentativa {index + 1} · {attempt.status === 'running' ? 'Em execução' : attempt.status === 'unclosed' ? 'Interrompida / sem fechamento' : attempt.status === 'complete' ? 'Resposta recebida' : 'Falhou'}</h4><small>{attempt.created_at ? new Date(attempt.created_at).toLocaleString('pt-BR') : ''} · {attempt.record?.result?.tokens ?? '—'} tokens</small><p>{attempt.instruction}</p>{attempt.error ? <p className="danger">{attempt.error}</p> : null}{attempt.check ? <div className="adjustment-check"><p>{contributionSummary(attempt.check)}</p>{attempt.check.rejected.length ? <details open><summary>Partes recusadas nesta tentativa · {attempt.check.rejected.length}</summary><ul>{attempt.check.rejected.map((part, rejectedIndex) => <li key={rejectedIndex}>{part.kind === 'relation' ? 'Relação' : 'Unidade'}: {part.reason}</li>)}</ul></details> : null}</div> : null}{attempt.record?.result ? <><NorvaldMarkdown content={responseProjection(attempt.record.result.content).markdown} /><details><summary>Resposta do ajuste em Markdown</summary><pre>{attempt.record.result.content}</pre></details>{!attempt.record.result.content.trim() ? <p className="danger">Houve consumo registrado, mas nenhum texto de resposta foi disponibilizado. Os tokens, sozinhos, não confirmam uma resposta completa.</p> : null}{attempt.record.result.reasoning ? <details><summary>Reasoning disponibilizado nesta tentativa</summary><NorvaldMarkdown content={attempt.record.result.reasoning} /></details> : null}<MarkdownToolbar markdown={attempt.record.result.content} filename={attempt.id} /><div className="experiment-actions">{attempt.check?.rejected.length ? <button className="button secondary" disabled={busy || running} onClick={() => continueAttempt(attempt, true)}>Corrigir partes recusadas</button> : null}<button className="button secondary" disabled={busy || running} onClick={() => continueAttempt(attempt)}>Continuar este ajuste</button><button className="button secondary" disabled={busy || !attempt.record.result.content.trim()} onClick={() => { void saveNote(attempt); }}><NotebookPen size={15} />Salvar nas Notes</button></div></> : null}<details><summary>Registro desta tentativa</summary><pre>{JSON.stringify(attempt, null, 2)}</pre></details></article>)}
    {preview ? <Modal title="Pedido de ajuste para a LLM" onClose={() => setPreview(null)}><div className="modal-scroll"><p className="muted">Esta conferência não chama a LLM. O envio inclui o mesmo objetivo, material original, resposta anterior, diagnóstico e sua orientação.</p><h3>Diagnóstico que será enviado</h3><p>{preview.diagnostic.message}</p>{preview.diagnostic.details.map((detail, index) => <p key={index}>{detail}</p>)}{preview.diagnostic.rejected.length ? <ul>{preview.diagnostic.rejected.map((part, index) => <li key={index}>{part.kind} · {part.identifier || 'Sem identificador'}: {part.reason}</li>)}</ul> : null}{preview.diagnostic.execution_error ? <pre>{JSON.stringify(preview.diagnostic.execution_error, null, 2)}</pre> : null}<h3>Sua orientação</h3><p>{preview.instruction}</p><p>Limite de saída: {preview.max_tokens ?? 'Padrão do provedor'}</p><details open><summary>Pergunta e resposta que serão enviadas</summary><pre>{preview.request.user_message}</pre></details><details><summary>Instruções completas do ajuste</summary><pre>{preview.request.instructions}</pre></details><details><summary>Material e regras compartilhadas</summary><pre>{preview.request.shared_instructions}</pre></details><details><summary>Contexto original completo</summary><pre>{preview.request.wave_instructions}</pre></details></div><footer className="modal-footer"><button className="button secondary" onClick={() => setPreview(null)}>Voltar ao ajuste</button></footer></Modal> : null}
  </section>;
}
