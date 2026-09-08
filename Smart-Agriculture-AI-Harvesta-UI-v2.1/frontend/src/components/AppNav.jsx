import { useState } from 'react';
import PropTypes from 'prop-types';
import {
  Leaf,
  LayoutGrid,
  Sprout,
  Tractor,
  CloudSun,
  BellRing,
  Package,
  FileBarChart,
  HelpCircle,
  Settings,
  ShieldCheck,
  Camera,
  Menu,
  UserRound,
  X,
} from 'lucide-react';
import { usePreferences } from '../context/PreferencesContext';
import { avatarStyle } from '../utils/accountForms';

const NAV_ITEMS = [
  { view: 'dashboard', id: 'dashboard', labelKey: 'dashboard', icon: LayoutGrid },
  { view: 'my-farm', id: 'my-farm', labelKey: 'fields', icon: Sprout, hasDot: true },
  { view: 'disease-scan', id: 'disease-scan', labelKey: 'diseaseScan', icon: Camera },
  { view: 'equipment', id: 'equipment', labelKey: 'equipment', icon: Tractor },
  { view: 'climate', id: 'climate', labelKey: 'climate', icon: CloudSun },
  { view: 'notifications', id: 'alerts', labelKey: 'alerts', icon: BellRing },
  { view: 'inventory', id: 'inventory', labelKey: 'inventory', icon: Package },
  { view: 'reports', id: 'reports', labelKey: 'reports', icon: FileBarChart },
];

const FOOTER_ITEMS = [
  { view: 'help', id: 'help', labelKey: 'help', icon: HelpCircle },
  { view: 'settings', id: 'settings', labelKey: 'settings', icon: Settings },
];

