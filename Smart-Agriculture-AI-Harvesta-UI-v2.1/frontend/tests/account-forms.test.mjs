import test from 'node:test';
import assert from 'node:assert/strict';
import { accountFormReducer as reduce, avatarStyle, createAccountForm, hasUnsavedChanges, normalizeProfile, preferenceFields, profilePayload, savedAppearance } from '../src/utils/accountForms.js';

const ready = (value) => reduce(createAccountForm(value), { type: 'loaded', value });
test('settings selections change only the draft until successful Save', () => {
  const original = { language: 'en', theme: 'light' };
  const changed = reduce(ready(original), { type: 'change', key: 'theme', value: 'dark' });
  assert.equal(changed.draft.theme, 'dark');
  assert.equal(changed.saved.theme, 'light');
  assert.equal(original.theme, 'light');
  assert.equal(hasUnsavedChanges(changed), true);
  const committed = reduce(changed, { type: 'saved', value: changed.draft });
  assert.equal(committed.saved.theme, 'dark');
  assert.equal(committed.success, true);
  assert.equal(hasUnsavedChanges(committed), false);
});
test('failed Save retains saved settings and keeps the draft for retry', () => {
  let form = reduce(ready({ theme: 'light' }), { type: 'change', key: 'theme', value: 'dark' });
  form = reduce(form, { type: 'saving' });
  form = reduce(form, { type: 'failed', error: 'Network unavailable' });
  assert.equal(form.saved.theme, 'light');
  assert.equal(form.draft.theme, 'dark');
  assert.equal(form.success, false);
  assert.equal(form.error, 'Network unavailable');
});
test('Discard restores saved values, and editing while saving is ignored', () => {
  const changed = reduce(ready({ theme: 'light' }), { type: 'change', key: 'theme', value: 'dark' });
  assert.equal(reduce(changed, { type: 'discard' }).draft.theme, 'light');
  const saving = reduce(changed, { type: 'saving' });
  assert.equal(reduce(saving, { type: 'change', key: 'theme', value: 'system' }), saving);
});
test('profile summary colour stays saved until Save completes', () => {
  const profile = normalizeProfile({ full_name: 'Farmer', avatar_color: '#A6BC12' });
  const changed = reduce(ready(profile), { type: 'change', key: 'avatar_color', value: '#112233' });
  assert.equal(avatarStyle(changed.saved.avatar_color).background, '#A6BC12');
  assert.equal(profilePayload(changed.draft).avatar_color, '#112233');
  const saved = reduce(changed, { type: 'saved', value: changed.draft });
  assert.equal(avatarStyle(saved.saved.avatar_color).background, '#112233');
});
test('profile normalization prevents null-controlled inputs and sends only editable fields', () => {
  const profile = normalizeProfile({ full_name: ' Farmer ', phone: null, bio: null, experience_years: 0, role: 'admin', id: 99 });
  assert.equal(profile.phone, '');
  assert.equal(profile.bio, '');
  const payload = profilePayload(profile);
  assert.equal(payload.full_name, 'Farmer');
  assert.equal(payload.experience_years, 0);
  assert.equal(payload.phone, null);
  assert.equal('role' in payload, false);
  assert.equal('id' in payload, false);
});
test('app avatar updates cannot replace user identity or role', () => {
  const user = { id: 2, role: 'farmer', email: 'farmer@example.test', is_verified: true };
  const updated = savedAppearance(user, { id: 9, role: 'admin', full_name: 'Farmer', avatar_color: '#123456' });
  assert.equal(updated.id, 2);
  assert.equal(updated.role, 'farmer');
  assert.equal(updated.avatar_color, '#123456');
});
test('avatar colours keep readable text and reject invalid CSS', () => {
  assert.equal(avatarStyle('#000000').color, '#FFFFFF');
  assert.equal(avatarStyle('#FFFFFF').color, '#000000');
  assert.equal(avatarStyle('url(example)').background, '#A6BC12');
});
test('load failure cannot enable a form that never loaded', () => {
  const form = reduce(createAccountForm({ theme: 'light' }), { type: 'failed', error: 'Offline' });
  assert.equal(form.loaded, false);
  assert.equal(reduce(form, { type: 'change', key: 'theme', value: 'dark' }), form);
  assert.equal('updated_at' in preferenceFields({ theme: 'light', updated_at: 'not-editable' }), false);
});
