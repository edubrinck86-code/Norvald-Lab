import { useCallback, useEffect, useState } from 'react';
import { BarChart3, Bot, ListChecks, Play, RefreshCw, Send } from 'lucide-react';
import { api, type ExperimentItem, type Spec } from '../api';

type ChatMessage = { seq: number; role: string; content: string; model: string };
type Plan = {
  id: string; action: string; status: string; experiment_id: string;
  incident_id: string; payload: { spec?: Spec; instruction?: string; observation_id?: string };
  created_at: string;
};
type Routine = {
  id: string; active: number; interval_seconds: number;
  next_due: string; spec: Spec;
};
type RecoveryItem = {
  experiment_id: string; observation_id: string; incident_id: string;
  plan_id: string; state: string; last_error: string;
};
type Comparison = {
  left_experiment_id: string; right_experiment_id: string;
  left: { responses: number; usable: number; fully_valid: number };
  right: { responses: number; usable: number; fully_valid: number };
  differences: { responses: number; usable: number; fully_valid: number };
  comparability: { structurally_aligned: boolean; shared_observation_pairs: number;
    participants_and_models_match: boolean; same_task: boolean; same_documents: boolean };
  limitations: string[];
};

export function AssistantWorkspace({ canChat, stopped, onStarted }: {
  canChat: boolean; stopped: boolean; onStarted(id: string): void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [plans, setPlans] = useState<Plan[]>([]);
  const [routines, setRoutines] = useState<Routine[]>([]);
  const [recovery, setRecovery] = useState<RecoveryItem[]>([]);
  const [autoRecovery, setAutoRecovery] = useState(false);
  const [experiments, setExperiments] = useState<ExperimentItem[]>([]);
  const [left, setLeft] = useState('');
  const [right, setRight] = useState('');
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [history, setHistory] = useState<Record<string, unknown>[]>([]);
  const [activeHistory, setActiveHistory] = useState('');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const refresh = useCallback(async () => {
    const [conversation, pending, scheduled, recoveries, existing] = await Promise.all([
      api<{ messages: ChatMessage[] }>('/api/assistant/conversation'),
      api<Plan[]>('/api/assistant/plans'),
      api<Routine[]>('/api/assistant/routines'),
      api<{ settings: { auto_recovery: boolean }; queue: RecoveryItem[] }>('/api/assistant/automation/recovery'),
      api<ExperimentItem[]>('/api/experiments'),
    ]);
    setMessages(conversation.messages);
    setPlans(pending);
    setRoutines(scheduled);
    setRecovery(recoveries.queue);
    setAutoRecovery(recoveries.settings.auto_recovery);
    const complete = existing.filter(item => item.status === 'complete' && !item.deleted);
    setExperiments(complete);
    setLeft(current => current || complete[0]?.experiment_id || '');
    setRight(current => current || complete[1]?.experiment_id || '');
  }, []);

  useEffect(() => { void refresh().catch(reason => setError(String(reason))); }, [refresh]);

  async function speak() {
    if (!question.trim() || !canChat || stopped) return;
    setBusy('chat'); setError('');
    try {
      const reply = await api<{ messages: ChatMessage[] }>('/api/assistant/chat', {
        method: 'POST', body: JSON.stringify({ text: question }),
      });
      setQuestion('');
      setMessages(reply.messages);
      await refresh();
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  async function execute(plan: Plan) {
    if (stopped || plan.status !== 'planned') return;
    setBusy(plan.id); setError(''); setNotice('');
    try {
      const result = await api<{ status: string; result: { experiment_id?: string; adjustment_id?: string } | null }>(
        '/api/assistant/plans/' + encodeURIComponent(plan.id) + '/execute',
        { method: 'POST', body: '{}' });
      setNotice('Execução do plano ' + plan.id + ': ' + result.status);
      if (result.result?.experiment_id && plan.action === 'lab.experiment.start') {
        onStarted(result.result.experiment_id);
      }
      await refresh();
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  async function cycle() {
    setBusy('monitor'); setError(''); setNotice('');
    try {
      const result = await api<{ recovery_planned: string[]; recovery_executed: { status: string }[];
        occurrence: { status: string } | null; errors: { error: string }[] }>(
        '/api/assistant/automation/tick', { method: 'POST', body: '{}' });
      setNotice('Ciclo concluído: ' + result.recovery_planned.length
        + ' novos planos de recuperação; ' + result.recovery_executed.length + ' recuperações executadas.'
        + (result.occurrence ? ' Rotina: ' + result.occurrence.status + '.' : '')
        + (result.errors.length ? ' Ocorrências com erro: ' + result.errors.length + '.' : ''));
      await refresh();
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  async function toggleRecovery() {
    setBusy('recovery'); setError('');
    try {
      const result = await api<{ auto_recovery: boolean }>('/api/assistant/automation/recovery/settings', {
        method: 'PUT', body: JSON.stringify({ auto_recovery: !autoRecovery }),
      });
      setAutoRecovery(result.auto_recovery);
      setNotice(result.auto_recovery
        ? 'Recuperação automática habilitada para planos não destrutivos; novos ajustes poderão chamar providers.'
        : 'Recuperação automática pausada. Planos persistidos permanecem consultáveis.');
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  async function changeRoutine(routine: Routine) {
    setBusy(routine.id); setError('');
    try {
      await api('/api/assistant/routines/' + routine.id + '/state', {
        method: 'POST', body: JSON.stringify({ active: !routine.active }),
      });
      await refresh();
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  async function readHistory(routine: Routine) {
    setBusy('history'); setError('');
    try {
      const result = await api<Record<string, unknown>[]>(
        '/api/assistant/routines/' + routine.id + '/history');
      setActiveHistory(routine.id);
      setHistory(result);
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  async function compare() {
    if (!left || !right) return;
    setBusy('compare'); setError(''); setComparison(null);
    try {
      const result = await api<Comparison>(
        '/api/assistant/compare?left=' + encodeURIComponent(left)
        + '&right=' + encodeURIComponent(right));
      setComparison(result);
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(''); }
  }

  return <div className="assistant-workspace">
    {error ? <p className="error-banner" role="alert">{error}</p> : null}
    {notice ? <p role="status" className="assistant-notice">{notice}</p> : null}
    <article className="form-card assistant-chat">
      <div className="row-heading"><div><h3><Bot size={17} /> Converse com o Lab Assistant</h3>
        <small>Pode consultar o laboratório e criar planos não destrutivos; nenhum plano é executado na mesma chamada.</small>
      </div></div>
      <div className="assistant-messages" aria-live="polite">
        {messages.length ? messages.map(m => <div key={m.seq} className={'assistant-message ' +
          (m.role === 'assistant' ? 'reply' : 'question')}>
          <small>{m.role === 'assistant' ? 'Lab Assistant · ' + m.model : 'Você'}</small>
          <p>{m.content}</p>
        </div>) : <p className="muted">Descreva um experimento, peça um planejamento, consulte resultados ou explique um critério.</p>}
      </div>
      <label>Mensagem para o Assistant<textarea rows={4} value={question}
        placeholder="Planeje um experimento B1 com os participantes e o corpus que eu indicar…"
        onChange={event => setQuestion(event.target.value)} /></label>
      <button className="button" disabled={!canChat || stopped || !!busy || !question.trim()}
        onClick={() => { void speak(); }}><Send size={15} />{busy === 'chat' ? 'Consultando…' : 'Enviar mensagem'}</button>
      {!canChat ? <small>Configure o modelo operador e habilite chamadas reais para conversar.</small> : null}
    </article>
    <article className="form-card">
      <div className="row-heading"><div><h3><ListChecks size={17} /> Planos disponíveis</h3>
        <small>Planejamento persistido antes da execução. Nenhuma aprovação individual é exigida para operações não destrutivas.</small>
      </div><button className="button secondary" disabled={!!busy} onClick={() => { void refresh(); }}>
        <RefreshCw size={15} />Atualizar</button></div>
      {plans.length ? plans.map(plan => <div key={plan.id} className="assistant-plan-row">
        <div><strong>{plan.action}</strong><small>{plan.experiment_id} · {plan.id} · {plan.status}</small>
          {plan.payload.spec ? <p>{plan.payload.spec.task.objective} · {plan.payload.spec.condition.exposure}
            · {plan.payload.spec.participants.map(p => p.model).join(', ')}</p>
            : <p>Ajuste separado da observação {plan.payload.observation_id || '—'}</p>}
        </div>
        <button className="button secondary" disabled={!!busy || stopped || plan.status !== 'planned'}
          onClick={() => { void execute(plan); }}><Play size={15} />Executar plano</button>
      </div>) : <p className="muted">Nenhum plano registrado.</p>}
    </article>
    <article className="form-card">
      <div className="row-heading"><div><h3><ListChecks size={17} /> Acompanhamento e recuperação</h3>
        <small>O observador verifica fechamentos sem alterar o RAW. Recuperações são registradas antes de começar.</small>
      </div><button className="button secondary" disabled={!!busy} onClick={() => { void cycle(); }}>
        <RefreshCw size={15} />Verificar agora</button></div>
      <label className="assistant-confirm">
        <input type="checkbox" checked={autoRecovery} disabled={!!busy}
          onChange={() => { void toggleRecovery(); }} />
        Executar automaticamente recuperações não destrutivas previamente planejadas
      </label>
      <p className="muted">Desativado por padrão. Se habilitado, ajustes podem consumir APIs dos participantes;
        cada ajuste permanece distinto da evidência original.</p>
      {recovery.length ? <div className="assistant-attempts">
        {recovery.map(item => <p key={item.experiment_id + item.observation_id}>
          <strong>{item.experiment_id}</strong> · {item.observation_id} · {item.state}
          · plano {item.plan_id} {item.last_error ? '· ' + item.last_error : ''}</p>)}
      </div> : <p className="muted">Nenhuma recuperação automática planejada.</p>}
    </article>
    <article className="form-card">
      <div className="row-heading"><div><h3><RefreshCw size={17} /> Rotinas recorrentes</h3>
        <small>Agende a repetição de um plano na seção de planejamento acima. Cada rodada recebe um ID independente.</small>
      </div></div>
      {routines.length ? routines.map(routine => <div key={routine.id} className="assistant-plan-row">
        <div><strong>{routine.spec.task.objective}</strong>
          <small>{routine.id} · a cada {routine.interval_seconds}s · próxima: {new Date(routine.next_due).toLocaleString('pt-BR')}</small>
        </div>
        <div className="assistant-actions">
          <button className="button secondary" disabled={!!busy}
            onClick={() => { void readHistory(routine); }}>Histórico</button>
          <button className="button secondary" disabled={!!busy}
            onClick={() => { void changeRoutine(routine); }}>{routine.active ? 'Pausar' : 'Ativar'}</button>
        </div>
      </div>) : <p className="muted">Nenhuma rotina agendada.</p>}
      {activeHistory ? <details open><summary>Ocorrências da rotina {activeHistory}</summary>
        <pre>{JSON.stringify(history, null, 2)}</pre></details> : null}
    </article>
    <article className="form-card">
      <div className="row-heading"><div><h3><BarChart3 size={17} /> Comparação científica estruturada</h3>
        <small>Somente experimentos íntegros e concluídos. Métricas descritivas, sem inferência causal automática.</small>
      </div></div>
      <div className="assistant-compare-controls">
        <label>Primeiro experimento<select value={left} onChange={event => setLeft(event.target.value)}>
          <option value="">Selecione</option>{experiments.map(item =>
            <option key={item.experiment_id} value={item.experiment_id}>{item.experiment_id}</option>)}
        </select></label>
        <label>Segundo experimento<select value={right} onChange={event => setRight(event.target.value)}>
          <option value="">Selecione</option>{experiments.map(item =>
            <option key={item.experiment_id} value={item.experiment_id}>{item.experiment_id}</option>)}
        </select></label>
        <button className="button secondary" disabled={!!busy || !left || !right || left === right}
          onClick={() => { void compare(); }}>Comparar</button>
      </div>
      {comparison ? <div className="assistant-preview">
        <h4>{comparison.comparability.structurally_aligned
          ? 'Pareamento estrutural compatível' : 'Diferenças estruturais encontradas'}</h4>
        <p>Observações pareadas: {comparison.comparability.shared_observation_pairs}</p>
        <div className="assistant-compare-grid">
          <p><strong>{comparison.left_experiment_id}</strong>
            <span>{comparison.left.responses} respostas · {comparison.left.usable} utilizáveis
              · {comparison.left.fully_valid} integralmente válidas</span></p>
          <p><strong>{comparison.right_experiment_id}</strong>
            <span>{comparison.right.responses} respostas · {comparison.right.usable} utilizáveis
              · {comparison.right.fully_valid} integralmente válidas</span></p>
        </div>
        <p>Diferença de contribuições totalmente válidas: {comparison.differences.fully_valid}</p>
        {comparison.limitations.map((text, index) => <small key={index}>{text}</small>)}
        <details><summary>Relatório JSON e pares</summary><pre>{JSON.stringify(comparison, null, 2)}</pre></details>
      </div> : null}
    </article>
  </div>;
}