export function AppNav({ active, onNavigate, user }) {
  const { t } = usePreferences();
  const [moreOpen, setMoreOpen] = useState(false);
  const go = (view) => () => { setMoreOpen(false); onNavigate(view); };
  const initials = (user?.full_name || user?.email || 'Aanya Sharma')
    .split(' ')
    .map((s) => s[0])
    .join('')
    .slice(0, 2)
    .toUpperCase();
  const displayName = user?.full_name?.split(' ')[0] || 'Aanya';
  const isAdmin = user?.role === 'admin';

  return (
    <>
      <aside className="harvesta-sidebar" aria-label="Primary navigation">
        {/* Brand */}
        <button
          type="button"
          onClick={go('dashboard')}
          className="brand-block"
          title="Harvesta — Smart Agriculture AI"
          aria-label="Harvesta home"
        >
          <span className="brand-mark-circle">
            <Leaf size={18} strokeWidth={2.6} />
          </span>
          <span className="brand-word">Harvesta</span>
          <span className="brand-version-badge" title="Harvesta UI v2.1 — official version">v2.1</span>
        </button>

        {/* Primary nav */}
        <nav className="nav-list">
          {NAV_ITEMS.map((item, idx) => {
            const Icon = item.icon;
            const isActive = active === item.id || (active === 'dashboard' && idx === 0);
            return (
              <button
                key={idx}
                type="button"
                className={`nav-row ${isActive ? 'active' : ''}`}
                onClick={go(item.view)}
              >
                <span className="nav-row-ico">
                  <Icon size={18} strokeWidth={2} />
                  {item.hasDot && <span className="nav-dot" />}
                  {item.badge && <span className="nav-badge">{item.badge}</span>}
                </span>
                <span className="nav-row-label">{t(item.labelKey)}</span>
              </button>
            );
          })}

          {/* Admin Navigation Button (Only visible to verified admins) */}
          {isAdmin && (
            <button
              type="button"
              className={`nav-row ${active === 'admin' ? 'active' : ''}`}
              onClick={go('admin')}
              style={{ marginTop: 8, background: active === 'admin' ? 'var(--c-emerald-50)' : 'rgba(139, 92, 246, 0.08)', color: active === 'admin' ? 'var(--c-emerald-800)' : '#7c3aed' }}
              title={t('adminPortal')}
            >
              <span className="nav-row-ico">
                <ShieldCheck size={18} strokeWidth={2.2} />
              </span>
              <span className="nav-row-label" style={{ fontWeight: 700 }}>{t('adminPortal')}</span>
            </button>
          )}
        </nav>

        <div className="sidebar-spacer" />

        {/* Footer: Help + Settings + User */}
        <nav className="nav-list nav-list-footer" aria-label="Secondary">
          {FOOTER_ITEMS.map((item, idx) => {
            const Icon = item.icon;
            return (
              <button
                key={idx}
                type="button"
                className={`nav-row ${active === item.id ? 'active' : ''}`}
                onClick={go(item.view)}
                title={t(item.labelKey)}
                aria-label={t(item.labelKey)}
              >
                <span className="nav-row-ico">
                  <Icon size={18} strokeWidth={2} />
                </span>
                <span className="nav-row-label">{t(item.labelKey)}</span>
              </button>
            );
          })}
        </nav>

        <button type="button" className={`sidebar-user ${active === 'profile' ? 'active' : ''}`} onClick={go('profile')} title={t('profile')}>
          <span className="sidebar-avatar" style={avatarStyle(user?.avatar_color)}>{initials}</span>
          <div className="sidebar-user-meta">
            <span className="sidebar-user-name">{displayName}</span>
            <span className="sidebar-user-role" style={{ color: isAdmin ? '#7c3aed' : 'var(--c-ink-400)', fontWeight: isAdmin ? 700 : 400 }}>
              {isAdmin ? t('admin') : t('farmer')}
            </span>
          </div>
        </button>
      </aside>

      {/* Mobile bottom navigation fallback — icon-only */}
      <nav className="mobile-bottom-nav" aria-label="Primary">
        {NAV_ITEMS.filter((item) => ['dashboard', 'my-farm', 'disease-scan', 'alerts'].includes(item.id)).map((item, idx) => {
          const Icon = item.icon;
          const isActive = active === item.id;
          return (
            <button
              key={idx}
              type="button"
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={go(item.view)}
              aria-label={t(item.labelKey)}
            >
              <Icon size={20} strokeWidth={2} />
            </button>
          );
        })}
        <button type="button" className={`nav-item ${moreOpen || ['inventory', 'reports', 'settings', 'help', 'profile', 'admin', 'equipment', 'climate'].includes(active) ? 'active' : ''}`} onClick={() => setMoreOpen((open) => !open)} aria-label="More"><Menu size={20} /></button>
      </nav>
      {moreOpen && <div className="mobile-more-sheet" role="dialog" aria-label="More navigation">
        <div className="mobile-more-head"><strong>Harvesta</strong><button type="button" onClick={() => setMoreOpen(false)} aria-label="Close"><X size={18} /></button></div>
        <div className="mobile-more-grid">
          {[
            { view: 'equipment', key: 'equipment', icon: Tractor }, { view: 'climate', key: 'climate', icon: CloudSun },
            { view: 'inventory', key: 'inventory', icon: Package }, { view: 'reports', key: 'reports', icon: FileBarChart },
            { view: 'profile', key: 'profile', icon: UserRound }, { view: 'settings', key: 'settings', icon: Settings },
            { view: 'help', key: 'help', icon: HelpCircle }, ...(isAdmin ? [{ view: 'admin', key: 'adminPortal', icon: ShieldCheck }] : []),
          ].map((item) => {
            const Icon = item.icon;
            return <button type="button" key={item.view} className={active === item.view ? 'active' : ''} onClick={go(item.view)}><Icon size={19} /><span>{t(item.key)}</span></button>;
          })}
        </div>
      </div>}
    </>
  );
}

AppNav.propTypes = {
  active: PropTypes.string.isRequired,
  onNavigate: PropTypes.func.isRequired,
  user: PropTypes.object,
};

export default AppNav;
