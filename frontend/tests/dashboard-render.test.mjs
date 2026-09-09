import test from 'node:test';
import assert from 'node:assert/strict';
import { createElement as h } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { createServer } from 'vite';
import react from '@vitejs/plugin-react';

test('dashboard views and detail content render without contacting the backend', async (t) => {
  const vite = await createServer({
    configFile: false, envDir: false, appType: 'custom',
    cacheDir: 'node_modules/.vite-render-tests',
    optimizeDeps: { noDiscovery: true, include: [] },
    server: { middlewareMode: true, hmr: false },
    plugins: [react()],
  });
  try {
    const { default: Dashboard } = await vite.ssrLoadModule('/src/pages/Dashboard.jsx');
    const { PreferencesProvider } = await vite.ssrLoadModule('/src/context/PreferencesContext.jsx');
    const { default: Details } = await vite.ssrLoadModule('/src/components/DashboardDetails.jsx');
    const { default: Equipment } = await vite.ssrLoadModule('/src/pages/EquipmentPage.jsx');
    const { default: UserProfile } = await vite.ssrLoadModule('/src/components/UserProfile.jsx');
    const { default: AppNav } = await vite.ssrLoadModule('/src/components/AppNav.jsx');
    const { default: SettingsPage } = await vite.ssrLoadModule('/src/pages/SettingsPage.jsx');
    const { default: ProfilePage } = await vite.ssrLoadModule('/src/pages/ProfilePage.jsx');
    const props = { user: { full_name: 'Test Farmer', email: 'farmer@example.test' }, onLogout() {}, onNavigate() {} };
    const renderView = (view) => renderToStaticMarkup(h(PreferencesProvider, null, h(Dashboard, { ...props, view })));

    await t.test('saved avatar colour appears in both sidebar and dashboard header', () => {
      const user = { ...props.user, avatar_color: '#112233' };
      const header = renderToStaticMarkup(h(UserProfile, { user, onLogout() {} }));
      const sidebar = renderToStaticMarkup(h(PreferencesProvider, null, h(AppNav, { user, active: 'dashboard', onNavigate() {} })));
      assert.match(header, /background:#112233;color:#FFFFFF/);
      assert.match(sidebar, /background:#112233;color:#FFFFFF/);
    });
    await t.test('settings and profile render safely while saved values load', () => {
      for (const Page of [SettingsPage, ProfilePage]) {
        const output = renderToStaticMarkup(h(PreferencesProvider, null, h(Page, { user: props.user, onNavigate() {} })));
        assert.match(output, /utility-loading/);
      }
    });

    await t.test('overview retains the map and cards but not analysis forms or history', () => {
      const output = renderView('overview');
      assert.match(output, /hero-map dashboard-tap-surface/);
      assert.match(output, /NPK Levels/);
      assert.match(output, /Soil Moisture/);
      assert.doesNotMatch(output, /id="ai-workspace"/);
      assert.doesNotMatch(output, /Recent Field Analyses/);
      assert.ok((output.match(/aria-haspopup="dialog"/g) || []).length >= 6);
    });
    await t.test('analysis is a separate view with forms and a return button', () => {
      const output = renderView('analysis');
      assert.match(output, /id="ai-workspace"/);
      assert.match(output, /Analyze Field/);
      assert.match(output, /Show saved analyses/);
      assert.doesNotMatch(output, /hero-map dashboard-tap-surface/);
    });
    await t.test('climate and equipment do not render the overview', () => {
      const climate = renderView('climate');
      assert.match(climate, />Climate</);
      assert.doesNotMatch(climate, /hero-map dashboard-tap-surface/);
      const equipment = renderToStaticMarkup(h(PreferencesProvider, null, h(Equipment, { onNavigate() {} })));
      assert.match(equipment, />Equipment</);
      assert.doesNotMatch(equipment, /hero-map dashboard-tap-surface/);
    });
    await t.test('all detail types explain missing data without invented readings', () => {
      for (const type of ['area', 'location', 'npk', 'humidity', 'soil', 'health', 'recommendation', 'loss']) {
        const output = renderToStaticMarkup(h(Details, { type, location: { status: 'unavailable' }, onLocate() {}, onNavigate() {} }));
        assert.ok(output.includes('dashboard-detail-body'), type);
        assert.doesNotMatch(output, /undefined|NaN/);
      }
    });
    await t.test('location separates device GPS from saved farm address', () => {
      const output = renderToStaticMarkup(h(Details, {
        type: 'location', location: { status: 'ready', latitude: 10.5, longitude: 77.5, label: 'GPS 10.5, 77.5', accuracy: 25 },
        farm: { location: 'Saved farm location' }, onLocate() {}, onNavigate() {},
      }));
      assert.match(output, /query=10.5,77.5/);
      assert.match(output, /Saved farm location/);
      assert.match(output, /not necessarily the location of your farm/);
    });
  } finally {
    await vite.close();
  }
});
