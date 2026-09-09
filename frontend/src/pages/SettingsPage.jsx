import { useEffect, useReducer } from 'react';
import { Bell, CheckCircle2, Languages, LayoutPanelTop, Loader2, Moon, Palette, Save, Sparkles, Sun, Volume2 } from 'lucide-react';
import { getAppPreferences, updateAppPreferences } from '../services/api';
import { LANGUAGES, usePreferences } from '../context/PreferencesContext';
import { accountFormReducer, createAccountForm, hasUnsavedChanges, preferenceFields } from '../utils/accountForms';

function Toggle({ checked, onChange, label, description }) {
  return (
    <label className="setting-toggle-row">
      <span>
        <strong>{label}</strong>
        {description && <small>{description}</small>}
      </span>
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span className="harvesta-switch" aria-hidden="true" />
    </label>
  );
}

export default function SettingsPage({ onNavigate }) {
  const { preferences, updateLocalPreferences, t } = usePreferences();
  const [form, dispatch] = useReducer(accountFormReducer, preferenceFields(preferences), createAccountForm);
  const { draft, error } = form;
  const isLoading = form.phase === 'loading';
  const isSaving = form.phase === 'saving';
  const isDirty = hasUnsavedChanges(form);

  useEffect(() => {
    let active = true;
    getAppPreferences()
      .then((data) => {
        if (!active) return;
        updateLocalPreferences(data);
        dispatch({ type: 'loaded', value: preferenceFields(data) });
      })
      .catch((err) => active && dispatch({ type: 'failed', error: err.message || 'Could not load settings. Please reload the page.' }));
    return () => { active = false; };
  }, [updateLocalPreferences]);

  const change = (key, value) => {
    dispatch({ type: 'change', key, value });
  };

  const save = async () => {
    if (!form.loaded || !isDirty || isSaving) return;
    dispatch({ type: 'saving' });
    try {
      const saved = await updateAppPreferences(preferenceFields(draft));
      updateLocalPreferences(saved);
      dispatch({ type: 'saved', value: preferenceFields(saved) });
    } catch (err) {
      dispatch({ type: 'failed', error: err.message || 'Could not save settings. Your previous settings are still active.' });
    }
  };

  return (
    <div className="page-shell utility-page">
      <header className="utility-header">
        <div>
          <span className="eyebrow-text">{t('preferences')}</span>
          <h1><Palette size={26} /> {t('settings')}</h1>
          <p>{t('settingsIntro')}</p>
        </div>
        <button type="button" className="btn-primary" onClick={save} disabled={isSaving || !form.loaded || !isDirty}>
          {isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
          {isSaving ? t('saving') : t('saveChanges')}
        </button>
      </header>

      {form.success && <div className="status-banner success" role="status"><CheckCircle2 size={17} />{t('saved')}</div>}
      {error && <div className="status-banner error" role="alert">{error}</div>}
      {isDirty && <div className="account-save-notice" role="status"><span>Unsaved changes. They apply only after you press Save changes.</span><button type="button" className="btn-secondary" disabled={isSaving} onClick={() => dispatch({ type: 'discard' })}>Discard changes</button></div>}

      {isLoading ? (
        <div className="analytic-card utility-loading"><Loader2 className="animate-spin" /> {t('loadingSettings')}</div>
      ) : (
        <fieldset className="settings-grid account-form-fields" disabled={isSaving || !form.loaded}>
          <section className="analytic-card settings-section settings-section-wide">
            <div className="section-heading"><Languages size={20} /><div><h2>{t('language')}</h2><p>{t('languageDesc')}</p></div></div>
            <div className="language-grid">
              {LANGUAGES.map((language) => (
                <button
                  type="button"
                  key={language.code}
                  className={`language-option ${draft.language === language.code ? 'selected' : ''}`}
                  aria-pressed={draft.language === language.code}
                  onClick={() => change('language', language.code)}
                >
                  <span>{language.nativeLabel}</span><small>{language.label}</small>
                </button>
              ))}
            </div>
          </section>

          <section className="analytic-card settings-section">
            <div className="section-heading"><Sun size={20} /><div><h2>{t('appearance')}</h2><p>{t('appearanceDesc')}</p></div></div>
            <div className="segmented-choice">
              {[
                ['light', t('light'), Sun], ['dark', t('dark'), Moon], ['system', t('system'), Sparkles],
              ].map(([value, label, Icon]) => (
                <button type="button" key={value} className={draft.theme === value ? 'active' : ''} aria-pressed={draft.theme === value} onClick={() => change('theme', value)}>
                  <Icon size={16} />{label}
                </button>
              ))}
            </div>
            <Toggle checked={draft.compact_mode} onChange={(value) => change('compact_mode', value)} label={t('compactLayout')} description={t('compactDesc')} />
            <Toggle checked={draft.reduce_motion} onChange={(value) => change('reduce_motion', value)} label={t('reduceMotion')} description={t('reduceMotionDesc')} />
          </section>

          <section className="analytic-card settings-section">
            <div className="section-heading"><Volume2 size={20} /><div><h2>{t('voiceAssistant')}</h2><p>{t('voiceDesc')}</p></div></div>
            <Toggle checked={draft.voice_enabled} onChange={(value) => change('voice_enabled', value)} label={t('enableVoice')} />
            <Toggle checked={draft.voice_auto_speak} onChange={(value) => change('voice_auto_speak', value)} label={t('autoSpeak')} />
          </section>

          <section className="analytic-card settings-section settings-link-card">
            <div className="section-heading"><Bell size={20} /><div><h2>{t('notificationSettings')}</h2><p>{t('alertEmailDesc')}</p></div></div>
            <button type="button" className="btn-secondary" onClick={() => onNavigate('notification-settings')}>{t('openNotificationSettings')}</button>
          </section>

          <section className="analytic-card settings-section settings-link-card">
            <div className="section-heading"><LayoutPanelTop size={20} /><div><h2>{t('accountProfile')}</h2><p>{t('accountProfileDesc')}</p></div></div>
            <button type="button" className="btn-secondary" onClick={() => onNavigate('profile')}>{t('profile')}</button>
          </section>
        </fieldset>
      )}
    </div>
  );
}
