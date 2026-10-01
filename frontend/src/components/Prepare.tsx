import { useEffect, useState } from 'react';
import { FilePlus2, Play, Plus, Trash2, Upload, Eye, FlaskConical } from 'lucide-react';
import { api, type Spec, type PreparedRequest, conditions } from '../api';
import { Modal } from './Modal';
import { NorvaldMarkdown } from '../ui/markdown/NorvaldMarkdown';

export function ContextView({ request }: { request: PreparedRequest }) {
  const [raw, setRaw] = useState(false);
  let context: { items?: { id: string; type: string; content: string; author_id?: string }[]; relations?: unknown[] } = {};
  try { context = JSON.parse(request.context.working_context); } catch { /* mostrar original abaixo */ }
  return <div className="context-view">
    <p className="muted">Conteúdo preparado na fronteira do motor de execução. O provedor adapta esse contrato para sua API.</p>
    <div className="context-summary"><span>{request.agent_id}</span><span>Repetição {request.context.metadata.repetition_index}</span><span>{request.context.metadata.source_observation_ids.length} respostas de origem</span></div>
    <h3>Pergunta</h3><NorvaldMarkdown content={request.user_message} />
    <h3>Instruções do participante</h3><NorvaldMarkdown content={request.instructions} />
    <h3>Contexto congelado</h3>
    {context.items?.map(item => <div className="context-item" key={item.id}><span className="eyebrow">{item.type} · {item.author_id || 'Material inicial'} · {item.id}</span><NorvaldMarkdown content={item.content} /></div>)}
    <details><summary>Relações do contexto</summary><pre>{JSON.stringify(context.relations ?? [], null, 2)}</pre></details>
    <details><summary>Instruções compartilhadas e corpus integral</summary><pre>{request.shared_instructions}</pre></details>
    <button className="text-button" onClick={() => setRaw(value => !value)}>{raw ? 'Ocultar contrato original' : 'Ver contrato original completo'}</button>
    {raw ? <pre>{JSON.stringify(request, null, 2)}</pre> : null}
  </div>;
}

