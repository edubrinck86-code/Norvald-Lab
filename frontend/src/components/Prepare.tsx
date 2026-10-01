import { useEffect, useState } from 'react';
import { FilePlus2, Play, Plus, Trash2, Upload, Eye, ChevronDown } from 'lucide-react';
import { api, type Spec, type PreparedRequest, type LabSettings, type CatalogModel, conditions } from '../api';
import { liveProviders, providerChoices, selectProvider } from '../lib/providers';
import { ModelPicker, capabilityLabel } from './ModelPicker';
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

export function Prepare({ liveEnabled, initialSpec, onStarted, onSettings }: { onSettings(): void; liveEnabled: boolean; initialSpec?: Spec; onStarted(id: string): void }) {
  const [connections, setConnections] = useState<LabSettings['connections']>([]);
  const [loadingConnections, setLoadingConnections] = useState(true);
  const [picking, setPicking] = useState<string | null>(null);
  const [modelInfo, setModelInfo] = useState<Record<string, CatalogModel>>({});
  useEffect(() => { const controller = new AbortController(); api<LabSettings>('/api/settings', { signal: controller.signal }).then(value => setConnections(value.connections)).catch(reason => { if (!controller.signal.aborted) setError(String(reason)); }).finally(() => { if (!controller.signal.aborted) setLoadingConnections(false); }); return () => controller.abort(); }, []);
  function providerConfig(kind: string) { const c = connections.find(c => c.kind === kind); return { kind, credential_env: c?.credential_env ?? '', ...(c?.base_url ? { base_url: c.base_url } : {}) }; }
  const [spec, setSpec] = useState<Spec | null>(initialSpec ?? null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState<{ spec: Spec; requests: PreparedRequest[] } | null>(null);
  const [requestIndex, setRequestIndex] = useState(0);
  useEffect(() => {
    if (initialSpec) { setSpec(initialSpec); return; }
    api<Spec>('/api/experiment-template').then(value => setSpec({
      ...value, participants: value.participants.map(p => ({ ...p, reasoning_effort: 'off', sampling: {} })),
      budget: { max_concurrency: 3, max_concurrency_per_provider: 2, timeout_seconds: 300, max_logical_executions: value.participants.length },
    })).catch(reason => setError(String(reason)));
  }, [initialSpec]);
  const [configured, setConfigured] = useState(false);
  useEffect(() => { if (spec && !loadingConnections && !initialSpec && !configured) { const providers = liveProviders(connections); setSpec({ ...spec, providers, participants: spec.participants.map(p => ({ ...p, provider: Object.keys(providers)[0] })) }); setConfigured(true); } }, [spec, loadingConnections, initialSpec, configured, connections]);
  function change(patch: Partial<Spec>) { setSpec(current => current ? { ...current, ...patch } : current); setPreview(null); }
  async function inspect() {
    if (!spec) return;
    if (spec.condition.tools === 'corpus' && spec.participants.some(p => modelInfo[p.id]?.id === p.model && modelInfo[p.id]?.tools === false)) { setError('Um dos modelos selecionados declara não suportar tools. Troque o modelo ou desative as ferramentas.'); return; }
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
  const choices = providerChoices(spec.providers, connections);
  function chooseProvider(participantId: string, value: string) {
    if (!spec || derived) return;
    const next = selectProvider(spec, participantId, value, connections);
    if (next === spec) return;
    setModelInfo(current => { const copy = { ...current }; delete copy[participantId]; return copy; });
    change(next); setPicking(participantId);
  }
  return <div className="prepare-view">
    <div className="section-heading"><div><span className="eyebrow">Antes de observar</span><h2>Prepare seu experimento</h2><p>Confira os participantes e o material que cada um receberá.</p></div></div>
    {error ? <div role="alert" className="error-banner">{error}</div> : null}
    <div className="form-card">
      <div className="form-grid"><label>Nome do registro<input value={spec.experiment_id} onChange={event => change({ experiment_id: event.target.value })} /></label><div className="execution-mode"><span className="field-label">Execução</span><span className="badge">Modelos reais</span></div></div>
      {!liveEnabled ? <button className="text-button" onClick={onSettings}>Configurar chaves e habilitar modelos reais</button> : null}
      <label>Pergunta / objetivo<textarea value={spec.task.objective} disabled={derived} onChange={event => change({ task: { ...spec.task, objective: event.target.value } })} rows={3} /></label>
      <label>Orientações comuns aos participantes<textarea value={spec.task.instructions} disabled={derived} onChange={event => change({ task: { ...spec.task, instructions: event.target.value } })} rows={2} /></label>
      <div className="condition-description"><span className="condition-dot" /><div><strong>{conditions[spec.condition.exposure].title}</strong><p>{conditions[spec.condition.exposure].description}</p>{derived ? <small>Origem: {spec.condition.prior_experiment}. Os parâmetros pareados estão preservados.</small> : null}</div></div>
    </div>
    <div className="form-card"><div className="row-heading"><h3>Participantes</h3><button className="text-button" disabled={derived} onClick={() => {
      const index = spec.participants.length + 1;
      change({ participants: [...spec.participants, { id: 'analista-' + crypto.randomUUID().slice(0, 8), name: 'Analista ' + index, role: 'Analista', provider: Object.keys(spec.providers)[0], model: '', reasoning_effort: 'off', sampling: {} }], budget: { ...spec.budget, max_logical_executions: index * spec.repetitions } });
    }}><Plus size={15} />Adicionar</button></div>
      {spec.participants.map((p, index) => <div className="participant-form" key={p.id}>
        <span className={'participant-avatar tone-' + index % 4}>{index + 1}</span>
        <label>Nome<input value={p.name} disabled={derived} onChange={event => change({ participants: spec.participants.map((item, i) => i === index ? { ...item, name: event.target.value } : item) })} /></label>
        <label className="participant-provider">Provedor<select aria-label={'Provedor · ' + p.name} value={p.provider} disabled={derived || loadingConnections} onChange={event => chooseProvider(p.id, event.target.value)}>{choices.map(option => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label>
        <div className="participant-model"><span className="field-label">Modelo</span>{spec.mode === 'live' ? <><button className="button secondary model-select" aria-label="Selecionar modelo · filtros" disabled={derived || loadingConnections} onClick={() => setPicking(p.id)}><span>{p.model || 'Escolher modelo'}</span><ChevronDown size={15} /></button><small>Catálogo de {spec.providers[p.provider]?.kind} · preço, tools e reasoning</small><details className="manual-model"><summary>Informar ID manualmente</summary><input aria-label={'Modelo · ' + p.name} value={p.model} disabled={derived} placeholder="ID exato no provedor" onChange={event => { setModelInfo(current => { const copy = { ...current }; delete copy[p.id]; return copy; }); change({ participants: spec.participants.map((item, i) => i === index ? { ...item, model: event.target.value, reasoning_effort: 'off' } : item) }); }} /></details></> : <input aria-label={'Modelo · ' + p.name} value={p.model} disabled />}{modelInfo[p.id]?.id === p.model ? <small>Tools: {capabilityLabel(modelInfo[p.id].tools)} · Reasoning: {capabilityLabel(modelInfo[p.id].reasoning)}</small> : null}</div>
        <label>Reasoning<select aria-label="Reasoning" value={p.reasoning_effort} disabled={derived || modelInfo[p.id]?.id === p.model && modelInfo[p.id]?.reasoning === false} onChange={event => change({ participants: spec.participants.map((item, i) => i === index ? { ...item, reasoning_effort: event.target.value } : item) })}>{['off', 'low', 'medium', 'high', ...(!['off', 'low', 'medium', 'high'].includes(p.reasoning_effort) ? [p.reasoning_effort] : [])].map(value => <option key={value} value={value}>{value === 'off' ? 'Padrão / sem solicitação' : value}</option>)}</select></label>
        <button className="icon-button" disabled={derived || spec.participants.length < 2} aria-label={'Remover ' + p.name} onClick={() => change({ participants: spec.participants.filter((_, i) => i !== index) })}><Trash2 size={16} /></button>
        <details className="participant-options"><summary>Papel e amostragem</summary><div className="form-grid"><label>Papel<input value={p.role} disabled={derived} onChange={event => change({ participants: spec.participants.map((item, i) => i === index ? { ...item, role: event.target.value } : item) })} /></label>{(['temperature', 'top_p', 'max_tokens'] as const).map(key => <label key={key}>{key}<input type="number" min="0" step={key === 'max_tokens' ? 1 : 0.1} value={p.sampling[key] ?? ''} disabled={derived} placeholder="Padrão do provedor" onChange={event => change({ participants: spec.participants.map((item, i) => i === index ? { ...item, sampling: { ...item.sampling, [key]: event.target.value === '' ? undefined : Number(event.target.value) } } : item) })} /></label>)}</div></details>
      </div>)}
    </div>
    {spec.mode === 'live' ? <details className="form-card provider-advanced"><summary>Ajustes avançados das conexões</summary><div className="row-heading"><h3>Conexões do experimento</h3><button className="text-button" disabled={derived} onClick={() => change({ providers: { ...spec.providers, ['provider-' + crypto.randomUUID().slice(0, 6)]: providerConfig('openrouter') } })}><Plus size={15} />Adicionar</button></div><p className="muted">Escolha o provedor em cada participante. Aqui você pode ajustar referências de credencial ou endereços próprios, se precisar. As chaves salvas em Configurações são usadas automaticamente.</p>{Object.entries(spec.providers).map(([name, provider]) => <div className="form-grid provider-form" key={name}><label>Provedor · {name}<select value={provider.kind} disabled={derived} onChange={event => { setModelInfo({}); change({ providers: { ...spec.providers, [name]: providerConfig(event.target.value) }, participants: spec.participants.map(p => p.provider === name ? { ...p, model: '', reasoning_effort: 'off' } : p) }); }}>{connections.map(c => c.kind).map(kind => <option key={kind}>{kind}</option>)}</select></label><label>Variável da credencial<input value={provider.credential_env ?? ''} disabled={derived} placeholder="Alternativa: variável existente" onChange={event => change({ providers: { ...spec.providers, [name]: { ...provider, credential_env: event.target.value } } })} /></label><label>Endereço da API (opcional)<input value={provider.base_url ?? ''} disabled={derived} placeholder="https://…" onChange={event => change({ providers: { ...spec.providers, [name]: { ...provider, base_url: event.target.value || undefined } } })} /></label></div>)}</details> : null}
    <div className="form-card"><div className="row-heading"><h3>Documentos do experimento</h3><button className="text-button" disabled={derived} onClick={() => change({ documents: [...spec.documents, { id: 'doc-' + crypto.randomUUID().slice(0, 8), title: 'Novo documento', text: '', source: '' }] })}><FilePlus2 size={16} />Adicionar</button></div>
      {spec.documents.map((doc, index) => <div className="document-form" key={doc.id}><div className="form-grid"><label>Título<input value={doc.title} disabled={derived} onChange={event => change({ documents: spec.documents.map((item, i) => i === index ? { ...item, title: event.target.value } : item) })} /></label><label>Fonte<input value={doc.source} disabled={derived} onChange={event => change({ documents: spec.documents.map((item, i) => i === index ? { ...item, source: event.target.value } : item) })} /></label></div><label>Conteúdo em Markdown<textarea rows={4} value={doc.text} disabled={derived} onChange={event => change({ documents: spec.documents.map((item, i) => i === index ? { ...item, text: event.target.value } : item) })} /></label><div className="row-heading"><label className="text-button file-button"><Upload size={14} />Importar .md / .txt<input type="file" accept=".md,.txt" disabled={derived} onChange={async event => { const file = event.target.files?.[0]; if (file) { const text = await file.text(); change({ documents: spec.documents.map((item, i) => i === index ? { ...item, text } : item) }); } }} /></label><button className="text-button" disabled={derived} onClick={() => change({ documents: spec.documents.filter((_, i) => i !== index) })}>Remover documento</button></div></div>)}
    </div>
    <div className="form-card"><h3>Repetições e limites</h3><div className="form-grid"><label>Repetições<input type="number" min="1" value={spec.repetitions} disabled={derived} onChange={event => change({ repetitions: Number(event.target.value), budget: { ...spec.budget, max_logical_executions: Number(event.target.value) * spec.participants.length } })} /></label><label>Execuções simultâneas<input type="number" min="1" value={spec.budget.max_concurrency} onChange={event => change({ budget: { ...spec.budget, max_concurrency: Number(event.target.value) } })} /></label><label>Simultâneas por provedor<input type="number" min="1" value={spec.budget.max_concurrency_per_provider} onChange={event => change({ budget: { ...spec.budget, max_concurrency_per_provider: Number(event.target.value) } })} /></label><label>Tempo máximo por execução (s)<input type="number" min="1" value={spec.budget.timeout_seconds} onChange={event => change({ budget: { ...spec.budget, timeout_seconds: Number(event.target.value) } })} /></label><label>Ferramentas<select value={spec.condition.tools} disabled={derived} onChange={event => change({ condition: { ...spec.condition, tools: event.target.value as 'off' | 'corpus' } })}><option value="off">Desativadas</option><option value="corpus">Consultar corpus local</option></select></label><label>Orçamento de execuções<input type="number" min="1" value={spec.budget.max_logical_executions} onChange={event => change({ budget: { ...spec.budget, max_logical_executions: Number(event.target.value) } })} /></label></div></div>
    <div className="prepare-footer"><label className="button secondary file-button"><Upload size={15} />Importar configuração<input type="file" accept=".json" onChange={event => { void importFile(event.target.files?.[0]); }} /></label><span>{spec.participants.length * spec.repetitions} execuções planejadas</span><button className="button" disabled={busy} onClick={inspect}><Eye size={16} />Conferir o que será enviado</button></div>
    {picking && spec.participants.some(p => p.id === picking) ? <ModelPicker provider={spec.providers[spec.participants.find(p => p.id === picking)!.provider]} onClose={() => setPicking(null)} onSelect={model => { setModelInfo(current => ({ ...current, [picking]: model })); change({ participants: spec.participants.map(p => p.id === picking ? { ...p, model: model.id, reasoning_effort: 'off' } : p) }); setPicking(null); }} /> : null}
    {preview ? <Modal title="Confira antes de iniciar" onClose={() => setPreview(null)}>
      <div className="preview-contract"><div className="preview-top"><label>Participante / repetição<select value={requestIndex} onChange={event => setRequestIndex(Number(event.target.value))}>{preview.requests.map((request, index) => <option key={index} value={index}>{request.agent_id} · repetição {request.context.metadata.repetition_index}</option>)}</select></label><span className="badge">{'Chamadas reais às APIs'}</span></div><ContextView request={preview.requests[requestIndex]} /></div>
      <footer className="modal-footer"><p>{'Ao iniciar, serão feitas chamadas aos provedores configurados.'}</p><button className="button" disabled={busy || !liveEnabled} onClick={start}><Play size={15} />Iniciar experimento</button></footer>
    </Modal> : null}
  </div>;
}
