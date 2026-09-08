import { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { LogOut, Settings, UserRound, X } from 'lucide-react';
import { avatarStyle } from '../utils/accountForms';

export function UserProfile({ user, onLogout, onNavigate }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    if (!isOpen) return undefined;
    const closeOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) setIsOpen(false);
    };
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setIsOpen(false);
    };
    document.addEventListener('pointerdown', closeOutside);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('pointerdown', closeOutside);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [isOpen]);

  if (!user) return null;

  const initial = (user.full_name || user.email || 'F').charAt(0).toUpperCase();
  const navigate = (view) => {
    setIsOpen(false);
    onNavigate?.(view);
  };

  return (
    <div className="dashboard-user-profile" ref={menuRef}>
      <div className="desktop-user-profile flex items-center gap-3 p-2 pr-3 rounded-2xl bg-white/80 backdrop-blur-sm border border-black/5 shadow-soft">
        <div
          className="w-9 h-9 rounded-xl flex items-center justify-center font-bold text-sm"
          style={avatarStyle(user.avatar_color)}
        >
          {initial}
        </div>
        <div className="flex flex-col leading-tight pr-1">
          <span className="text-[13px] font-semibold text-ink-900 truncate max-w-[140px]">
            {user.full_name || 'Farmer Account'}
          </span>
          <span className="text-[11px] text-ink-500 truncate max-w-[140px]">
            {user.email}
          </span>
        </div>
        <button
          type="button"
          onClick={onLogout}
          title="Sign out"
          aria-label="Sign out"
          className="w-9 h-9 rounded-xl flex items-center justify-center text-ink-500 hover:text-red-600 hover:bg-red-50 transition-colors"
        >
          <LogOut size={16} />
        </button>
      </div>

      <button
        type="button"
        className="mobile-profile-trigger"
        style={avatarStyle(user.avatar_color)}
        onClick={() => setIsOpen((open) => !open)}
        title="Account menu"
        aria-label="Open account menu"
        aria-expanded={isOpen}
        aria-haspopup="menu"
      >
        {initial}
      </button>

      {isOpen && (
        <div className="mobile-account-menu" role="menu" aria-label="Account options">
          <div className="mobile-account-head">
            <div>
              <strong>{user.full_name || 'Farmer Account'}</strong>
              <span>{user.email}</span>
            </div>
            <button type="button" onClick={() => setIsOpen(false)} aria-label="Close account menu"><X size={17} /></button>
          </div>
          <button type="button" role="menuitem" onClick={() => navigate('profile')}><UserRound size={17} />Profile</button>
          <button type="button" role="menuitem" onClick={() => navigate('settings')}><Settings size={17} />Settings</button>
          <button type="button" role="menuitem" className="danger" onClick={() => { setIsOpen(false); onLogout(); }}><LogOut size={17} />Sign out</button>
        </div>
      )}
    </div>
  );
}

UserProfile.propTypes = {
  user: PropTypes.shape({
    email: PropTypes.string,
    full_name: PropTypes.string,
    avatar_color: PropTypes.string,
  }),
  onLogout: PropTypes.func.isRequired,
  onNavigate: PropTypes.func,
};

export default UserProfile;
