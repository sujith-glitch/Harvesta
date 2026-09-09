import { useState, useEffect, useRef, useCallback } from 'react';
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
  ExternalLink,
  Loader2,
} from 'lucide-react';
import {
  getNotifications,
  getUnreadNotificationCount,
  markNotificationRead,
  markAllNotificationsRead,
} from '../services/api';

function formatTimeAgo(dateString) {
  if (!dateString) return '';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return '';
    const diffMs = Date.now() - d.getTime();
    if (diffMs < 0) return 'Just now';
    const diffMins = Math.floor(diffMs / (1000 * 60));
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays}d ago`;
    return d.toLocaleDateString();
  } catch {
    return '';
  }
}

function getNotificationMeta(type = '') {
  switch (type.toUpperCase()) {
    case 'IRRIGATION_ALERT':
      return {
        icon: Droplets,
        color: '#0284c7',
        bg: '#e0f2fe',
        label: 'Irrigation',
      };
    case 'WEATHER':
    case 'WEATHER_ALERT':
      return {
        icon: CloudSun,
        color: '#d97706',
        bg: '#fef3c7',
        label: 'Weather',
      };
    case 'SECURITY':
      return {
        icon: ShieldAlert,
        color: '#7c3aed',
        bg: '#ede9fe',
        label: 'Security',
      };
    case 'DISEASE':
    case 'DISEASE_ALERT':
      return {
        icon: Bug,
        color: '#dc2626',
        bg: '#fee2e2',
        label: 'Disease',
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

export function NotificationBell({ onNavigate }) {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isMarkingAll, setIsMarkingAll] = useState(false);
  const [filterUnreadOnly, setFilterUnreadOnly] = useState(false);
  const dropdownRef = useRef(null);

  const fetchUnreadCount = useCallback(async () => {
    try {
      const res = await getUnreadNotificationCount();
      setUnreadCount(res?.unread_count || 0);
    } catch {
      // Silently ignore polling errors
    }
  }, []);

  const loadNotifications = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await getNotifications({ limit: 20, unread_only: filterUnreadOnly });
      setNotifications(res?.notifications || []);
      if (res?.unread_count != null) {
        setUnreadCount(res.unread_count);
      }
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setIsLoading(false);
    }
  }, [filterUnreadOnly]);

  useEffect(() => {
    fetchUnreadCount();
    const interval = setInterval(fetchUnreadCount, 30000); // 30s gentle poll
    return () => clearInterval(interval);
  }, [fetchUnreadCount]);

  useEffect(() => {
    if (isOpen) {
      loadNotifications();
    }
  }, [isOpen, loadNotifications]);

  // Click outside to close
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  const handleToggle = () => {
    setIsOpen((prev) => !prev);
  };

  const handleMarkRead = async (id, isRead) => {
    if (isRead) return;
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n))
      );
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch (err) {
      console.error('Error marking notification read:', err);
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
      console.error('Failed to mark all as read:', err);
    } finally {
      setIsMarkingAll(false);
    }
  };

  const handleViewAll = () => {
    setIsOpen(false);
    onNavigate?.('notifications');
  };

  const handleGoToSettings = () => {
    setIsOpen(false);
    onNavigate?.('notification-settings');
  };

  return (
    <div className="notification-bell-wrapper" ref={dropdownRef} style={{ position: 'relative' }}>
      <button
        type="button"
        className={`harvesta-bell-btn ${unreadCount > 0 ? 'has-unread' : ''}`}
        onClick={handleToggle}
        title={unreadCount > 0 ? `${unreadCount} unread farm notifications` : 'Farm notifications'}
        aria-label="Farm notifications"
        aria-expanded={isOpen}
      >
        <Bell size={18} strokeWidth={2.2} />
        {unreadCount > 0 && (
          <span className="harvesta-bell-badge">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="notification-dropdown-panel" role="dialog" aria-label="Notifications panel">
          {/* Panel Header */}
          <div className="notif-panel-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--c-ink-900)' }}>
                Farm Alerts & Advisories
              </span>
              {unreadCount > 0 && (
                <span className="notif-count-pill">
                  {unreadCount} new
                </span>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {unreadCount > 0 && (
                <button
                  type="button"
                  className="notif-action-btn"
                  onClick={handleMarkAllRead}
                  disabled={isMarkingAll}
                  title="Mark all as read"
                >
                  {isMarkingAll ? (
                    <Loader2 size={12} className="animate-spin" />
                  ) : (
                    <CheckCheck size={13} />
                  )}
                  <span>Mark all read</span>
                </button>
              )}
              <button
                type="button"
                className="notif-icon-btn"
                onClick={handleGoToSettings}
                title="Notification preferences"
                aria-label="Notification settings"
              >
                <Settings size={14} />
              </button>
            </div>
          </div>

          {/* Filter Bar */}
          <div className="notif-filter-bar">
            <button
              type="button"
              className={`notif-filter-tab ${!filterUnreadOnly ? 'active' : ''}`}
              onClick={() => setFilterUnreadOnly(false)}
            >
              All
            </button>
            <button
              type="button"
              className={`notif-filter-tab ${filterUnreadOnly ? 'active' : ''}`}
              onClick={() => setFilterUnreadOnly(true)}
            >
              Unread {unreadCount > 0 && `(${unreadCount})`}
            </button>
          </div>

          {/* Notification List */}
          <div className="notif-list-container">
            {isLoading ? (
              <div className="notif-empty-state">
                <Loader2 size={20} className="animate-spin" style={{ color: 'var(--c-leaf-500)', margin: '0 auto 8px' }} />
                <span style={{ fontSize: 13, color: 'var(--c-ink-500)' }}>Loading farm alerts…</span>
              </div>
            ) : notifications.length === 0 ? (
              <div className="notif-empty-state">
                <Bell size={24} style={{ color: 'var(--c-ink-300)', margin: '0 auto 8px', strokeWidth: 1.5 }} />
                <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--c-ink-700)' }}>
                  {filterUnreadOnly ? 'No unread alerts' : 'No notifications yet'}
                </span>
                <p style={{ fontSize: 12, color: 'var(--c-ink-400)', marginTop: 4 }}>
                  Farm irrigation advisories, weather warnings, and security updates will appear here.
                </p>
              </div>
            ) : (
              notifications.map((item) => {
                const meta = getNotificationMeta(item.type);
                const IconComponent = meta.icon;
                return (
                  <div
                    key={item.id}
                    className={`notif-item-card ${!item.is_read ? 'unread' : ''}`}
                    onClick={() => handleMarkRead(item.id, item.is_read)}
                    role="button"
                    tabIndex={0}
                  >
                    <div
                      className="notif-item-icon"
                      style={{ background: meta.bg, color: meta.color }}
                    >
                      <IconComponent size={15} strokeWidth={2.2} />
                    </div>

                    <div className="notif-item-content">
                      <div className="notif-item-top">
                        <span className="notif-item-title">{item.title}</span>
                        {!item.is_read && <span className="notif-unread-dot" />}
                      </div>
                      <p className="notif-item-msg">{item.message}</p>
                      <div className="notif-item-footer">
                        <span className="notif-item-tag" style={{ color: meta.color }}>
                          {meta.label}
                        </span>
                        <span className="notif-item-time">{formatTimeAgo(item.created_at)}</span>
                        {item.delivery_channel === 'BOTH' && (
                          <span className="notif-channel-pill" title="Sent via in-app notification and email">
                            ✉ Email sent
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Panel Footer */}
          <div className="notif-panel-footer">
            <button
              type="button"
              className="notif-view-all-link"
              onClick={handleViewAll}
            >
              <span>View full notification history</span>
              <ExternalLink size={12} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

NotificationBell.propTypes = {
  onNavigate: PropTypes.func,
};

export default NotificationBell;
