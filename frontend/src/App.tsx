import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowUpRight, Bot, BookOpen, ChevronRight, FileText, FlaskConical, Layers, List, NotebookPen, Pin, Plus, RefreshCw, Settings2, X } from 'lucide-react';
import { api, ApiError, conditions, statusLabel, type Anchor, type CorpusCapture, type ExperimentItem, type Note, type PreparedRequest, type Snapshot, type Spec } from './api';
import { familyId, eventLabel } from './lib/observation';
import { Modal } from './components/Modal';
import { Notebook } from './components/Notebook';
import { Workbook, bookMarkdown } from './components/Workbook';
import { useWorkbooks } from './hooks/useWorkbooks';
import { Settings } from './components/Settings';
import { Observe } from './components/Observe';
import { FloatingAssistant } from './components/FloatingAssistant';
import { Compare } from './components/Compare';
import { Experiments } from './components/Experiments';
import { ContextView, Prepare } from './components/Prepare';
import { NorvaldMarkdown } from './ui/markdown/NorvaldMarkdown';
import { MarkdownToolbar } from './ui/MarkdownToolbar';
import { ResourceReferenceContext } from './ui/references/ResourceReferenceContext';
import type { ResourceReference } from './ui/references/resourceReference';

type View = 'prepare' | 'observe' | 'compare' | 'experiments' | 'records' | 'workbook' | 'settings' | 'assistant';
type Resource = { title: string; content: string; section?: string };

