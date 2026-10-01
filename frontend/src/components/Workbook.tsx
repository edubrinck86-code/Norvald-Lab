import { useEffect, useRef, useState } from 'react';
import { ArrowDown, ArrowUp, BookOpen, Check, Copy, Eye, FileText, GripVertical, Link2, ListTree, NotebookPen, Pencil, Plus, Search, Trash2 } from 'lucide-react';
import { api, type CorpusCapture, type DocumentItem, type Note, type WorkBlock, type Workbook as Book } from '../api';
import type { useWorkbooks } from '../hooks/useWorkbooks';
import { Modal } from './Modal';
import { NorvaldMarkdown } from '../ui/markdown/NorvaldMarkdown';
import { MarkdownIndexSidebar, scrollMarkdownHeading } from '../ui/markdown/MarkdownIndexSidebar';
import { MarkdownToolbar } from '../ui/MarkdownToolbar';
import { countWords } from '../lib/markdownText';

type Store = ReturnType<typeof useWorkbooks>;
type Resource = { title: string; content: string };
const blockTypes = ['Contexto', 'Hipótese', 'Observação', 'Protocolo', 'Análise'];
export function bookMarkdown(book: Book) {
  return '# ' + book.title + '\n\n' + book.blocks.map(block => '## ' + (block.title || 'Sem título') + '\n\n' + block.content).join('\n\n');
}

