import { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { User, Mail, Sprout, MailCheck, AlertTriangle, ArrowRight, Loader2, RefreshCw, Lock, CheckCircle2, ShieldCheck } from 'lucide-react';
import { completeRegistration, getRegistrationStatus, resendVerificationEmail, verifyRegistrationOtp } from '../services/api';

const REGISTRATION_SESSION_KEY = 'harvesta_pending_registration';

function readPendingRegistration() {
  try {
    return JSON.parse(sessionStorage.getItem(REGISTRATION_SESSION_KEY) || 'null');
  } catch {
    return null;
  }
}

export function Signup({ onSignupSuccess, onRegistrationComplete, onSwitchToLogin }) {
  const pendingRegistration = readPendingRegistration();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [registeredEmail, setRegisteredEmail] = useState(pendingRegistration?.email || '');
  const [setupToken, setSetupToken] = useState(pendingRegistration?.setupToken || '');
  const [registrationState, setRegistrationState] = useState('waiting_for_otp');
  const [otp, setOtp] = useState('');
  const [isVerifyingOtp, setIsVerifyingOtp] = useState(false);
  const [resendStatus, setResendStatus] = useState('');
  const [isResending, setIsResending] = useState(false);
  const [resendCooldown, setResendCooldown] = useState(0);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isCompleting, setIsCompleting] = useState(false);

  useEffect(() => {
    if (resendCooldown <= 0) return undefined;
    const timerId = window.setInterval(() => {
      setResendCooldown((seconds) => Math.max(0, seconds - 1));
    }, 1000);
    return () => window.clearInterval(timerId);
  }, [resendCooldown]);

  useEffect(() => {
    if (!registeredEmail || !setupToken) return undefined;
    let cancelled = false;

    const checkStatus = async () => {
      try {
        const result = await getRegistrationStatus(setupToken);
        if (!cancelled && result?.status) {
          setRegistrationState(result.status === 'waiting_for_email' ? 'waiting_for_otp' : result.status);
          if (result.status === 'complete') sessionStorage.removeItem(REGISTRATION_SESSION_KEY);
          setError('');
        }
      } catch (err) {
        if (!cancelled) setError(err.message || 'Could not check verification status.');
      }
    };

    checkStatus();
    return () => { cancelled = true; };
  }, [registeredEmail, setupToken]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!fullName || !email) {
      setError('Please fill in all required fields.');
      return;
    }
    setError('');
    setIsLoading(true);
    try {
      const res = await onSignupSuccess({ full_name: fullName, email });
      if (!res?.setup_token) throw new Error('Registration session was not created. Please try again.');
      const normalizedEmail = res.email || email;
      setRegisteredEmail(normalizedEmail);
      setSetupToken(res.setup_token);
      setRegistrationState('waiting_for_otp');
      sessionStorage.setItem(REGISTRATION_SESSION_KEY, JSON.stringify({
        email: normalizedEmail,
        setupToken: res.setup_token,
      }));
      setResendCooldown(60);
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOtp = async (e) => {
    e.preventDefault();
    if (!/^\d{4}$/.test(otp)) {
      setError('Enter the four-digit code from your Harvesta email.');
      return;
    }
    setError('');
    setResendStatus('');
    setIsVerifyingOtp(true);
    try {
      const result = await verifyRegistrationOtp(setupToken, otp);
      setRegistrationState(result?.status || 'ready_for_password');
      setPassword('');
      setConfirmPassword('');
    } catch (err) {
      setError(err.message || 'Could not verify this code. Please try again.');
    } finally {
      setIsVerifyingOtp(false);
    }
  };

  const handleCreatePassword = async (e) => {
    e.preventDefault();
    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('New password and confirm password must be the same.');
      return;
    }
    setError('');
    setIsCompleting(true);
    try {
      await completeRegistration(setupToken, password);
      sessionStorage.removeItem(REGISTRATION_SESSION_KEY);
      try {
        await onRegistrationComplete({ email: registeredEmail, password });
      } catch (loginError) {
        setRegistrationState('complete');
        setError(loginError.message || 'Password created, but automatic login failed. Please sign in.');
      }
    } catch (err) {
      setError(err.message || 'Could not create your password. Please try again.');
    } finally {
      setIsCompleting(false);
    }
  };

  const handleResend = async () => {
    if (!registeredEmail || isResending || resendCooldown > 0) return;
    setIsResending(true);
    setResendStatus('');
    try {
      const res = await resendVerificationEmail(registeredEmail);
      setResendStatus(res.message || 'A new four-digit code has been sent.');
      setRegistrationState('waiting_for_otp');
      setOtp('');
      setError('');
      setResendCooldown(60);
    } catch (err) {
      setResendStatus(err.message || 'Could not resend the email. Please try again.');
    } finally {
      setIsResending(false);
    }
  };

  if (registeredEmail) {
    if (registrationState === 'ready_for_password') {
      return (
        <div className="auth-shell">
          <div className="auth-card-h">
            <div style={{ textAlign: 'center', marginBottom: 22 }}>
              <div className="brand-ring" style={{ margin: '0 auto 16px' }}>
                <Lock size={28} strokeWidth={2.2} />
              </div>
              <span className="eyebrow-text">Gmail Verification Successful</span>
              <h2 style={{ fontSize: 24, fontWeight: 700, marginTop: 6 }}>Create new password</h2>
              <p className="muted" style={{ fontSize: 13, marginTop: 4 }}>
                Your Gmail is verified. Create the password you will use for Harvesta login.
              </p>
            </div>

            {error && (
              <div className="alert-h error" role="alert">
                <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                {error}
              </div>
            )}

            <form onSubmit={handleCreatePassword}>
              <div className="form-group-h" style={{ marginBottom: 14 }}>
                <label htmlFor="newPassword" className="form-label-h">Create New Password</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
                  <input
                    type="password"
                    id="newPassword"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Minimum 6 characters"
                    className="form-input-h"
                    style={{ paddingLeft: 38 }}
                    autoComplete="new-password"
                    disabled={isCompleting}
                    required
                  />
                </div>
              </div>
              <div className="form-group-h" style={{ marginBottom: 18 }}>
                <label htmlFor="confirmNewPassword" className="form-label-h">Confirm Password</label>
                <div style={{ position: 'relative' }}>
                  <Lock size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
                  <input
                    type="password"
                    id="confirmNewPassword"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Enter the same password again"
                    className="form-input-h"
                    style={{ paddingLeft: 38 }}
                    autoComplete="new-password"
                    disabled={isCompleting}
                    required
                  />
                </div>
              </div>
              <button type="submit" className="btn-pill" disabled={isCompleting} style={{ width: '100%', justifyContent: 'center' }}>
                {isCompleting ? <><Loader2 size={16} className="animate-spin" /> Saving Password…</> : <>Create Password <ArrowRight size={14} /></>}
              </button>
            </form>
          </div>
        </div>
      );
    }

    if (registrationState === 'complete') {
      return (
        <div className="auth-shell">
          <div className="auth-card-h">
            <div style={{ textAlign: 'center', marginBottom: 22 }}>
              <div className="brand-ring" style={{ margin: '0 auto 16px' }}>
                <CheckCircle2 size={30} strokeWidth={2.2} />
              </div>
              <span className="eyebrow-text">Registration Complete</span>
              <h2 style={{ fontSize: 24, fontWeight: 700, marginTop: 6 }}>Password created successfully</h2>
              <p className="muted" style={{ fontSize: 13, marginTop: 6 }}>You can now log in with your Gmail and new password.</p>
            </div>
            {error && (
              <div className="alert-h error" role="alert" style={{ marginBottom: 14 }}>
                <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
                {error}
              </div>
            )}
            <button type="button" className="btn-pill" onClick={onSwitchToLogin} style={{ width: '100%', justifyContent: 'center' }}>
              Proceed to Farmer Login <ArrowRight size={14} />
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="auth-shell">
        <div className="auth-card-h">
          <div style={{ textAlign: 'center', marginBottom: 18 }}>
            <div className="brand-ring" style={{ margin: '0 auto 16px' }}>
              <MailCheck size={30} strokeWidth={2.2} />
            </div>
            <span className="eyebrow-text">Email Verification</span>
            <h2 style={{ fontSize: 22, fontWeight: 700, marginTop: 6 }}>Enter your 4-digit code</h2>
            <p className="muted" style={{ fontSize: 13, marginTop: 6 }}>
              We sent a verification code to <strong className="strong-600">{registeredEmail}</strong>.
            </p>
          </div>
          <div className="alert-h success">
            <MailCheck size={16} style={{ flexShrink: 0, marginTop: 2 }} />
            <p>
              Open the newest Harvesta email, copy the four-digit code, and enter it below.
              The code expires in 10 minutes.
            </p>
          </div>
          <form onSubmit={handleVerifyOtp} style={{ marginTop: 16 }}>
            <div className="form-group-h" style={{ marginBottom: 14 }}>
              <label htmlFor="verificationCode" className="form-label-h">Verification Code</label>
              <div style={{ position: 'relative' }}>
                <ShieldCheck size={17} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
                <input
                  type="text"
                  id="verificationCode"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 4))}
                  placeholder="0000"
                  className="form-input-h"
                  style={{ paddingLeft: 42, textAlign: 'center', fontSize: 24, fontWeight: 700, letterSpacing: '0.5em', textIndent: '0.5em' }}
                  inputMode="numeric"
                  pattern="[0-9]{4}"
                  maxLength={4}
                  autoComplete="one-time-code"
                  autoFocus
                  disabled={isVerifyingOtp}
                  required
                />
              </div>
            </div>
            <button type="submit" className="btn-pill" disabled={isVerifyingOtp || otp.length !== 4} style={{ width: '100%', justifyContent: 'center' }}>
              {isVerifyingOtp ? <><Loader2 size={16} className="animate-spin" /> Verifying…</> : <>Verify Code <ArrowRight size={14} /></>}
            </button>
          </form>
          <div className="alert-h" style={{ marginTop: 12 }}>
            <Mail size={16} style={{ flexShrink: 0, marginTop: 2 }} />
            <p>
              If Gmail placed it in Spam, open the message and choose <strong className="strong-600">Report not spam</strong>.
              Future Harvesta emails are then more likely to arrive in your Inbox.
            </p>
          </div>
          <button
            type="button"
            className="btn-pill"
            onClick={handleResend}
            disabled={isResending || resendCooldown > 0}
            style={{ width: '100%', justifyContent: 'center', marginTop: 18 }}
          >
            {isResending ? (
              <><Loader2 size={15} className="animate-spin" /> Sending…</>
            ) : (
              <><RefreshCw size={15} /> {resendCooldown > 0 ? `Resend available in ${resendCooldown}s` : 'Resend Code'}</>
            )}
          </button>
          {resendStatus && <p className="muted" style={{ textAlign: 'center', fontSize: 12, marginTop: 10 }}>{resendStatus}</p>}
          {registrationState === 'verification_expired' && (
            <div className="alert-h error" style={{ marginTop: 12 }}>
              <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
              This verification code expired. Use Resend Code to receive a fresh one.
            </div>
          )}
          {error && <p className="muted" style={{ textAlign: 'center', fontSize: 12, marginTop: 10 }}>{error}</p>}
        </div>
      </div>
    );
  }

  return (
    <div className="auth-shell">
      <div className="auth-card-h">
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <div className="brand-ring" style={{ margin: '0 auto 16px' }}>
            <Sprout size={30} strokeWidth={2.2} />
          </div>
          <span className="eyebrow-text">Harvesta · Smart Agriculture AI</span>
          <h2 style={{ fontSize: 26, fontWeight: 700, marginTop: 6 }}>Create Farmer Account</h2>
          <p className="muted" style={{ fontSize: 13, marginTop: 4 }}>
            Register to manage your farm, get AI diagnoses, and receive personalized advice.
          </p>
        </div>

        {error && (
          <div className="alert-h error" role="alert">
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group-h" style={{ marginBottom: 14 }}>
            <label htmlFor="fullName" className="form-label-h">Full Name</label>
            <div style={{ position: 'relative' }}>
              <User size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
              <input
                type="text"
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. John Doe"
                className="form-input-h"
                style={{ paddingLeft: 38 }}
                disabled={isLoading}
                required
              />
            </div>
          </div>

          <div className="form-group-h" style={{ marginBottom: 18 }}>
            <label htmlFor="email" className="form-label-h">Email Address</label>
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

          <button type="submit" className="btn-pill" disabled={isLoading} style={{ width: '100%', justifyContent: 'center' }}>
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" /> Creating Account & Sending Code…
              </>
            ) : (
              <>
                <Sprout size={16} strokeWidth={2.4} /> Register Account <ArrowRight size={14} />
              </>
            )}
          </button>
        </form>

        <div className="divider-h" />

        <p className="muted" style={{ textAlign: 'center', fontSize: 13 }}>
          Already have a farmer account?{' '}
          <button type="button" className="btn-ghost" onClick={onSwitchToLogin} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
            Sign In Here <ArrowRight size={12} />
          </button>
        </p>
      </div>
    </div>
  );
}

Signup.propTypes = {
  onSignupSuccess: PropTypes.func.isRequired,
  onRegistrationComplete: PropTypes.func.isRequired,
  onSwitchToLogin: PropTypes.func.isRequired,
};

export default Signup;
