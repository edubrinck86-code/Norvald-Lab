import assert from 'node:assert/strict';
import { test } from 'node:test';
import { liveProviders, providerChoices, selectProvider } from '../src/lib/providers.ts';
import type { Connection, Spec } from '../src/api.ts';

const connections: Connection[] = [
  { kind: 'openrouter', credential_env: 'NORVALD_LAB_OPENROUTER_KEY', base_url: '', has_key: true, saved_key: true, credential_source: 'local' },
  { kind: 'openai', credential_env: 'NORVALD_LAB_OPENAI_KEY', base_url: '', has_key: true, saved_key: true, credential_source: 'local' },
  { kind: 'ollama', credential_env: 'NORVALD_LAB_OLLAMA_KEY', base_url: 'http://localhost:11434', has_key: false, saved_key: false, credential_source: 'none' },
];
function draft() { return {
  providers: { provider: { kind: 'openrouter', credential_env: connections[0].credential_env } },
  participants: [
    { id: 'p1', provider: 'provider', model: 'first/model', reasoning_effort: 'high', sampling: { max_tokens: 128 } },
    { id: 'p2', provider: 'provider', model: 'second/model', reasoning_effort: 'medium', sampling: {} },
  ],
  documents: [{ id: 'doc1', text: 'Literal document' }],
} as unknown as Spec; }

test('a draft with one internal provider alias offers saved connections by actual provider name', () => {
  const spec = draft();
  const options = providerChoices(spec.providers, connections);
  assert.equal(options.find(o => o.value === 'provider')?.label, 'openrouter');
  assert.ok(options.some(o => o.label.startsWith('openai') && o.connection?.has_key));
  assert.ok(options.some(o => o.label.startsWith('ollama')));
  assert.equal(options.filter(o => o.kind === 'openrouter').length, 1);
  assert.deepEqual(Object.keys(liveProviders(connections)), ['openrouter', 'openai', 'ollama']);
});
test('choosing a saved connection resets only that participant and preserves custom credential scopes', () => {
  const spec = draft();
  spec.providers.openai = { kind: 'openai', credential_env: 'LEGACY_TEAM_KEY', base_url: 'https://team.invalid/v1' };
  const changed = selectProvider(spec, 'p2', 'connection:openai', connections);
  assert.deepEqual(changed.participants[0], spec.participants[0]);
  assert.equal(changed.participants[1].model, '');
  assert.equal(changed.participants[1].reasoning_effort, 'off');
  assert.equal(changed.providers[changed.participants[1].provider].credential_env, connections[1].credential_env);
  assert.deepEqual(changed.providers.openai, spec.providers.openai);
  assert.deepEqual(changed.documents, spec.documents);
  assert.equal(spec.participants[1].model, 'second/model');
  const repeated = providerChoices(changed.providers, connections);
  assert.equal(repeated.filter(o => o.kind === 'openai').length, 2);
  assert.ok(!repeated.some(o => o.value === 'connection:openai'));
});
