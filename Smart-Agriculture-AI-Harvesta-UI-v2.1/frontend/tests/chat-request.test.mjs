import test from 'node:test';
import assert from 'node:assert/strict';
import { requestChatTurn, resolveApiBase } from '../src/utils/chatRequest.js';

test('development and HTTPS default to same-origin API, not insecure port 8000', () => {
  assert.equal(resolveApiBase('', { hostname: '10.219.10.29', protocol: 'http:' }, true), '');
  assert.equal(resolveApiBase('', { hostname: 'farm.example', protocol: 'https:' }), '');
  assert.equal(resolveApiBase('https://api.example/', {}, true), 'https://api.example');
  assert.equal(resolveApiBase('', { hostname: '10.0.0.1', protocol: 'http:' }), 'http://10.0.0.1:8000');
});
test('first message uses a single API call and preserves returned metadata', async () => {
  let calls = 0;
  const response = await requestChatTurn({
    url: '/api/chat/messages', message: 'crop status', headers: {},
    fetcher: async (url, options) => {
      calls++;
      assert.equal(url, '/api/chat/messages');
      assert.deepEqual(JSON.parse(options.body), { conversation_id: null, message: 'crop status' });
      return Response.json({ conversation: { id: 2 }, response_mode: 'instant-local-knowledge' });
    },
  });
  assert.equal(calls, 1);
  assert.equal((await response.json()).conversation.id, 2);
});
const hangingFetch = (_, { signal }) => new Promise((resolve, reject) => {
  if (signal.aborted) reject(new DOMException('Aborted', 'AbortError'));
  else signal.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')), { once: true });
});
test('server stalls produce a useful timeout instead of an endless spinner', async () => {
  await assert.rejects(requestChatTurn({ url: '/', message: 'hello', fetcher: hangingFetch, timeoutMs: 10 }), /took too long/);
});
test('closing chat cancels its pending request without a retry', async () => {
  const controller = new AbortController();
  const pending = requestChatTurn({ url: '/', message: 'hello', signal: controller.signal, fetcher: hangingFetch });
  controller.abort();
  await assert.rejects(pending, { name: 'AbortError' });
});
test('HTTP auth errors remain available to the API response handler', async () => {
  const response = await requestChatTurn({ url: '/', message: 'hello', fetcher: async () => Response.json({ detail: 'Please sign in' }, { status: 401 }) });
  assert.equal(response.status, 401);
  assert.equal((await response.json()).detail, 'Please sign in');
});