export function Workbook({ store, active, documents, onResource, onOrigin, onNotes, onCorpus }: {
  store: Store; active: boolean; documents: DocumentItem[];
  onResource(resource: Resource): void; onOrigin(note: Note): void; onNotes(id?: string): void; onCorpus(capture: CorpusCapture): void;
}) {
  const book = store.selected;
  const [openId, setOpenId] = useState('');
  const [search, setSearch] = useState('');
  const [picker, setPicker] = useState(false);
  const [notes, setNotes] = useState<Note[]>([]);
  const [noteError, setNoteError] = useState('');
  const [capturing, setCapturing] = useState(false);
  const [deleting, setDeleting] = useState('');
  const [corpus, setCorpus] = useState<CorpusCapture | null>(null);
  const dragged = useRef('');
  useEffect(() => { if (!active) { setOpenId(''); setPicker(false); setCorpus(null); void store.flush(); } }, [active]);
  const openBlock = book?.blocks.find(block => block.id === openId);
  function updateBlock(blockId: string, change: Partial<WorkBlock>) {
    if (book) store.update({ ...book, blocks: book.blocks.map(block => block.id === blockId ? { ...block, ...change } : block) });
  }
  function addBlock() {
    if (!book) return;
    const block: WorkBlock = { id: crypto.randomUUID(), title: '', content: '', type: 'Contexto', source_note: null };
    store.update({ ...book, blocks: [...book.blocks, block] }); setOpenId(block.id);
  }
  function reorder(id: string, targetId: string) {
    if (!book || id === targetId) return;
    const next = [...book.blocks], start = next.findIndex(b => b.id === id), end = next.findIndex(b => b.id === targetId);
    if (start < 0 || end < 0) return;
    next.splice(end, 0, next.splice(start, 1)[0]); store.update({ ...book, blocks: next });
  }
  function duplicate(block: WorkBlock) {
    if (!book) return;
    const blocks = [...book.blocks], index = blocks.findIndex(b => b.id === block.id);
    blocks.splice(index + 1, 0, { ...block, id: crypto.randomUUID(), title: (block.title || 'Sem título') + ' · cópia' });
    store.update({ ...book, blocks });
  }
  async function closeBlock() { if (await store.flush()) setOpenId(''); }
  async function pickNotes() {
    setPicker(true); setNoteError('');
    try { setNotes(await api<Note[]>('/api/notes')); } catch (reason) { setNoteError(String(reason)); }
  }
  async function capture(note: Note) {
    setCapturing(true);
    try { const block = await store.captureNote(note.id); if (block) { setPicker(false); setOpenId(block.id); } }
    finally { setCapturing(false); }
  }
  async function prepareCorpus(ids?: string[]) {
    const capture = await store.captureCorpus(ids); if (capture) setCorpus(capture);
  }
  async function externalVersion() {
    const saved = await store.savedVersion(); if (saved) onResource({ title: 'Versão salva · ' + saved.title + ' · r' + saved.revision, content: bookMarkdown(saved) });
  }
  const visibleBlocks = book?.blocks.filter(block => (block.title + block.content + block.type).toLowerCase().includes(search.toLowerCase())) ?? [];
  if (!active) return null;
  return <div className="workbook-workspace" hidden={!active}>
    {store.error ? <div className="error-banner" role="alert">{store.error}<button className="text-button" onClick={() => { void store.flush(); }}>Tentar salvar</button><button className="text-button" onClick={externalVersion}>Conferir versão salva</button>{store.error.includes('outra aba') ? <button className="text-button" onClick={() => { void store.keepLocal(); }}>Substituir pela minha edição</button> : null}</div> : null}
    {!store.loaded ? <div className="empty-state">Abrindo seus cadernos…</div> : !book ? <div className="welcome"><span className="welcome-symbol"><BookOpen size={35} /></span><h2>Seu caderno de trabalho</h2><p>Reúna observações, desenvolva hipóteses e organize seu trabalho em blocos de Markdown.</p><button className="button" onClick={() => { void store.create(); }}><Plus size={16} />Criar caderno</button></div> : <>
      <div className="workbook-topbar"><label>Caderno<select aria-label="Selecionar caderno" value={book.id} onChange={event => { setOpenId(''); void store.choose(event.target.value); }}>{store.books.map(item => <option value={item.id} key={item.id}>{item.title || 'Sem título'}</option>)}</select></label><button className="text-button" onClick={() => { setOpenId(''); void store.create(); }}><Plus size={15} />Novo caderno</button><span role="status" className="save-status">{store.status.startsWith('Salvo') ? <Check size={12} /> : null}{store.status}</span></div>
      <div className="workbook-layout">
        <section className="workbook-canvas" aria-label="Blocos do caderno">
          <div className="workbook-heading"><div><span className="eyebrow">Notebook</span><input aria-label="Título do caderno" value={book.title} maxLength={300} onChange={event => store.update({ ...book, title: event.target.value })} /><p>{book.blocks.length} blocos · revisão {book.revision} · {countWords(book.blocks.map(b => b.content).join(' '))} palavras</p></div><MarkdownToolbar markdown={bookMarkdown(book)} filename={book.title || 'caderno'} showSyntaxHelp /></div>
          <div className="workbook-controls"><label className="search-field"><Search size={15} /><input aria-label="Buscar blocos" placeholder="Buscar título, texto ou tipo…" value={search} onChange={event => setSearch(event.target.value)} /></label><button className="button secondary" onClick={pickNotes}><NotebookPen size={15} />Trazer anotação</button></div>
          <div className="workbook-grid">{visibleBlocks.map(block => {
            const index = book.blocks.findIndex(b => b.id === block.id);
            return <article className={'work-block ' + (openId === block.id ? 'selected' : '')} key={block.id} onDragOver={event => { if (dragged.current) event.preventDefault(); }} onDrop={event => { event.preventDefault(); reorder(dragged.current, block.id); dragged.current = ''; }}>
              <header><button className="icon-button block-drag" draggable aria-label={'Arrastar ' + (block.title || 'bloco')} title="Arrastar para reorganizar" onDragStart={event => { dragged.current = block.id; event.dataTransfer.effectAllowed = 'move'; event.dataTransfer.setData('text/plain', block.id); }} onDragEnd={() => { dragged.current = ''; }}><GripVertical size={16} /></button><button className="block-title" onClick={() => setOpenId(block.id)}><FileText size={15} /><h3>{block.title || 'Sem título'}</h3></button></header>
              <span className={'block-type ' + (block.type === 'Hipótese' ? 'hypothesis' : block.type === 'Observação' ? 'observation' : '')}>{block.type || 'Contexto'}</span>
              <div className="block-preview">{block.content.trim() ? <NorvaldMarkdown content={block.content} mode="compact" /> : <p>Este bloco está vazio. Abra para escrever em Markdown.</p>}</div>
              {block.source_note ? <span className="block-source"><Link2 size={12} />Anotação capturada com origem</span> : null}
              <footer><button className="text-button" onClick={() => setOpenId(block.id)}><Pencil size={13} />Abrir bloco</button><div className="block-options"><button className="icon-button" disabled={index === 0 || !!search} aria-label={'Mover para cima ' + (block.title || 'bloco')} onClick={() => reorder(block.id, book.blocks[index - 1].id)}><ArrowUp size={13} /></button><button className="icon-button" disabled={index === book.blocks.length - 1 || !!search} aria-label={'Mover para baixo ' + (block.title || 'bloco')} onClick={() => reorder(block.id, book.blocks[index + 1].id)}><ArrowDown size={13} /></button><button className="icon-button" aria-label={'Duplicar ' + (block.title || 'bloco')} onClick={() => duplicate(block)}><Copy size={13} /></button><button className={'icon-button ' + (deleting === block.id ? 'danger' : '')} aria-label={deleting === block.id ? 'Confirmar exclusão do bloco' : 'Excluir ' + (block.title || 'bloco')} onClick={() => { if (deleting !== block.id) { setDeleting(block.id); return; } store.update({ ...book, blocks: book.blocks.filter(b => b.id !== block.id) }); setDeleting(''); }}><Trash2 size={13} /></button></div></footer>
              {deleting === block.id ? <div className="block-delete">Clique novamente na lixeira para excluir.<button className="text-button" onClick={() => setDeleting('')}>Cancelar</button></div> : null}
            </article>;
          })}<button className="work-block add-work-block" onClick={addBlock}><span><Plus size={22} /></span><strong>Adicionar bloco</strong><small>Contexto, hipótese, observação ou análise</small></button></div>
          {search && !visibleBlocks.length ? <p className="muted">Nenhum bloco corresponde à busca.</p> : null}
        </section>
        <aside className="workbook-knowledge" aria-label="Visão geral do caderno"><div className="knowledge-heading"><BookOpen size={17} /><h3>Seu trabalho reunido</h3></div><p>O que você registrou e organizou neste caderno.</p><div className="knowledge-metrics"><div><strong>{book.blocks.length}</strong><span>Blocos</span></div><div><strong>{book.blocks.filter(b => b.type === 'Hipótese').length}</strong><span>Hipóteses</span></div><div><strong>{book.blocks.filter(b => b.source_note).length}</strong><span>Anotações capturadas</span></div><div><strong>{new Set(book.blocks.flatMap(b => b.source_note?.anchor ? [b.source_note.anchor.experiment_id] : [])).size}</strong><span>Experimentos de origem</span></div></div><section><h4>Temas do caderno</h4><div className="block-types">{[...new Set(book.blocks.map(b => b.type || 'Contexto'))].map(type => <span className="block-type" key={type}>{type}</span>)}{!book.blocks.length ? <p>Adicione seu primeiro bloco.</p> : null}</div></section><section><h4>Material para um experimento</h4><p>Inclua uma cópia da versão atual no corpus de um novo experimento.</p><button className="button secondary" disabled={!book.blocks.some(b => b.content.trim())} onClick={() => { void prepareCorpus(); }}><FileText size={14} />Usar caderno no corpus</button></section><section><h4>Anotações rápidas</h4><p>Volte às suas percepções e aos momentos marcados durante a coleta.</p><button className="text-button" onClick={() => onNotes()}><NotebookPen size={15} />Abrir minhas anotações</button></section><footer>Atualizado {new Date(book.updated_at).toLocaleString('pt-BR')}</footer></aside>
      </div>
    </>}
    {active && book && openBlock ? <WorkBlockEditor key={openBlock.id} book={book} block={openBlock} status={store.status} error={store.error} onRetry={() => { void store.flush(); }} onSavedVersion={externalVersion} onKeepLocal={() => { void store.keepLocal(); }} documents={documents} onChange={change => updateBlock(openBlock.id, change)} onClose={() => { void closeBlock(); }} onSelect={setOpenId} onResource={onResource} onOrigin={onOrigin} onNotes={onNotes} onCorpus={() => { void prepareCorpus([openBlock.id]); }} /> : null}
    {active && picker ? <Modal title="Trazer anotação para o caderno" onClose={() => { if (!capturing) setPicker(false); }}><div className="modal-scroll"><p>Uma cópia do texto e da origem será preservada no bloco. A anotação pode continuar evoluindo separadamente.</p>{noteError ? <div role="alert" className="error-banner">{noteError}</div> : null}{store.error ? <div role="alert" className="error-banner">{store.error}</div> : null}{notes.map(note => <button className="document-row" key={note.id} disabled={capturing} onClick={() => { void capture(note); }}><NotebookPen size={18} /><div><strong>{note.title || 'Sem título'}</strong><small>{note.anchor?.experiment_id || 'Anotação pessoal'} · {countWords(note.content)} palavras</small></div><Plus size={16} /></button>)}{!notes.length && !noteError ? <p>Você ainda não tem anotações. Elas podem ser criadas durante a observação ou em Notes.</p> : null}</div></Modal> : null}
    {active && corpus ? <Modal title="Versão do caderno para o corpus" onClose={() => setCorpus(null)}><div className="modal-scroll"><p>Revisão {corpus.revision} · {corpus.block_ids.length} blocos. Confira a cópia que será incluída em um novo experimento.</p><NorvaldMarkdown content={corpus.document.text} /><details><summary>Identificação da versão</summary><p>{corpus.document.source}</p><code>{corpus.sha256}</code></details></div><footer className="modal-footer"><p>O experimento receberá este texto. Edições futuras no caderno não alteram esta cópia.</p><button className="button" onClick={async () => { if (await store.flush()) { setCorpus(null); setOpenId(''); onCorpus(corpus); } }}>Preparar experimento com esta versão</button></footer></Modal> : null}
  </div>;
}

