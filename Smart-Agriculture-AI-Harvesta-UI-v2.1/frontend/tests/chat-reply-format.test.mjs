import test from 'node:test';
import assert from 'node:assert/strict';

import { formatChatReply } from '../src/utils/chatReplyFormat.js';

test('detailed chat replies become safe headings, bullets, and paragraphs', () => {
  const blocks = formatChatReply('Recommendation\nA direct answer.\n\n- First check\n2. Second check');
  assert.deepEqual(blocks.map(({ type }) => type), ['heading', 'paragraph', 'spacer', 'bullet', 'bullet']);
  assert.equal(blocks[3].text, 'First check');
  assert.equal(blocks[4].marker, '2.');
});

test('formatting markers are shown as text content, never executable HTML', () => {
  const blocks = formatChatReply('**Next step**\n- `<img src=x onerror=alert(1)>`');
  assert.equal(blocks[0].text, 'Next step');
  assert.equal(blocks[1].text, '<img src=x onerror=alert(1)>');
});

test('multilingual Unicode content is preserved', () => {
  const [block] = formatChatReply('மண் ஈரப்பதத்தைச் சரிபார்க்கவும்.');
  assert.equal(block.text, 'மண் ஈரப்பதத்தைச் சரிபார்க்கவும்.');
});
