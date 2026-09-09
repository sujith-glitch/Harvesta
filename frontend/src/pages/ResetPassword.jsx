import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { resetPassword } from '../services/api';
import { Lock, AlertTriangle, CheckCircle2, Loader2, ArrowRight, ArrowLeft, Eye, EyeOff, KeyRound } from 'lucide-react';

const MIN_PASSWORD_LENGTH = 6;

export function ResetPassword({ onContinue, onForgotPassword }) {
  const [token, setToken] = useState('');
  const [statusState, setStatusState] = useState('pending');
  const [message, setMessage] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    if (urlToken) {
      setToken(urlToken);
    } else {
      setStatusState('error');
      setMessage('No password reset token found in the link. Please request a new reset email.');
    }
  }, []);

  const validateForm = () => {
    if (!newPassword) return 'Please enter a new password.';
    if (newPassword.length < MIN_PASSWORD_LENGTH) return `Password must be at least ${MIN_PASSWORD_LENGTH} characters long.`;
    if (newPassword !== confirmPassword) return 'Passwords do not match.';
    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationMessage = validateForm();
    if (validationMessage) {
      setValidationError(validationMessage);
      return;
    }
    setValidationError('');
    setIsLoading(true);
    try {
      const res = await resetPassword(token, newPassword);
      setStatusState('success');
      setMessage(res.message || 'Your password has been updated successfully. You can now log in with your new password.');
    } catch (err) {
      setStatusState('error');
      setMessage(err.message || 'Invalid or expired password reset link.');
    } finally {
      setIsLoading(false);
    }
  };

  const BrandIcon =
    statusState === 'error' ? AlertTriangle :
    statusState === 'success' ? CheckCircle2 : KeyRound;

  return (
    <div className="auth-shell">
      <div className="auth-card-h">
        <div style={{ textAlign: 'center', marginBottom: 22 }}>
          <div className="brand-ring" style={{ margin: '0 auto 16px' }}>
            <BrandIcon size={28} strokeWidth={2.2} />
          </div>
          <span className="eyebrow-text">Account Recovery</span>
          <h2 style={{ fontSize: 24, fontWeight: 700, marginTop: 6 }}>Reset Password</h2>
          <p className="muted" style={{ fontSize: 13, marginTop: 4 }}>Choose a new password for your farmer account.</p>
        </div>

        {validationError && (
          <div className="alert-h error" role="alert" style={{ marginBottom: 14 }}>
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
            {validationError}
          </div>
        )}

        {statusState === 'pending' && (
          <form onSubmit={handleSubmit}>
            <div className="form-group-h" style={{ marginBottom: 14 }}>
              <label htmlFor="new-password" className="form-label-h">
                New Password (min {MIN_PASSWORD_LENGTH} characters)
              </label>
              <div style={{ position: 'relative' }}>
                <Lock size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="new-password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter a new password"
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
            <div className="form-group-h" style={{ marginBottom: 18 }}>
              <label htmlFor="confirm-new-password" className="form-label-h">Confirm New Password</label>
              <div style={{ position: 'relative' }}>
                <Lock size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="confirm-new-password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your new password"
                  className="form-input-h"
                  style={{ paddingLeft: 38 }}
                  disabled={isLoading}
                  required
                />
              </div>
            </div>
            <label className="flex items-center gap-2 cursor-pointer" style={{ fontSize: 13, color: 'var(--c-ink-600)', marginBottom: 14 }}>
              <input
                type="checkbox"
                checked={showPassword}
                onChange={(e) => setShowPassword(e.target.checked)}
                style={{ accentColor: 'var(--c-lime-deep)' }}
              />
              Show passwords
            </label>
            <button type="submit" className="btn-pill" disabled={isLoading} style={{ width: '100%', justifyContent: 'center' }}>
              {isLoading ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> Updating Password…
                </>
              ) : (
                <>
                  Reset Password <ArrowRight size={14} />
                </>
              )}
            </button>
          </form>
        )}

        {statusState === 'success' && (
          <div>
            <div className="alert-h success">
              <CheckCircle2 size={16} style={{ flexShrink: 0, marginTop: 2 }} />
              {message}
            </div>
            <button type="button" className="btn-pill" onClick={onContinue} style={{ width: '100%', justifyContent: 'center', marginTop: 18 }}>
              Proceed to Farmer Login <ArrowRight size={14} />
            </button>
          </div>
        )}

        {statusState === 'error' && !isLoading && (
          <div>
            <div className="alert-h error">
              <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
              {message || 'This password reset link is invalid or has expired.'}
            </div>
            <p className="muted" style={{ fontSize: 13, marginBottom: 14 }}>
              Password reset links expire after 30 minutes and can only be used once. Request a fresh one to continue.
            </p>
            <button type="button" className="btn-pill" onClick={onForgotPassword} style={{ width: '100%', justifyContent: 'center' }}>
              Request New Reset Link
            </button>
            <div style={{ textAlign: 'center', marginTop: 18 }}>
              <button type="button" className="btn-ghost" onClick={onContinue}>
                <ArrowLeft size={12} /> Back to Login
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

ResetPassword.propTypes = {
  onContinue: PropTypes.func.isRequired,
  onForgotPassword: PropTypes.func.isRequired,
};

export default ResetPassword;
