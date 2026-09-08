import { useState } from 'react';
import PropTypes from 'prop-types';
import { Leaf, Mail, Lock, Eye, EyeOff, LogIn, AlertTriangle, Loader2, ArrowRight, Sparkles } from 'lucide-react';

export function Login({ onLogin, onSwitchToSignup, onSwitchToForgotPassword }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [isUnverified, setIsUnverified] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isDemoLoading, setIsDemoLoading] = useState(false);

  const handleDemoLogin = async () => {
    setIsDemoLoading(true);
    setError('');
    try {
      await onLogin({ email: 'demo', password: 'demo' });
    } catch (err) {
      setError(err.message || 'Demo login failed.');
      setIsDemoLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password.');
      return;
    }
    setError('');
    setIsUnverified(false);
    setIsLoading(true);
    try {
      await onLogin({ email, password });
    } catch (err) {
      const errorMessage = err.message || '';
      const normalizedMessage = errorMessage.toLowerCase();
      if (normalizedMessage.includes('create your password') || normalizedMessage.includes('original device')) {
        setError(errorMessage);
      } else if (err.status === 403 && normalizedMessage.includes('not verified')) {
        setIsUnverified(true);
        setError('Your email address is not verified. Continue registration and enter the four-digit code from your email.');
      } else {
        setError(err.message || 'Login failed. Please check your credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card-h">
        {/* Brand + heading */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div className="brand-ring" style={{ margin: '0 auto 16px' }}>
            <Leaf size={30} strokeWidth={2.4} />
          </div>
          <span className="eyebrow-text">Harvesta · Smart Agriculture AI</span>
          <h2 style={{ fontSize: 26, fontWeight: 700, marginTop: 6 }}>Farmer Login</h2>
          <p className="muted" style={{ fontSize: 13, marginTop: 4 }}>
            Sign in to access your AI Farm Assistant.
          </p>
        </div>

        {error && (
          <div className="alert-h error" role="alert">
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
            {error}
          </div>
        )}

        {isUnverified && (
          <div style={{ textAlign: 'center', marginTop: 12, marginBottom: 4 }}>
            <p className="muted" style={{ fontSize: 13, marginBottom: 12 }}>
              Open the registration screen with the same email to enter or resend your code.
            </p>
            <button type="button" className="btn-pill-outline" onClick={onSwitchToSignup}>
              <Mail size={14} /> Continue Email Verification
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} style={{ marginTop: 16 }}>
          {/* Email */}
          <div className="form-group-h" style={{ marginBottom: 14 }}>
            <label htmlFor="email" className="form-label-h">Farmer Email Address</label>
            <div style={{ position: 'relative' }}>
              <Mail size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
              <input
                type="email"
                id="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="e.g. farmer@gmail.com"
                className="form-input-h"
                style={{ paddingLeft: 38 }}
                disabled={isLoading}
                required
              />
            </div>
          </div>

          {/* Password */}
          <div className="form-group-h" style={{ marginBottom: 12 }}>
            <label htmlFor="password" className="form-label-h">Password</label>
            <div style={{ position: 'relative' }}>
              <Lock size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
              <input
                type={showPassword ? 'text' : 'password'}
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="form-input-h"
                style={{ paddingLeft: 38, paddingRight: 38 }}
                disabled={isLoading}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: 12,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--c-ink-400)',
                  cursor: 'pointer',
                  padding: 4,
                }}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between flex-wrap gap-2" style={{ marginBottom: 18 }}>
            <label className="flex items-center gap-2 cursor-pointer" style={{ fontSize: 13, color: 'var(--c-ink-600)' }}>
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={isLoading}
                style={{ accentColor: 'var(--c-lime-deep)' }}
              />
              Remember me
            </label>
            <button type="button" className="btn-ghost" onClick={onSwitchToForgotPassword}>
              Forgot Password?
            </button>
          </div>

          <button type="submit" className="btn-pill w-full justify-center" disabled={isLoading || isDemoLoading} style={{ width: '100%', justifyContent: 'center' }}>
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" /> Authenticating…
              </>
            ) : (
              <>
                <LogIn size={16} strokeWidth={2.4} /> Sign In to Dashboard <ArrowRight size={14} />
              </>
            )}
          </button>

          {/* Demo Login — only available when VITE_ENABLE_DEMO_MODE=true */}
          {import.meta.env.VITE_ENABLE_DEMO_MODE === 'true' && (
            <>
              <button
                type="button"
                onClick={handleDemoLogin}
                disabled={isLoading || isDemoLoading}
                style={{
                  width: '100%',
                  marginTop: 10,
                  display: 'inline-flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 8,
                  padding: '11px 16px',
                  borderRadius: 999,
                  border: '1.5px dashed var(--c-lime-deep)',
                  background: 'rgba(212, 225, 87, 0.18)',
                  color: 'var(--c-ink-900)',
                  fontWeight: 600,
                  fontSize: 13,
                  cursor: isLoading || isDemoLoading ? 'not-allowed' : 'pointer',
                  opacity: isLoading || isDemoLoading ? 0.6 : 1,
                  transition: 'all 0.18s ease',
                }}
              >
                {isDemoLoading ? (
                  <>
                    <Loader2 size={15} className="animate-spin" /> Loading demo workspace…
                  </>
                ) : (
                  <>
                    <Sparkles size={15} strokeWidth={2.4} /> Test Login (Demo Mode)
                  </>
                )}
              </button>
              <p className="muted" style={{ textAlign: 'center', fontSize: 11.5, marginTop: 8 }}>
                Demo environment enabled via VITE_ENABLE_DEMO_MODE.
              </p>
            </>
          )}
        </form>

        <div className="divider-h" />

        <p className="muted" style={{ textAlign: 'center', fontSize: 13 }}>
          New to Smart Agriculture AI?{' '}
          <button type="button" className="btn-ghost" onClick={onSwitchToSignup} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            Create Farmer Account <ArrowRight size={12} />
          </button>
        </p>

        <p style={{ textAlign: 'center', fontSize: 10.5, marginTop: 14, letterSpacing: '0.04em', opacity: 0.62 }}>
          HARVESTA UI · v2.1 · OFFICIAL BUILD
        </p>
      </div>
    </div>
  );
}

Login.propTypes = {
  onLogin: PropTypes.func.isRequired,
  onSwitchToSignup: PropTypes.func.isRequired,
  onSwitchToForgotPassword: PropTypes.func.isRequired,
};

export default Login;
