import { useState, useEffect, useCallback } from 'react';
import { getAuthToken, clearAuthToken, getMe, getProfile, getAppPreferences, login, signup, logout, sendSessionHeartbeat } from './services/api';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Signup from './pages/Signup';
import VerifyEmail from './pages/VerifyEmail';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import MyFarm from './pages/MyFarm';
import FarmForm from './pages/FarmForm';
import CropForm from './pages/CropForm';
import CropDetail from './pages/CropDetail';
import AdminDashboard from './pages/AdminDashboard';
import Notifications from './pages/Notifications';
import NotificationSettings from './pages/NotificationSettings';
import DiseaseScan from './pages/DiseaseScan';
import SettingsPage from './pages/SettingsPage';
import ProfilePage from './pages/ProfilePage';
import InventoryPage from './pages/InventoryPage';
import ReportsPage from './pages/ReportsPage';
import HelpPage from './pages/HelpPage';
import EquipmentPage from './pages/EquipmentPage';
import AppNav from './components/AppNav';
import { Leaf, Loader2 } from 'lucide-react';
import { usePreferences } from './context/PreferencesContext';
import { savedAppearance } from './utils/accountForms';

async function loadUserAppearance(user) {
  try { return savedAppearance(user, await getProfile()); }
  catch { return user; }
}

