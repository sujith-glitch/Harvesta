import { useState } from 'react';
import PropTypes from 'prop-types';
import { forgotPassword } from '../services/api';
import { KeyRound, Mail, AlertTriangle, MailCheck, ArrowLeft, Loader2, ArrowRight } from 'lucide-react';

export function ForgotPassword({ onSwitchToLogin }) {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !email.trim()) {
      setError('Please enter your registered email address.');
      return;
    }
    setError('');
    setSuccessMessage('');
    setIsLoading(true);
    try {
      const res = await forgotPassword(email.trim());
      setSuccessMessage(res.message || 'If an account exists for this email, a password reset link has been sent.');
    } catch (err) {
      setError(err.message || 'Failed to send reset email. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card-h">
        <div style={{ textAlign: 'center', marginBottom: 22 }}>
          <div className="brand-ring" style={{ margin: '0 auto 16px' }}>
            <KeyRound size={28} strokeWidth={2.2} />
          </div>
          <span className="eyebrow-text">Account Recovery</span>
          <h2 style={{ fontSize: 24, fontWeight: 700, marginTop: 6 }}>Forgot Password</h2>
          <p className="muted" style={{ fontSize: 13, marginTop: 4 }}>
            Enter your registered farmer email and we will send you a password reset link.
          </p>
        </div>

        {error && (
          <div className="alert-h error" role="alert">
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
            {error}
          </div>
        )}

        {successMessage && (
          <div className="alert-h success">
            <MailCheck size={16} style={{ flexShrink: 0, marginTop: 2 }} />
            {successMessage}
          </div>
        )}

        {!successMessage && (
          <form onSubmit={handleSubmit} style={{ marginTop: 4 }}>
            <div className="form-group-h" style={{ marginBottom: 18 }}>
              <label htmlFor="forgot-email" className="form-label-h">Farmer Email Address</label>
              <div style={{ position: 'relative' }}>
                <Mail size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
                <input
                  type="email"
                  id="forgot-email"
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
            <button type="submit" className="btn-pill" disabled={isLoading} style={{ width: '100%', justifyContent: 'center' }}>
              {isLoading ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> Sending Reset Link…
                </>
              ) : (
                <>
                  Send Reset Link <ArrowRight size={14} />
                </>
              )}
            </button>
          </form>
        )}

        {(successMessage || error) && !isLoading && (
          <button type="button" className="btn-pill-outline" onClick={onSwitchToLogin} style={{ width: '100%', justifyContent: 'center', marginTop: 16 }}>
            <ArrowLeft size={14} /> Back to Farmer Login
          </button>
        )}

        <div className="divider-h" />

        <p className="muted" style={{ textAlign: 'center', fontSize: 13 }}>
          Remembered your password?{' '}
          <button type="button" className="btn-ghost" onClick={onSwitchToLogin}>Back to Login</button>
        </p>
      </div>
    </div>
  );
}

ForgotPassword.propTypes = {
  onSwitchToLogin: PropTypes.func.isRequired,
};

export default ForgotPassword;
