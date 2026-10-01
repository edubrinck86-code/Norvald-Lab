import assert from 'node:assert/strict';
import { test } from 'node:test';
import { compareWords, responseProjection, eventParticipant, eventRun, familyId } from '../src/lib/observation.ts';
import type { Snapshot } from '../src/api.ts';

test('projection preserves malformed source and separates structured contribution without changing source', () => {
  const source = 'Texto anterior\n<<CONTRIBUTION>>\n{"knowledge":[{"content":"Decisão literal"}]}\n<<END_CONTRIBUTION>>';
  assert.equal(responseProjection(source).markdown, 'Texto anterior\n\nDecisão literal');
  assert.equal(responseProjection(source).structured, '{"knowledge":[{"content":"Decisão literal"}]}');
  const incomplete = '<<CONTRIBUTION>>{broken';
  assert.equal(responseProjection(incomplete).markdown, incomplete);
});
test('literal changes distinguish addition and removal, without a semantic score', () => {
  const parts = compareWords('Recursos e prazo.', 'Recursos e manutenção.');
  assert.ok(parts?.some(part => part.removed && part.value.includes('prazo')));
  assert.ok(parts?.some(part => part.added && part.value.includes('manutenção')));
  assert.equal(compareWords('a'.repeat(100_001), 'b'), null);
});
test('tool event is paired by exact execution id, including repetition', () => {
  const snapshot = { requests: [{ agent_id: 'p1', context: { metadata: { execution_id: 'lab:2:p1', run_id: 'r0002' } } }] } as Snapshot;
  const event = { at: '', event: 'tool.started', data: { execution_id: 'lab:2:p1' } };
  assert.equal(eventParticipant(event, snapshot), 'p1');
  assert.equal(eventRun(event, snapshot), 'r0002');
  assert.equal(eventParticipant({ ...event, data: { execution_id: 'lab:1:p1' } }, snapshot), undefined);
  assert.equal(familyId({ experiment_id: 'e', source_experiment_id: 'b1' }), 'b1');
});
