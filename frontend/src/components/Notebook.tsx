import { useEffect, useRef, useState } from 'react';
import { BookOpen, Check, Eye, Pencil, Plus, Search, Tag, Trash2, X, Link2, AlertCircle } from 'lucide-react';
import { api, type Note } from '../api';
import { Modal } from './Modal';
import { NorvaldMarkdown } from '../ui/markdown/NorvaldMarkdown';
import { MarkdownToolbar } from '../ui/MarkdownToolbar';
import { countWords } from '../lib/markdownText';

export function Notebook({ initialId, onClose, onOrigin, onSaved }: { initialId?: string; onClose(): void; onOrigin(note: Note): void; onSaved(note: Note): void }) {
  const [notes, setNotes] = useState<Note[]>([]);
  const [selected, setSelected] = useState(initialId ?? '');
  const [search, setSearch] = useState('');
  const [edit, setEdit] = useState(false);
  const [draft, setDraft] = useState<Note | null>(null);
  const [status, setStatus] = useState('Salvo');
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);
  // Escritas serializadas; trocar de nota ou fechar não perde a última edição.
  const pending = useRef(new Map<string, Note>());
  const latest = useRef(new Map<string, Note>());
  const queue = useRef(Promise.resolve());
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const selectedRef = useRef(selected);
  selectedRef.current = selected;
  const mounted = useRef(true);
  function flush() {
    if (timer.current) clearTimeout(timer.current);
    const changes = [...pending.current.values()];
    pending.current.clear();
    for (const note of changes) {
      queue.current = queue.current.then(async () => {
        try {
          const saved = await api<Note>('/api/notes/' + note.id, { method: 'PUT', body: JSON.stringify({ title: note.title, content: note.content }) });
          if (mounted.current) {
            setNotes(current => current.map(item => item.id === saved.id && item.content === note.content && item.title === note.title ? saved : item));
            onSaved(saved);
            if (latest.current.get(saved.id) === note) {
              latest.current.set(saved.id, saved);
              if (pending.current.get(saved.id) === note) pending.current.delete(saved.id);
              if (selectedRef.current === saved.id) setStatus('Salvo agora');
            }
          }
        } catch (reason) {
          if (latest.current.get(note.id) === note) {
            pending.current.set(note.id, note);
            if (mounted.current) { setStatus('Não salvo'); setError(String(reason)); }
          }
        }
      });
    }
    return queue.current;
  }
  useEffect(() => {
    mounted.current = true;
    api<Note[]>('/api/notes').then(items => {
      if (!mounted.current) return;
      setNotes(items);
      items.forEach(note => latest.current.set(note.id, note));
      const chosen = items.find(item => item.id === initialId) ?? items[0] ?? null;
      setSelected(chosen?.id ?? ''); setDraft(chosen);
    }).catch(reason => setError(String(reason)));
    return () => { mounted.current = false; void flush(); };
  }, []);
  function update(change: Partial<Note>) {
    if (!draft) return;
    const updated = { ...draft, ...change };
    setDraft(updated); setNotes(current => current.map(item => item.id === updated.id ? updated : item));
    latest.current.set(updated.id, updated);
    pending.current.set(updated.id, updated); setStatus('Salvando…');
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => { void flush(); }, 600);
  }
  async function close() {
    await flush();
    if (pending.current.size) return;
    onClose();
  }
  async function choose(note: Note) {
    await flush();
    if (pending.current.size) return;
    setSelected(note.id); setDraft(latest.current.get(note.id) ?? note); setEdit(false); setDeleting(false); setStatus('Salvo'); setError('');
  }
  async function create() {
    await flush();
    if (pending.current.size) return;
    try {
      const note = await api<Note>('/api/notes', { method: 'POST', body: JSON.stringify({ title: 'Sem título', content: '' }) });
      latest.current.set(note.id, note);
      setNotes(current => [note, ...current]); setSelected(note.id); setDraft(note); setEdit(true); setDeleting(false);
    } catch (reason) { setError(String(reason)); }
  }
  async function remove() {
    if (!draft) return;
    if (!deleting) { setDeleting(true); return; }
    await flush();
    if (pending.current.size) return;
    try {
      await api('/api/notes/' + draft.id, { method: 'DELETE' });
      const remaining = notes.filter(note => note.id !== draft.id);
      setNotes(remaining); setDraft(remaining[0] ?? null); setSelected(remaining[0]?.id ?? ''); setDeleting(false);
    } catch (reason) { setError(String(reason)); }
  }
  const tags = [...new Set(draft?.content.match(/(?:^|\s)#[\p{L}\p{N}_-]+/gu)?.map(value => value.trim()) ?? [])];
  return <Modal title="Notes" onClose={() => { void close(); }} className="notebook-modal">
    <div className="notebook-layout">
      <aside className="notebook-sidebar">
        <header><BookOpen size={19} /><div><h2>Notes</h2><p>Suas notas pessoais em Markdown.</p></div><button className="icon-button" onClick={create} aria-label="Criar nota"><Pencil size={17} /></button></header>
        <label className="search-field"><Search size={16} /><input aria-label="Buscar notas" placeholder="Buscar notas…" value={search} onChange={event => setSearch(event.target.value)} /></label>
        <nav aria-label="Notas">{notes.filter(note => (note.title + note.content).toLocaleLowerCase('pt-BR').includes(search.toLocaleLowerCase('pt-BR'))).map(note => <button key={note.id} className={'note-list-item ' + (note.id === selected ? 'selected' : '')} onClick={() => { void choose(note); }}><span>{note.title || 'Sem título'}</span><time>{new Date(note.updated_at).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</time></button>)}</nav>
        <footer><button className="icon-button" onClick={create} aria-label="Nova nota"><Plus size={18} /></button><button className="icon-button" onClick={() => titleRef.current?.focus()} disabled={!draft} aria-label="Renomear nota"><Pencil size={15} /></button><button className={'icon-button ' + (deleting ? 'danger' : '')} onClick={remove} disabled={!draft} aria-label={deleting ? 'Confirmar exclusão' : 'Excluir nota'} title={deleting ? 'Clique para confirmar a exclusão' : 'Excluir nota'}><Trash2 size={16} /></button>{deleting ? <button className="text-button" onClick={() => setDeleting(false)}>Cancelar</button> : null}</footer>
      </aside>
      <section className="notebook-editor">
        <header className="notebook-toolbar">
          <input ref={titleRef} aria-label="Título da nota" value={draft?.title ?? ''} placeholder="Sem título" disabled={!draft} maxLength={300} onChange={event => update({ title: event.target.value })} />
          <div className="notebook-actions">
            <span className={'save-status ' + (status === 'Não salvo' ? 'danger' : '')} role="status">{status.startsWith('Salvo') ? <Check size={12} /> : null}{status}</span>
            <button className={'icon-button ' + (edit ? 'selected' : '')} disabled={!draft} onClick={() => setEdit(current => !current)} aria-label={edit ? 'Ver preview' : 'Editar nota'} title={edit ? 'Ver preview' : 'Editar'}>{edit ? <Eye size={16} /> : <Pencil size={16} />}</button>
            <MarkdownToolbar markdown={draft?.content ?? ''} filename={draft?.title || 'nota'} showSyntaxHelp />
            <button className="icon-button" onClick={() => { void close(); }} aria-label="Fechar caderno"><X size={17} /></button>
          </div>
        </header>
        {error ? <div role="alert" className="error-banner"><AlertCircle size={16} />{error}<button onClick={() => { setError(''); void flush(); }}>Tentar salvar novamente</button></div> : null}
        {draft?.anchor ? <div className="note-origin"><Link2 size={14} /><span>{draft.anchor.excerpt ? 'Trecho fixado' : 'Momento marcado'} · {draft.anchor.experiment_id}</span><button onClick={async () => { await flush(); if (!pending.current.size) { onOrigin(draft); onClose(); } }}>Abrir origem</button></div> : null}
        <main className="notebook-content">
          {!draft ? <div className="empty-note"><BookOpen size={25} /><p>Nenhuma nota selecionada.</p><button className="button" onClick={create}>Criar a primeira nota</button></div> :
            edit ? <textarea autoFocus aria-label="Conteúdo da nota em Markdown" spellCheck={false} value={draft.content} onChange={event => update({ content: event.target.value })} placeholder="Escreva em Markdown…&#10;&#10;Use # para títulos, - [ ] para tarefas e [[documento]] para referências." /> :
            draft.content.trim() ? <div className="note-preview"><NorvaldMarkdown content={draft.content} /></div> :
            <button className="empty-note dashed" onClick={() => setEdit(true)}><Pencil size={24} /><span>Nota vazia — clique para começar a escrever</span></button>}
        </main>
        <div className="note-tags"><Tag size={14} />{tags.length ? tags.join('  ') : 'Sem tags no texto ainda.'}</div>
        <footer className="note-count"><span>Markdown</span><span>{countWords(draft?.content ?? '')} palavras · {(draft?.content.length ?? 0).toLocaleString('pt-BR')} caracteres</span></footer>
      </section>
    </div>
  </Modal>;
}
