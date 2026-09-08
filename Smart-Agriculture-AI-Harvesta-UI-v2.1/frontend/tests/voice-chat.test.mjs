import test from 'node:test';
import assert from 'node:assert/strict';
import { createVoiceSession, voiceErrorMessage, voiceSetupError } from '../src/utils/voiceChat.js';

function harness() {
  let browser;
  const events = { listening: [], draft: [], final: [], errors: [] };
  class Recognition {
    constructor() { browser = this; }
    start() { this.onstart?.(); }
    stop() { this.onend?.(); }
    abort() { this.onerror?.({ error: 'aborted' }); this.onend?.(); }
  }
  const session = createVoiceSession({
    Recognition, locale: 'ta-IN',
    onListening: (value) => events.listening.push(value),
    onDraft: (value) => events.draft.push(value),
    onFinal: (value) => events.final.push(value),
    onError: (value) => events.errors.push(value),
  });
  return { session, browser, events };
}
const result = (transcript, isFinal) => Object.assign([{ transcript }], { isFinal });

test('insecure phone address gives HTTPS and keyboard-dictation instructions', () => {
  const error = voiceSetupError({ isSecureContext: false, webkitSpeechRecognition() {} });
  assert.match(error, /HTTPS/);
  assert.match(error, /keyboard/);
});
test('secure supported browser is allowed; unsupported browser explains fallback', () => {
  assert.equal(voiceSetupError({ isSecureContext: true, webkitSpeechRecognition() {} }), '');
  assert.match(voiceSetupError({ isSecureContext: true }), /does not support/);
});
test('voice starts immediately and keeps selected language', () => {
  const { session, browser, events } = harness();
  session.start();
  assert.equal(browser.lang, 'ta-IN');
  assert.equal(browser.continuous, false);
  assert.deepEqual(events.listening, [true]);
});
test('interim transcript remains a draft, final sends exactly once', () => {
  const { session, browser, events } = harness();
  session.start();
  browser.onresult({ results: [result('crop', false)] });
  assert.deepEqual(events.final, []);
  browser.onresult({ results: [result('crop status', true)] });
  browser.onresult({ results: [result('crop status', true)] });
  assert.deepEqual(events.final, ['crop status']);
  assert.deepEqual(events.errors, []);
});
for (const code of ['not-allowed', 'service-not-allowed', 'audio-capture', 'network', 'no-speech', 'language-not-supported']) {
  test(`${code} stops after one useful error, without retrying on end`, () => {
    const { session, browser, events } = harness();
    session.start();
    browser.onerror({ error: code });
    browser.onend();
    assert.deepEqual(events.errors, [voiceErrorMessage(code)]);
    assert.deepEqual(events.final, []);
    assert.equal(events.listening.at(-1), false);
  });
}
test('abort/unmount ignores queued transcript and end events', () => {
  const { session, browser, events } = harness();
  const lateResult = browser.onresult;
  const lateEnd = browser.onend;
  session.start();
  session.abort();
  lateResult({ results: [result('do not send this', true)] });
  lateEnd();
  assert.deepEqual(events.final, []);
  assert.deepEqual(events.errors, []);
});
test('browser ending without final speech does not silently submit an interim draft', () => {
  const { session, browser, events } = harness();
  session.start();
  browser.onresult({ results: [result('unfinished draft', false)] });
  browser.onend();
  assert.deepEqual(events.final, []);
  assert.match(events.errors[0], /No speech/);
});
