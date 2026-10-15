import { useCallback, useEffect, useState } from 'react';
import { AlertCircle, Bot, CheckCircle2, ClipboardCheck, MessageCircle, RefreshCw, Send, ShieldCheck } from 'lucide-react';
import { api, type LabSettings } from '../api';

type Issue = {
  id: string; experiment_id: string; criterion_id: string; criterion_version: string;
  observation_id: string; participant_id: string; run_id: string;
  status: string; validator_code: string; message: string; note: string;
};
type Recovery = {
  action: string; allowed: boolean; automatic: boolean; requires_approval: boolean;
  reason: string; original_still_unmet: boolean; current_evaluation_status: string;
  proposed_payload: { observation_id: string; instruction: string; max_tokens: number | null } | null;
  revalidations: { adjustment_id: string; status: string; criterion_status: string; integrity_verified: boolean; source_link_verified: boolean }[];
};
type Detail = Issue & { history: { seq: number; event: string; at: string; payload: Record<string, unknown> }[]; recovery: Recovery };
type Message = { seq: number; role: string; content: string; provider: string; model: string; tokens: number | null; at: string };
type AssistantSettings = { kind: string; model: string; max_output_tokens: number; configured: boolean };
type Preview = {
  incident_id: string; approval: { approval_token: string; expires_at: string };
  preview: { request: { instructions: string; user_message: string }; diagnostic: { code: string; message: string; details: string[] } };
  requires_approval: boolean;
};

const explanation: Record<string, string> = {
  preview_adjustment: 'Um ajuste separado pode ser revisado e autorizado. Não substitui a observação original.',
  new_collection_review: 'Avalie uma nova coleta independente; não é permitido completar artificialmente o RAW.',
  investigate_integrity: 'A integridade precisa ser investigada; a recuperação está bloqueada.',
  review_manually: 'Não há ajuste automático admissível para esta ocorrência.',
};