function WorkBlockEditor({ book, block, status, error, onRetry, onSavedVersion, onKeepLocal, documents, onChange, onClose, onSelect, onResource, onOrigin, onNotes, onCorpus }: {
  book: Book; block: WorkBlock; status: string; error: string; onRetry(): void; onSavedVersion(): void; onKeepLocal(): void; documents: DocumentItem[];
  onChange(change: Partial<WorkBlock>): void; onClose(): void; onSelect(id: string): void;
  onResource(resource: Resource): void; onOrigin(note: Note): void; onNotes(id?: string): void; onCorpus(): void;
}) {
  const [edit, setEdit] = useState(!block.content.trim());
  const [indexOpen, setIndexOpen] = useState(true);
  const [panelsOpen, setPanelsOpen] = useState(true);
  const editor = useRef<HTMLTextAreaElement>(null);
  const preview = useRef<HTMLDivElement>(null);
  const scroll = useRef<HTMLDivElement>(null);
  function heading(index: number) {
    setEdit(false);
    requestAnimationFrame(() => requestAnimationFrame(() => scrollMarkdownHeading(preview.current, scroll.current, index)));
  }
  function insert(before: string, after = '', placeholder = 'texto') {
    const input = editor.current;
    const start = input?.selectionStart ?? block.content.length, end = input?.selectionEnd ?? start;
    const selected = block.content.slice(start, end) || placeholder;
    onChange({ content: block.content.slice(0, start) + before + selected + after + block.content.slice(end) });
    setEdit(true);
    requestAnimationFrame(() => { editor.current?.focus(); editor.current?.setSelectionRange(start + before.length, start + before.length + selected.length); });
  }
  return <Modal title={'Bloco · ' + (block.title || 'Sem título')} onClose={onClose} className="work-block-modal">
    {error ? <div role="alert" className="error-banner">{error}<button className="text-button" onClick={onRetry}>Tentar salvar</button><button className="text-button" onClick={onSavedVersion}>Conferir versão salva</button>{error.includes('outra aba') ? <button className="text-button" onClick={onKeepLocal}>Substituir pela minha edição</button> : null}</div> : null}
    <div className="block-editor-bar"><button className="text-button" onClick={onClose}>← Voltar ao caderno</button><div><span role="status" className="save-status">{status}</span><button className={'button secondary ' + (edit ? 'selected' : '')} onClick={() => setEdit(value => !value)}>{edit ? <Eye size={15} /> : <Pencil size={15} />}{edit ? 'Visualizar bloco' : 'Editar bloco'}</button><MarkdownToolbar markdown={block.content} filename={block.title || 'bloco'} showSyntaxHelp /></div></div>
    <div className="block-panel-controls"><button className="text-button" aria-expanded={indexOpen} onClick={() => setIndexOpen(value => !value)}><ListTree size={14} />Índice</button><button className="text-button" aria-expanded={panelsOpen} onClick={() => setPanelsOpen(value => !value)}>Inspector e navegação</button></div>
    <div className={'block-editor-layout ' + (!indexOpen ? 'index-closed ' : '') + (!panelsOpen ? 'panels-closed' : '')}>
      {indexOpen ? <MarkdownIndexSidebar className="work-block-index" title={block.title || 'Sem título'} markdown={block.content} contentRef={preview} scrollRef={scroll} onNavigate={heading} /> : null}
      <section className="work-block-document">
        {edit ? <div className="block-format-toolbar" aria-label="Formatação Markdown"><button className="text-button" onClick={() => insert('**', '**')}>Negrito</button><button className="text-button" onClick={() => insert('*', '*')}>Itálico</button><button className="text-button" onClick={() => insert('\n## ', '\n', 'Título')}>Título</button><button className="text-button" onClick={() => insert('\n- [ ] ', '\n', 'Conferir')}>Checklist</button><button className="text-button" onClick={() => insert('\n> ', '\n')}>Citação</button><button className="text-button" onClick={() => insert('\n| A | B |\n|---|---|\n| ', ' | |\n', 'valor')}>Tabela</button><button className="text-button" onClick={() => insert('$', '$', 'N_{eff}')}>Fórmula</button><button className="text-button" onClick={() => insert('\n> [!NOTE]\n> ', '\n', 'Observação')}>Callout</button></div> : null}
        <div className="work-block-scroll" ref={scroll}>{edit ? <textarea ref={editor} autoFocus aria-label="Conteúdo do bloco em Markdown" value={block.content} spellCheck={false} onChange={event => onChange({ content: event.target.value })} placeholder="# Comece a escrever…" /> : <article><h1>{block.title || 'Sem título'}</h1><div ref={preview}><NorvaldMarkdown content={block.content} /></div>{!block.content.trim() ? <button className="empty-note dashed" onClick={() => setEdit(true)}>Clique para escrever neste bloco.</button> : null}</article>}</div>
        <footer className="note-count"><span>Markdown · revisão {book.revision}</span><span>{countWords(block.content)} palavras · {block.content.length.toLocaleString('pt-BR')} caracteres</span></footer>
      </section>
      {panelsOpen ? <aside className="work-block-panels"><section className="block-inspector" aria-label="Inspector do bloco"><h3>Inspector</h3><label>Título<input aria-label="Título do bloco" value={block.title} maxLength={300} onChange={event => onChange({ title: event.target.value })} placeholder="Sem título" /></label><label>Tipo<select aria-label="Tipo do bloco" value={block.type} onChange={event => onChange({ type: event.target.value })}>{[...new Set([...blockTypes, block.type])].map(type => <option key={type}>{type}</option>)}</select></label><small>{block.type === 'Hipótese' ? 'Uma hipótese registrada por você para investigar.' : 'Organização pessoal do seu trabalho.'}</small>{block.source_note ? <div className="block-origin"><h4>Origem preservada</h4><p>{block.source_note.title}</p><small>Capturada {new Date(block.source_note.captured_at).toLocaleString('pt-BR')}</small><button className="text-button" onClick={() => onResource({ title: 'Anotação capturada · ' + block.source_note!.title, content: block.source_note!.content })}>Ver cópia original</button><button className="text-button" onClick={() => onNotes(block.source_note!.id)}>Abrir anotação atual</button>{block.source_note.anchor ? <button className="text-button" onClick={() => onOrigin(block.source_note!)}>Conferir origem no experimento</button> : null}</div> : null}<button className="text-button" disabled={!block.content.trim()} onClick={onCorpus}>Usar este bloco no corpus</button></section>
        <section className="block-navigation" aria-label="Navegação do bloco"><h3>Navegação</h3><details open><summary><FileText size={14} />Blocos <span>{book.blocks.length}</span></summary>{book.blocks.map(item => <button className={item.id === block.id ? 'selected' : ''} key={item.id} onClick={() => onSelect(item.id)}>{item.title || 'Sem título'}</button>)}</details><details open><summary><BookOpen size={14} />Corpus na bancada <span>{documents.length}</span></summary>{documents.map(doc => <div className="block-nav-resource" key={doc.id}><button onClick={() => onResource({ title: doc.title, content: doc.text })}>{doc.title}</button><button className="icon-button" aria-label={'Inserir referência ' + doc.title} title="Inserir referência em Markdown" onClick={() => insert('[', '](repository:' + doc.id + ')', doc.title)}><Link2 size={13} /></button></div>)}{!documents.length ? <p>Abra um experimento para consultar seu corpus.</p> : null}</details><details open><summary><NotebookPen size={14} />Anotações vinculadas <span>{book.blocks.filter(b => b.source_note).length}</span></summary>{book.blocks.filter(b => b.source_note).map(b => <div className="block-nav-resource" key={b.id}><button onClick={() => onResource({ title: b.source_note!.title, content: b.source_note!.content })}>{b.source_note!.title}</button><button className="icon-button" aria-label={'Inserir referência à anotação ' + b.source_note!.title} onClick={() => insert('[', '](notebook:' + book.id + '/' + b.id + '/source)', b.source_note!.title)}><Link2 size={13} /></button></div>)}{!book.blocks.some(b => b.source_note) ? <p>Use “Trazer anotação” para reunir suas observações.</p> : null}</details></section>
      </aside> : null}
    </div>
  </Modal>;
}
