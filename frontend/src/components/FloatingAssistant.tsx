import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react';
import {
  Activity, AlertTriangle, ArrowUp, Bot, CheckCircle2,
  FileCheck2, Maximize2, MessageCircle, Minimize2, PanelLeft,
  Plus, Settings2, ShieldAlert, ShieldCheck, X,
} from 'lucide-react';
import { api, type LabSettings, type Spec } from '../api';
import { NorvaldMarkdown } from '../ui/markdown/NorvaldMarkdown';

type Thread = { id: string; title: string; context: Record<string, string>; created_at: string; updated_at: string };
type Message = { seq: number; role: 'owner' | 'assistant'; content: string; model: string; at: string };
type OperationEvent = {
  seq: number; message_seq: number | null; tool: string; operation: string;
  status: 'ok' | 'error' | 'blocked'; payload: {
    plan_id?: string; plan_action?: string; experiment_id?: string; adjustment_id?: string;
    status?: string; schema_version?: string; routine_id?: string; view?: string;
    error?: string; destructive_request?: { id: string; experiment_id: string; status: string; expires_at: string };
  }; at: string;
};
type Plan = {
  id: string; status: string; action: string; experiment_id: string;
  payload: { spec?: Spec; instruction?: string; observation_id?: string };
};
type State = { thread: Thread; messages: Message[]; events: OperationEvent[] };
type OperatorSettings = { kind: string; model: string; configured: boolean };
type ScreenContext = { view: string; experiment_id?: string; observation_id?: string };
type Activity = { plan_id?: string; experiment_id?: string; adjustment_id?: string; status?: string };
type Props = {
  fullScreen: boolean;
  context: ScreenContext;
  onExpand(): void;
  onMinimize(): void;
  onOpenExperiment(id: string): void;
  onNavigate(view: string): void;
  onExperimentStarted(id: string): void;
};

function PlanPreview({ id, threadId, onExecuted }: {
  id: string; threadId: string; onExecuted(value: Activity): void;
}) {
  const [plan, setPlan] = useState<Plan | null>(null);
  const [error, setError] = useState('');
  const [working, setWorking] = useState(false);
  const [presented, setPresented] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let valid = true;
    api<Plan>('/api/assistant/plans/' + encodeURIComponent(id))
      .then(value => { if (valid) setPlan(value); })
      .catch(reason => { if (valid) setError(String(reason)); });
    return () => { valid = false; };
  }, [id]);

  useEffect(() => {
    const node = ref.current;
    if (!plan || !node || presented) return;
    let active = true;
    const show = () => {
      if (!active) return;
      active = false;
      // A GET/listagem não equivale a apresentação: só a montagem visível marca o plano.
      void api('/api/assistant/plans/' + encodeURIComponent(id) + '/present', {
        method: 'POST', body: '{}',
      }).then(() => setPresented(true)).catch(reason => setError(String(reason)));
    };
    if (!('IntersectionObserver' in window)) { show(); return; }
    const observer = new IntersectionObserver(items => {
      if (items.some(item => item.isIntersecting)) { observer.disconnect(); show(); }
    }, { threshold: 0.1 });
    observer.observe(node);
    return () => { active = false; observer.disconnect(); };
  }, [id, plan, presented]);

  async function execute() {
    if (working || !plan || plan.status !== 'planned' || !presented) return;
    setWorking(true); setError('');
    try {
      const result = await api<{ status: string; result: Activity | null }>(
        '/api/assistant/threads/' + encodeURIComponent(threadId)
        + '/plans/' + encodeURIComponent(id) + '/execute', { method: 'POST', body: '{}' });
      setPlan(current => current ? { ...current, status: result.status } : null);
      onExecuted(result.result ?? { status: result.status });
    } catch (reason) { setError(String(reason)); }
    finally { setWorking(false); }
  }
  return <div className="nca-plan" ref={ref} aria-label="Plano de operação apresentado">
    <div className="nca-plan-heading"><strong>{plan?.action ?? 'Plano operacional'}</strong>
      <span className="badge">{plan?.status ?? 'Lendo…'}</span></div>
    <small>{id}</small>
    {plan ? <>
      <p>{plan.payload.spec?.task.objective ?? 'Ajuste separado da observação ' + (plan.payload.observation_id ?? 'original')}</p>
      {plan.payload.spec ? <p className="nca-plan-meta">
        {plan.payload.spec.mode} · {plan.payload.spec.condition.exposure} ·
        {plan.payload.spec.repetitions} repetições ·
        {plan.payload.spec.participants.map(p => p.model).join(', ')}
      </p> : null}
      <details><summary>Inspecionar o plano completo</summary>
        <pre>{JSON.stringify(plan.payload, null, 2)}</pre></details>
      <div className="nca-plan-actions">
        <button className="button secondary" disabled={!presented || working || !threadId || plan.status !== 'planned'}
          onClick={() => { void execute(); }}>
          <ArrowUp size={14} />{working ? 'Iniciando…' : plan.status === 'planned' ? 'Executar plano apresentado' : plan.status}
        </button>
      </div>
      <small>Não destrutivo · sem autorização adicional · RAW preservado</small>
    </> : null}
    {error ? <p role="alert" className="danger">{error}</p> : null}
  </div>;
}

