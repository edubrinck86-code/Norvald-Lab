import { useState } from 'react';
import { ClipboardList, Play, RefreshCw } from 'lucide-react';
import { api, type Spec } from '../api';

type PreparedPlan = {
  plan: { id: string; experiment_id: string; status: string };
  planning: {
    objective: string; mode: string; condition: Spec['condition'];
    participants: { id: string; provider: string; model: string }[];
    repetitions: number; prepared_requests: number; fingerprint: string;
  };
  requires_approval: boolean;
};

export function AssistantExperimentPlanner({ selectedExperiment, stopped, onStarted }: {
  selectedExperiment: string; stopped: boolean; onStarted(experimentId: string): void;
}) {
  const [draft, setDraft] = useState('');
  const [plan, setPlan] = useState<PreparedPlan | null>(null);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [started, setStarted] = useState(false);

  async function loadTemplate() {
    setBusy('draft'); setError(''); setNotice(''); setPlan(null); setStarted(false);
    try {
      const path = selectedExperiment
        ? '/api/experiments/' + encodeURIComponent(selectedExperiment) + '/editable-copy'
        : '/api/experiment-template';
      const spec = await api<Spec>(path);
      setDraft(JSON.stringify(spec, null, 2));
    } catch (err) { setError(String(err)); }
    finally { setBusy(''); }
  }

  async function prepare() {
    setBusy('prepare'); setError(''); setNotice(''); setPlan(null); setStarted(false);
    try {
      const spec = JSON.parse(draft) as Spec;
      const value = await api<PreparedPlan>('/api/assistant/plans/experiment', {
        method: 'POST', body: JSON.stringify({ spec }),
      });
      setPlan(value);
    } catch (err) { setError(String(err)); }
    finally { setBusy(''); }
  }

  async function execute() {
    if (!plan || stopped || started) return;
    setBusy('execute'); setError('');
    try {
      const value = await api<{ status: string; result: { experiment_id: string } | null }>(
        '/api/assistant/plans/' + plan.plan.id + '/execute',
        { method: 'POST', body: '{}' },
      );
      if (value.status === 'accepted' && value.result?.experiment_id) {
        setStarted(true); setNotice('Coleta aceita. Acompanhe o experimento na Bancada.');
        onStarted(value.result.experiment_id);
      } else {
        setNotice('Estado do plano: ' + value.status);
      }
    } catch (err) { setError(String(err)); }
    finally { setBusy(''); }
  }

  return <article className="form-card assistant-study-planner">
    <div className="row-heading">
      <div><h3><ClipboardList size={17} /> Planejar novo experimento</h3>
        <small>Confira o Spec e todas as chamadas preparadas antes de iniciar uma coleta.</small></div>
      <button className="button secondary" disabled={!!busy} onClick={() => { void loadTemplate(); }}>
        <RefreshCw size={15} />{selectedExperiment ? 'Copiar experimento selecionado' : 'Novo rascunho'}
      </button>
    </div>
    {error ? <p role="alert" className="error-banner">{error}</p> : null}
    {notice ? <p role="status" className="muted">{notice}</p> : null}
    {draft ? <>
      <label>Spec experimental (JSON)<textarea rows={7} spellCheck={false} value={draft}
        onChange={event => { setDraft(event.target.value); setPlan(null); setStarted(false); }} /></label>
      <button className="button secondary" disabled={!!busy} onClick={() => { void prepare(); }}>
        <ClipboardList size={15} />{busy === 'prepare' ? 'Verificando…' : 'Gerar e mostrar plano'}
      </button>
    </> : <p className="muted">Abra um rascunho, preencha os campos e prepare um plano verificável. Esta etapa não chama modelos.</p>}
    {plan ? <section className="assistant-preview">
      <h4>Plano apresentado — ainda não executado</h4>
      <p><strong>Objetivo:</strong> {plan.planning.objective}</p>
      <p><strong>Experimento:</strong> {plan.plan.experiment_id} · {plan.planning.mode}</p>
      <p><strong>Condição:</strong> {plan.planning.condition.exposure} · ferramentas {plan.planning.condition.tools}</p>
      <p><strong>Repetições:</strong> {plan.planning.repetitions} · <strong>Chamadas preparadas:</strong> {plan.planning.prepared_requests}</p>
      <div className="assistant-attempts">{plan.planning.participants.map(p =>
        <p key={p.id}><strong>{p.id}</strong> · {p.provider} / {p.model}</p>)}</div>
      <small>Fingerprint: {plan.planning.fingerprint}</small>
      <p className="muted">Execução normal não exige aprovação adicional. A integridade e as regras do Runner são preservadas.</p>
      <button className="button" disabled={!!busy || stopped || started} onClick={() => { void execute(); }}>
        <Play size={15}/>{started ? 'Execução solicitada' : busy === 'execute' ? 'Iniciando…' : 'Executar plano apresentado'}
      </button>
      {stopped ? <small>Parada emergencial ativa: novas execuções bloqueadas.</small> : null}
    </section> : null}
  </article>;
}
