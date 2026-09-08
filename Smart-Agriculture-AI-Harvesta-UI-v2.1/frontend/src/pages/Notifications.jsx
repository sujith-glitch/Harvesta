import { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  Bell,
  CheckCheck,
  Droplets,
  CloudSun,
  ShieldAlert,
  Bug,
  Info,
  Settings,
  ArrowLeft,
  Loader2,
  Filter,
  Inbox,
} from 'lucide-react';
import {
  getNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from '../services/api';

function formatDateTime(dateString) {
  if (!dateString) return 'Not available';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return 'Not available';
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return 'Not available';
  }
}

function getNotificationMeta(type = '') {
  switch (type.toUpperCase()) {
    case 'IRRIGATION_ALERT':
      return {
        icon: Droplets,
        color: '#0284c7',
        bg: '#e0f2fe',
        label: 'Irrigation AI',
      };
    case 'WEATHER':
    case 'WEATHER_ALERT':
      return {
        icon: CloudSun,
        color: '#d97706',
        bg: '#fef3c7',
        label: 'Weather Advisory',
      };
    case 'SECURITY':
      return {
        icon: ShieldAlert,
        color: '#7c3aed',
        bg: '#ede9fe',
        label: 'Security & Auth',
      };
    case 'DISEASE':
    case 'DISEASE_ALERT':
      return {
        icon: Bug,
        color: '#dc2626',
        bg: '#fee2e2',
        label: 'Crop Disease',
      };
    default:
      return {
        icon: Info,
        color: 'var(--c-leaf-600)',
        bg: 'var(--c-leaf-50)',
        label: 'Notice',
      };
  }
}