export function LabAssistant({ selectedExperiment, onOpenExperiment }: {
  selectedExperiment: string; onOpenExperiment(id: string): void;
}) {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [selected, setSelected] = useState('');
  const [detail, setDetail] = useState<Detail | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [settings, setSettings] = useState<AssistantSettings>({ kind: '', model: '', max_output_tokens: 1500, configured: false });
  const [connections, setConnections] = useState<LabSettings | null>(null);
  const [question, setQuestion] = useState('');
  const [instruction, setInstruction] = useState('');
  const [limit, setLimit] = useState('');
  const [preview, setPreview] = useState<Preview | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const load = useCallback(async () => {
    const [found, conf, all] = await Promise.all([
      api<Issue[]>('/api/criteria/incidents?limit=500'),
      api<AssistantSettings>('/api/assistant/settings'),
      api<LabSettings>('/api/settings'),
    ]);
    setIssues(found); setSettings(conf); setConnections(all);
    setSelected(previous => previous && found.some(x => x.id === previous)
      ? previous
      : (found.find(x => x.experiment_id === selectedExperiment)?.id ?? found[0]?.id ?? ''));
  }, [selectedExperiment]);

  useEffect(() => { void load().catch(reason => setError(String(reason))); }, [load]);
  useEffect(() => {
    if (!selected) { setDetail(null); setMessages([]); return; }
    let active = true;
    setPreview(null); setConfirmed(false); setError(''); setNotice('');
    Promise.all([
      api<Detail>('/api/criteria/incidents/' + selected),
      api<{ messages: Message[] }>('/api/assistant/incidents/' + selected + '/conversation'),
    ]).then(([next, chat]) => {
      if (!active) return;
      setDetail(next); setMessages(chat.messages);
      setInstruction(next.recovery.proposed_payload?.instruction ?? '');
      setLimit(next.recovery.proposed_payload?.max_tokens?.toString() ?? '');
    }).catch(reason => { if (active) setError(String(reason)); });
    return () => { active = false; };
  }, [selected]);

  async function resync() {
    if (!selectedExperiment) { setError('Selecione um experimento na Bancada para verificar os critérios.'); return; }
    setBusy('refresh'); setError('');
    try {
      await api('/api/experiments/' + selectedExperiment + '/criteria/reconcile', { method: 'POST' });
      await load();
      if (selected) setDetail(await api<Detail>('/api/criteria/incidents/' + selected));
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  async function saveModel() {
    setBusy('model'); setError('');
    try {
      const chosen = await api<AssistantSettings>('/api/assistant/settings', {
        method: 'PUT',
        body: JSON.stringify({ kind: settings.kind, model: settings.model, max_output_tokens: settings.max_output_tokens }),
      });
      setSettings(chosen); setNotice('Modelo operador configurado. Não altera os modelos dos experimentos.');
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  async function sendQuestion() {
    if (!selected || !question.trim()) return;
    setBusy('chat'); setError('');
    try {
      const result = await api<{ answer: string; messages: Message[] }>('/api/assistant/incidents/' + selected + '/message', {
        method: 'POST', body: JSON.stringify({ text: question.trim() }),
      });
      setMessages(result.messages); setQuestion('');
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  async function inspectAdjustment() {
    if (!detail) return;
    setBusy('preview'); setError(''); setNotice(''); setPreview(null); setConfirmed(false);
    try {
      const result = await api<Preview>('/api/assistant/incidents/' + detail.id + '/adjustment/preview', {
        method: 'POST',
        body: JSON.stringify({ instruction, max_tokens: limit === '' ? null : Number(limit) }),
      });
      setPreview(result);
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  async function authorize() {
    if (!detail || !preview || !confirmed) return;
    setBusy('authorize'); setError('');
    try {
      const result = await api<{ adjustment_id: string }>('/api/assistant/incidents/' + detail.id + '/adjustment/authorize', {
        method: 'POST', body: JSON.stringify({ approved: true, approval_token: preview.approval.approval_token }),
      });
      setNotice('Ajuste ' + result.adjustment_id + ' autorizado e iniciado. O RAW original permanece intacto.');
      setPreview(null); setConfirmed(false);
      setDetail(await api<Detail>('/api/criteria/incidents/' + detail.id));
    } catch (reason) { setPreview(null); setConfirmed(false); setError(String(reason)); }
    finally { setBusy(''); }
  }

  async function decision(state: 'acknowledge' | 'escalate') {
    if (!detail) return;
    const note = state === 'acknowledge' ? 'Ocorrência revisada no Lab Assistant.' : 'Requer revisão do proprietário.';
    setBusy('decision'); setError('');
    try {
      setDetail(await api<Detail>('/api/criteria/incidents/' + detail.id + '/' + state, {
        method: 'POST', body: JSON.stringify({ note }),
      }));
      setIssues(current => current.map(item => item.id === detail.id
        ? { ...item, status: state === 'acknowledge' ? 'acknowledged' : 'escalated' } : item));
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  return <section className="lab-assistant-view">
    <div className="section-heading"><div><span className="eyebrow">Norvald Lab Assistant</span>
      <h2>Critérios, incidentes e recuperação</h2>
      <p>Converse sobre uma ocorrência verificada. Ajustes dependem de uma prévia e da sua autorização explícita.</p>
    </div><Bot size={28} /></div>
    {error ? <p role="alert" className="error-banner">{error}</p> : null}
    {notice ? <p role="status" className="assistant-notice"><CheckCircle2 size={16} />{notice}</p> : null}
    <div className="assistant-model form-card">
      <div><strong>Modelo operador</strong><small>Separado dos modelos participantes. Enviar uma pergunta consome sua API.</small></div>
      <label>Provider<select value={settings.kind} onChange={event => setSettings(current => ({ ...current, kind: event.target.value }))}>
        <option value="">Escolha o provider</option>
        {connections?.connections.map(c => <option key={c.kind} value={c.kind}>{c.kind} {c.has_key || c.kind === 'ollama' ? '' : '(sem chave)'}</option>)}
      </select></label>
      <label>Modelo<input value={settings.model} maxLength={200} placeholder="ID do modelo" onChange={event => setSettings(current => ({ ...current, model: event.target.value }))} /></label>
      <label>Máx. tokens<input type="number" min={256} max={8000} value={settings.max_output_tokens} onChange={event => setSettings(current => ({ ...current, max_output_tokens: Number(event.target.value) }))} /></label>
      <button className="button secondary" disabled={!!busy || !settings.model.trim() || !settings.kind} onClick={() => { void saveModel(); }}>Salvar operador</button>
    </div>
    <div className="assistant-columns">
      <aside className="assistant-issues">
        <div className="row-heading"><h3>Critérios não atendidos</h3><button className="icon-button" disabled={!!busy || !selectedExperiment} onClick={() => { void resync(); }} aria-label="Verificar critérios do experimento selecionado"><RefreshCw size={16} /></button></div>
        <p className="muted">O botão verifica o experimento selecionado na Bancada. A lista também inclui ocorrências anteriores.</p>
        {issues.length ? issues.map(issue => <button key={issue.id} className={'assistant-issue ' + (selected === issue.id ? 'selected' : '')} onClick={() => setSelected(issue.id)}>
          <span className="assistant-issue-head"><AlertCircle size={15} /><strong>{issue.criterion_id}</strong></span>
          <small>{issue.experiment_id} · {issue.participant_id || 'Experimento'} · {issue.run_id || '—'}</small>
          <span>{issue.validator_code} · {issue.status}</span>
        </button>) : <p className="muted">Nenhuma ocorrência registrada. Verifique os critérios de um experimento fechado.</p>}
      </aside>
      <div className="assistant-work">
        {!detail ? <div className="form-card"><p>Selecione um incidente para abrir a conversa e o plano de recuperação.</p></div> : <>
          <article className="form-card assistant-diagnostic">
            <div className="row-heading"><div><span className="eyebrow">{detail.experiment_id} · {detail.run_id || 'Conjunto'}</span><h3>{detail.criterion_id}</h3></div><span className="badge">{detail.status}</span></div>
            <p><strong>Diagnóstico:</strong> {detail.message}</p><p><strong>Código do validador:</strong> {detail.validator_code}</p>
            <p><strong>Encaminhamento:</strong> {explanation[detail.recovery.action] ?? detail.recovery.reason}</p>
            <p className="muted">{detail.recovery.original_still_unmet ? 'A observação original continua sem satisfazer este critério.' : 'A conferência atual não afirma uma falha original persistente.'}</p>
            <div className="assistant-actions">
              <button className="button secondary" onClick={() => onOpenExperiment(detail.experiment_id)}>Abrir experimento</button>
              <button className="button secondary" disabled={!!busy} onClick={() => { void decision('acknowledge'); }}>Registrar ciência</button>
              <button className="button secondary" disabled={!!busy} onClick={() => { void decision('escalate'); }}>Escalar</button>
            </div>
          </article>
          <article className="form-card assistant-chat">
            <div className="row-heading"><div><h3><MessageCircle size={16} /> Conversa sobre o critério</h3><small>Respostas do modelo operador são interpretações; as validações vêm do Lab.</small></div></div>
            <div className="assistant-messages" aria-live="polite">
              {messages.length ? messages.map(m => <div key={m.seq} className={'assistant-message ' + (m.role === 'assistant' ? 'reply' : 'question')}>
                <small>{m.role === 'assistant' ? 'Lab Assistant · ' + m.model : 'Você'}</small><p>{m.content}</p>
              </div>) : <p className="muted">Pergunte por que o critério não foi atendido, o que o validador aceitou ou quais correções são permitidas.</p>}
            </div>
            <label htmlFor="assistant-question">Sua pergunta<textarea id="assistant-question" rows={3} maxLength={4000} value={question} placeholder="Por que esta contribuição foi recusada?" onChange={event => setQuestion(event.target.value)} /></label>
            <button className="button" disabled={!!busy || !question.trim() || !settings.configured || !connections?.live_enabled} onClick={() => { void sendQuestion(); }}><Send size={15} />{busy === 'chat' ? 'Consultando…' : 'Enviar ao Assistant'}</button>
            {!connections?.live_enabled ? <small>Habilite chamadas reais em Configurações para conversar com um modelo.</small> : !settings.configured ? <small>Configure e salve um modelo operador acima.</small> : null}
          </article>
          <article className="form-card assistant-recovery">
            <div className="row-heading"><div><h3><ClipboardCheck size={16} /> Plano de recuperação</h3><small>Ajustes são chamados fora da coleta original e não corrigem seu RAW.</small></div></div>
            <p>{detail.recovery.reason}</p>
            {detail.recovery.revalidations.length ? <div className="assistant-attempts">{detail.recovery.revalidations.map(item => <p key={item.adjustment_id}><strong>{item.adjustment_id}</strong> · {item.status} · {item.criterion_status} {item.integrity_verified && item.source_link_verified ? '· íntegro e vinculado' : '· sem confirmação integral'}</p>)}</div> : null}
            {detail.recovery.allowed && detail.recovery.proposed_payload ? <>
              <label>Orientação para o ajuste<textarea rows={5} maxLength={20000} value={instruction} onChange={event => { setInstruction(event.target.value); setPreview(null); setConfirmed(false); }} /></label>
              <label>Máximo de tokens (opcional)<input type="number" min={1} max={200000} value={limit} onChange={event => { setLimit(event.target.value); setPreview(null); setConfirmed(false); }} placeholder="Manter limite original" /></label>
              <button className="button secondary" disabled={!!busy || !instruction.trim()} onClick={() => { void inspectAdjustment(); }}><ClipboardCheck size={15} />Examinar pedido antes de autorizar</button>
              {preview ? <div className="assistant-preview">
                <h4>Prévia da chamada real</h4>
                <p><strong>Diagnóstico:</strong> {preview.preview.diagnostic.code} · {preview.preview.diagnostic.message}</p>
                <details><summary>Instruções completas que serão enviadas</summary><pre>{preview.preview.request.instructions}</pre></details>
                <details><summary>Pergunta que será enviada</summary><pre>{preview.preview.request.user_message}</pre></details>
                <p className="muted">Autorização válida até {new Date(preview.approval.expires_at).toLocaleString('pt-BR')}. Uma chamada adicional poderá consumir tokens.</p>
                <label className="assistant-confirm"><input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} />Autorizo esta chamada paga de ajuste independente, preservando o RAW original.</label>
                <button className="button" disabled={!confirmed || !!busy} onClick={() => { void authorize(); }}><ShieldCheck size={15} />{busy === 'authorize' ? 'Autorizando…' : 'Autorizar e executar ajuste'}</button>
              </div> : null}
            </> : <p className="muted">Não há chamada automática disponível para este critério.</p>}
            <details><summary>Histórico de auditoria ({detail.history.length})</summary><pre>{JSON.stringify(detail.history, null, 2)}</pre></details>
          </article>
        </>}
      </div>
    </div>
  </section>;
}
