import assert from 'node:assert/strict';
import test from 'node:test';
import { filterAnalyses, formatRecordedAt, getBackgroundTap, MAP_FOREGROUND } from '../src/utils/dashboardDetails.js';

const records = [
  { id: 1, analysis: { status: 'IRRIGATION_REQUIRED', priority: 'HIGH' } },
  { id: 2, analysis: { status: 'MONITOR', priority: 'MEDIUM' } },
  { id: 3, analysis: { status: 'NO_IRRIGATION_NEEDED', priority: 'LOW' } },
  { id: 4 },
];

test('summary filters select matching records without changing the source', () => {
  for (const [key, id] of [['irrigation_required_count', 1], ['monitor_count', 2], ['no_irrigation_needed_count', 3], ['high_priority_count', 1]]) {
    assert.deepEqual(filterAnalyses(records, key).map((r) => r.id), [id]);
  }
  assert.equal(filterAnalyses(records, 'total_analyses').length, 4);
  assert.equal(records.length, 4);
  assert.deepEqual(filterAnalyses([], 'monitor_count'), []);
});

const click = (overrides = {}) => ({
  detail: 1, button: 0, clientX: 260, clientY: 180,
  currentTarget: { getBoundingClientRect: () => ({ left: 100, top: 50, width: 600, height: 400 }) },
  target: { closest: () => null },
  ...overrides,
});
test('background taps use map-relative coordinates, including after scrolling', () => {
  assert.deepEqual(getBackgroundTap(click()), { x: 160, y: 130 });
  assert.deepEqual(getBackgroundTap(click({
    currentTarget: { getBoundingClientRect: () => ({ left: 100, top: -150, width: 600, height: 400 }) },
  })), { x: 160, y: 330 });
});
test('foreground controls and cards do not create a pulse', () => {
  assert.equal(getBackgroundTap(click({ target: { closest: () => ({}) } })), null);
  for (const selector of ['button', 'a', '.topbar', '.metric-mini', '.health-score-pill', '.crop-scroller', '.farmer-card']) {
    assert.ok(MAP_FOREGROUND.split(', ').includes(selector));
  }
});
test('keyboard, right clicks and taps outside the map do not create a pulse', () => {
  assert.equal(getBackgroundTap(click({ detail: 0 })), null);
  assert.equal(getBackgroundTap(click({ button: 2 })), null);
  assert.equal(getBackgroundTap(click({ clientY: 451 })), null);
  assert.equal(getBackgroundTap(click({ clientX: 90 })), null);
});
test('missing timestamps stay unavailable and backend timestamps are read as UTC', () => {
  assert.equal(formatRecordedAt(null), 'Not recorded');
  assert.equal(formatRecordedAt('bad-date'), 'Not recorded');
  assert.equal(formatRecordedAt('2026-08-31T10:30:00'), formatRecordedAt('2026-08-31T10:30:00Z'));
});
