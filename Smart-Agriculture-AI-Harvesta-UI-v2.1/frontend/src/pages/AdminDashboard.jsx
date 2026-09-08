import { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  Users,
  ShieldCheck,
  Activity,
  Trees,
  Sprout,
  BarChart3,
  Clock,
  LogIn,
  Search,
  RefreshCw,
  AlertTriangle,
  ShieldAlert,
  Layers,
  ChevronRight,
  Database,
  Radio,
} from 'lucide-react';
import {
  getAdminOverview,
  getAdminUsers,
  getAdminActivity,
  getAdminAuditLogs,
  getAdminSessions,
  getAdminDataInventory,
  getAdminDataset,
} from '../services/api';

export function AdminDashboard({ onNavigate }) {
  const [activeTab, setActiveTab] = useState('overview'); // 'overview' | 'users' | 'activity' | 'audits' | 'sessions'
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isAccessDenied, setIsAccessDenied] = useState(false);

  // Users Tab State
  const [usersData, setUsersData] = useState({ users: [], total: 0 });
  const [userSearch, setUserSearch] = useState('');
  const [userRoleFilter, setUserRoleFilter] = useState('');
  const [loadingUsers, setLoadingUsers] = useState(false);

  // Activity Tab State
  const [activityData, setActivityData] = useState({ events: [], total: 0 });
  const [loadingActivity, setLoadingActivity] = useState(false);

  // Audit Logs State
  const [auditData, setAuditData] = useState({ logs: [], total: 0 });
  const [loadingAudits, setLoadingAudits] = useState(false);

  // Sessions State
  const [sessionsData, setSessionsData] = useState({ sessions: [], total: 0 });
  const [loadingSessions, setLoadingSessions] = useState(false);

  // Stored Data State
  const [dataInventory, setDataInventory] = useState({ datasets: [], excluded_secrets: [] });
  const [selectedDataset, setSelectedDataset] = useState('users');
  const [datasetData, setDatasetData] = useState({ records: [], total: 0 });
  const [loadingData, setLoadingData] = useState(false);

  // Fetch Overview Data
  const loadOverview = useCallback(async () => {
    setLoading(true);
    setError(null);
    setIsAccessDenied(false);
    try {
      const data = await getAdminOverview();
      setOverview(data);
    } catch (err) {
      if (err.message && err.message.toLowerCase().includes('administrator privileges required')) {
        setIsAccessDenied(true);
      } else {
        setError(err.message || 'Failed to load executive analytics.');
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch Users
  const loadUsers = useCallback(async () => {
    setLoadingUsers(true);
    try {
      const data = await getAdminUsers({
        limit: 50,
        search: userSearch,
        role: userRoleFilter,
      });
      setUsersData(data);
    } catch (err) {
      console.error('Failed to load admin users:', err);
    } finally {
      setLoadingUsers(false);
    }
  }, [userSearch, userRoleFilter]);

  // Fetch Activity
  const loadActivity = useCallback(async () => {
    setLoadingActivity(true);
    try {
      const data = await getAdminActivity({ limit: 50 });
      setActivityData(data);
    } catch (err) {
      console.error('Failed to load activity events:', err);
    } finally {
      setLoadingActivity(false);
    }
  }, []);

  // Fetch Audit Logs
  const loadAudits = useCallback(async () => {
    setLoadingAudits(true);
    try {
      const data = await getAdminAuditLogs({ limit: 50 });
      setAuditData(data);
    } catch (err) {
      console.error('Failed to load audit logs:', err);
    } finally {
      setLoadingAudits(false);
    }
  }, []);

  // Fetch Sessions
  const loadSessions = useCallback(async () => {
    setLoadingSessions(true);
    try {
      const data = await getAdminSessions({ limit: 50 });
      setSessionsData(data);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setLoadingSessions(false);
    }
  }, []);

  const loadStoredData = useCallback(async () => {
    setLoadingData(true);
    try {
      const inventory = await getAdminDataInventory();
      setDataInventory(inventory);
      const available = inventory.datasets || [];
      const activeDataset = available.some((item) => item.key === selectedDataset)
        ? selectedDataset
        : available[0]?.key;
      if (activeDataset) {
        if (activeDataset !== selectedDataset) setSelectedDataset(activeDataset);
        setDatasetData(await getAdminDataset(activeDataset, { limit: 50 }));
      }
    } catch (err) {
      setError(err.message || 'Failed to load stored company data.');
    } finally {
      setLoadingData(false);
    }
  }, [selectedDataset]);

  useEffect(() => {
    loadOverview();
  }, [loadOverview]);

  useEffect(() => {
    if (activeTab === 'users') loadUsers();
    else if (activeTab === 'activity') loadActivity();
    else if (activeTab === 'audits') loadAudits();
    else if (activeTab === 'sessions') loadSessions();
    else if (activeTab === 'data') loadStoredData();
  }, [activeTab, loadUsers, loadActivity, loadAudits, loadSessions, loadStoredData]);

  // Handle 403 Forbidden Access Denied
  if (isAccessDenied) {
    return (
      <div className="harvesta-page">
        <div className="harvesta-card" style={{ textAlign: 'center', padding: '60px 24px', maxWidth: 540, margin: '40px auto' }}>
          <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'rgba(239, 68, 68, 0.12)', color: '#ef4444', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
            <ShieldAlert size={32} />
          </div>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: 'var(--c-ink-900)', marginBottom: 8 }}>
            Access Denied
          </h2>
          <p style={{ color: 'var(--c-ink-500)', fontSize: 14, lineHeight: 1.6, marginBottom: 24 }}>
            You do not have administrator permissions to view platform analytics. Please contact your organization owner if you believe this is an error.
          </p>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => onNavigate('dashboard')}
          >
            Return to Farmer Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="harvesta-page">
      {/* Top Header */}
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <span className="badge badge-emerald" style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.04em' }}>
              EXECUTIVE PORTAL
            </span>
            <span style={{ fontSize: 12, color: 'var(--c-ink-400)' }}>• Real-time Telemetry</span>
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 800, color: 'var(--c-ink-900)', margin: 0 }}>
            Company Analytics & System Control
          </h1>
          <p style={{ color: 'var(--c-ink-500)', fontSize: 14, margin: '4px 0 0' }}>
            Platform health, farmer activity metrics, and security audit logs.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => {
              loadOverview();
              if (activeTab === 'users') loadUsers();
              if (activeTab === 'activity') loadActivity();
              if (activeTab === 'audits') loadAudits();
              if (activeTab === 'sessions') loadSessions();
              if (activeTab === 'data') loadStoredData();
            }}
            disabled={loading}
            title="Refresh All Metrics"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="admin-tabs" style={{ display: 'flex', gap: 8, borderBottom: '1px solid var(--c-ink-100)', paddingBottom: 12, margin: '20px 0', overflowX: 'auto' }}>
        {[
          { id: 'overview', label: 'Executive Overview', icon: BarChart3 },
          { id: 'users', label: 'User Directory', icon: Users, count: overview?.user_metrics?.total_users },
          { id: 'activity', label: 'Feature Telemetry', icon: Activity },
          { id: 'sessions', label: 'Active Sessions', icon: Radio, count: overview?.session_metrics?.active_sessions },
          { id: 'data', label: 'Stored Data', icon: Database },
          { id: 'audits', label: 'Security Audit Trail', icon: ShieldCheck },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 8,
                padding: '8px 16px',
                borderRadius: 8,
                fontSize: 13,
                fontWeight: isActive ? 700 : 500,
                color: isActive ? 'var(--c-emerald-700)' : 'var(--c-ink-600)',
                background: isActive ? 'var(--c-emerald-50)' : 'transparent',
                border: isActive ? '1px solid var(--c-emerald-200)' : '1px solid transparent',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease',
              }}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  style={{
                    fontSize: 11,
                    padding: '2px 6px',
                    borderRadius: 10,
                    background: isActive ? 'var(--c-emerald-200)' : 'var(--c-ink-100)',
                    color: isActive ? 'var(--c-emerald-900)' : 'var(--c-ink-600)',
                  }}
                >
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {error && (
        <div style={{ padding: '12px 16px', borderRadius: 8, background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#b91c1c', marginBottom: 20, display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      {/* ===================== TAB 1: EXECUTIVE OVERVIEW ===================== */}
      {activeTab === 'overview' && (
        <div>
          {loading ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--c-ink-400)' }}>
              <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 12px' }} />
              <p>Aggregating platform metrics…</p>
            </div>
          ) : (
            <>
              {/* Primary KPI Row */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 20 }}>
                <div className="harvesta-card" style={{ padding: '18px 20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--c-ink-500)', textTransform: 'uppercase' }}>Total Farmers</span>
                    <Users size={18} color="var(--c-emerald-600)" />
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--c-ink-900)' }}>
                    {overview?.user_metrics?.total_users ?? 0}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--c-ink-500)', marginTop: 4 }}>
                    <span style={{ color: 'var(--c-emerald-600)', fontWeight: 600 }}>{overview?.user_metrics?.verified_users ?? 0}</span> verified accounts
                  </div>
                </div>

                <div className="harvesta-card" style={{ padding: '18px 20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--c-ink-500)', textTransform: 'uppercase' }}>Active Sessions</span>
                    <Radio size={18} color="#3b82f6" />
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--c-ink-900)' }}>
                    {overview?.session_metrics?.active_sessions ?? 0}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--c-ink-500)', marginTop: 4 }}>
                    Active in last 30m
                  </div>
                </div>

                <div className="harvesta-card" style={{ padding: '18px 20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--c-ink-500)', textTransform: 'uppercase' }}>Registered Farms</span>
                    <Trees size={18} color="var(--c-emerald-700)" />
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--c-ink-900)' }}>
                    {overview?.platform_totals?.total_farms ?? 0}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--c-ink-500)', marginTop: 4 }}>
                    {overview?.platform_totals?.total_crops ?? 0} active crops tracked
                  </div>
                </div>

                <div className="harvesta-card" style={{ padding: '18px 20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--c-ink-500)', textTransform: 'uppercase' }}>AI Analyses</span>
                    <BarChart3 size={18} color="#8b5cf6" />
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--c-ink-900)' }}>
                    {overview?.platform_totals?.total_field_analyses ?? 0}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--c-ink-500)', marginTop: 4 }}>
                    Weather-integrated runs
                  </div>
                </div>

                <div className="harvesta-card" style={{ padding: '18px 20px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--c-ink-500)', textTransform: 'uppercase' }}>Avg Duration</span>
                    <Clock size={18} color="#f59e0b" />
                  </div>
                  <div style={{ fontSize: 26, fontWeight: 800, color: 'var(--c-ink-900)' }}>
                    {Math.round((overview?.session_metrics?.average_session_duration_seconds ?? 0) / 60)}m
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--c-ink-500)', marginTop: 4 }}>
                    {overview?.session_metrics?.logins_24h ?? 0} logins past 24h
                  </div>
                </div>
              </div>

              {/* Grid: Feature Breakdown & Recent Feeds */}
              <div className="admin-overview-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20 }}>
                {/* Feature Usage Breakdown */}
                <div className="harvesta-card" style={{ padding: 24 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--c-ink-900)', margin: 0 }}>
                      Feature Usage Telemetry
                    </h3>
                    <Layers size={16} color="var(--c-ink-400)" />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {(overview?.feature_usage || []).length === 0 ? (
                      <p style={{ color: 'var(--c-ink-400)', fontSize: 13 }}>No feature usage recorded yet.</p>
                    ) : (
                      overview.feature_usage.map((f, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'var(--c-ink-50)', borderRadius: 8 }}>
                          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--c-ink-800)', textTransform: 'capitalize' }}>
                            {f.feature}
                          </span>
                          <span className="badge badge-emerald" style={{ fontSize: 12 }}>
                            {f.count} events
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Recent Activity Stream */}
                <div className="harvesta-card" style={{ padding: 24 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                    <h3 style={{ fontSize: 15, fontWeight: 700, color: 'var(--c-ink-900)', margin: 0 }}>
                      Live Platform Activity
                    </h3>
                    <Activity size={16} color="var(--c-ink-400)" />
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {(overview?.recent_activity || []).length === 0 ? (
                      <p style={{ color: 'var(--c-ink-400)', fontSize: 13 }}>No recent activity.</p>
                    ) : (
                      overview.recent_activity.slice(0, 5).map((act, i) => (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--c-ink-100)', paddingBottom: 8 }}>
                          <div>
                            <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--c-ink-800)' }}>
                              {act.event_name.replace(/_/g, ' ')}
                            </span>
                            <span style={{ fontSize: 11, color: 'var(--c-ink-400)', marginLeft: 8 }}>
                              User #{act.user_id || 'guest'}
                            </span>
                          </div>
                          <span style={{ fontSize: 11, color: 'var(--c-ink-400)' }}>
                            {act.created_at ? new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      )}

      {/* ===================== TAB 2: USER DIRECTORY ===================== */}
      {activeTab === 'users' && (
        <div className="harvesta-card" style={{ padding: 20 }}>
          {/* Controls */}
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
            <div style={{ position: 'relative', flex: '1 1 240px', maxWidth: 360 }}>
              <Search size={16} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--c-ink-400)' }} />
              <input
                type="text"
                placeholder="Search by name or email…"
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                style={{ width: '100%', padding: '8px 12px 8px 36px', borderRadius: 8, border: '1px solid var(--c-ink-200)', fontSize: 13 }}
              />
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <select
                value={userRoleFilter}
                onChange={(e) => setUserRoleFilter(e.target.value)}
                style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid var(--c-ink-200)', fontSize: 13 }}
              >
                <option value="">All Roles</option>
                <option value="farmer">Farmers</option>
                <option value="admin">Admins</option>
              </select>
            </div>
          </div>

          {/* Table */}
          {loadingUsers ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--c-ink-400)' }}>
              <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 8px' }} />
              <p>Loading users…</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--c-ink-200)', color: 'var(--c-ink-500)' }}>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>User</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Role</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Status</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Farms / Crops</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Analyses</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {usersData.users.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: 24, color: 'var(--c-ink-400)' }}>
                        No users match the search criteria.
                      </td>
                    </tr>
                  ) : (
                    usersData.users.map((u) => (
                      <tr key={u.id} style={{ borderBottom: '1px solid var(--c-ink-100)' }}>
                        <td style={{ padding: '12px' }}>
                          <div style={{ fontWeight: 600, color: 'var(--c-ink-900)' }}>{u.full_name}</div>
                          <div style={{ fontSize: 12, color: 'var(--c-ink-400)' }}>{u.email}</div>
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span className={`badge ${u.role === 'admin' ? 'badge-purple' : 'badge-emerald'}`} style={{ textTransform: 'capitalize' }}>
                            {u.role}
                          </span>
                        </td>
                        <td style={{ padding: '12px' }}>
                          {u.is_verified ? (
                            <span style={{ color: 'var(--c-emerald-600)', fontWeight: 600, fontSize: 12 }}>✓ Verified</span>
                          ) : (
                            <span style={{ color: '#f59e0b', fontSize: 12 }}>Unverified</span>
                          )}
                        </td>
                        <td style={{ padding: '12px', color: 'var(--c-ink-700)' }}>
                          {u.farms_count} farms
                        </td>
                        <td style={{ padding: '12px', color: 'var(--c-ink-700)' }}>
                          {u.analyses_count}
                        </td>
                        <td style={{ padding: '12px', color: 'var(--c-ink-400)', fontSize: 12 }}>
                          {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ===================== TAB 3: FEATURE TELEMETRY ===================== */}
      {activeTab === 'activity' && (
        <div className="harvesta-card" style={{ padding: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Platform Feature Telemetry</h3>
          {loadingActivity ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--c-ink-400)' }}>
              <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 8px' }} />
              <p>Loading activity logs…</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--c-ink-200)', color: 'var(--c-ink-500)' }}>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Timestamp</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Event Name</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Feature</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>User ID</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Metadata</th>
                  </tr>
                </thead>
                <tbody>
                  {activityData.events.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ textAlign: 'center', padding: 24, color: 'var(--c-ink-400)' }}>
                        No activity events recorded.
                      </td>
                    </tr>
                  ) : (
                    activityData.events.map((e) => (
                      <tr key={e.id} style={{ borderBottom: '1px solid var(--c-ink-100)' }}>
                        <td style={{ padding: '10px 12px', color: 'var(--c-ink-400)', whiteSpace: 'nowrap' }}>
                          {e.created_at ? new Date(e.created_at).toLocaleString() : '—'}
                        </td>
                        <td style={{ padding: '10px 12px', fontWeight: 600, color: 'var(--c-ink-900)' }}>
                          {e.event_name}
                        </td>
                        <td style={{ padding: '10px 12px' }}>
                          <span className="badge badge-secondary" style={{ textTransform: 'capitalize' }}>
                            {e.feature || 'system'}
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px', color: 'var(--c-ink-600)' }}>
                          {e.user_id ? `#${e.user_id}` : 'Anonymous'}
                        </td>
                        <td style={{ padding: '10px 12px', fontFamily: 'monospace', fontSize: 11, color: 'var(--c-ink-500)' }}>
                          {e.event_metadata ? JSON.stringify(e.event_metadata) : '—'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ===================== TAB 4: ACTIVE SESSIONS ===================== */}
      {activeTab === 'sessions' && (
        <div className="harvesta-card" style={{ padding: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Authenticated User Sessions</h3>
          {loadingSessions ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--c-ink-400)' }}>
              <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 8px' }} />
              <p>Loading session logs…</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--c-ink-200)', color: 'var(--c-ink-500)' }}>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Login Time</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>User ID</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Platform</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Device</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Last Active</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {sessionsData.sessions.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', padding: 24, color: 'var(--c-ink-400)' }}>
                        No session telemetry recorded.
                      </td>
                    </tr>
                  ) : (
                    sessionsData.sessions.map((s) => (
                      <tr key={s.id} style={{ borderBottom: '1px solid var(--c-ink-100)' }}>
                        <td style={{ padding: '10px 12px', color: 'var(--c-ink-400)', whiteSpace: 'nowrap' }}>
                          {s.login_at ? new Date(s.login_at).toLocaleString() : '—'}
                        </td>
                        <td style={{ padding: '10px 12px', fontWeight: 600, color: 'var(--c-ink-900)' }}>
                          #{s.user_id}
                        </td>
                        <td style={{ padding: '10px 12px', color: 'var(--c-ink-700)' }}>
                          {s.platform || 'Unknown'}
                        </td>
                        <td style={{ padding: '10px 12px', color: 'var(--c-ink-600)' }}>
                          {s.device_type || 'desktop'}
                        </td>
                        <td style={{ padding: '10px 12px', color: 'var(--c-ink-500)' }}>
                          {s.last_active_at ? new Date(s.last_active_at).toLocaleTimeString() : '—'}
                        </td>
                        <td style={{ padding: '10px 12px' }}>
                          {s.logout_at ? (
                            <span style={{ color: 'var(--c-ink-400)', fontSize: 12 }}>Closed ({s.duration_seconds ? `${Math.round(s.duration_seconds / 60)}m` : '0m'})</span>
                          ) : (
                            <span className="badge badge-emerald" style={{ fontSize: 11 }}>Active</span>
                          )}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ===================== TAB 5: STORED COMPANY DATA ===================== */}
      {activeTab === 'data' && (
        <div className="harvesta-card" style={{ padding: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, flexWrap: 'wrap', marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>Stored Company Data</h3>
              <p style={{ color: 'var(--c-ink-500)', fontSize: 12, margin: '4px 0 0' }}>
                Browse the latest 50 records from each approved Supabase dataset.
              </p>
            </div>
            <select
              className="admin-dataset-select"
              value={selectedDataset}
              onChange={(event) => setSelectedDataset(event.target.value)}
              style={{ minWidth: 220, padding: '8px 12px', borderRadius: 8, border: '1px solid var(--c-ink-200)', fontSize: 13 }}
            >
              {dataInventory.datasets.map((item) => (
                <option key={item.key} value={item.key}>{item.label} ({item.row_count})</option>
              ))}
            </select>
          </div>

          {loadingData ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--c-ink-400)' }}>
              <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 8px' }} />
              <p>Loading stored records…</p>
            </div>
          ) : (
            <>
              <div style={{ padding: 12, borderRadius: 8, background: 'var(--c-ink-50)', marginBottom: 14 }}>
                <strong style={{ fontSize: 13, color: 'var(--c-ink-800)' }}>{datasetData.label || selectedDataset}</strong>
                <p style={{ fontSize: 12, color: 'var(--c-ink-500)', margin: '4px 0 0' }}>{datasetData.description}</p>
              </div>
              {datasetData.records?.length ? (
                <div style={{ display: 'grid', gap: 8 }}>
                  {datasetData.records.map((record, index) => (
                    <details key={`${selectedDataset}-${record.id ?? index}`} style={{ border: '1px solid var(--c-ink-100)', borderRadius: 8, padding: '10px 12px' }}>
                      <summary style={{ cursor: 'pointer', fontSize: 13, fontWeight: 600, color: 'var(--c-ink-800)' }}>
                        {datasetData.label || selectedDataset} record #{record.id ?? index + 1}
                      </summary>
                      <pre style={{ margin: '10px 0 0', padding: 12, overflowX: 'auto', borderRadius: 8, background: 'var(--c-ink-50)', color: 'var(--c-ink-700)', fontSize: 11, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {JSON.stringify(record, null, 2)}
                      </pre>
                    </details>
                  ))}
                </div>
              ) : (
                <p style={{ padding: 24, textAlign: 'center', color: 'var(--c-ink-400)', fontSize: 13 }}>No records stored in this dataset yet.</p>
              )}
              <p style={{ color: 'var(--c-ink-400)', fontSize: 11, marginTop: 16 }}>
                Never shown here: {(dataInventory.excluded_secrets || []).join(', ')}.
              </p>
            </>
          )}
        </div>
      )}

      {/* ===================== TAB 6: AUDIT LOGS ===================== */}
      {activeTab === 'audits' && (
        <div className="harvesta-card" style={{ padding: 20 }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>Administrative & Security Audit Trail</h3>
          {loadingAudits ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--c-ink-400)' }}>
              <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 8px' }} />
              <p>Loading audit trail…</p>
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--c-ink-200)', color: 'var(--c-ink-500)' }}>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Timestamp</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Action</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Entity</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>User</th>
                    <th style={{ padding: '10px 12px', fontWeight: 600 }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {auditData.logs.length === 0 ? (
                    <tr>
                      <td colSpan={5} style={{ textAlign: 'center', padding: 24, color: 'var(--c-ink-400)' }}>
                        No audit events recorded.
                      </td>
                    </tr>
                  ) : (
                    auditData.logs.map((a) => (
                      <tr key={a.id} style={{ borderBottom: '1px solid var(--c-ink-100)' }}>
                        <td style={{ padding: '10px 12px', color: 'var(--c-ink-400)', whiteSpace: 'nowrap' }}>
                          {a.created_at ? new Date(a.created_at).toLocaleString() : '—'}
                        </td>
                        <td style={{ padding: '10px 12px', fontWeight: 600, color: 'var(--c-ink-900)' }}>
                          {a.action}
                        </td>
                        <td style={{ padding: '10px 12px', color: 'var(--c-ink-600)' }}>
                          {a.entity_type} {a.entity_id ? `#${a.entity_id}` : ''}
                        </td>
                        <td style={{ padding: '10px 12px', color: 'var(--c-ink-600)' }}>
                          {a.user_id ? `#${a.user_id}` : 'System'}
                        </td>
                        <td style={{ padding: '10px 12px' }}>
                          <span className={`badge ${a.status === 'SUCCESS' ? 'badge-emerald' : 'badge-danger'}`} style={{ fontSize: 11 }}>
                            {a.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

AdminDashboard.propTypes = {
  onNavigate: PropTypes.func.isRequired,
};

export default AdminDashboard;