function ExclusionPreview({ request, threadId, onConfirmed }: {
  request: NonNullable<OperationEvent['payload']['destructive_request']>;
  threadId: string; onConfirmed(): void;
}) {
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  async function run() {
    if (!confirmed || done) return;
    setBusy(true); setError('');
    try {
      await api('/api/assistant/threads/' + encodeURIComponent(threadId)
        + '/destructive/' + encodeURIComponent(request.id) + '/confirm', {
          method: 'POST', body: JSON.stringify({
            experiment_id: request.experiment_id, confirmed: true,
          }),
        });
      setDone(true); onConfirmed();
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(false); }
  }
  return <div className="nca-plan nca-danger">
    <div className="nca-plan-heading"><strong><ShieldAlert size={15}/> Ação destrutiva</strong>
      <span className="badge">{done ? 'Confirmada' : 'Pendente de confirmação'}</span></div>
    <p>Excluir <strong>{request.experiment_id}</strong> da lista de experimentos.</p>
    <small>O RAW será mantido, e a exclusão da lista é reversível.</small>
    <label className="nca-check"><input type="checkbox" checked={confirmed}
      onChange={event => setConfirmed(event.target.checked)} disabled={done}/>
      Confirmo expressamente esta ação.
    </label>
    <button className="button secondary" onClick={() => { void run(); }}
      disabled={!confirmed || busy || done}>
      <ShieldCheck size={14}/>{done ? 'Executada' : busy ? 'Aplicando…' : 'Confirmar exclusão'}
    </button>
    {error ? <p role="alert" className="danger">{error}</p> : null}
  </div>;
}

function EventResult({ event, threadId, onNavigate, onOpenExperiment, onExecuted, onRefresh }: {
  event: OperationEvent; threadId: string;
  onNavigate(view: string): void; onOpenExperiment(id: string): void;
  onExecuted(value: Activity): void; onRefresh(): void;
}) {
  const meta = event.payload;
  return <div className={'nca-event ' + (event.status === 'error' ? 'nca-event-error' : '')}>
    <div className="nca-event-label">
      {event.status === 'ok' ? <CheckCircle2 size={14} /> : <AlertTriangle size={14}/>}
      <strong>{event.operation}</strong><small>{event.status === 'ok' ? 'Operação registrada' : event.status}</small>
    </div>
    {meta.error ? <p>{meta.error}</p> : null}
    {meta.plan_id && event.operation !== 'lab.plan.execute' ? <PlanPreview id={meta.plan_id}
      threadId={threadId} onExecuted={onExecuted} /> : null}
    {meta.destructive_request ? <ExclusionPreview request={meta.destructive_request}
      threadId={threadId} onConfirmed={onRefresh}/> : null}
    {meta.experiment_id ? <button className="text-button" onClick={() => onOpenExperiment(meta.experiment_id!)}>
      Abrir experimento {meta.experiment_id}</button> : null}
    {meta.view ? <button className="text-button" onClick={() => onNavigate(meta.view!)}>
      Abrir tela {meta.view}</button> : null}
    {meta.status ? <small>Estado: {meta.status}</small> : null}
    {meta.routine_id ? <small>Rotina: {meta.routine_id}</small> : null}
  </div>;
}

