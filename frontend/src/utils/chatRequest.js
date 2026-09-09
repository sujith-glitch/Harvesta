export function resolveApiBase(configured, location, development = false) {
  if (configured?.trim()) return configured.trim().replace(/\/$/, '');
  // Development requests go through Vite's proxy. A secure website must not
  // send authentication or chat to an insecure HTTP backend (mixed content).
  if (development || location?.protocol === 'https:') return '';
  return `http://${location?.hostname || '127.0.0.1'}:8000`;
}

export async function requestChatTurn({ url, headers, conversationId, message, signal, fetcher = fetch, timeoutMs = 25000 }) {
  const controller = new AbortController();
  let timedOut = false;
  const cancel = () => controller.abort();
  if (signal?.aborted) controller.abort();
  signal?.addEventListener('abort', cancel, { once: true });
  const timer = setTimeout(() => { timedOut = true; controller.abort(); }, timeoutMs);
  try {
    const response = await fetcher(url, {
      method: 'POST', headers, signal: controller.signal,
      body: JSON.stringify({ conversation_id: conversationId || null, message }),
    });
    // Include body reading in the deadline (a stalled connection can send
    // headers without ever finishing the response body).
    const text = await response.text();
    return new Response(text, { status: response.status, statusText: response.statusText, headers: response.headers });
  } catch (error) {
    if (timedOut) throw new Error('The chat server took too long to respond. Your message may have been saved. Check your connection and try again when the server is available.');
    if (signal?.aborted) throw error;
    throw new Error('Cannot reach the chat server. Keep Harvesta running on your computer and check your phone’s connection.');
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener('abort', cancel);
  }
}
