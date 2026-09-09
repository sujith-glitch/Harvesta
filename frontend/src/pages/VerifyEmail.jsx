import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { resendVerificationEmail, verifyEmailToken } from '../services/api';
import { AlertTriangle, CheckCircle2, Loader2, MailCheck } from 'lucide-react';

export function VerifyEmail({ onContinue }) {
  const [verificationToken] = useState(() => new URLSearchParams(window.location.search).get('token'));
  const [statusState, setStatusState] = useState(verificationToken ? 'verifying' : 'error');
  const [message, setMessage] = useState(
    verificationToken
      ? 'Please wait while Harvesta verifies your Gmail address…'
      : 'No verification token was found in this link.',
  );
  const [resendEmail, setResendEmail] = useState('');
  const [resendStatus, setResendStatus] = useState('');
  const [isResending, setIsResending] = useState(false);

  useEffect(() => {
    if (!verificationToken) return undefined;

    let cancelled = false;
    verifyEmailToken(verificationToken)
      .then((result) => {
        if (cancelled) return;
        setStatusState('success');
        setMessage(result.message || 'Gmail verification successful.');
        window.history.replaceState({}, document.title, '/verify-email');
      })
      .catch((err) => {
        if (cancelled) return;
        setStatusState('error');
        setMessage(err.message || 'This verification link is invalid or expired.');
      });

    return () => {
      cancelled = true;
    };
  }, [verificationToken]);

  const handleResend = async (e) => {
    e.preventDefault();
    setIsResending(true);
    setResendStatus('');
    try {
      const result = await resendVerificationEmail(resendEmail);
      setResendStatus(result.message || 'A fresh verification email has been sent.');
    } catch (err) {
      setResendStatus(err.message || 'Failed to resend the verification email.');
    } finally {
      setIsResending(false);
    }
  };

  const BrandIcon = statusState === 'error' ? AlertTriangle : statusState === 'success' ? CheckCircle2 : Loader2;

  return (
    <div className="auth-shell">
      <div className="auth-card-h">
        <div style={{ textAlign: 'center', marginBottom: 22 }}>
          <div className="brand-ring" style={{ margin: '0 auto 16px' }}>
            <BrandIcon size={30} strokeWidth={2.2} className={statusState === 'verifying' ? 'animate-spin' : ''} />
          </div>
          <span className="eyebrow-text">Harvesta Gmail Verification</span>
          <h2 style={{ fontSize: 24, fontWeight: 700, marginTop: 6 }}>
            {statusState === 'verifying' ? 'Verifying Gmail…' : statusState === 'success' ? 'Verification successful' : 'Verification link problem'}
          </h2>
          <p className="muted" style={{ fontSize: 13, marginTop: 6 }}>{message}</p>
        </div>

        {statusState === 'verifying' && (
          <div className="alert-h">
            <MailCheck size={16} style={{ flexShrink: 0, marginTop: 2 }} />
            Checking the secure email link…
          </div>
        )}

        {statusState === 'success' && (
          <div className="alert-h success">
            <CheckCircle2 size={17} style={{ flexShrink: 0, marginTop: 2 }} />
            <p>
              Your Gmail address is verified. Return to the device where you registered.
              That screen will now show <strong className="strong-600">Create New Password</strong> and <strong className="strong-600">Confirm Password</strong>.
            </p>
          </div>
        )}

        {statusState === 'error' && (
          <div>
            <div className="alert-h error">
              <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
              {message}
            </div>
            <form onSubmit={handleResend}>
              <p className="muted" style={{ fontSize: 13, marginBottom: 12 }}>
                Enter the registered Gmail address to receive a fresh link:
              </p>
              <input
                type="email"
                value={resendEmail}
                onChange={(e) => setResendEmail(e.target.value)}
                placeholder="e.g. farmer@gmail.com"
                className="form-input-h"
                required
              />
              <button type="submit" className="btn-pill" disabled={isResending} style={{ width: '100%', justifyContent: 'center', marginTop: 14 }}>
                {isResending ? 'Sending…' : 'Resend Verification Email'}
              </button>
            </form>
            {resendStatus && <div className="alert-h success" style={{ marginTop: 12 }}>{resendStatus}</div>}
            <div style={{ textAlign: 'center', marginTop: 18 }}>
              <button type="button" className="btn-ghost" onClick={onContinue}>Back to Login</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

VerifyEmail.propTypes = {
  onContinue: PropTypes.func.isRequired,
};

export default VerifyEmail;
