import { useEffect, useReducer } from 'react';
import { BadgeCheck, CalendarDays, Loader2, Mail, MapPin, Save, ShieldCheck, UserRound } from 'lucide-react';
import { getProfile, updateProfile } from '../services/api';
import { usePreferences } from '../context/PreferencesContext';
import { accountFormReducer, avatarStyle, createAccountForm, hasUnsavedChanges, normalizeProfile, profilePayload } from '../utils/accountForms';

export default function ProfilePage({ user, onProfileUpdated }) {
  const { t } = usePreferences();
  const [form, dispatch] = useReducer(accountFormReducer, normalizeProfile(user || {}), createAccountForm);
  const profile = form.draft;
  const savedProfile = form.saved;
  const isLoading = form.phase === 'loading';
  const isSaving = form.phase === 'saving';
  const isDirty = hasUnsavedChanges(form);
  const error = form.error;

  useEffect(() => {
    let active = true;
    getProfile()
      .then((data) => active && dispatch({ type: 'loaded', value: normalizeProfile(data) }))
      .catch((err) => active && dispatch({ type: 'failed', error: err.message || 'Could not load profile. Please reload the page.' }));
    return () => { active = false; };
  }, []);

  const set = (key) => (event) => dispatch({ type: 'change', key, value: event.target.value });
  const save = async (event) => {
    event.preventDefault();
    if (!form.loaded || !isDirty || isSaving) return;
    dispatch({ type: 'saving' });
    try {
      const saved = await updateProfile(profilePayload(profile));
      dispatch({ type: 'saved', value: normalizeProfile(saved) });
      onProfileUpdated?.(saved);
    } catch (err) {
      dispatch({ type: 'failed', error: err.message || 'Could not save profile. Your previous profile is unchanged.' });
    }
  };

  const initials = (savedProfile.full_name || savedProfile.email || 'F').split(' ').map((part) => part[0]).join('').slice(0, 2).toUpperCase();

  return (
    <div className="page-shell utility-page">
      <header className="utility-header">
        <div><span className="eyebrow-text">{t('profile')}</span><h1><UserRound size={26} /> {t('profileTitle')}</h1><p>{t('profileIntro')}</p></div>
      </header>
      {form.success && <div className="status-banner success" role="status"><BadgeCheck size={17} />{t('saved')}</div>}
      {error && <div className="status-banner error" role="alert">{error}</div>}
      {isLoading ? <div className="analytic-card utility-loading"><Loader2 className="animate-spin" /> {t('loadingProfile')}</div> : (
        <form onSubmit={save}>
          <fieldset className="profile-layout account-form-fields" disabled={isSaving || !form.loaded}>
          <aside className="analytic-card profile-summary">
            <div className="profile-avatar-large" style={avatarStyle(savedProfile.avatar_color)}>{initials}</div>
            <h2>{savedProfile.full_name}</h2><p>{savedProfile.email}</p>
            <div className="profile-fact"><BadgeCheck size={16} /><span><strong>{t('verified')}</strong><small>Gmail verified</small></span></div>
            <div className="profile-fact"><ShieldCheck size={16} /><span><strong>{t('accountRole')}</strong><small>{profile.role === 'admin' ? t('admin') : t('farmer')}</small></span></div>
            <div className="profile-fact"><CalendarDays size={16} /><span><strong>{t('memberSince')}</strong><small>{profile.member_since ? new Date(profile.member_since).toLocaleDateString() : '—'}</small></span></div>
            <label className="avatar-colour"><span>{t('profileColour')}</span><input type="color" value={profile.avatar_color} onChange={set('avatar_color')} /></label>
            {isDirty && <small className="muted">Your new colour and details apply after Save changes.</small>}
          </aside>
          <section className="analytic-card profile-form-card">
            <div className="profile-form-grid">
              <label><span>{t('fullName')}</span><input className="harvesta-input" value={profile.full_name} onChange={set('full_name')} required minLength={2} /></label>
              <label><span>{t('email')}</span><div className="input-with-icon"><Mail size={16} /><input className="harvesta-input" value={profile.email || ''} disabled /></div></label>
              <label><span>{t('phone')}</span><input className="harvesta-input" value={profile.phone} onChange={set('phone')} placeholder="+91 …" /></label>
              <label><span>{t('primaryCrop')}</span><input className="harvesta-input" value={profile.primary_crop} onChange={set('primary_crop')} placeholder="e.g. Tomato" /></label>
              <label><span>{t('experience')}</span><input className="harvesta-input" type="number" min="0" max="100" value={profile.experience_years} onChange={set('experience_years')} /></label>
              <label><span>{t('district')}</span><input className="harvesta-input" value={profile.district} onChange={set('district')} /></label>
              <label><span>{t('state')}</span><input className="harvesta-input" value={profile.state} onChange={set('state')} /></label>
              <label><span>{t('country')}</span><input className="harvesta-input" value={profile.country} onChange={set('country')} placeholder="India" /></label>
              <label className="span-all"><span>{t('address')}</span><div className="input-with-icon"><MapPin size={16} /><input className="harvesta-input" value={profile.address} onChange={set('address')} /></div></label>
              <label className="span-all"><span>{t('bio')}</span><textarea className="harvesta-input" rows="4" value={profile.bio} onChange={set('bio')} placeholder={t('profileBioHint')} /></label>
            </div>
            <div className="form-actions account-save-actions">
              <span role="status">{isSaving ? t('saving') : error || (form.success ? t('saved') : isDirty ? 'Unsaved changes' : '')}</span>
              {isDirty && <button type="button" className="btn-secondary" onClick={() => dispatch({ type: 'discard' })}>Discard changes</button>}
              <button type="submit" className="btn-primary" disabled={isSaving || !form.loaded || !isDirty}>{isSaving ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}{isSaving ? t('saving') : t('saveChanges')}</button>
            </div>
          </section>
          </fieldset>
        </form>
      )}
    </div>
  );
}
