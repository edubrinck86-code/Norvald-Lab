import { useEffect, useRef, useState } from 'react';
import { api, type Workbook, type CorpusCapture } from '../api';

// Persiste na App: navegar para a bancada não desmonta uma escrita pendente.
export function useWorkbooks() {
  const [books, setBooks] = useState<Workbook[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('Salvo');
  const drafts = useRef(new Map<string, Workbook>());
  const versions = useRef(new Map<string, number>());
  const dirty = useRef(new Set<string>());
  const queue = useRef(Promise.resolve());
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mounted = useRef(true);
  const selected = books.find(book => book.id === selectedId) ?? null;

  function accept(book: Workbook, fromServer = true) {
    drafts.current.set(book.id, book);
    if (fromServer) versions.current.set(book.id, book.revision);
    setBooks(current => current.some(b => b.id === book.id) ? current.map(b => b.id === book.id ? book : b) : [book, ...current]);
  }
  function flush() {
    if (timer.current) clearTimeout(timer.current);
    queue.current = queue.current.then(async () => {
      for (const id of [...dirty.current]) {
        const draft = drafts.current.get(id)!;
        try {
          const saved = await api<Workbook>('/api/workbooks/' + id, { method: 'PUT', body: JSON.stringify({ title: draft.title, blocks: draft.blocks, revision: versions.current.get(id) }) });
          versions.current.set(id, saved.revision);
          if (drafts.current.get(id) === draft) {
            dirty.current.delete(id);
            if (mounted.current) accept(saved);
          } else {
            // Uma resposta antiga não substitui texto digitado enquanto salvava.
            const newest = { ...drafts.current.get(id)!, revision: saved.revision, updated_at: saved.updated_at };
            drafts.current.set(id, newest);
            if (mounted.current) setBooks(current => current.map(b => b.id === id ? newest : b));
          }
        } catch (reason) {
          if (mounted.current) { setError(String(reason)); setStatus('Não salvo'); }
          return false;
        }
      }
      if (dirty.current.size) {
        if (mounted.current) setStatus('Salvando…');
        timer.current = setTimeout(() => { void flush(); }, 250);
        return false;
      }
      if (mounted.current) { setStatus('Salvo agora'); setError(''); }
      return true;
    }).then(() => {});
    return queue.current.then(() => dirty.current.size === 0);
  }
  useEffect(() => {
    mounted.current = true;
    let active = true;
    api<Workbook[]>('/api/workbooks').then(values => {
      if (!active) return;
      values.forEach(book => { drafts.current.set(book.id, book); versions.current.set(book.id, book.revision); });
      setBooks(values); setSelectedId(values[0]?.id ?? ''); setLoaded(true);
    }).catch(reason => { if (active) { setError(String(reason)); setLoaded(true); } });
    function leaving(event: BeforeUnloadEvent) {
      if (dirty.current.size) { event.preventDefault(); event.returnValue = ''; }
    }
    window.addEventListener('beforeunload', leaving);
    return () => { active = false; mounted.current = false; if (timer.current) clearTimeout(timer.current); void flush(); window.removeEventListener('beforeunload', leaving); };
  }, []);

  function update(book: Workbook) {
    accept(book, false); dirty.current.add(book.id); setStatus('Salvando…');
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => { void flush(); }, 600);
  }
  async function create() {
    if (!await flush()) return null;
    try {
      const book = await api<Workbook>('/api/workbooks', { method: 'POST', body: JSON.stringify({ title: 'Meu caderno', blocks: [] }) });
      accept(book); setSelectedId(book.id); return book;
    } catch (reason) { setError(String(reason)); return null; }
  }
  async function choose(id: string) { if (await flush()) setSelectedId(id); }
  async function captureNote(noteId: string) {
    if (!selected || !await flush()) return null;
    try {
      const book = await api<Workbook>('/api/workbooks/' + selected.id + '/capture-note', { method: 'POST', body: JSON.stringify({ note_id: noteId, revision: versions.current.get(selected.id) }) });
      accept(book); setStatus('Salvo agora'); return book.blocks.at(-1)!;
    } catch (reason) { setError(String(reason)); return null; }
  }
  async function captureCorpus(blockIds?: string[]) {
    if (!selected || !await flush()) return null;
    try {
      return await api<CorpusCapture>('/api/workbooks/' + selected.id + '/corpus', { method: 'POST', body: JSON.stringify({ revision: versions.current.get(selected.id), block_ids: blockIds }) });
    } catch (reason) { setError(String(reason)); return null; }
  }
  // A versão externa é aberta para consulta; não apaga o rascunho local.
  async function savedVersion() {
    if (!selected) return null;
    try { return await api<Workbook>('/api/workbooks/' + selected.id); }
    catch (reason) { setError(String(reason)); return null; }
  }
  async function keepLocal() {
    const saved = await savedVersion();
    if (!saved || !selected) return;
    versions.current.set(selected.id, saved.revision);
    dirty.current.add(selected.id); await flush();
  }
  return { books, selected, loaded, error, status, update, create, choose, flush, captureNote, captureCorpus, savedVersion, keepLocal };
}
