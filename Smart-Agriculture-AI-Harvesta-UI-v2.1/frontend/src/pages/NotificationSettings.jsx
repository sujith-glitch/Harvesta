import { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  Settings,
  Mail,
  Droplets,
  CloudSun,
  ShieldCheck,
  Bug,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Bell,
  Sparkles,
} from 'lucide-react';
import {
  getNotificationPreferences,
  updateNotificationPreferences,
} from '../services/api';

export function NotificationSettings({ onNavigate }) {
  const [preferences, setPreferences] = useState({
    email_enabled: true,
    irrigation_alerts: true,
    weather_alerts: true,
    security_alerts: true,
    disease_alerts: true,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const loadPreferences = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await getNotificationPreferences();
      setPreferences({
        email_enabled: data.email_enabled ?? true,
        irrigation_alerts: data.irrigation_alerts ?? true,
        weather_alerts: data.weather_alerts ?? true,
        security_alerts: data.security_alerts ?? true,
        disease_alerts: data.disease_alerts ?? true,
      });
    } catch (err) {
      console.error('Failed to load preferences:', err);
      setErrorMessage('Unable to load current notification preferences.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPreferences();
  }, [loadPreferences]);

  const handleToggle = async (key) => {
    const updatedValue = !preferences[key];
    const newPrefs = { ...preferences, [key]: updatedValue };
    setPreferences(newPrefs);
    setIsSaving(true);
    setStatusMessage(null);
    setErrorMessage(null);

    try {
      await updateNotificationPreferences({ [key]: updatedValue });
      setStatusMessage('Preferences updated successfully.');
      setTimeout(() => setStatusMessage(null), 3000);
    } catch (err) {
      console.error('Failed to update preferences:', err);
      setErrorMessage('Could not save settings. Reverting change.');
      // Revert on error
      setPreferences(preferences);
    } finally {
      setIsSaving(false);
    }
  };

  const SETTING_ITEMS = [
    {
      key: 'email_enabled',
      title: 'Email Delivery (Master Switch)',
      description: 'Receive high-priority advisories and account security notices directly in your registered Gmail inbox.',
      icon: Mail,
      color: '#0284c7',
      bg: '#e0f2fe',
    },
    {
      key: 'irrigation_alerts',
      title: 'AI Irrigation Recommendations',
      description: 'Alerts when soil moisture drops below optimal levels or critical irrigation is recommended for your active crops.',
      icon: Droplets,
      color: '#059669',
      bg: '#ecfdf5',
    },
    {
      key: 'weather_alerts',
      title: 'Weather & Microclimate Advisories',
      description: 'Warnings when temperature exceeds 38°C, heavy rainfall (≥20mm), or high wind speeds affect your farm.',
      icon: CloudSun,
      color: '#d97706',
      bg: '#fef3c7',
    },
    {
      key: 'security_alerts',
      title: 'Account & Security Alerts',
      description: 'Critical notices regarding password resets, email verification, and administrator role assignments.',
      icon: ShieldCheck,
      color: '#7c3aed',
      bg: '#ede9fe',
    },
    {
      key: 'disease_alerts',
      title: 'Crop Disease & Anomaly Scans',
      description: 'Automated warnings when leaf diagnostic scans detect potential blight, mildew, or nutrient deficiencies.',
      icon: Bug,
      color: '#dc2626',
      bg: '#fee2e2',
    },
  ];

  return (
    <div className="page-shell" style={{ maxWidth: 760, margin: '0 auto', paddingTop: 28, paddingBottom: 48 }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            type="button"
            className="icon-btn-back"
            onClick={() => onNavigate?.('notifications')}
            title="Back to Notifications"
            aria-label="Back to Notifications"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 36,
              height: 36,
              borderRadius: '50%',
              background: 'var(--c-card-bg)',
              border: '1px solid var(--c-border)',
              cursor: 'pointer',
            }}
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <span className="eyebrow-text">Alert Configuration</span>
            <h1 style={{ fontSize: 24, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 10 }}>
              <Settings size={24} style={{ color: 'var(--c-leaf-500)' }} />
              Notification Preferences
            </h1>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => onNavigate?.('notifications')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13 }}
          >
            <Bell size={14} />
            View Notifications
          </button>
        </div>
      </div>

      {/* Status Toasts */}
      {statusMessage && (
        <div
          style={{
            padding: '10px 16px',
            borderRadius: 8,
            background: 'var(--c-leaf-50)',
            border: '1px solid var(--c-leaf-200)',
            color: 'var(--c-leaf-800)',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 13,
            fontWeight: 600,
            marginBottom: 20,
          }}
        >
          <CheckCircle2 size={16} style={{ color: 'var(--c-leaf-600)' }} />
          {statusMessage}
        </div>
      )}

      {errorMessage && (
        <div
          style={{
            padding: '10px 16px',
            borderRadius: 8,
            background: '#fef2f2',
            border: '1px solid #fecaca',
            color: '#991b1b',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            fontSize: 13,
            fontWeight: 600,
            marginBottom: 20,
          }}
        >
          <AlertCircle size={16} style={{ color: '#dc2626' }} />
          {errorMessage}
        </div>
      )}

      {/* Preferences Card */}
      <div className="analytic-card" style={{ padding: 24 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20, paddingBottom: 14, borderBottom: '1px solid var(--c-border)' }}>
          <div>
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0, color: 'var(--c-ink-900)' }}>
              Alert Notification Channels
            </h2>
            <p className="muted" style={{ fontSize: 13, margin: '4px 0 0' }}>
              Configure how and when Harvesta communicates agricultural telemetry advisories.
            </p>
          </div>
          {isSaving && (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--c-leaf-600)', fontWeight: 600 }}>
              <Loader2 size={13} className="animate-spin" /> Saving…
            </span>
          )}
        </div>

        {isLoading ? (
          <div style={{ padding: 32, textAlign: 'center' }}>
            <Loader2 size={24} className="animate-spin" style={{ color: 'var(--c-leaf-500)', margin: '0 auto 12px' }} />
            <p className="muted" style={{ fontSize: 13 }}>Loading preferences…</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
            {SETTING_ITEMS.map((item) => {
              const IconComponent = item.icon;
              const isChecked = Boolean(preferences[item.key]);
              return (
                <div
                  key={item.key}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between',
                    gap: 16,
                    padding: '12px 14px',
                    borderRadius: 10,
                    background: isChecked ? 'rgba(255, 255, 255, 0.7)' : 'var(--c-ink-50)',
                    border: '1px solid',
                    borderColor: isChecked ? 'var(--c-border)' : 'var(--c-ink-200)',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
                    <div
                      style={{
                        width: 36,
                        height: 36,
                        borderRadius: 8,
                        background: item.bg,
                        color: item.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0,
                        marginTop: 2,
                      }}
                    >
                      <IconComponent size={18} strokeWidth={2.2} />
                    </div>

                    <div>
                      <span style={{ fontSize: 14, fontWeight: 700, color: 'var(--c-ink-900)', display: 'block' }}>
                        {item.title}
                      </span>
                      <p style={{ fontSize: 12, color: 'var(--c-ink-500)', margin: '3px 0 0', lineHeight: 1.45 }}>
                        {item.description}
                      </p>
                    </div>
                  </div>

                  {/* Toggle Switch */}
                  <label
                    style={{
                      position: 'relative',
                      display: 'inline-block',
                      width: 44,
                      height: 24,
                      flexShrink: 0,
                      cursor: 'pointer',
                      marginTop: 6,
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={() => handleToggle(item.key)}
                      style={{ opacity: 0, width: 0, height: 0 }}
                    />
                    <span
                      style={{
                        position: 'absolute',
                        cursor: 'pointer',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: 0,
                        backgroundColor: isChecked ? 'var(--c-leaf-500)' : '#cbd5e1',
                        borderRadius: 24,
                        transition: '0.2s ease',
                      }}
                    />
                    <span
                      style={{
                        position: 'absolute',
                        height: 18,
                        width: 18,
                        left: isChecked ? 23 : 3,
                        bottom: 3,
                        backgroundColor: '#ffffff',
                        borderRadius: '50%',
                        transition: '0.2s ease',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.2)',
                      }}
                    />
                  </label>
                </div>
              );
            })}
          </div>
        )}

        <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid var(--c-border)', display: 'flex', alignItems: 'center', gap: 8, color: 'var(--c-ink-500)', fontSize: 12 }}>
          <Sparkles size={14} style={{ color: 'var(--c-leaf-500)' }} />
          <span>Alert changes take effect immediately across all active sessions.</span>
        </div>
      </div>
    </div>
  );
}

NotificationSettings.propTypes = {
  onNavigate: PropTypes.func,
};

export default NotificationSettings;
