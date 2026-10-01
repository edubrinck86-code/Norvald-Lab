import { useEffect, useState } from 'react';
import { ArrowLeftRight, ChevronRight } from 'lucide-react';
import { api, conditions, type ExperimentItem, type Exposure, type RawRecord, type Snapshot } from '../api';
import { compareWords, familyId, responseProjection } from '../lib/observation';
import { Modal } from './Modal';
import { NorvaldMarkdown } from '../ui/markdown/NorvaldMarkdown';
import { MarkdownToolbar } from '../ui/MarkdownToolbar';

export function Compare({ selected, items, repetition, onRepetition }: { selected: ExperimentItem; items: ExperimentItem[]; repetition: number; onRepetition(index: number): void }) {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [participant, setParticipant] = useState('');
  const [targetId, setTargetId] = useState('');
  const [opened, setOpened] = useState(false);
  const [reading, setReading] = useState<'responses' | 'changes'>('responses');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const family = items.filter(item => familyId(item) === familyId(selected) && item.status !== 'running');
  const key = family.map(item => item.experiment_id + ':' + item.status).join('|');
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    setSnapshots([]); setError(''); setLoading(true);
    Promise.all(family.map(item => api<Snapshot>('/api/experiments/' + item.experiment_id + '/observe', { signal: controller.signal }))).then(values => {
      if (!active) return;
      const verified = values.filter(value => value.integrity?.valid).sort((a, b) => (a.records[0]?.captured_at ?? '').localeCompare(b.records[0]?.captured_at ?? ''));
      setSnapshots(verified);
      setParticipant(current => verified[0]?.spec.participants.some(p => p.id === current) ? current : verified[0]?.spec.participants[0]?.id ?? '');
    }).catch(reason => { if (active) setError(String(reason)); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; controller.abort(); };
  }, [key]);
  useEffect(() => { setOpened(false); setTargetId(''); }, [selected.experiment_id]);
  const run = 'r' + repetition.toString().padStart(4, '0');
  const baseline = snapshots.find(snapshot => snapshot.spec.condition.exposure === 'blind');
  const alternatives = snapshots.filter(snapshot => snapshot.spec.condition.exposure !== 'blind');
  const preferred = alternatives.find(snapshot => snapshot.experiment_id === selected.experiment_id) ?? alternatives.filter(snapshot => snapshot.spec.condition.exposure === 'exposed').at(-1) ?? alternatives.at(-1);
  const target = alternatives.find(snapshot => snapshot.experiment_id === targetId) ?? preferred;
  const recordFor = (snapshot?: Snapshot) => snapshot?.records.find(record => record.participant_id === participant && record.run_id === run);
  const baseRecord = recordFor(baseline);
  const targetRecord = recordFor(target);
  const before = responseProjection(baseRecord?.result?.content ?? '').markdown;
  const after = responseProjection(targetRecord?.result?.content ?? '').markdown;
  const changes = reading === 'changes' && baseRecord?.result && targetRecord?.result ? compareWords(before, after) : null;
  function open(exposure?: Exposure) {
    if (exposure && exposure !== 'blind') { const available = snapshots.filter(snapshot => snapshot.spec.condition.exposure === exposure); setTargetId((available.find(snapshot => snapshot.experiment_id === selected.experiment_id) ?? available.at(-1))?.experiment_id ?? ''); }
    setReading('responses'); setOpened(true);
  }
  const participants = (baseline ?? snapshots[0])?.spec.participants ?? [];
  return <section className="comparison-panel comparison-compact">
    <div className="row-heading"><div><h3>O que mudou?</h3><p>Abra para comparar o mesmo participante e repetição, em condições ligadas à mesma base.</p></div><button className="button secondary" disabled={loading || !snapshots.length} onClick={() => open()}><ArrowLeftRight size={15} />Abrir comparação</button></div>
    {error ? <div role="alert" className="error-banner">{error}</div> : null}
    <div className="comparison-condition-list">{(['blind', 'self', 'exposed'] as Exposure[]).map((exposure, index) => {
      const available = snapshots.filter(snapshot => snapshot.spec.condition.exposure === exposure);
      const snapshot = available.find(item => item.experiment_id === selected.experiment_id) ?? available.at(-1);
      const record = recordFor(snapshot);
      return <button className={'comparison-condition-card ' + (exposure === selected.exposure ? 'selected' : '')} key={exposure} disabled={!snapshot} onClick={() => open(exposure)}><span className="eyebrow">0{index + 1}</span><strong>{conditions[exposure].title}</strong><small>{loading ? 'Conferindo registros…' : record?.error ? 'Falha registrada' : record?.result ? 'Resposta disponível' : snapshot ? 'Sem resposta nesta repetição' : 'Condição ainda não executada'}</small><ChevronRight size={15} /></button>;
    })}</div>
    {opened ? <Modal title="O que mudou? · Comparação" className="comparison-modal" onClose={() => setOpened(false)}>
      <div className="comparison-navigation"><label>Participante<select aria-label="Participante da comparação" value={participant} onChange={event => setParticipant(event.target.value)}>{participants.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label><label>Repetição<select aria-label="Repetição da comparação" value={repetition} onChange={event => onRepetition(Number(event.target.value))}>{Array.from({ length: (baseline ?? target)?.spec.repetitions ?? 1 }, (_, index) => <option key={index} value={index + 1}>{index + 1}</option>)}</select></label><label>Comparar com<select aria-label="Condição da comparação" value={target?.experiment_id ?? ''} onChange={event => setTargetId(event.target.value)}>{alternatives.length ? alternatives.map(snapshot => <option key={snapshot.experiment_id} value={snapshot.experiment_id}>{conditions[snapshot.spec.condition.exposure].title} · {snapshot.experiment_id}</option>) : <option value="">Aguardando outra condição</option>}</select></label></div>
      <div className="comparison-reading-controls" role="group" aria-label="Modo de leitura da comparação"><button className={'button secondary ' + (reading === 'responses' ? 'selected' : '')} aria-pressed={reading === 'responses'} onClick={() => setReading('responses')}>Respostas completas</button><button className={'button secondary ' + (reading === 'changes' ? 'selected' : '')} aria-pressed={reading === 'changes'} disabled={!baseRecord?.result || !targetRecord?.result} onClick={() => setReading('changes')}>Alterações</button>{reading === 'changes' ? <span className="diff-legend"><span className="diff-removed">Removido</span><span className="diff-added">Adicionado</span></span> : null}</div>
      <div className="comparison-reading-area">{reading === 'responses' ? <div className="comparison-pair"><ComparisonResponse title={conditions.blind.title} snapshot={baseline} record={baseRecord} /><ComparisonResponse title={target ? conditions[target.spec.condition.exposure].title : 'Outra condição'} snapshot={target} record={targetRecord} /></div> : <section className="comparison-changes"><h3>{conditions.blind.title} → {target ? conditions[target.spec.condition.exposure].title : ''}</h3><p className="muted">Alterações literais no texto exibido. Marcas de Markdown aparecem como texto para preservar a comparação.</p>{changes ? <div className="literal-diff"><p>{changes.map((part, index) => part.added ? <ins key={index} className="diff-added">{part.value}</ins> : part.removed ? <del key={index} className="diff-removed">{part.value}</del> : <span key={index}>{part.value}</span>)}</p></div> : <p>Texto extenso: veja as respostas completas ou baixe os originais para comparar.</p>}</section>}</div>
      <footer className="modal-footer"><p>Destaques indicam mudanças no texto. Não avaliam qualidade, equivalência de sentido ou influência causal.</p></footer>
    </Modal> : null}
  </section>;
}

function ComparisonResponse({ title, snapshot, record }: { title: string; snapshot?: Snapshot; record?: RawRecord }) {
  return <article className="comparison-response"><header><span className="eyebrow">{title}</span><h3>{record?.participant_name || 'Resposta'}</h3><small>{snapshot?.experiment_id || 'Condição ainda não executada'}</small>{record?.result ? <MarkdownToolbar markdown={record.result.content} filename={(snapshot?.experiment_id ?? 'resposta') + '-' + record.participant_id} /> : null}</header><div className="comparison-response-body">{record?.result ? <><NorvaldMarkdown content={responseProjection(record.result.content).markdown} />{record.result.reasoning ? <details><summary>Reasoning disponibilizado</summary><NorvaldMarkdown content={record.result.reasoning} /></details> : null}<details><summary>Resposta original em Markdown</summary><pre>{record.result.content}</pre></details></> : <p className={record?.error ? 'danger' : 'muted'}>{record?.error ? 'Falha registrada: ' + record.error.message : 'Ainda sem resposta fechada e verificável nesta condição.'}</p>}</div></article>;
}