function App() {
  const { updateLocalPreferences } = usePreferences();
  const [user, setUser] = useState(null);
  const [authView, setAuthView] = useState('login');
  const [isAuthInitializing, setIsAuthInitializing] = useState(true);

  const [route, setRoute] = useState({ view: 'dashboard', params: {} });

  const navigate = useCallback((view, params = {}) => {
    setRoute({ view, params });
    window.scrollTo({ top: 0 });
  }, []);

  const initUserSession = useCallback(async () => {
    const currentPath = window.location.pathname.replace(/\/+$/, '');

    if (currentPath.endsWith('/forgot-password')) {
      setAuthView('forgot');
    } else if (currentPath.endsWith('/reset-password') && window.location.search.includes('token=')) {
      setAuthView('reset');
    } else if (window.location.search.includes('token=')) {
      setAuthView('verify');
    }

    const token = getAuthToken();
    if (!token) {
      setUser(null);
      setIsAuthInitializing(false);
      return;
    }

    try {
      const userData = await getMe();
      setUser(await loadUserAppearance(userData));
    } catch (err) {
      console.warn('Session verification failed:', err.message);
      clearAuthToken();
      setUser(null);
    } finally {
      setIsAuthInitializing(false);
    }
  }, []);

  useEffect(() => {
    initUserSession();
  }, [initUserSession]);

  useEffect(() => {
    if (!user?.is_verified) return;
    getAppPreferences().then(updateLocalPreferences).catch(() => {});
  }, [user?.id, user?.is_verified, updateLocalPreferences]);

  useEffect(() => {
    if (!user?.is_verified) return undefined;

    const heartbeat = () => {
      if (document.visibilityState === 'visible') {
        sendSessionHeartbeat(route.view).catch(() => {});
      }
    };
    heartbeat();
    const intervalId = window.setInterval(heartbeat, 5 * 60 * 1000);
    document.addEventListener('visibilitychange', heartbeat);
    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener('visibilitychange', heartbeat);
    };
  }, [user?.is_verified, route.view]);

  const handleLoginSubmit = async (credentials) => {
    const data = await login(credentials);
    setUser(await loadUserAppearance(data.user));
  };

  const handleSignupSuccess = async (credentials) => {
    const data = await signup(credentials);
    return data;
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      clearAuthToken();
    }
    setUser(null);
    setAuthView('login');
  };

  const switchAuthView = (view) => {
    setAuthView(view);
    window.history.replaceState({}, document.title, '/');
  };

  if (isAuthInitializing) {
    return (
      <div className="center-loading">
        <div className="auth-card-h" style={{ maxWidth: 380, textAlign: 'center' }}>
          <div className="brand-ring" style={{ margin: '0 auto 18px' }}>
            <Leaf size={28} />
          </div>
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>Harvesta</h2>
          <p className="muted" style={{ fontSize: 13, marginBottom: 20 }}>
            Smart Agriculture AI Platform
          </p>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--c-ink-500)', fontSize: 13 }}>
            <Loader2 size={14} className="animate-spin" />
            Initializing your workspace…
          </div>
        </div>
      </div>
    );
  }

  if (authView === 'verify') {
    return <VerifyEmail onContinue={() => switchAuthView('login')} />;
  }
  if (authView === 'forgot') {
    return <ForgotPassword onSwitchToLogin={() => switchAuthView('login')} />;
  }
  if (authView === 'reset') {
    return (
      <ResetPassword
        user={user}
        onContinue={() => switchAuthView('login')}
        onForgotPassword={() => switchAuthView('forgot')}
      />
    );
  }

  if (user && user.is_verified) {
    const renderView = () => {
      switch (route.view) {
        case 'my-farm':
          return <MyFarm onNavigate={navigate} />;
        case 'farm-form':
          return <FarmForm farmId={route.params.farmId ?? null} onNavigate={navigate} />;
        case 'crop-form':
          return (
            <CropForm
              farmId={route.params.farmId}
              crop={route.params.crop ?? null}
              onNavigate={navigate}
            />
          );
        case 'crop-detail':
          return <CropDetail cropId={route.params.cropId} onNavigate={navigate} />;
        case 'disease-scan':
          return <DiseaseScan onNavigate={navigate} />;
        case 'equipment':
          return <EquipmentPage onNavigate={navigate} />;
        case 'climate':
          return <Dashboard user={user} onLogout={handleLogout} onNavigate={navigate} view="climate" />;
        case 'analysis':
          return <Dashboard user={user} onLogout={handleLogout} onNavigate={navigate} view="analysis" analysisFilter={route.params.filter || 'total_analyses'} />;
        case 'notifications':
          return <Notifications onNavigate={navigate} />;
        case 'notification-settings':
          return <NotificationSettings onNavigate={navigate} />;
        case 'settings':
          return <SettingsPage onNavigate={navigate} />;
        case 'profile':
          return <ProfilePage user={user} onProfileUpdated={(profile) => setUser((current) => savedAppearance(current, profile))} />;
        case 'inventory':
          return <InventoryPage />;
        case 'reports':
          return <ReportsPage />;
        case 'help':
          return <HelpPage onNavigate={navigate} />;
        case 'admin':
          // The backend is the security boundary and returns 403 to farmers.
          // This guard also prevents a farmer from opening the admin screen by
          // changing client-side state in the browser.
          return user.role === 'admin'
            ? <AdminDashboard onNavigate={navigate} />
            : <Dashboard user={user} onLogout={handleLogout} onNavigate={navigate} />;
        case 'dashboard':
        default:
          return <Dashboard user={user} onLogout={handleLogout} onNavigate={navigate} />;
      }
    };

    const directNavViews = ['admin', 'inventory', 'reports', 'help', 'settings', 'profile', 'equipment', 'climate'];
    const navActive = directNavViews.includes(route.view)
      ? route.view
      : (route.view === 'notifications' || route.view === 'notification-settings')
        ? 'alerts'
        : route.view === 'disease-scan'
          ? 'disease-scan'
          : (route.view.startsWith('farm') || route.view.startsWith('crop') || route.view === 'my-farm' ? 'my-farm' : 'dashboard');

    return (
      <div className="app-shell">
        <AppNav active={navActive} onNavigate={navigate} user={user} />
        <div className="app-main">{renderView()}</div>
      </div>
    );
  }

  if (authView === 'signup') {
    return (
      <Signup
        onSignupSuccess={handleSignupSuccess}
        onRegistrationComplete={handleLoginSubmit}
        onSwitchToLogin={() => setAuthView('login')}
      />
    );
  }

  return (
    <Login
      onLogin={handleLoginSubmit}
      onSwitchToSignup={() => setAuthView('signup')}
      onSwitchToForgotPassword={() => switchAuthView('forgot')}
    />
  );
}

export default App;