export function Prepare({ liveEnabled, initialSpec, onStarted, onDemo }: { liveEnabled: boolean; initialSpec?: Spec; onStarted(id: string): void; onDemo(): void }) {
  const [spec, setSpec] = useState<Spec | null>(initialSpec ?? null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<{ spec: Spec; requests: PreparedRequest[] } | null>(null);
  const [requestIndex, setRequestIndex] = useState(0);
  useEffect(() => {
    if (initialSpec) { setSpec(initialSpec); return; }
    api<Spec>('/api/demo-template').then(value => setSpec({
      ...value, participants: value.participants.map(p => ({ ...p, reasoning_effort: 'off', sampling: {} })),
      budget: { max_concurrency: 3, max_concurrency_per_provider: 2, timeout_seconds: 300, max_logical_executions: 3 },
    })).catch(reason => setError(String(reason)));
  }, [initialSpec]);
  function change(patch: Partial<Spec>) { setSpec(current => current ? { ...current, ...patch } : current); setPreview(null); }
  async function inspect() {
    if (!spec) return;
    setBusy(true); setError('');
    try { setPreview(await api('/api/prepare', { method: 'POST', body: JSON.stringify(spec) })); setRequestIndex(0); }
    catch (reason) { setError(String(reason)); }
    finally { setBusy(false); }
  }
  async function start() {
    if (!preview) return;
    setBusy(true); setError('');
    try {
      const result = await api<{ experiment_id: string }>('/api/experiments', { method: 'POST', body: JSON.stringify(preview.spec) });
      setPreview(null); onStarted(result.experiment_id);
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(false); }
  }
  async function importFile(file?: File) {
    if (!file) return;
    try {
      const value = JSON.parse(await file.text());
      const prepared = await api<{ spec: Spec }>('/api/prepare', { method: 'POST', body: JSON.stringify(value) });
      setSpec(prepared.spec); setPreview(null); setError('');
    } catch (reason) { setError(String(reason)); }
  }
  if (!spec) return <div className="empty-state">{error || 'Preparando a bancada…'}</div>;
  const derived = spec.condition.exposure !== 'blind';
  return <div className="prepare-view">
    <div className="section-heading"><div><span className="eyebrow">Antes de observar</span><h2>Prepare seu experimento</h2><p>Confira os participantes e o material que cada um receberá.</p></div><button className="button secondary" onClick={onDemo}><FlaskConical size={16} />Experimentar demonstração</button></div>
    {error ? <div role="alert" className="error-banner">{error}</div> : null}
    <div className="form-card">
      <div className="form-grid"><label>Nome do registro<input value={spec.experiment_id} onChange={event => change({ experiment_id: event.target.value })} /></label><label>Modo<select value={spec.mode} disabled={derived} onChange={event => {
        const mode = event.target.value as Spec['mode'];
        change({ mode, providers: mode === 'demo' ? { simulador: { kind: 'demo' } } : { provider: { kind: 'openai', credential_env: 'OPENAI_API_KEY' } }, participants: spec.participants.map(p => ({ ...p, provider: mode === 'demo' ? 'simulador' : 'provider', model: mode === 'demo' ? 'demo-v1' : '', reasoning_effort: 'off' })) });
      }}><option value="demo">Demonstração · sem API</option><option value="live" disabled={!liveEnabled}>Modelos reais{!liveEnabled ? ' · habilite serve --live' : ''}</option></select></label></div>
      <label>Pergunta / objetivo<textarea value={spec.task.objective} disabled={derived} onChange={event => change({ task: { ...spec.task, objective: event.target.value } })} rows={3} /></label>
      <label>Orientações comuns aos participantes<textarea value={spec.task.instructions} disabled={derived} onChange={event => change({ task: { ...spec.task, instructions: event.target.value } })} rows={2} /></label>
      <div className="condition-description"><span className="condition-dot" /><div><strong>{conditions[spec.condition.exposure].title}</strong><p>{conditions[spec.condition.exposure].description}</p>{derived ? <small>Origem: {spec.condition.prior_experiment}. Os parâmetros pareados estão preservados.</small> : null}</div></div>
    </div>
    <div className="form-card"><div className="row-heading"><h3>Participantes</h3><button className="text-button" disabled={derived} onClick={() => {
      const index = spec.participants.length + 1;
      change({ participants: [...spec.participants, { id: 'analista-' + crypto.randomUUID().slice(0, 8), name: 'Analista ' + index, role: 'Analista', provider: Object.keys(spec.providers)[0], model: spec.mode === 'demo' ? 'demo-v1' : '', reasoning_effort: 'off', sampling: {} }], budget: { ...spec.budget, max_logical_executions: index * spec.repetitions } });
    }}><Plus size={15} />Adicionar</button></div>
      {spec.participants.map((p, index) => <div className="participant-form" key={p.id}>
        <span className={'participant-avatar tone-' + index % 4}>{index + 1}</span>
        <label>Nome<input value={p.name} disabled={derived} onChange={event => change({ participants: spec.participants.map((item, i) => i === index ? { ...item, name: event.target.value } : item) })} /></label>
        <label>Modelo<input value={p.model} disabled={derived || spec.mode === 'demo'} placeholder="ID do modelo no provedor" onChange={event => change({ participants: spec.participants.map((item, i) => i === index ? { ...item, model: event.target.value } : item) })} /></label>
        <label>Provedor<select value={p.provider} disabled={derived || spec.mode === 'demo'} onChange={event => change({ participants: spec.participants.map((item, i) => i === index ? { ...item, provider: event.target.value } : item) })}>{Object.keys(spec.providers).map(name => <option key={name}>{name}</option>)}</select></label>
        <label>Reasoning<select value={p.reasoning_effort} disabled={derived} onChange={event => change({ participants: spec.participants.map((item, i) => i === index ? { ...item, reasoning_effort: event.target.value } : item) })}>{['off', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max'].map(value => <option key={value}>{value}</option>)}</select></label>
        <button className="icon-button" disabled={derived || spec.participants.length < 2} aria-label={'Remover ' + p.name} onClick={() => change({ participants: spec.participants.filter((_, i) => i !== index) })}><Trash2 size={16} /></button>
        <details className="participant-options"><summary>Papel e amostragem</summary><div className="form-grid"><label>Papel<input value={p.role} disabled={derived} onChange={event => change({ participants: spec.participants.map((item, i) => i === index ? { ...item, role: event.target.value } : item) })} /></label>{(['temperature', 'top_p', 'max_tokens'] as const).map(key => <label key={key}>{key}<input type="number" min="0" step={key === 'max_tokens' ? 1 : 0.1} value={p.sampling[key] ?? ''} disabled={derived} placeholder="Padrão do provedor" onChange={event => change({ participants: spec.participants.map((item, i) => i === index ? { ...item, sampling: { ...item.sampling, [key]: event.target.value === '' ? undefined : Number(event.target.value) } } : item) })} /></label>)}</div></details>
      </div>)}
    </div>
    {spec.mode === 'live' ? <div className="form-card"><div className="row-heading"><h3>Provedores</h3><button className="text-button" disabled={derived} onClick={() => change({ providers: { ...spec.providers, ['provider-' + crypto.randomUUID().slice(0, 6)]: { kind: 'openai', credential_env: '' } } })}><Plus size={15} />Adicionar</button></div><p className="muted">Informe o nome da variável de ambiente que contém a chave. A chave permanece no seu computador.</p>{Object.entries(spec.providers).map(([name, provider]) => <div className="form-grid provider-form" key={name}><label>Provedor · {name}<select value={provider.kind} disabled={derived} onChange={event => change({ providers: { ...spec.providers, [name]: { ...provider, kind: event.target.value } } })}>{['openai', 'openrouter', 'anthropic', 'gemini', 'ollama'].map(kind => <option key={kind}>{kind}</option>)}</select></label><label>Variável da credencial<input value={provider.credential_env ?? ''} disabled={derived} placeholder="EX.: OPENROUTER_API_KEY" onChange={event => change({ providers: { ...spec.providers, [name]: { ...provider, credential_env: event.target.value } } })} /></label><label>Endereço da API (opcional)<input value={provider.base_url ?? ''} disabled={derived} placeholder="https://…" onChange={event => change({ providers: { ...spec.providers, [name]: { ...provider, base_url: event.target.value || undefined } } })} /></label></div>)}</div> : null}
    <div className="form-card"><div className="row-heading"><h3>Documentos do experimento</h3><button className="text-button" disabled={derived} onClick={() => change({ documents: [...spec.documents, { id: 'doc-' + crypto.randomUUID().slice(0, 8), title: 'Novo documento', text: '', source: '' }] })}><FilePlus2 size={16} />Adicionar</button></div>
      {spec.documents.map((doc, index) => <div className="document-form" key={doc.id}><div className="form-grid"><label>Título<input value={doc.title} disabled={derived} onChange={event => change({ documents: spec.documents.map((item, i) => i === index ? { ...item, title: event.target.value } : item) })} /></label><label>Fonte<input value={doc.source} disabled={derived} onChange={event => change({ documents: spec.documents.map((item, i) => i === index ? { ...item, source: event.target.value } : item) })} /></label></div><label>Conteúdo em Markdown<textarea rows={4} value={doc.text} disabled={derived} onChange={event => change({ documents: spec.documents.map((item, i) => i === index ? { ...item, text: event.target.value } : item) })} /></label><div className="row-heading"><label className="text-button file-button"><Upload size={14} />Importar .md / .txt<input type="file" accept=".md,.txt" disabled={derived} onChange={async event => { const file = event.target.files?.[0]; if (file) { const text = await file.text(); change({ documents: spec.documents.map((item, i) => i === index ? { ...item, text } : item) }); } }} /></label><button className="text-button" disabled={derived} onClick={() => change({ documents: spec.documents.filter((_, i) => i !== index) })}>Remover documento</button></div></div>)}
    </div>
    <div className="form-card"><h3>Repetições e limites</h3><div className="form-grid"><label>Repetições<input type="number" min="1" value={spec.repetitions} disabled={derived} onChange={event => change({ repetitions: Number(event.target.value), budget: { ...spec.budget, max_logical_executions: Number(event.target.value) * spec.participants.length } })} /></label><label>Execuções simultâneas<input type="number" min="1" value={spec.budget.max_concurrency} onChange={event => change({ budget: { ...spec.budget, max_concurrency: Number(event.target.value) } })} /></label><label>Simultâneas por provedor<input type="number" min="1" value={spec.budget.max_concurrency_per_provider} onChange={event => change({ budget: { ...spec.budget, max_concurrency_per_provider: Number(event.target.value) } })} /></label><label>Tempo máximo por execução (s)<input type="number" min="1" value={spec.budget.timeout_seconds} onChange={event => change({ budget: { ...spec.budget, timeout_seconds: Number(event.target.value) } })} /></label><label>Ferramentas<select value={spec.condition.tools} disabled={derived || spec.mode === 'demo'} onChange={event => change({ condition: { ...spec.condition, tools: event.target.value as 'off' | 'corpus' } })}><option value="off">Desativadas</option><option value="corpus">Consultar corpus local</option></select></label><label>Orçamento de execuções<input type="number" min="1" value={spec.budget.max_logical_executions} onChange={event => change({ budget: { ...spec.budget, max_logical_executions: Number(event.target.value) } })} /></label></div></div>
    <div className="prepare-footer"><label className="button secondary file-button"><Upload size={15} />Importar configuração<input type="file" accept=".json" onChange={event => { void importFile(event.target.files?.[0]); }} /></label><span>{spec.participants.length * spec.repetitions} execuções planejadas</span><button className="button" disabled={busy} onClick={inspect}><Eye size={16} />Conferir o que será enviado</button></div>
    {preview ? <Modal title="Confira antes de iniciar" onClose={() => setPreview(null)}>
      <div className="preview-contract"><div className="preview-top"><label>Participante / repetição<select value={requestIndex} onChange={event => setRequestIndex(Number(event.target.value))}>{preview.requests.map((request, index) => <option key={index} value={index}>{request.agent_id} · repetição {request.context.metadata.repetition_index}</option>)}</select></label><span className="badge">{preview.spec.mode === 'demo' ? 'Sintético · sem API' : 'Chamadas reais às APIs'}</span></div><ContextView request={preview.requests[requestIndex]} /></div>
      <footer className="modal-footer"><p>{preview.spec.mode === 'demo' ? 'Demonstração sem valor empírico para a tese.' : 'Ao iniciar, serão feitas chamadas aos provedores configurados.'}</p><button className="button" disabled={busy} onClick={start}><Play size={15} />Iniciar experimento</button></footer>
    </Modal> : null}
  </div>;
}
