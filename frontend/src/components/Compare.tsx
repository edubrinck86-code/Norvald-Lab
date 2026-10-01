import { useEffect, useState } from 'react';
import { api, conditions, type ExperimentItem, type Exposure, type Snapshot } from '../api';
import { compareWords, familyId, responseProjection } from '../lib/observation';
import { NorvaldMarkdown } from '../ui/markdown/NorvaldMarkdown';
import { MarkdownToolbar } from '../ui/MarkdownToolbar';

export function Compare({ selected, items, repetition }: { selected: ExperimentItem; items: ExperimentItem[]; repetition: number }) {
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [participant, setParticipant] = useState('');
  const [highlight, setHighlight] = useState(true);
  const [error, setError] = useState('');
  const family = items.filter(item => familyId(item) === familyId(selected) && item.status !== 'running');
  const key = family.map(item => item.experiment_id + ':' + item.status).join('|');
  useEffect(() => {
    let active = true;
    setSnapshots([]); setError('');
    Promise.all(family.map(item => api<Snapshot>('/api/experiments/' + item.experiment_id + '/observe'))).then(values => {
      if (!active) return;
      const verified = values.filter(value => value.integrity?.valid);
      setSnapshots(verified);
      setParticipant(current => verified[0]?.spec.participants.some(p => p.id === current) ? current : verified[0]?.spec.participants[0]?.id ?? '');
    }).catch(reason => { if (active) setError(String(reason)); });
    return () => { active = false; };
  }, [key]);
  const run = 'r' + repetition.toString().padStart(4, '0');
  const baseline = snapshots.find(snapshot => snapshot.spec.condition.exposure === 'blind');
  const baseRecord = baseline?.records.find(record => record.participant_id === participant && record.run_id === run);
  const before = responseProjection(baseRecord?.result?.content ?? '').markdown;
  return <section className="comparison-panel">
    <div className="row-heading"><div><h3>O que mudou?</h3><p>Mesmo participante e repetição, em condições ligadas à mesma base independente.</p></div><div className="comparison-controls"><label>Participante<select value={participant} onChange={event => setParticipant(event.target.value)}>{(baseline ?? snapshots[0])?.spec.participants.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}</select></label><label className="switch-label"><input type="checkbox" checked={highlight} onChange={event => setHighlight(event.target.checked)} />Destacar alterações</label></div></div>
    {error ? <div role="alert" className="error-banner">{error}</div> : null}
    <div className="comparison-grid">{(['blind', 'self', 'exposed'] as Exposure[]).map(exposure => {
      const available = snapshots.filter(snapshot => snapshot.spec.condition.exposure === exposure);
      const snapshot = available.find(item => item.experiment_id === selected.experiment_id) ?? available.sort((a, b) => (b.records[0]?.captured_at ?? '').localeCompare(a.records[0]?.captured_at ?? ''))[0];
      const record = snapshot?.records.find(item => item.participant_id === participant && item.run_id === run);
      const after = responseProjection(record?.result?.content ?? '').markdown;
      const changes = highlight && exposure !== 'blind' && baseRecord?.result && record?.result ? compareWords(before, after) : null;
      return <article className={'comparison-card ' + (exposure === selected.exposure ? 'selected' : '')} key={exposure}><span className="eyebrow">{exposure === 'blind' ? '01' : exposure === 'self' ? '02' : '03'}</span><h4>{conditions[exposure].title}</h4>{record?.result ? <><NorvaldMarkdown content={after} />{changes ? <details open className="literal-diff"><summary>Mudanças literais frente à resposta independente</summary><p>{changes.map((part, index) => <span key={index} className={part.added ? 'diff-added' : part.removed ? 'diff-removed' : ''}>{part.value}</span>)}</p></details> : highlight && exposure !== 'blind' && before.length + after.length > 100_000 ? <p className="muted">Texto extenso: compare os originais baixados.</p> : null}<MarkdownToolbar markdown={record.result.content} filename={exposure + '-' + participant} /><small>{snapshot?.experiment_id}</small></> : <p className="comparison-empty">{record?.error ? 'Falha registrada: ' + record.error.message : 'Ainda sem resposta fechada e verificável nesta condição.'}</p>}</article>;
    })}</div>
    <p className="reading-caption">Destaques indicam alterações no texto exibido. Não avaliam qualidade, equivalência de sentido ou influência causal. Os originais permanecem disponíveis em Markdown.</p>
  </section>;
}
