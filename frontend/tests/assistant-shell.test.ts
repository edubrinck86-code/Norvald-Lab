import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';

const read = (path: string) => readFileSync(new URL(path, import.meta.url), 'utf8');

test('single floating Assistant instance is mounted globally in the Lab', () => {
  const app = read('../src/App.tsx');
  assert.match(app, /import \{ FloatingAssistant \} from '\.\/components\/FloatingAssistant'/);
  assert.match(app, /<FloatingAssistant fullScreen=\{view === 'assistant'\}/);
  assert.match(app, /context=\{\{ view, experiment_id: selected \|\| undefined/);
  assert.match(app, /view === 'assistant' \? null/);
  assert.doesNotMatch(app, /<LabAssistant/);
});

test('same Assistant component supports launcher, full screen, thread navigation and context', () => {
  const source = read('../src/components/FloatingAssistant.tsx');
  assert.match(source, /nca-launcher/);
  assert.match(source, /fullScreen \? 'nca-full' : 'nca-panel'/);
  assert.match(source, /\/api\/assistant\/threads/);
  assert.match(source, /\/send'/);
  assert.match(source, /context\.observation_id/);
  assert.match(source, /\/present'/);
  assert.match(source, /<ExclusionPreview/);
  assert.match(source, /aria-label="Mensagem para o Norvald Assistant"/);
});

test('floating styling supports full viewport and narrow screens', () => {
  const style = read('../src/styles/floating-assistant.css');
  assert.match(style, /\.nca-launcher/);
  assert.match(style, /\.nca-full \{ inset:0/);
  assert.match(style, /@media\(max-width:600px\)/);
});
