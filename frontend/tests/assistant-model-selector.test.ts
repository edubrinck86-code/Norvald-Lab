import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { matchesCapability } from '../src/components/ModelPicker';

const source = (name: string) => readFileSync(new URL('../src/' + name, import.meta.url), 'utf8');

test('operator provider and model drafts are not overwritten by the background poll', () => {
  const assistant = source('components/FloatingAssistant.tsx');
  const refresh = assistant.split('const refreshGlobal = useCallback(async () => {')[1]
    .split('}, []);')[0];
  assert.match(refresh, /\/api\/settings/);
  assert.match(refresh, /\/api\/assistant\/emergency/);
  assert.doesNotMatch(refresh, /setOperator\(/);
  assert.doesNotMatch(refresh, /\/api\/assistant\/settings/);
  assert.match(assistant, /operatorLoaded\.current = true/);
  assert.match(assistant, /if \(!operatorDraftDirty\.current\) setOperator\(value\)/);
  assert.match(assistant, /operatorDraftDirty\.current = true/);
  assert.match(assistant, /kind, model: '', configured: false/);
});

test('Assistant opens the real provider catalog with search and price, tools, reasoning filters', () => {
  const assistant = source('components/FloatingAssistant.tsx');
  const picker = source('components/ModelPicker.tsx');
  assert.match(assistant, /<ModelPicker/);
  assert.match(assistant, /credential_env: selectedConnection\.credential_env/);
  assert.match(assistant, /base_url: selectedConnection\.base_url/);
  assert.match(assistant, /model: model\.id/);
  assert.match(assistant, /Buscar modelos e filtrar/);
  assert.match(picker, /\/api\/models/);
  assert.match(picker, /m\.name \+ ' ' \+ m\.id/);
  assert.match(picker, /Filtrar por preço/);
  assert.match(picker, /Filtrar por ' \+ label/);
  assert.match(picker, /Atualizar catálogo/);
  assert.equal(matchesCapability(true, 'yes'), true);
  assert.equal(matchesCapability(false, 'yes'), false);
  assert.equal(matchesCapability(null, 'unknown'), true);
});

test('catalog popup layers above Assistant and owns Escape and Tab', () => {
  const assistant = source('components/FloatingAssistant.tsx');
  const modal = source('components/Modal.tsx');
  const css = source('styles/floating-assistant.css');
  assert.match(assistant, /overlayClassName="nca-model-modal"/);
  assert.match(assistant, /if \(modelPickerOpen\) return;/);
  assert.match(modal, /"modal-scrim " \+ overlayClassName/);
  assert.match(css, /\.modal-scrim\.nca-model-modal \{ z-index: 1110; \}/);
  assert.match(css, /\.nca-shell \{ position: fixed; z-index:1103;/);
});