export default function App() {
  const workbooks = useWorkbooks();
  const [view, setView] = useState<View>('observe');
  const [items, setItems] = useState<ExperimentItem[]>([]);
  const [comparisonItems, setComparisonItems] = useState<ExperimentItem[]>([]);
  const [selected, setSelected] = useState('');
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [observationFailed, setObservationFailed] = useState(false);
  const [health, setHealth] = useState<{ live_enabled: boolean } | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [repetition, setRepetition] = useState(1);
  const [replay, setReplay] = useState<number | null>(null);
  const [notebook, setNotebook] = useState<{ id?: string } | null>(null);
  const [pinned, setPinned] = useState<Note | null>(null);
  const [context, setContext] = useState<PreparedRequest | null>(null);
  const [resource, setResource] = useState<Resource | null>(null);
  const [documents, setDocuments] = useState(false);
  const [initialSpec, setInitialSpec] = useState<Spec | undefined>();
  const [assistantAnchor, setAssistantAnchor] = useState<{ experiment_id: string; observation_id: string } | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [awaitingStarts, setAwaitingStarts] = useState(0);
  const [listPollingFailed, setListPollingFailed] = useState(false);
  const acceptedStarts = useRef(new Set<string>());
  const listRequest = useRef<Promise<void> | null>(null);
  const hasSelected = useRef(false);
  const originRequest = useRef<Anchor | null>(null);
  const assistantReturn = useRef<View>('observe');

  const refreshList = useCallback((): Promise<void> => {
    if (listRequest.current) return listRequest.current;
    const request = (async () => {
      try {
        const all = await api<ExperimentItem[]>('/api/experiments?include_deleted=true');
        // Um início aceito pode ainda não ter manifest, ou falhar antes de criá-lo.
        await Promise.all([...acceptedStarts.current].map(async id => {
          if (all.some(item => item.experiment_id === id)) { acceptedStarts.current.delete(id); return; }
          try {
            const state = await api<{ status: string; error?: string }>('/api/experiments/' + id);
            if (state.status !== 'running') {
              acceptedStarts.current.delete(id);
              if (state.error) setError(state.error);
            }
          } catch (reason) {
            if (reason instanceof ApiError && reason.status === 404) acceptedStarts.current.delete(id);
            throw reason;
          }
        }));
        setAwaitingStarts(acceptedStarts.current.size);
        const values = all.filter(item => !item.deleted);
        setItems(values); setComparisonItems(all); setListPollingFailed(false);
        if (!hasSelected.current && values.length) { setSelected(values.at(-1)!.experiment_id); hasSelected.current = true; }
      } catch (reason) { setError(String(reason)); setListPollingFailed(true); }
    })().finally(() => { listRequest.current = null; });
    listRequest.current = request;
    return request;
  }, []);
  useEffect(() => {
    api<{ live_enabled: boolean }>('/health').then(setHealth).catch(reason => setError(String(reason)));
    void refreshList();
    const resume = () => {
      if (document.visibilityState !== 'visible') return;
      void refreshList(); setObservationFailed(false); setRefresh(value => value + 1);
    };
    window.addEventListener('focus', resume);
    return () => window.removeEventListener('focus', resume);
  }, [refreshList]);
  const listActive = !listPollingFailed && (awaitingStarts > 0 || comparisonItems.some(item => item.status === 'running'));
  useEffect(() => {
    if (!listActive) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    async function read() {
      await refreshList();
      if (active) timer = setTimeout(() => { void read(); }, 2000);
    }
    timer = setTimeout(() => { void read(); }, 2000);
    return () => { active = false; clearTimeout(timer); };
  }, [listActive, refreshList]);
  const selectedItem = comparisonItems.find(item => item.experiment_id === selected);
  const pending = !observationFailed && (!snapshot || snapshot.experiment_id !== selected || snapshot.provisional && (snapshot.status === 'running' || selectedItem?.status === 'running'));
  useEffect(() => {
    if (!selected) return;
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const controller = new AbortController();
    async function read() {
      try {
        const value = await api<Snapshot>('/api/experiments/' + selected + '/observe', { signal: controller.signal });
        if (!active) return;
        setSnapshot(value); setError('');
        const origin = originRequest.current;
        if (origin?.experiment_id === selected) {
          if (origin.observation_id) {
            const record = value.records.find(row => row.observation_id === origin.observation_id);
            if (record) setRepetition(Number(record.run_id.slice(1)));
          }
          setReplay(origin.event_index ?? null); originRequest.current = null;
        }
      } catch (reason) {
        if (!active) return;
        // O POST pode retornar antes de o runner reservar e gravar o diretório.
        if (reason instanceof ApiError && reason.status === 404 && (selectedItem?.status === 'running' || acceptedStarts.current.has(selected))) return;
        setError(String(reason));
        setObservationFailed(true);
      } finally {
        if (active && pending) timer = setTimeout(() => { void read(); }, 900);
      }
    }
    void read();
    return () => { active = false; controller.abort(); clearTimeout(timer); };
  }, [selected, selectedItem?.status, pending, refresh]);

  function choose(id: string, nextView: View = 'observe') {
    hasSelected.current = true; setSelected(id); setView(nextView); setRepetition(1); setReplay(null); setSnapshot(null); setError(''); setObservationFailed(false); setAssistantAnchor(null);
  }
  function started(id: string) { acceptedStarts.current.add(id); setAwaitingStarts(acceptedStarts.current.size); setListPollingFailed(false); choose(id); void refreshList(); }
  async function pin(anchor: Anchor) {
    try {
      const content = anchor.excerpt ? '> ' + anchor.excerpt.replace(/\n/g, '\n> ') + '\n\n## Minha observação\n\n' : '## Momento marcado\n\n' + eventLabel(snapshot!.events[anchor.event_index!]) + '\n\n## Minha observação\n\n';
      const note = await api<Note>('/api/notes', { method: 'POST', body: JSON.stringify({ title: anchor.excerpt ? 'Observação de um trecho' : 'Observação de um momento', content, anchor }) });
      setPinned(note); setNotebook({ id: note.id });
    } catch (reason) { setError(String(reason)); }
  }
  async function derive(exposure: 'self' | 'exposed') {
    if (!snapshot) return;
    setBusy(true);
    try {
      const spec = await api<Spec>('/api/derive', { method: 'POST', body: JSON.stringify({ source_id: snapshot.experiment_id, experiment_id: 'experimento-' + crypto.randomUUID().slice(0, 12), exposure }) });
      setInitialSpec(spec); setView('prepare');
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(false); }
  }
  function origin(note: Note) {
    if (!note.anchor) return;
    originRequest.current = note.anchor;
    setPinned(note); choose(note.anchor.experiment_id);
  }
  async function openResource(reference: ResourceReference) {
    const clean = reference.id.replace(/^evidence-/, '');
    const docs = snapshot?.spec.documents ?? [];
    const doc = docs.find(item => [item.id, item.title, item.source, item.source.split('/').at(-1)].some(value => value?.toLowerCase() === clean.toLowerCase()));
    if (doc) { setResource({ title: doc.title, content: doc.text, section: reference.section }); return; }
    if (reference.source === 'notebook' || reference.source === 'auto') {
      const [bookId, blockId, part] = clean.replace(/^Notebook\//i, '').split('/');
      const book = workbooks.books.find(item => item.id === bookId || item.title.toLowerCase() === clean.toLowerCase());
      const block = book?.blocks.find(item => item.id === blockId) ?? workbooks.books.flatMap(item => item.blocks).find(item => item.id === clean || item.title && item.title.toLowerCase() === clean.toLowerCase());
      if (book && !blockId && !block) { setResource({ title: book.title, content: bookMarkdown(book), section: reference.section }); return; }
      if (block) {
        const source = part === 'source' ? block.source_note : block;
        if (source) { setResource({ title: source.title || 'Sem título', content: source.content, section: reference.section }); return; }
      }
    }
    if (reference.source === 'note' || reference.source === 'auto') {
      try {
        const notes = await api<Note[]>('/api/notes');
        const note = notes.find(item => item.id === reference.id || item.title.toLowerCase() === clean.toLowerCase());
        if (note) { setResource({ title: note.title, content: note.content, section: reference.section }); return; }
      } catch (reason) { setError(String(reason)); return; }
    }
    setResource({ title: 'Referência não encontrada', content: 'O item **' + reference.id.replace(/[<>\[\]*]/g, '') + '** não está no corpus deste experimento, nas anotações ou nos cadernos locais.\n\nAs referências são preservadas no Markdown original.' });
  }
  async function useCorpus(capture: CorpusCapture) {
    try {
      const spec = await api<Spec>('/api/experiment-template');
      setInitialSpec({ ...spec, documents: [capture.document] }); setView('prepare');
    } catch (reason) { setError(String(reason)); }
  }
  const resourceValue = { open: (reference: ResourceReference) => { void openResource(reference); } };
  const current = snapshot?.experiment_id === selected ? snapshot : null;
  const verified = current && current.integrity?.valid !== false && current.spec.participants?.length;
  const currentItem = selectedItem ?? (verified ? { experiment_id: selected, exposure: current.spec.condition.exposure, source_experiment_id: current.spec.condition.prior_experiment, synthetic: current.spec.mode === 'demo', task: current.spec.task.objective, status: current.status } : null);
  return <ResourceReferenceContext.Provider value={resourceValue}>
    <div className={'app-shell ' + (['workbook', 'settings', 'assistant'].includes(view) ? 'workbook-shell' : '')}>
      <aside className="app-sidebar"><a href="/" className="brand"><span className="brand-mark"><FlaskConical size={22} /></span><span>NORVALD <small>LAB</small></span></a>
        <nav aria-label="Navegação principal">{([
          ['observe', 'Bancada', FlaskConical], ['experiments', 'Experimentos', Layers], ['records', 'Registros', List], ['assistant', 'Lab Assistant', Bot], ['workbook', 'Notebook', BookOpen],
        ] as const).map(([id, label, Icon]) => <button key={id} aria-label={label} title={label} className={'nav-button ' + ((view === id || id === 'observe' && ['prepare', 'compare'].includes(view)) ? 'active' : '')} onClick={() => { if (id === 'assistant' && view !== 'assistant') assistantReturn.current = view; setView(id); if (id === 'experiments') void refreshList(); }}><Icon size={18} />{label}</button>)}<button className="nav-button" aria-label="Notes" title="Notes" onClick={() => setNotebook({})}><NotebookPen size={18} />Notes</button></nav>
        <div className="sidebar-bottom"><div className="local-label"><span />Ambiente local</div><button className={'nav-button ' + (view === 'settings' ? 'active' : '')} onClick={() => setView('settings')}><Settings2 size={18} />Configurações</button></div>
      </aside>
      <main className="app-main">
        <header className="app-header"><div><div className="title-line"><h1>{view === 'settings' ? 'Configurações' : view === 'assistant' ? 'Lab Assistant' : view === 'workbook' ? 'Notebook' : view === 'experiments' ? 'Seus experimentos' : view === 'records' ? 'Registros do experimento' : 'Bancada de observação'}</h1>{view === 'settings' ? <span className="badge">Conexões locais</span> : view === 'assistant' ? <span className="badge">Incidentes verificados</span> : view === 'workbook' ? <span className="badge">Seu espaço de escrita</span> : <span className="badge">{'Modelos reais'}</span>}</div><p>{view === 'settings' ? 'Suas APIs, seus modelos e seus limites.' : view === 'assistant' ? 'Critérios e recuperação sem alterar o registro original.' : view === 'workbook' ? 'Observe, reúna e desenvolva suas ideias.' : (selected || 'Prepare, acompanhe e compare.') + (current ? ' · ' + statusLabel(current.status) : '')}</p></div><div className="header-actions"><button className="icon-button" aria-label="Atualizar registros" onClick={() => { setObservationFailed(false); setRefresh(value => value + 1); void refreshList(); }}><RefreshCw size={17} /></button><button className="button secondary" onClick={() => { setInitialSpec(undefined); setView('prepare'); }}><Plus size={15} />Novo experimento</button></div></header>
        {error ? <div role="alert" className="error-banner">{error}<button className="icon-button" onClick={() => setError('')} aria-label="Dispensar aviso"><X size={15} /></button></div> : null}
        {['prepare', 'observe', 'compare'].includes(view) ? <nav className="stage-nav" aria-label="Etapas do experimento">{([['prepare', 'Preparar'], ['observe', 'Acompanhar'], ['compare', 'Comparar']] as const).map(([id, label], index) => <button key={id} className={view === id ? 'active' : ''} onClick={() => setView(id)}><span>{index + 1}</span>{label}</button>)}</nav> : null}
        <Workbook store={workbooks} active={view === 'workbook'} documents={current?.spec.documents ?? []} onResource={setResource} onOrigin={origin} onNotes={id => setNotebook({ id })} onCorpus={capture => { void useCorpus(capture); }} />
        {view === 'settings' ? <Settings onChanged={setHealth} /> : view === 'assistant' ? null : view === 'workbook' ? null : view === 'prepare' ? <Prepare onSettings={() => setView('settings')} liveEnabled={health?.live_enabled ?? false} initialSpec={initialSpec} onStarted={started} /> :
          view === 'experiments' ? <Experiments items={items} onChoose={choose} onRefresh={refreshList} onEdit={spec => { setInitialSpec(spec); setView('prepare'); }} onDeleted={ids => { if (ids.includes(selected)) { setSelected(''); setSnapshot(null); hasSelected.current = true; } }} onNew={() => { setInitialSpec(undefined); setView('prepare'); }} /> :
          !selected ? <Empty onNew={() => { setInitialSpec(undefined); setView('prepare'); }} /> :
          !current ? <div className="empty-state">{observationFailed ? <p>Não foi possível abrir esta coleta. Confira o aviso acima.</p> : <><span className="activity-dot" /><p>Carregando os registros…</p></>}</div> :
          !verified ? <div role="alert" className="error-banner">O experimento contém registros ausentes ou alterados. A leitura foi bloqueada para preservar a análise.<ul>{current.integrity?.issues.map(issue => <li key={issue}>{issue}</li>)}</ul></div> :
          view === 'records' ? <Records snapshot={current} onContext={setContext} onAsk={observationId => {
            assistantReturn.current = view;
            setAssistantAnchor({ experiment_id: selected, observation_id: observationId });
            setView('assistant');
          }} /> :
          view === 'compare' && currentItem ? <><div className="compare-intro"><span className="eyebrow">Comparação entre condições</span><h2>Observe as respostas na mesma base</h2><label>Repetição<select value={repetition} onChange={event => setRepetition(Number(event.target.value))}>{Array.from({ length: current.spec.repetitions }, (_, i) => <option key={i} value={i + 1}>{i + 1}</option>)}</select></label></div><Compare selected={currentItem} items={comparisonItems} repetition={repetition} onRepetition={setRepetition} /></> :
          <><Observe snapshot={current} refreshKey={refresh} repetition={repetition} onRepetition={setRepetition} onContext={setContext} onDocuments={() => setDocuments(true)} onPin={anchor => { void pin(anchor); }} onDerive={exposure => { void derive(exposure); }} replay={replay} onReplay={setReplay} />{currentItem ? <Compare selected={currentItem} items={comparisonItems} repetition={repetition} onRepetition={setRepetition} /> : null}</>}
      </main>
      {!['workbook', 'settings', 'assistant'].includes(view) ? <aside className="inspector"><div className="inspector-heading"><Pin size={16} /><h3>Seu olhar</h3></div>{pinned ? <><span className="eyebrow">{pinned.anchor?.excerpt ? 'Trecho fixado' : 'Momento marcado'}</span>{pinned.anchor?.excerpt ? <blockquote>{pinned.anchor.excerpt}</blockquote> : null}<small>{pinned.anchor?.experiment_id}</small><h3>Minha observação</h3><button className="note-open-card" onClick={() => setNotebook({ id: pinned.id })}><NotebookPen size={17} />Abrir esta nota<ArrowUpRight size={14} /></button><span className="hypothesis-badge">Hipótese para investigar</span>{pinned.anchor ? <button className="button secondary" onClick={() => origin(pinned)}>Conferir origem</button> : null}</> : <><p>Selecione um trecho de uma resposta e clique em <strong>Fixar trecho</strong>.</p><div className="inspector-empty"><Pin size={24} /><span>Uma particularidade pode virar uma pergunta para investigar.</span></div><button className="button secondary" onClick={() => setNotebook({})}><NotebookPen size={15} />Abrir anotações</button></>}<div className="inspector-footnote"><FileText size={14} />Suas notas ficam separadas dos registros originais.</div></aside> : null}
    </div>
    <FloatingAssistant fullScreen={view === 'assistant'}
      context={{ view, experiment_id: selected || undefined,
        observation_id: assistantAnchor?.experiment_id === selected ? assistantAnchor.observation_id : undefined }}
      onExpand={() => { if (view !== 'assistant') assistantReturn.current = view; setView('assistant'); }}
      onMinimize={() => setView(assistantReturn.current === 'assistant' ? 'observe' : assistantReturn.current)}
      onOpenExperiment={id => choose(id)}
      onNavigate={next => { if (['observe', 'prepare', 'compare', 'experiments', 'records', 'workbook', 'settings'].includes(next)) setView(next as View); }}
      onExperimentStarted={id => {
        acceptedStarts.current.add(id); setAwaitingStarts(acceptedStarts.current.size);
        setListPollingFailed(false); void refreshList();
      }} />
    {notebook ? <Notebook initialId={notebook.id} onClose={() => setNotebook(null)} onOrigin={origin} onSaved={note => setPinned(current => current?.id === note.id ? note : current)} /> : null}
    {context ? <Modal title="Contexto preparado para o participante" onClose={() => setContext(null)}><div className="modal-scroll"><ContextView request={context} /></div></Modal> : null}
    {documents && current ? <Modal title="Corpus congelado do experimento" onClose={() => setDocuments(false)}><div className="modal-scroll">{current.spec.documents.map(doc => <button className="document-row" key={doc.id} onClick={() => { setDocuments(false); setResource({ title: doc.title, content: doc.text }); }}><BookOpen size={20} /><div><strong>{doc.title}</strong><small>{doc.source || doc.id}</small></div><ChevronRight size={17} /></button>)}{!current.spec.documents.length ? <p className="muted">Este experimento não possui documentos.</p> : null}</div></Modal> : null}
    {resource ? <ResourceModal resource={resource} onClose={() => setResource(null)} /> : null}
  </ResourceReferenceContext.Provider>;
}

function Empty({ onNew }: { onNew(): void }) {
  return <section className="welcome"><span className="welcome-symbol"><FlaskConical size={38} /></span><span className="eyebrow">Norvald Lab</span><h2>Uma bancada para observar<br />o que muda entre participantes.</h2><p>Prepare sua pergunta, escolha os modelos e reúna o material do experimento.</p><button className="button" onClick={onNew}><Plus size={17} />Preparar experimento</button></section>;
}
function ResourceModal({ resource, onClose }: { resource: Resource; onClose(): void }) {
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!resource.section) return;
    const section = resource.section.toLowerCase().replace(/^#/, '');
    const heading = [...(root.current?.querySelectorAll<HTMLElement>('h1,h2,h3,h4,h5,h6') ?? [])].find(item => item.textContent?.toLowerCase().includes(section));
    heading?.scrollIntoView({ block: 'start' });
  }, [resource]);
  return <Modal title={resource.title} onClose={onClose}><div className="resource-toolbar"><MarkdownToolbar markdown={resource.content} filename={resource.title} showSyntaxHelp /></div><div ref={root} className="modal-scroll resource-view"><NorvaldMarkdown content={resource.content} /></div></Modal>;
}
function Records({ snapshot, onContext, onAsk }: { snapshot: Snapshot; onContext(request: PreparedRequest): void; onAsk(observationId: string): void }) {
  return <section className="records-view"><div className="row-heading"><div><h2>Registro original</h2><p>{snapshot.records.length} observações · {snapshot.provisional ? 'Coleta ainda sem fechamento verificável' : 'Integridade conferida'}</p></div></div>{snapshot.records.map(record => <article className="raw-card" key={record.observation_id}><div className="row-heading"><div><h3>{record.participant_name} · {record.run_id}</h3><small>{record.observation_id}</small></div><div className="assistant-actions"><button className="button secondary" onClick={() => onAsk(record.observation_id)}><Bot size={14}/>Perguntar ao Assistant</button><button className="button secondary" onClick={() => onContext(snapshot.requests.find(request => request.context.metadata.execution_id === record.logical_execution_id)!)}>Abrir contexto</button></div></div><div className="raw-meta"><span>{record.requested_model}</span><time>{new Date(record.captured_at).toLocaleString('pt-BR')}</time><span>{record.result?.tokens ?? '—'} tokens</span></div>{record.result ? <><NorvaldMarkdown content={record.result.content} /><MarkdownToolbar markdown={record.result.content} filename={record.observation_id} /></> : <p className="danger">{record.error?.message}</p>}<details><summary>RAW completo · JSON</summary><pre>{JSON.stringify(record, null, 2)}</pre></details></article>)}<details><summary>Eventos gravados</summary><pre>{JSON.stringify(snapshot.events, null, 2)}</pre></details></section>;
}
