import assert from 'node:assert/strict';
import test from 'node:test';
import { resourceFromHref } from '../src/ui/references/resourceReference';
import { extractMarkdownIndex } from '../src/ui/markdown/MarkdownIndexSidebar';

test('notebook references preserve the captured source target and heading', () => {
  assert.deepEqual(resourceFromHref('notebook:book-id/block-id/source#Minha%20observação', 'http://localhost'), {
    source: 'notebook', id: 'book-id/block-id/source', section: 'Minha observação',
  });
  assert.equal(resourceFromHref('https://example.com/notebook/123', 'http://localhost'), null);
  assert.equal(resourceFromHref('javascript:alert(1)', 'http://localhost'), null);
});

test('Studio index excludes headings inside fenced code and preserves navigation order', () => {
  assert.deepEqual(extractMarkdownIndex('# Pergunta\n\n```md\n# Dentro do código\n```\n\n## **Hipótese**\n\n### [Fonte](https://example.com)'), [
    { level: 1, text: 'Pergunta', index: 0 },
    { level: 2, text: 'Hipótese', index: 1 },
    { level: 3, text: 'Fonte', index: 2 },
  ]);
});