export function Notifications({ onNavigate }) {
  const [notifications, setNotifications] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isMarkingAll, setIsMarkingAll] = useState(false);
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'unread', 'irrigation', 'weather', 'security'

  const loadNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await getNotifications({
        limit: 100,
        unread_only: activeTab === 'unread',
      });
      setNotifications(res?.notifications || []);
      setTotalCount(res?.total || 0);
      setUnreadCount(res?.unread_count || 0);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setIsLoading(false);
    }
  }, [activeTab]);

  useEffect(() => {
    loadNotifications();
  }, [loadNotifications]);

  const handleMarkRead = async (id, isRead) => {
    if (isRead) return;
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.error('Failed to mark read:', err);
    }
  };

  const handleMarkAllRead = async () => {
    if (unreadCount === 0 || isMarkingAll) return;
    setIsMarkingAll(true);
    try {
      await markAllNotificationsRead();
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, is_read: true, read_at: new Date().toISOString() }))
      );
      setUnreadCount(0);
    } catch (err) {
      console.error('Failed to mark all read:', err);
    } finally {
      setIsMarkingAll(false);
    }
  };

  // Filter client side for type tabs if needed
  const filteredNotifications = notifications.filter((item) => {
    if (activeTab === 'irrigation') return item.type === 'IRRIGATION_ALERT';
    if (activeTab === 'weather') return item.type === 'WEATHER' || item.type === 'WEATHER_ALERT';
    if (activeTab === 'security') return item.type === 'SECURITY';
    return true;
  });

  return (
    <div className="page-shell" style={{ maxWidth: 880, margin: '0 auto', paddingTop: 28, paddingBottom: 48 }}>
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            type="button"
            className="icon-btn-back"
            onClick={() => onNavigate?.('dashboard')}
            title="Back to Dashboard"
            aria-label="Back to Dashboard"
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
            <span className="eyebrow-text">Farmer Communications</span>
            <h1 style={{ fontSize: 24, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 10 }}>
              <Bell size={24} style={{ color: 'var(--c-leaf-500)' }} />
              Notifications & Farm Alerts
            </h1>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {unreadCount > 0 && (
            <button
              type="button"
              className="btn-secondary"
              onClick={handleMarkAllRead}
              disabled={isMarkingAll}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13 }}
            >
              {isMarkingAll ? <Loader2 size={14} className="animate-spin" /> : <CheckCheck size={14} />}
              Mark all as read
            </button>
          )}

          <button
            type="button"
            className="btn-primary"
            onClick={() => onNavigate?.('notification-settings')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 13 }}
          >
            <Settings size={14} />
            Alert Preferences
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="notif-page-tabs" style={{ display: 'flex', gap: 8, overflowX: 'auto', marginBottom: 20, paddingBottom: 4 }}>
        {[
          { id: 'all', label: 'All Alerts', count: totalCount },
          { id: 'unread', label: 'Unread', count: unreadCount },
          { id: 'irrigation', label: 'Irrigation AI' },
          { id: 'weather', label: 'Weather Advisories' },
          { id: 'security', label: 'Security & Auth' },
        ].map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`tab-btn-harvesta ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            style={{
              padding: '7px 14px',
              borderRadius: 20,
              fontSize: 13,
              fontWeight: 600,
              border: '1px solid',
              borderColor: activeTab === tab.id ? 'var(--c-leaf-500)' : 'var(--c-border)',
              background: activeTab === tab.id ? 'var(--c-leaf-50)' : 'var(--c-card-bg)',
              color: activeTab === tab.id ? 'var(--c-leaf-800)' : 'var(--c-ink-600)',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            {tab.label}
            {tab.count != null && tab.count > 0 && (
              <span
                style={{
                  background: activeTab === tab.id ? 'var(--c-leaf-500)' : 'var(--c-ink-200)',
                  color: activeTab === tab.id ? '#ffffff' : 'var(--c-ink-700)',
                  borderRadius: 10,
                  padding: '1px 6px',
                  fontSize: 11,
                  fontWeight: 700,
                }}
              >
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Notifications List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {isLoading ? (
          <div className="analytic-card" style={{ padding: 48, textAlign: 'center' }}>
            <Loader2 size={24} className="animate-spin" style={{ color: 'var(--c-leaf-500)', margin: '0 auto 12px' }} />
            <p className="muted" style={{ fontSize: 14 }}>Loading notification history…</p>
          </div>
        ) : filteredNotifications.length === 0 ? (
          <div className="analytic-card" style={{ padding: 48, textAlign: 'center' }}>
            <Inbox size={40} style={{ color: 'var(--c-ink-300)', margin: '0 auto 12px', strokeWidth: 1.5 }} />
            <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--c-ink-800)', marginBottom: 4 }}>
              No notifications found
            </h3>
            <p className="muted" style={{ fontSize: 13, maxWidth: 400, margin: '0 auto' }}>
              {activeTab === 'unread'
                ? 'You have caught up on all farm alerts and advisories.'
                : 'No alerts have been recorded in this category yet.'}
            </p>
          </div>
        ) : (
          filteredNotifications.map((item) => {
            const meta = getNotificationMeta(item.type);
            const IconComponent = meta.icon;
            return (
              <div
                key={item.id}
                className="analytic-card"
                style={{
                  padding: 16,
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 14,
                  borderLeft: item.is_read ? '3px solid transparent' : `4px solid ${meta.color}`,
                  background: item.is_read ? 'var(--c-card-bg)' : 'rgba(255, 255, 255, 0.95)',
                  boxShadow: item.is_read ? 'var(--c-shadow-sm)' : '0 2px 8px rgba(0,0,0,0.06)',
                  cursor: item.is_read ? 'default' : 'pointer',
                  transition: 'all 0.15s ease',
                }}
                onClick={() => handleMarkRead(item.id, item.is_read)}
              >
                <div
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 10,
                    background: meta.bg,
                    color: meta.color,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: 2,
                  }}
                >
                  <IconComponent size={18} strokeWidth={2.2} />
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 4 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span
                        style={{
                          fontSize: 14,
                          fontWeight: item.is_read ? 600 : 700,
                          color: item.is_read ? 'var(--c-ink-800)' : 'var(--c-ink-950)',
                        }}
                      >
                        {item.title}
                      </span>
                      {!item.is_read && (
                        <span
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            background: 'var(--c-leaf-500)',
                            display: 'inline-block',
                          }}
                        />
                      )}
                    </div>
                    <span style={{ fontSize: 12, color: 'var(--c-ink-400)', whiteSpace: 'nowrap' }}>
                      {formatDateTime(item.created_at)}
                    </span>
                  </div>

                  <p style={{ fontSize: 13, color: 'var(--c-ink-600)', lineHeight: 1.5, margin: 0 }}>
                    {item.message}
                  </p>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 10, flexWrap: 'wrap' }}>
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        padding: '2px 8px',
                        borderRadius: 6,
                        background: meta.bg,
                        color: meta.color,
                      }}
                    >
                      {meta.label}
                    </span>

                    {item.delivery_channel === 'BOTH' && (
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 500,
                          padding: '2px 8px',
                          borderRadius: 6,
                          background: 'var(--c-ink-100)',
                          color: 'var(--c-ink-600)',
                        }}
                      >
                        ✉ Email Delivered
                      </span>
                    )}

                    {!item.is_read && (
                      <span style={{ fontSize: 11, color: 'var(--c-leaf-600)', fontWeight: 600, marginLeft: 'auto' }}>
                        Click to mark as read
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

Notifications.propTypes = {
  onNavigate: PropTypes.func,
};

export default Notifications;
