export const PROFILE_DEFAULTS = {
  full_name: '', phone: '', address: '', district: '', state: '', country: '', bio: '',
  primary_crop: '', experience_years: '', avatar_color: '#A6BC12',
};

export function normalizeProfile(data = {}) {
  const result = { ...data };
  for (const [key, fallback] of Object.entries(PROFILE_DEFAULTS)) {
    result[key] = data[key] ?? fallback;
  }
  return result;
}

export function profilePayload(draft) {
  const result = {};
  for (const key of Object.keys(PROFILE_DEFAULTS)) {
    result[key] = draft[key] === '' ? null : draft[key];
  }
  result.full_name = draft.full_name.trim();
  result.experience_years = draft.experience_years === '' ? null : Number(draft.experience_years);
  return result;
}

const PREFERENCE_KEYS = ['language', 'theme', 'compact_mode', 'reduce_motion', 'voice_enabled', 'voice_auto_speak'];
export function preferenceFields(data) {
  return Object.fromEntries(PREFERENCE_KEYS.map((key) => [key, data[key]]));
}

export function createAccountForm(value) {
  return { saved: value, draft: value, phase: 'loading', error: '', success: false, loaded: false };
}

export function accountFormReducer(state, action) {
  switch (action.type) {
    case 'loaded':
    case 'saved':
      return { saved: action.value, draft: action.value, phase: 'ready', loaded: true, error: '', success: action.type === 'saved' };
    case 'change':
      if (!state.loaded || state.phase === 'saving') return state;
      return { ...state, draft: { ...state.draft, [action.key]: action.value }, error: '', success: false };
    case 'saving':
      return { ...state, phase: 'saving', error: '', success: false };
    case 'failed':
      return { ...state, phase: 'ready', error: action.error, success: false };
    case 'discard':
      return { ...state, draft: state.saved, error: '', success: false };
    default:
      return state;
  }
}

export function hasUnsavedChanges(state) {
  return Object.keys(state.draft).some((key) => state.draft[key] !== state.saved[key]);
}

export function savedAppearance(user, profile) {
  // A profile response must never overwrite identity, verification or role.
  return { ...user, full_name: profile.full_name, avatar_color: profile.avatar_color };
}

export function avatarStyle(colour) {
  const background = /^#[0-9a-f]{6}$/i.test(colour || '') ? colour : '#A6BC12';
  const rgb = [1, 3, 5].map((start) => parseInt(background.slice(start, start + 2), 16) / 255);
  const linear = rgb.map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4);
  const luminance = .2126 * linear[0] + .7152 * linear[1] + .0722 * linear[2];
  return { background, color: luminance > .179 ? '#000000' : '#FFFFFF' };
}
