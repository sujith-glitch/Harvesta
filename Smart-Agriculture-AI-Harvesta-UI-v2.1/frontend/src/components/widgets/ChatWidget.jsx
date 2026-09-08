import { useEffect, useRef, useState } from 'react';
import { ArrowUp, Loader2, Mic, MicOff, Volume2, Waves, X } from 'lucide-react';
import { sendChatMessage } from '../../services/api';
import { usePreferences } from '../../context/PreferencesContext';
import { createVoiceSession, voiceSetupError } from '../../utils/voiceChat';

export default function ChatWidget() {
  const { preferences, speechLocale, t } = usePreferences();
  const [msg, setMsg] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceMode, setVoiceMode] = useState(false);
  const [error, setError] = useState('');
  const [isSlow, setIsSlow] = useState(false);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const voiceModeRef = useRef(false);
  const mountedRef = useRef(true);
  const sendingRef = useRef(false);
  const restartTimerRef = useRef(null);
  const startListeningRef = useRef(null);
  const requestRef = useRef(null);
  const speechRef = useRef(null);

  useEffect(() => {
    mountedRef.current = true;
    const pause = () => { if (document.hidden) stopVoiceMode(); };
    document.addEventListener('visibilitychange', pause);
    return () => {
      mountedRef.current = false;
      voiceModeRef.current = false;
      clearTimeout(restartTimerRef.current);
      recognitionRef.current?.abort();
      requestRef.current?.abort();
      speechRef.current = null;
      window.speechSynthesis?.cancel?.();
      document.removeEventListener('visibilitychange', pause);
    };
  }, []);

  useEffect(() => {
    // Do not keep listening in a previous language or after voice is disabled.
    stopVoiceMode();
  }, [preferences.voice_enabled, speechLocale]);

  useEffect(() => {
    setIsSlow(false);
    if (!isSending) return undefined;
    const timer = setTimeout(() => setIsSlow(true), 4000);
    return () => clearTimeout(timer);
  }, [isSending]);

  function stopVoiceMode() {
    voiceModeRef.current = false;
    clearTimeout(restartTimerRef.current);
    recognitionRef.current?.abort();
    recognitionRef.current = null;
    speechRef.current = null;
    setVoiceMode(false);
    setIsListening(false);
    setIsSpeaking(false);
    window.speechSynthesis?.cancel?.();
  }

  function listenAgain() {
    clearTimeout(restartTimerRef.current);
    restartTimerRef.current = setTimeout(() => {
      if (mountedRef.current && voiceModeRef.current) startListeningRef.current?.();
    }, 300);
  }

  function startListening() {
    if (!mountedRef.current || !voiceModeRef.current || !preferences.voice_enabled || sendingRef.current) return;
    const setupError = voiceSetupError(window);
    if (setupError) { stopVoiceMode(); setError(setupError); return; }
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognitionRef.current?.abort();
    window.speechSynthesis?.cancel?.();
    const session = createVoiceSession({
      Recognition, locale: speechLocale,
      onListening: setIsListening,
      onDraft: setMsg,
      onFinal: (text) => sendMessage(text, true),
      onError: (message) => { stopVoiceMode(); setError(message); },
    });
    recognitionRef.current = session;
    session.start();
  }
  startListeningRef.current = startListening;

  function speakReply(text, continueVoice) {
    if (continueVoice && !voiceModeRef.current) return;
    if (!preferences.voice_auto_speak || !('speechSynthesis' in window)) {
      if (continueVoice) listenAgain();
      return;
    }
    const spokenText = text.replace(/[*_#`>-]/g, ' ').replace(/\s+/g, ' ').trim();
    const utterance = new SpeechSynthesisUtterance(spokenText);
    utterance.lang = speechLocale;
    utterance.rate = 0.98;
    const voices = window.speechSynthesis.getVoices();
    utterance.voice = voices.find((voice) => voice.lang.toLowerCase().startsWith(speechLocale.slice(0, 2).toLowerCase())) || null;
    speechRef.current = utterance;
    const isCurrent = () => mountedRef.current && speechRef.current === utterance;
    utterance.onstart = () => { if (isCurrent()) setIsSpeaking(true); };
    utterance.onend = () => { if (isCurrent()) { setIsSpeaking(false); if (continueVoice) listenAgain(); } };
    utterance.onerror = () => {
      if (!isCurrent()) return;
      stopVoiceMode();
      setError('Your browser could not play the reply aloud. The text reply is available below. Tap the mic to speak again.');
    };
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }

  async function sendMessage(overrideText = '', fromVoice = false) {
    const clean = (overrideText || msg).trim();
    if (!clean || sendingRef.current) return;
    recognitionRef.current?.abort();
    const controller = new AbortController();
    requestRef.current = controller;
    setMsg(''); setError(''); setIsSending(true); setIsListening(false); sendingRef.current = true;
    setMessages((current) => [...current, { id: `local-${Date.now()}`, role: 'user', content: clean }]);
    try {
      const result = await sendChatMessage(conversationId, clean, { signal: controller.signal });
      if (!mountedRef.current || controller.signal.aborted) return;
      setConversationId(result.conversation.id);
      setMessages((current) => [...current, { ...result.assistant_message, fallbackReason: result.fallback_reason }]);
      speakReply(result.assistant_message.content, fromVoice);
    } catch (err) {
      if (!mountedRef.current || controller.signal.aborted) return;
      stopVoiceMode();
      setMsg(clean);
      setError(err.message || 'The assistant could not respond. Please try again.');
    } finally {
      if (requestRef.current === controller) {
        requestRef.current = null;
        sendingRef.current = false;
        if (mountedRef.current) setIsSending(false);
      }
    }
  }

  function startVoiceMode() {
    if (!preferences.voice_enabled) { setError('Voice conversations are turned off in Settings.'); return; }
    const setupError = voiceSetupError(window);
    if (setupError) { setError(setupError); return; }
    voiceModeRef.current = true; setVoiceMode(true); setError('');
    // Start directly from the user's tap, preserving mobile user activation.
    startListening();
  }

  const closeChat = () => {
    stopVoiceMode(); requestRef.current?.abort(); requestRef.current = null;
    sendingRef.current = false; setIsSending(false); setMessages([]); setError('');
  };

  return (
    <>
      {(messages.length > 0 || isSending || error || voiceMode) && (
        <section className="chat-response-popover" aria-label="Harvesta AI response" aria-live="polite">
          <div className="chat-response-header"><strong>Harvesta AI</strong><button type="button" onClick={closeChat} aria-label="Close chat response"><X size={16} /></button></div>
          {voiceMode && <div className={`live-voice-state ${isListening ? 'listening' : ''} ${isSpeaking ? 'speaking' : ''}`}>
            <span className="voice-orb">{isListening ? <Waves size={25} /> : isSpeaking ? <Volume2 size={25} /> : <Loader2 size={23} className="animate-spin" />}</span>
            <div><strong>{isListening ? t('voiceListening') : isSpeaking ? t('voiceSpeaking') : isSending ? t('preparingAnswer') : 'Starting microphone…'}</strong><small>Speak naturally in {speechLocale.split('-')[0].toUpperCase()}. Browser speech may need internet.</small></div>
            <button type="button" onClick={stopVoiceMode}><MicOff size={15} />{t('endVoice')}</button>
          </div>}
          <div className="chat-response-messages">
            {messages.slice(-6).map((message) => <div key={message.id} className={`chat-response-message ${message.role === 'user' ? 'user' : 'assistant'}`}>{message.fallbackReason && <small className="chat-reply-note">Quick local guidance — the detailed AI model {message.fallbackReason === 'model_timeout' ? 'was too slow' : 'is unavailable'}.<br /></small>}{message.content}</div>)}
            {isSending && <div className="chat-response-message assistant chat-thinking"><Loader2 size={13} className="animate-spin" />{isSlow ? 'Still waiting for the server. Checking saved farm data…' : t('preparingAnswer')}</div>}
            {error && <div className="chat-response-error">{error}</div>}
          </div>
          <p>{t('aiDisclaimer')}</p>
        </section>
      )}
      <div className="chat-widget" role="search" aria-label="Ask AI assistant">
        <input ref={inputRef} type="text" className="chat-widget-input" placeholder={t('askPlaceholder')} value={msg} onChange={(event) => setMsg(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); sendMessage(); } }} maxLength={2000} disabled={isSending || voiceMode} />
        {preferences.voice_enabled && <button type="button" className={`chat-mic ${voiceMode ? 'active' : ''}`} aria-label={voiceMode ? t('endVoice') : t('startVoice')} onClick={voiceMode ? stopVoiceMode : startVoiceMode} disabled={isSending && !voiceMode}>{voiceMode ? <MicOff size={16} /> : <Mic size={16} />}</button>}
        <button type="button" className="chat-send" aria-label="Send" onClick={() => sendMessage()} disabled={!msg.trim() || isSending || voiceMode}>{isSending ? <Loader2 size={16} className="animate-spin" /> : <ArrowUp size={16} />}</button>
      </div>
    </>
  );
}
