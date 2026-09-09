export function voiceSetupError(scope) {
  if (!scope.isSecureContext) {
    return 'Phone voice chat needs a trusted HTTPS address. This HTTP Wi-Fi link cannot provide secure microphone access. For now, tap the message box and use your phone keyboard’s microphone, then tap Send.';
  }
  if (!(scope.SpeechRecognition || scope.webkitSpeechRecognition)) {
    return 'This browser does not support live speech recognition. Use a supported browser such as Chrome on Android, or dictate with your phone keyboard and tap Send.';
  }
  return '';
}

export function voiceErrorMessage(code) {
  const messages = {
    'not-allowed': 'Microphone permission was blocked. Allow Microphone in this site’s browser permissions and in your phone’s browser app permissions, then tap the mic again.',
    'service-not-allowed': 'Your browser’s speech service is blocked or unavailable. Try Chrome, or use your phone keyboard’s microphone instead.',
    'audio-capture': 'Your microphone is unavailable. Close other apps using it and check your phone’s Microphone permission, then try again.',
    network: 'Your browser could not reach its speech-recognition service. Check the phone’s internet connection, or use keyboard dictation. Harvesta’s local AI and browser speech recognition are separate services.',
    'no-speech': 'No speech was detected. Tap the mic and speak after “Listening”. You can also dictate using your phone keyboard.',
    'language-not-supported': 'The browser cannot recognise the selected voice language. Choose another language in Settings or use keyboard dictation.',
    aborted: 'Voice input stopped. Tap the mic when you are ready.',
  };
  return messages[code] || 'Voice input could not start. Check microphone access, then tap the mic again or type your question.';
}

// One browser recognition session, with no automatic retries on errors.
// Keeping this lifecycle independent of React makes late/duplicate phone events testable.
export function createVoiceSession({ Recognition, locale, onListening, onDraft, onFinal, onError }) {
  const recognition = new Recognition();
  recognition.lang = locale;
  recognition.interimResults = true;
  recognition.continuous = false;
  recognition.maxAlternatives = 1;
  let active = true;
  let submitted = false;
  const fail = (code) => {
    if (!active || submitted) return;
    active = false;
    onListening(false);
    onError(voiceErrorMessage(code));
  };
  recognition.onstart = () => { if (active && !submitted) onListening(true); };
  recognition.onresult = (event) => {
    if (!active || submitted) return;
    const results = Array.from(event.results);
    const draft = results.map((result) => result[0].transcript).join(' ').trim();
    const final = results.filter((result) => result.isFinal).map((result) => result[0].transcript).join(' ').trim();
    onDraft(draft);
    if (final) {
      submitted = true;
      onListening(false);
      recognition.stop();
      onFinal(final);
    }
  };
  recognition.onerror = (event) => fail(event.error);
  recognition.onend = () => {
    if (!active) return;
    if (submitted) onListening(false);
    else fail('no-speech');
    active = false;
  };
  return {
    start() {
      try { recognition.start(); }
      catch (error) { fail(error.name === 'NotAllowedError' ? 'not-allowed' : 'start-failed'); }
    },
    abort() {
      active = false;
      recognition.onstart = recognition.onresult = recognition.onerror = recognition.onend = null;
      try { recognition.abort(); } catch { /* Already stopped. */ }
    },
  };
}
