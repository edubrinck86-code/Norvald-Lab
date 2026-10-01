import { useEffect, useState } from 'react';
import { RefreshCw, Search } from 'lucide-react';
import { api, type Catalog, type CatalogModel, type Spec } from '../api';
import { Modal } from './Modal';

export function capabilityLabel(value: boolean | null) { return value === null ? 'Não declarado' : value ? 'Declarado' : 'Não suportado'; }
export function matchesCapability(value: boolean | null, filter: string) { return filter === 'all' || (filter === 'yes' ? value === true : filter === 'no' ? value === false : value === null); }
function matchesPrice(model: CatalogModel, filter: string) {
  if (filter === 'all') return true;
  if (filter === 'local') return model.local;
  if (filter === 'free') return model.free === true;
  if (filter === 'paid') return model.free === false;
  return model.free === null && !model.local;
}
export function ModelPicker({ provider, onSelect, onClose }: { provider: Spec['providers'][string]; onSelect(model: CatalogModel): void; onClose(): void }) {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [refresh, setRefresh] = useState(0);
  const [search, setSearch] = useState('');
  const [price, setPrice] = useState('all');
  const [tools, setTools] = useState('all');
  const [reasoning, setReasoning] = useState('all');
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setError('');
    api<Catalog>('/api/models', { method: 'POST', signal: controller.signal, body: JSON.stringify(provider) }).then(setCatalog).catch(reason => { if (!controller.signal.aborted) setError(String(reason)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [provider.kind, provider.credential_env, provider.base_url, refresh]);
  const models = (catalog?.models ?? []).filter(m => (m.name + ' ' + m.id).toLowerCase().includes(search.toLowerCase()) && matchesCapability(m.tools, tools) && matchesCapability(m.reasoning, reasoning) && matchesPrice(m, price));
  return <Modal title={'Selecionar modelo · ' + provider.kind} onClose={onClose} className="model-picker"><div className="model-filters"><label className="model-search"><Search size={16} /><input autoFocus aria-label="Buscar modelos" placeholder="Nome ou ID do modelo…" value={search} onChange={event => setSearch(event.target.value)} /></label><div className="form-grid"><label>Preço<select aria-label="Filtrar por preço" value={price} onChange={event => setPrice(event.target.value)}><option value="all">Todos</option><option value="free">Gratuito declarado</option><option value="paid">Com custo declarado</option><option value="unknown">Preço não declarado</option><option value="local">Local · Ollama</option></select></label>{([['tools', 'Tools', tools, setTools], ['reasoning', 'Reasoning', reasoning, setReasoning]] as const).map(([id, label, value, setter]) => <label key={id}>{label}<select aria-label={'Filtrar por ' + label} value={value} onChange={event => setter(event.target.value)}><option value="all">Todos</option><option value="yes">Suporte declarado</option><option value="no">Sem suporte declarado</option><option value="unknown">Não declarado</option></select></label>)}</div><p className="muted">Informações do catálogo do provedor. “Não declarado” significa que o catálogo não informou. Gratuito exige preço zero declarado; limites de uso ainda podem se aplicar.</p><div className="row-heading"><span>{loading ? 'Consultando catálogo…' : models.length + ' modelos'}</span><button className="text-button" disabled={loading} onClick={() => setRefresh(v => v + 1)}><RefreshCw size={14} />Atualizar catálogo</button></div>{error ? <p role="alert" className="danger">{error}</p> : null}</div><div className="model-list">{!loading && !error && !models.length ? <p className="empty-state">Nenhum modelo atende a estes filtros.</p> : null}{!loading && models.map(m => <button className="model-option" key={m.id} onClick={() => onSelect(m)}><div><strong>{m.name}</strong><code>{m.id}</code></div><span className="badge">{m.local ? 'Local' : m.free === true ? 'Gratuito' : m.free === false ? 'Com custo' : 'Preço não declarado'}</span><div className="model-capabilities"><span>Tools: {capabilityLabel(m.tools)}</span><span>Reasoning: {capabilityLabel(m.reasoning)}</span>{m.context_length ? <span>Contexto: {m.context_length.toLocaleString('pt-BR')}</span> : null}{m.dynamic_router ? <span>Roteador dinâmico · modelo subjacente variável</span> : null}</div></button>)}</div><footer className="modal-footer"><small>{catalog ? 'Catálogo consultado em ' + new Date(catalog.fetched_at).toLocaleString('pt-BR') : 'A consulta de catálogo não gera respostas de modelos.'}</small></footer></Modal>;
}