export function FloatingAssistant({ fullScreen, context, onExpand, onMinimize,
  onOpenExperiment, onNavigate, onExperimentStarted }: Props) {
  const [panelOpen, setPanelOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(true);
  const [tab, setTab] = useState<'chat' | 'activity' | 'settings'>('chat');
  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeId, setActiveId] = useState('');
  const [data, setData] = useState<State | null>(null);
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [plans, setPlans] = useState<Plan[]>([]);
  const [operator, setOperator] = useState<OperatorSettings>({ kind: '', model: '', configured: false });
  const [settings, setSettings] = useState<LabSettings | null>(null);
  const [emergency, setEmergency] = useState<{ stopped: boolean; reason: string }>({ stopped: false, reason: '' });
  const input = useRef<HTMLTextAreaElement>(null);
  const shell = useRef<HTMLElement>(null);
  const end = useRef<HTMLDivElement>(null);
  const open = panelOpen || fullScreen;
  const refreshThreads = useCallback(async () => {
    const list = await api<Thread[]>('/api/assistant/threads');
    setThreads(list);
    setActiveId(current => current && list.some(t => t.id === current) ? current : list[0]?.id ?? '');
  }, []);
  const refreshDetails = useCallback(async (id: string) => {
    if (!id) { setData(null); return; }
    const result = await api<State>('/api/assistant/threads/' + encodeURIComponent(id));
    setData(result);
  }, []);
  const refreshGlobal = useCallback(async () => {
    const [all, chosen, connections, control] = await Promise.all([
      api<Plan[]>('/api/assistant/plans'),
      api<OperatorSettings>('/api/assistant/settings'),
      api<LabSettings>('/api/settings'),
      api<{ stopped: boolean; reason: string }>('/api/assistant/emergency'),
    ]);
    setPlans(all); setOperator(chosen); setSettings(connections); setEmergency(control);
  }, []);
  useEffect(() => {
    void refreshThreads().catch(reason => setError(String(reason)));
  }, [refreshThreads]);
  useEffect(() => {
    if (!activeId) { setData(null); return; }
    let alive = true;
    api<State>('/api/assistant/threads/' + encodeURIComponent(activeId))
      .then(result => { if (alive) setData(result); })
      .catch(reason => { if (alive) setError(String(reason)); });
    return () => { alive = false; };
  }, [activeId]);
  useEffect(() => {
    if (!open) return;
    void refreshGlobal().catch(reason => setError(String(reason)));
    input.current?.focus();
    const timer = window.setInterval(() => {
      if (document.visibilityState === 'visible' && !busy) {
        if (activeId) void refreshDetails(activeId).catch(() => {});
        void refreshGlobal().catch(() => {});
      }
    }, 3500);
    return () => window.clearInterval(timer);
  }, [open, activeId, busy, refreshDetails, refreshGlobal]);
  useEffect(() => { if (open && tab === 'chat') end.current?.scrollIntoView({ block: 'end' }); },
    [data?.messages.length, data?.events.length, open, tab]);
  useEffect(() => {
    if (!open) return;
    const handle = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        if (fullScreen) onMinimize(); else setPanelOpen(false);
      }
      if (event.key === 'Tab' && shell.current) {
        const controls = Array.from(shell.current.querySelectorAll<HTMLElement>(
          'button:not([disabled]), a[href], input:not([disabled]), textarea:not([disabled]), select:not([disabled])'))
          .filter(node => node.getClientRects().length > 0);
        const first = controls[0], last = controls[controls.length - 1];
        if (first && last && event.shiftKey && document.activeElement === first) {
          event.preventDefault(); last.focus();
        } else if (first && last && !event.shiftKey && document.activeElement === last) {
          event.preventDefault(); first.focus();
        }
      }
    };
    document.addEventListener('keydown', handle);
    return () => document.removeEventListener('keydown', handle);
  }, [open, fullScreen, onMinimize]);

  async function newThread() {
    setBusy(true); setError(''); setTab('chat');
    try {
      const thread = await api<Thread>('/api/assistant/threads', {
        method: 'POST', body: JSON.stringify({}),
      });
      await refreshThreads(); setActiveId(thread.id);
      setData({ thread, messages: [], events: [] });
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(false); }
  }
  async function send() {
    if (!draft.trim() || busy || emergency.stopped || !operator.configured || !settings?.live_enabled) return;
    setBusy(true); setError(''); setNotice('');
    const text = draft;
    try {
      let id = activeId;
      if (!id) {
        const thread = await api<Thread>('/api/assistant/threads', {
          method: 'POST', body: JSON.stringify({}),
        });
        id = thread.id; setActiveId(id);
      }
      const result = await api<State>('/api/assistant/threads/' + encodeURIComponent(id) + '/send', {
        method: 'POST', body: JSON.stringify({ text, context }),
      });
      setDraft(''); setData(result);
      await refreshThreads(); await refreshGlobal();
    } catch (reason) { setError(String(reason)); }
    finally { setBusy(false); }
  }
  function keyboard(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault(); void send();
    }
  }
  async function executeRecorded(value: Activity) {
    if (value.experiment_id) onExperimentStarted(value.experiment_id);
    setNotice(value.adjustment_id ? 'Ajuste solicitado: ' + value.adjustment_id
      : value.experiment_id ? 'Experimento iniciado: ' + value.experiment_id
      : 'Estado atualizado: ' + (value.status ?? 'registrado'));
    if (activeId) await refreshDetails(activeId);
    await refreshGlobal();
  }
  async function resumeStop() {
    try {
      const value = await api<{ stopped: boolean; reason: string }>(
        '/api/assistant/emergency/' + (emergency.stopped ? 'resume' : 'stop'),
        { method: 'POST', body: '{}' });
      setEmergency(value);
    } catch (reason) { setError(String(reason)); }
  }
  async function saveOperator() {
    try {
      const value = await api<OperatorSettings>('/api/assistant/settings', {
        method: 'PUT', body: JSON.stringify({ kind: operator.kind, model: operator.model }),
      });
      setOperator(value); setNotice('Modelo operador salvo.');
    } catch (reason) { setError(String(reason)); }
  }
  const visibleEvents = data?.events.filter(event => event.message_seq === null) ?? [];
  const threadName = data?.thread.title ?? 'Nova conversa';

  return <>
    {!fullScreen ? <button type="button" className={'nca-launcher ' + (panelOpen ? 'nca-launcher-open' : '')}
      title="Abrir Norvald Assistant" aria-label={panelOpen ? 'Fechar Norvald Assistant' : 'Abrir Norvald Assistant'}
      aria-expanded={panelOpen} onClick={() => setPanelOpen(x => !x)}>
      {panelOpen ? <X size={24}/> : <Bot size={25}/>}
      <span className="nca-launcher-indicator"/>
    </button> : null}
    {open ? <>
      {!fullScreen ? <button className="nca-scrim" aria-label="Fechar painel do Assistant"
        onClick={() => setPanelOpen(false)}/> : null}
      <section ref={shell} className={'nca-shell ' + (fullScreen ? 'nca-full' : 'nca-panel')}
        aria-label="Norvald Assistant" role={fullScreen ? 'region' : 'dialog'}
        aria-modal={fullScreen ? undefined : true}>
        <header className="nca-topbar">
          <div className="nca-brand"><span className="nca-logo"><Bot size={20}/></span>
            <div><strong>Norvald Assistant</strong><small>{threadName}</small></div></div>
          <div className="nca-topbar-actions">
            <button className="icon-button" title="Conversas" aria-label="Mostrar conversas"
              onClick={() => setHistoryOpen(x => !x)}><PanelLeft size={18}/></button>
            <button className="icon-button" title={fullScreen ? 'Retornar ao Lab' : 'Tela completa'}
              aria-label={fullScreen ? 'Retornar ao Lab' : 'Expandir chat'}
              onClick={() => { if (fullScreen) onMinimize(); else { setPanelOpen(false); onExpand(); } }}>
              {fullScreen ? <Minimize2 size={18}/> : <Maximize2 size={18}/>}</button>
            <button className="icon-button" title="Fechar" aria-label="Fechar Assistant"
              onClick={() => { if (fullScreen) onMinimize(); else setPanelOpen(false); }}><X size={18}/></button>
          </div>
        </header>
        <div className="nca-layout">
          {historyOpen ? <aside className="nca-threads" aria-label="Histórico de conversas">
            <button className="nca-new" onClick={() => { void newThread(); }} disabled={busy}>
              <Plus size={16}/> Nova conversa</button>
            <div className="nca-thread-list">
              {threads.map(thread => <button key={thread.id}
                className={'nca-thread ' + (activeId === thread.id ? 'selected' : '')}
                aria-current={activeId === thread.id ? 'true' : undefined}
                onClick={() => { setActiveId(thread.id); setTab('chat'); }}>
                <MessageCircle size={15}/><span>{thread.title}</span></button>)}
              {!threads.length ? <small>Nenhuma conversa salva.</small> : null}
            </div>
            <div className="nca-side-footer">
              <span>Interface local</span><small>RAW experimental preservado</small>
            </div>
          </aside> : null}
          <div className="nca-main">
            <nav className="nca-tabs" aria-label="Área do Assistant">
              <button className={tab === 'chat' ? 'active' : ''} onClick={() => setTab('chat')}>
                <MessageCircle size={15}/> Conversa</button>
              <button className={tab === 'activity' ? 'active' : ''} onClick={() => setTab('activity')}>
                <Activity size={15}/> Atividades</button>
              <button className={tab === 'settings' ? 'active' : ''} onClick={() => setTab('settings')}>
                <Settings2 size={15}/> Operador</button>
            </nav>
            {error ? <div role="alert" className="nca-alert">
              {error}<button aria-label="Descartar erro" className="icon-button"
                onClick={() => setError('')}><X size={14}/></button></div> : null}
            {notice ? <div className="nca-notice" role="status">{notice}</div> : null}
            {tab === 'chat' ? <>
              <div className="nca-timeline" role="log" aria-live="polite" aria-relevant="additions">
                {!data?.messages.length ? <div className="nca-welcome">
                  <span className="nca-welcome-mark"><Bot size={28}/></span>
                  <h2>O que vamos fazer no laboratório?</h2>
                  <p>Planeje estudos, prepare e execute operações, acompanhe critérios, faça ajustes e peça relatórios — tudo nesta conversa.</p>
                  <div className="nca-prompts">
                    {['Planeje um experimento com os modelos configurados.',
                      'Quais experimentos estão ativos?',
                      'Analise os critérios do experimento selecionado.',
                      'Mostre as rotinas e os incidentes pendentes.'].map(prompt =>
                      <button key={prompt} onClick={() => setDraft(prompt)}>{prompt}</button>)}
                  </div>
                </div> : null}
                {data?.messages.map(message => <div key={message.seq}
                  className={'nca-turn ' + (message.role === 'owner' ? 'nca-user' : 'nca-assistant')}>
                  {message.role === 'assistant' ? <span className="nca-avatar"><Bot size={16}/></span> : null}
                  <div className="nca-turn-body">
                    {message.role === 'assistant' ? <small>Norvald Assistant · {message.model}</small> : null}
                    <div className="nca-bubble">
                      {message.role === 'assistant'
                        ? <NorvaldMarkdown content={message.content} mode="compact" />
                        : <p>{message.content}</p>}
                    </div>
                    {message.role === 'assistant' ? data.events.filter(event => event.message_seq === message.seq)
                      .map(event => <EventResult key={event.seq} event={event} threadId={activeId}
                        onNavigate={onNavigate} onOpenExperiment={onOpenExperiment}
                        onExecuted={value => { void executeRecorded(value); }}
                        onRefresh={() => { void refreshDetails(activeId); void refreshGlobal(); }}/>) : null}
                  </div>
                </div>)}
                {visibleEvents.map(event => <EventResult key={event.seq} event={event} threadId={activeId}
                  onNavigate={onNavigate} onOpenExperiment={onOpenExperiment}
                  onExecuted={value => { void executeRecorded(value); }}
                  onRefresh={() => { void refreshDetails(activeId); void refreshGlobal(); }}/>)}
                {busy ? <div className="nca-thinking"><span className="nca-pulse"/>
                  Consultando e executando operações permitidas…</div> : null}
                <div ref={end}/>
              </div>
              <div className="nca-composer">
                {emergency.stopped ? <div className="nca-stop">
                  <AlertTriangle size={16}/> Parada emergencial ativa.
                  <button onClick={() => { void resumeStop(); }}>Retomar</button></div> : null}
                <div className="nca-context"><FileCheck2 size={13}/>
                  {context.experiment_id ? 'Contexto: ' + context.experiment_id : 'Contexto geral do laboratório'}
                  {context.view ? ' · ' + context.view : null}
                  {context.observation_id ? ' · observação ' + context.observation_id : null}
                </div>
                <div className="nca-input-row">
                  <textarea ref={input} rows={2} value={draft} onChange={e => setDraft(e.target.value)}
                    onKeyDown={keyboard} placeholder="Peça qualquer operação ao laboratório…"
                    aria-label="Mensagem para o Norvald Assistant" disabled={busy}/>
                  <button className="nca-send" title="Enviar mensagem" aria-label="Enviar mensagem"
                    disabled={busy || !draft.trim() || emergency.stopped || !operator.configured || !settings?.live_enabled}
                    onClick={() => { void send(); }}><ArrowUp size={20}/></button>
                </div>
                <div className="nca-composer-foot">
                  <span>Enter envia · Shift+Enter quebra linha</span>
                  {!operator.configured || !settings?.live_enabled
                    ? <button onClick={() => setTab('settings')}>Configurar modelo operador</button>
                    : <span>Planos visíveis antes de executar · sem cotas próprias</span>}
                </div>
              </div>
            </> : tab === 'activity' ? <div className="nca-content-scroll">
              <div className="nca-content-title"><h3>Atividades e planos</h3>
                <button className="button secondary" onClick={() => { void refreshGlobal(); }}>Atualizar</button></div>
              <p className="muted">Planos persistidos pelo Lab. A execução é uma operação distinta do planejamento.</p>
              {plans.map(plan => <PlanPreview key={plan.id} id={plan.id} threadId={activeId}
                onExecuted={value => { void executeRecorded(value); }} />)}
              {!plans.length ? <p className="muted">Ainda não há planos.</p> : null}
              <div className="nca-emergency">
                <div><ShieldAlert size={17}/><strong>Controle emergencial</strong></div>
                <p>{emergency.stopped ? emergency.reason : 'Suspende novas operações. Não modifica registros selados.'}</p>
                <button className="button secondary" onClick={() => { void resumeStop(); }}>
                  {emergency.stopped ? 'Retomar novas ações' : 'Interromper novas ações'}</button>
              </div>
            </div> : <div className="nca-content-scroll">
              <h3>Modelo operador</h3>
              <p className="muted">Modelo independente dos participantes do experimento. Credenciais permanecem na configuração local do Lab.</p>
              <label>Provider
                <select value={operator.kind} onChange={event => setOperator(v => ({ ...v, kind: event.target.value }))}>
                  <option value="">Selecione</option>
                  {settings?.connections.map(c => <option key={c.kind} value={c.kind}>{c.kind}</option>)}
                </select>
              </label>
              <label>Modelo<input value={operator.model} onChange={e =>
                setOperator(v => ({ ...v, model: e.target.value }))} placeholder="ID do modelo"/></label>
              <button className="button secondary" onClick={() => { void saveOperator(); }}
                disabled={!operator.kind || !operator.model.trim()}>Salvar modelo operador</button>
              {!settings?.live_enabled ? <p className="danger">Chamadas reais estão desabilitadas nas configurações do Lab.</p> : null}
              <p className="muted">Sem teto próprio de tokens, gastos ou número de tarefas. Validações do Runner e limites do provider continuam válidos.</p>
            </div>}
          </div>
        </div>
      </section>
    </> : null}
  </>;
}
