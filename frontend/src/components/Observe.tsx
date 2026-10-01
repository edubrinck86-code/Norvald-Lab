import { useEffect, useState } from 'react';
import { BookOpen, ChevronLeft, ChevronRight, FileText, Pause, Pin, Play, RotateCcw, Wrench } from 'lucide-react';
import { conditions, statusLabel, type Snapshot, type PreparedRequest, type RawRecord, type Anchor } from '../api';
import { elapsed, eventLabel, eventParticipant, eventRun, responseProjection } from '../lib/observation';
import { AdjustResponse } from './AdjustResponse';
import { Drawer } from './Drawer';
import { NorvaldMarkdown } from '../ui/markdown/NorvaldMarkdown';
import { MarkdownToolbar } from '../ui/MarkdownToolbar';

export function Observe({ snapshot, repetition, onRepetition, onContext, onDocuments, onPin, onDerive, replay, onReplay }: {
  snapshot: Snapshot; repetition: number; onRepetition(index: number): void;
  onContext(request: PreparedRequest): void; onDocuments(): void; onPin(anchor: Anchor): void;
  onDerive(exposure: 'self' | 'exposed'): void; replay: number | null; onReplay(index: number | null): void;
}) {
  const [opened, setOpened] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const [visibleIds, setVisibleIds] = useState<string[]>([]);
  useEffect(() => { setVisibleIds(snapshot.spec.participants.map(p => p.id).slice(0, 3)); setPlaying(false); setOpened(null); }, [snapshot.experiment_id]);
  useEffect(() => {
    if (!playing) return;
    const timer = setTimeout(() => {
      if (replay === null || replay >= snapshot.events.length - 1) { setPlaying(false); return; }
      onReplay(replay + 1);
    }, 650);
    return () => clearTimeout(timer);
  }, [playing, replay, snapshot.events.length, onReplay]);
  const condition = conditions[snapshot.spec.condition.exposure];
  const origin = snapshot.events[0]?.at ?? snapshot.records[0]?.started_at;
  const cutoff = replay === null ? Infinity : Date.parse(snapshot.events[replay]?.at ?? '');
  const events = snapshot.events.map((event, index) => ({ ...event, index })).filter((_, index) => replay === null || index <= replay);
  const run = 'r' + repetition.toString().padStart(4, '0');
  const candidates = snapshot.records.filter(r => r.run_id === run && Date.parse(r.captured_at) <= cutoff);
  const invalidContributions = (snapshot.contribution_checks ?? []).filter(check => !check.usable);
  const openedCheck = snapshot.contribution_checks?.find(check => check.observation_id === candidates.find(r => r.participant_id === opened)?.observation_id);
  const openedParticipant = snapshot.spec.participants.find(p => p.id === opened);
  const openedRecord = candidates.find(r => r.participant_id === opened);
  const openedRequest = snapshot.requests.find(r => r.agent_id === opened && r.context.metadata.repetition_index === repetition);
  const openedEvents = events.filter(e => eventParticipant(e, snapshot) === opened && eventRun(e, snapshot) === run);
  function pin(record: RawRecord, element: HTMLElement) {
    const selection = window.getSelection();
    const selected = selection && element.contains(selection.anchorNode) && element.contains(selection.focusNode) ? selection.toString().trim() : '';
    const projection = responseProjection(record.result?.content ?? '');
    const excerpt = selected || projection.markdown.split('\n').find(text => text && !text.startsWith('DEMONSTRAÇÃO')) || record.result?.content || '';
    onPin({ experiment_id: snapshot.experiment_id, observation_id: record.observation_id, excerpt });
  }
  return <div className="observation-view">
    <div className="question-strip"><div><span className="eyebrow">Pergunta do experimento</span><NorvaldMarkdown content={snapshot.spec.task.objective} /></div><button className="button secondary" onClick={onDocuments}><BookOpen size={15} />Documentos · {snapshot.spec.documents.length}</button></div>
    <div className="condition-strip"><span className="condition-dot" /><div><h3>{condition.title}</h3><p>{condition.description}</p></div><button className="button secondary" onClick={() => onContext(snapshot.requests.find(r => r.context.metadata.repetition_index === repetition) ?? snapshot.requests[0])}><EyeIcon />Ver o que foi enviado</button></div>
    <div className="observation-controls"><label>Repetição<select value={repetition} onChange={event => onRepetition(Number(event.target.value))}>{Array.from({ length: snapshot.spec.repetitions }, (_, i) => <option key={i} value={i + 1}>{i + 1} de {snapshot.spec.repetitions}</option>)}</select></label>
      <div className="participant-filter"><span className="muted">Na mesa</span>{snapshot.spec.participants.map((p, index) => <label className={'filter-chip tone-' + index % 4} key={p.id}><input type="checkbox" checked={visibleIds.includes(p.id)} onChange={event => setVisibleIds(current => event.target.checked ? [...current, p.id] : current.filter(id => id !== p.id))} />{p.name}</label>)}</div>
      {snapshot.provisional ? <span className="badge">Coleta provisória · {statusLabel(snapshot.status)}</span> : <span className="badge">Integridade conferida</span>}
    </div>
    {snapshot.spec.condition.exposure === 'blind' && invalidContributions.length ? <section className="contribution-warning" role="status"><h3>Respostas salvas · exposição estruturada indisponível</h3><p>Para reconsideração individual ou exposição aos colegas, todos os participantes precisam declarar um bloco CONTRIBUTION válido. Esta conferência verifica o formato e a validação do bloco, sem avaliar a qualidade da resposta.</p><ul>{invalidContributions.map(check => <li key={check.observation_id}><strong>{check.participant_name} · repetição {Number(check.run_id.slice(1))} · {check.model}</strong><p>{check.message}</p><button className="text-button" onClick={() => { onRepetition(Number(check.run_id.slice(1))); onReplay(null); setPlaying(false); setOpened(check.participant_id); }}>Ver diagnóstico e resposta original</button></li>)}</ul></section> : null}
    <div className="participant-table">
      {snapshot.spec.participants.filter(p => visibleIds.includes(p.id)).map(p => {
        const index = snapshot.spec.participants.findIndex(item => item.id === p.id);
        const row = candidates.find(record => record.participant_id === p.id);
        const request = snapshot.requests.find(r => r.agent_id === p.id && r.context.metadata.repetition_index === repetition)!;
        const ownEvents = events.filter(event => eventParticipant(event, snapshot) === p.id && eventRun(event, snapshot) === run);
        const started = ownEvents.some(event => event.event === 'execution.started');
        const projection = responseProjection(row?.result?.content ?? '');
        return <article className={'participant-card tone-' + index % 4} key={p.id}>
          <header><span className="participant-avatar">{p.name.slice(0, 1).toUpperCase()}</span><div><h3><button className="participant-title" onClick={() => setOpened(p.id)}>{p.name}</button></h3><p>{p.model} · reasoning {p.reasoning_effort}</p></div><span className="participant-status">{row ? row.error ? 'Falhou' : 'Concluído' : started ? 'Em execução' : 'Aguardando'}</span></header>
          <button className="context-button" onClick={() => onContext(request)}><FileText size={15} />Contexto preparado<ChevronRight size={14} /></button>
          <div className="participant-events">{ownEvents.map(event => <div className={'recorded-event ' + (event.event.startsWith('tool.') ? 'tool-event' : '')} key={event.index}><span>{event.event.startsWith('tool.') ? <Wrench size={13} /> : <FileText size={13} />}</span><time title={event.at}>{elapsed(event.at, origin)}</time><span>{eventLabel(event)}</span></div>)}</div>
          <div className="participant-response" id={'response-' + p.id}>
            {row?.error ? <p className="danger">{row.error.message}</p> : row?.result ? <>
              <NorvaldMarkdown content={projection.markdown} />
              {row.result.reasoning ? <details><summary>Reasoning disponibilizado · {row.reasoning_exposure_mode}</summary><NorvaldMarkdown content={row.result.reasoning} /></details> : <p className="trace-note">O provedor não disponibilizou reasoning neste registro.</p>}
              {projection.structured ? <details><summary>Contribuição estruturada original</summary><pre>{projection.structured}</pre></details> : null}
              <details><summary>Resposta original em Markdown</summary><pre>{row.result.content}</pre></details>
            </> : <div className="waiting"><span className={started ? 'activity-dot' : 'waiting-dot'} /><p>{started ? 'Aguardando a resposta do provedor.' : 'Aguardando início desta execução.'}</p></div>}
          </div>
          <footer><button className="text-button drawer-open" onClick={() => setOpened(p.id)}>Abrir na bancada<ChevronRight size={14} /></button>{row?.result ? <><button className="text-button" onClick={() => { const element = document.getElementById('response-' + p.id); if (element) pin(row, element); }}><Pin size={14} />Fixar trecho</button><MarkdownToolbar markdown={row.result.content} filename={p.name + '-' + snapshot.experiment_id} /></> : <span className="muted">Os eventos aparecem quando registrados.</span>}</footer>
        </article>;
      })}
      {!visibleIds.length ? <div className="empty-state">Selecione um participante para observar.</div> : null}
    </div>
    {openedParticipant ? <Drawer title={openedParticipant.name + ' · Bancada'} onClose={() => setOpened(null)}>
      <div className="drawer-navigation"><label>Participante<select aria-label="Participante na bancada" value={openedParticipant.id} onChange={event => setOpened(event.target.value)}>{snapshot.spec.participants.map(p => <option value={p.id} key={p.id}>{p.name}</option>)}</select></label><span className="badge">Repetição {repetition} · {replay === null ? 'Registros disponíveis' : 'Revisão de eventos'}</span></div>
      <div className="drawer-content"><div className="drawer-meta"><span className="eyebrow">{openedParticipant.provider}</span><h3>{openedParticipant.model}</h3><p>Solicitação de reasoning: {openedParticipant.reasoning_effort === 'off' ? 'padrão / sem solicitação' : openedParticipant.reasoning_effort}</p></div>
        {openedRequest ? <button className="context-button" onClick={() => onContext(openedRequest)}><FileText size={15} />Contexto preparado<ChevronRight size={14} /></button> : null}
        {openedCheck ? <section className={'contribution-diagnostic ' + (openedCheck.usable ? '' : 'unusable')}><h3>Diagnóstico da contribuição</h3><p>{openedCheck.message}</p><small>{openedCheck.declared_items} unidades declaradas · {openedCheck.accepted_items} unidades aceitas pelo validador</small>{openedCheck.rejected.length ? <details><summary>Partes recusadas</summary><ul>{openedCheck.rejected.map((part, index) => <li key={index}>{part.kind} · {part.identifier || 'Sem identificador'}: {part.reason}</li>)}</ul></details> : null}<p className="muted">A resposta original está abaixo. Você pode pedir um ajuste separado à LLM, preservando este registro.</p></section> : null}
        <section className="drawer-response" id="drawer-response"><span className="eyebrow">Resposta registrada</span>{openedRecord?.error ? <p className="danger">{openedRecord.error.message}</p> : openedRecord?.result ? <><NorvaldMarkdown content={responseProjection(openedRecord.result.content).markdown} />{openedRecord.result.reasoning ? <details><summary>Reasoning disponibilizado · {openedRecord.reasoning_exposure_mode}</summary><NorvaldMarkdown content={openedRecord.result.reasoning} /></details> : <p className="trace-note">O provedor não disponibilizou reasoning neste registro.</p>}<details open={openedCheck?.usable === false}><summary>Resposta original em Markdown</summary><pre>{openedRecord.result.content}</pre></details>{responseProjection(openedRecord.result.content).structured ? <details><summary>Contribuição estruturada original</summary><pre>{responseProjection(openedRecord.result.content).structured}</pre></details> : null}</> : <p className="muted">A resposta aparecerá quando for registrada pelo motor.</p>}</section>
        {openedRecord && !snapshot.provisional && snapshot.integrity?.valid && snapshot.spec.mode === 'live' ? <AdjustResponse key={openedRecord.observation_id} experimentId={snapshot.experiment_id} record={openedRecord} invalid={openedCheck?.usable === false} maxTokens={openedParticipant.sampling.max_tokens} /> : null}
        <section className="drawer-events"><h3>Eventos registrados</h3>{openedEvents.map(event => <div className="recorded-event" key={event.index}><time title={event.at}>{elapsed(event.at, origin)}</time><span>{eventLabel(event)}</span></div>)}{!openedEvents.length ? <p className="muted">Aguardando eventos desta execução.</p> : null}</section>
      </div><footer className="modal-footer">{openedRecord?.result ? <><button className="text-button" onClick={() => { const element = document.getElementById('drawer-response'); if (element) pin(openedRecord, element); }}><Pin size={14} />Fixar trecho</button><MarkdownToolbar markdown={openedRecord.result.content} filename={openedParticipant.name + '-' + snapshot.experiment_id} /></> : <span className="muted">A coleta continua ao fechar a bancada.</span>}</footer>
    </Drawer> : null}
    <p className="reading-caption">A resposta e o reasoning aparecem quando são registrados pelo motor. O reasoning disponível não representa acesso completo ao processo interno do modelo.</p>
    <section className="timeline-panel">
      <div className="row-heading"><div><h3>Rever registros</h3><p>{replay === null ? 'Acompanhando os registros disponíveis' : 'Revisão de eventos gravados · execução continua independente'}</p></div>
        <div className="timeline-actions"><button className="icon-button" aria-label="Evento anterior" disabled={!snapshot.events.length} onClick={() => { setPlaying(false); onReplay(Math.max(0, (replay ?? snapshot.events.length - 1) - 1)); }}><ChevronLeft size={18} /></button>
          <button className="icon-button" aria-label={playing ? 'Pausar revisão' : 'Reproduzir revisão'} disabled={!snapshot.events.length} onClick={() => { if (replay === null || replay >= snapshot.events.length - 1) onReplay(0); setPlaying(value => !value); }}>{playing ? <Pause size={17} /> : <Play size={17} />}</button>
          <button className="icon-button" aria-label="Próximo evento" disabled={!snapshot.events.length} onClick={() => { setPlaying(false); onReplay(Math.min(snapshot.events.length - 1, (replay ?? -1) + 1)); }}><ChevronRight size={18} /></button>
          <button className="text-button" onClick={() => { setPlaying(false); onReplay(null); }}><RotateCcw size={13} />Todos os registros</button>
          <button className="button secondary" disabled={!snapshot.events.length} onClick={() => onPin({ experiment_id: snapshot.experiment_id, event_index: replay ?? snapshot.events.length - 1 })}><Pin size={14} />Marcar momento</button></div>
      </div>
      {snapshot.events.length ? <>
        <div className="timeline-lanes">{snapshot.spec.participants.filter(p => visibleIds.includes(p.id)).map(p => {
          const last = Date.parse(snapshot.events.at(-1)!.at);
          const first = Date.parse(origin);
          const duration = Math.max(1, last - first);
          const tone = snapshot.spec.participants.findIndex(item => item.id === p.id) % 4;
          return <div className={'timeline-lane tone-' + tone} key={p.id}><span>{p.name}</span><div className="timeline-track">{snapshot.events.map((event, index) => eventParticipant(event, snapshot) === p.id && eventRun(event, snapshot) === run ? <button key={index} className={'event-dot ' + (index === replay ? 'active' : '')} style={{ left: (Date.parse(event.at) - first) / duration * 98 + '%' }} title={elapsed(event.at, origin) + ' · ' + eventLabel(event)} aria-label={p.name + ' · ' + eventLabel(event) + ' · evento ' + (index + 1)} onClick={() => { setPlaying(false); onReplay(index); }} /> : null)}</div></div>;
        })}</div>
        <label className="replay-slider"><span>{replay === null ? snapshot.events.length : replay + 1} / {snapshot.events.length} eventos</span><input type="range" aria-label="Momento da revisão" min={0} max={Math.max(0, snapshot.events.length - 1)} value={replay ?? snapshot.events.length - 1} onChange={event => { setPlaying(false); onReplay(Number(event.target.value)); }} /><time>{elapsed(snapshot.events[replay ?? snapshot.events.length - 1].at, origin)}</time></label>
        <div className="selected-event">{eventLabel(snapshot.events[replay ?? snapshot.events.length - 1])}<time>{new Date(snapshot.events[replay ?? snapshot.events.length - 1].at).toLocaleString('pt-BR')}</time></div>
      </> : <p className="muted">Os primeiros eventos ainda não foram registrados.</p>}
    </section>
    {snapshot.spec.condition.exposure === 'blind' && snapshot.status === 'complete' && snapshot.integrity?.valid ? <div className="derive-actions"><span>Observe a mesma base em outra condição</span><button className="button secondary" disabled={invalidContributions.length > 0} onClick={() => onDerive('self')}>Reconsideração individual</button><button className="button secondary" disabled={snapshot.spec.participants.length < 2 || invalidContributions.length > 0} onClick={() => onDerive('exposed')}>Exposição aos colegas</button></div> : null}
  </div>;
}
function EyeIcon() { return <FileText size={15} />; }
