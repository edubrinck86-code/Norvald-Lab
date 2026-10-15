import assert from 'node:assert/strict';
import test from 'node:test';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { FloatingAssistant } from '../src/components/FloatingAssistant';

const props = {
  context: { view: 'observe', experiment_id: 'test-study', observation_id: 'obs-1' },
  onExpand: () => {},
  onMinimize: () => {},
  onOpenExperiment: (_id: string) => {},
  onNavigate: (_view: string) => {},
  onExperimentStarted: (_id: string) => {},
};

test('floating Assistant is present throughout the Lab while closed', () => {
  const html = renderToStaticMarkup(React.createElement(FloatingAssistant, {
    ...props, fullScreen: false,
  }));
  assert.match(html, /Abrir Norvald Assistant/);
  assert.match(html, /aria-expanded="false"/);
  assert.doesNotMatch(html, /nca-shell/);
});

test('same component renders a full-screen conversational shell with context', () => {
  const html = renderToStaticMarkup(React.createElement(FloatingAssistant, {
    ...props, fullScreen: true,
  }));
  assert.match(html, /nca-shell nca-full/);
  assert.match(html, /Norvald Assistant/);
  assert.match(html, /Conversa/);
  assert.match(html, /Atividades/);
  assert.match(html, /Nova conversa/);
  assert.match(html, /test-study/);
  assert.match(html, /obs-1/);
  assert.doesNotMatch(html, /nca-launcher-open/);
});
