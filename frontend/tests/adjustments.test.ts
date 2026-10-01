import assert from 'node:assert/strict';
import { test } from 'node:test';
import { adjustmentLabel, contributionSummary, latestAdjustment, validAdjustment } from '../src/lib/adjustments.ts';
import type { Adjustment, RawRecord } from '../src/api.ts';

const valid: Adjustment = { id: 'a1', observation_id: 'original-1', instruction: '', parent_id: null, created_at: '2026-10-01T20:00:00Z', max_tokens: null, status: 'complete',
  record: { result: { content: 'Resposta', tokens: 1 }, error: null } as RawRecord,
  check: { usable: true, code: 'usable', message: 'Disponível', accepted_items: 5, declared_items: 5, rejected: [] } };

test('historical usable checks with rejected relations are partial, not fully valid', () => {
  const partial = { ...valid, check: { ...valid.check!, rejected: Array.from({ length: 5 }, () => ({ kind: 'relation', identifier: 'uuid', reason: 'relação incompatível' })) } };
  assert.equal(validAdjustment(partial), false);
  assert.equal(adjustmentLabel(partial), 'Ajuste aceito parcialmente');
  assert.match(contributionSummary(partial.check), /5 unidades aceitas · 5 relações recusadas/);
  assert.equal(validAdjustment(valid), true);
});

test('latest failed or empty adjustment does not inherit validity from an earlier success', () => {
  const empty = { ...valid, id: 'a2', created_at: '2026-10-01T21:00:00Z', check: { ...valid.check!, usable: false, code: 'empty_response', message: 'Nenhum conteúdo', accepted_items: 0 } };
  const latest = latestAdjustment([empty, { ...valid, observation_id: 'other' }, valid], 'original-1');
  assert.equal(latest?.id, 'a2');
  assert.equal(adjustmentLabel(latest!), 'Último ajuste sem resposta');
  assert.equal(validAdjustment(latest), false);
  assert.equal(latestAdjustment([valid], 'other'), undefined);
  assert.equal(validAdjustment({ ...valid, status: 'altered' }), false);
});
