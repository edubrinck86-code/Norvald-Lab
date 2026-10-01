import { useEffect, useState } from 'react';
import { CheckSquare, ChevronRight, Pencil, RotateCcw, Trash2 } from 'lucide-react';
import { api, conditions, statusLabel, type ExperimentItem, type Spec } from '../api';
import { Modal } from './Modal';

export function Experiments({ items, onChoose, onRefresh, onEdit, onDeleted, onNew }: {
  items: ExperimentItem[]; onChoose(id: string): void; onRefresh(): Promise<void>;
  onEdit(spec: Spec): void; onDeleted(ids: string[]): void; onNew(): void;
}) {
  const [search, setSearch] = useState('');
  const [selectionMode, setSelectionMode] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const [confirm, setConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [showDeleted, setShowDeleted] = useState(false);
  const [excluded, setExcluded] = useState<ExperimentItem[]>([]);
  async function refreshExcluded() { setExcluded((await api<ExperimentItem[]>('/api/experiments?include_deleted=true')).filter(item => item.deleted)); }
  useEffect(() => { if (showDeleted) void refreshExcluded().catch(reason => setError(String(reason))); }, [showDeleted]);
  const rows = [...items, ...(showDeleted ? excluded : [])].filter(item => (item.task + item.experiment_id).toLowerCase().includes(search.toLowerCase())).reverse();
  const active = rows.filter(item => selected.includes(item.experiment_id) && !item.deleted);
  async function edit() {
    if (active.length !== 1) return;
    setBusy(true); setError('');
    try { onEdit(await api<Spec>('/api/experiments/' + active[0].experiment_id + '/editable-copy')); }
    catch (reason) { setError(String(reason)); } finally { setBusy(false); }
  }
  async function remove() {
    setBusy(true); setError('');
    const removed: string[] = [];
    try {
      for (const item of active) { await api('/api/experiments/' + item.experiment_id, { method: 'DELETE' }); removed.push(item.experiment_id); }
      setConfirm(false);
    } catch (reason) { setError(String(reason)); }
    finally {
      onDeleted(removed); setSelected(current => current.filter(id => !removed.includes(id)));
      await onRefresh(); if (showDeleted) await refreshExcluded().catch(reason => setError(String(reason)));
      setBusy(false);
    }
  }
  async function restore(id: string) {
    setBusy(true); setError('');
    try { await api('/api/experiments/' + id + '/restore', { method: 'POST' }); setExcluded(current => current.filter(item => item.experiment_id !== id)); await onRefresh(); await refreshExcluded(); }
    catch (reason) { setError(String(reason)); } finally { setBusy(false); }
  }
  return <section className="experiments-view">
    <div className="row-heading"><h2>Experimentos</h2><input className="experiment-search" aria-label="Buscar experimentos" placeholder="Buscar pergunta ou registro…" value={search} onChange={event => setSearch(event.target.value)} /></div>
    <div className="experiment-actions"><button className="button secondary" aria-pressed={selectionMode} onClick={() => { setSelectionMode(value => !value); setSelected([]); }}><CheckSquare size={15} />{selectionMode ? 'Concluir seleção' : 'Selecionar'}</button>{selectionMode ? <><span className="muted">{active.length} selecionado(s)</span><button className="button secondary" disabled={busy || active.length !== 1} onClick={() => { void edit(); }}><Pencil size={15} />Editar</button><button className="button secondary" disabled={busy || !active.length || active.some(item => item.status === 'running')} onClick={() => setConfirm(true)}><Trash2 size={15} />Excluir</button></> : null}<label className="filter-chip"><input type="checkbox" checked={showDeleted} onChange={event => setShowDeleted(event.target.checked)} />Mostrar excluídos</label></div>
    {selectionMode ? <p className="muted">Selecione um registro para editar a configuração em uma nova coleta. O experimento original é preservado.</p> : null}
    {error ? <div role="alert" className="error-banner">{error}</div> : null}
    {rows.map(item => <div className={'experiment-entry ' + (item.deleted ? 'excluded' : '')} key={item.experiment_id}>{selectionMode && !item.deleted ? <input type="checkbox" aria-label={'Selecionar ' + item.experiment_id} checked={selected.includes(item.experiment_id)} onChange={event => setSelected(current => event.target.checked ? [...current, item.experiment_id] : current.filter(id => id !== item.experiment_id))} /> : null}<button className="experiment-row" onClick={() => onChoose(item.experiment_id)}><span className="condition-dot" /><div><strong>{conditions[item.exposure].title}</strong><p>{item.task}</p><small>{item.experiment_id}</small></div><span className="badge">{item.deleted ? 'Excluído da lista' : statusLabel(item.status)}</span><ChevronRight size={18} /></button>{item.deleted ? <button className="text-button" disabled={busy} onClick={() => { void restore(item.experiment_id); }}><RotateCcw size={15} />Restaurar</button> : null}</div>)}
    {!rows.length ? <div className="empty-state"><p>{search ? 'Nenhum experimento encontrado.' : 'Sua lista de experimentos está vazia.'}</p><button className="button" onClick={onNew}>Novo experimento</button></div> : null}
    {confirm ? <Modal title="Excluir experimentos" onClose={() => { if (!busy) setConfirm(false); }}><div className="modal-scroll"><p>Retirar {active.length} experimento(s) da lista?</p><ul>{active.map(item => <li key={item.experiment_id}>{item.experiment_id}</li>)}</ul><p>Os registros originais serão preservados para manter as referências das Notes, do Notebook e das comparações. Você poderá restaurar em “Mostrar excluídos”.</p>{error ? <p role="alert" className="danger">{error}</p> : null}</div><footer className="modal-footer"><button className="button secondary" disabled={busy} onClick={() => setConfirm(false)}>Cancelar</button><button className="button" disabled={busy} onClick={() => { void remove(); }}><Trash2 size={15} />{busy ? 'Excluindo…' : 'Confirmar exclusão'}</button></footer></Modal> : null}
  </section>;
}
