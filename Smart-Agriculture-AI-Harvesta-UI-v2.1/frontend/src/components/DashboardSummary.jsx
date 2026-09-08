import PropTypes from 'prop-types';
import { BarChart3, Droplets, Eye, CheckCircle2, Zap } from 'lucide-react';

const METRICS = [
  { key: 'total_analyses', label: 'Total Analyses', icon: BarChart3, bg: 'rgba(85, 139, 47, 0.12)', color: 'var(--c-leaf-400)' },
  { key: 'irrigation_required_count', label: 'Irrigation Required', icon: Droplets, bg: 'rgba(239, 68, 68, 0.10)', color: '#EF4444' },
  { key: 'monitor_count', label: 'Monitor Closely', icon: Eye, bg: 'rgba(249, 168, 37, 0.14)', color: 'var(--c-amber-deep)' },
  { key: 'no_irrigation_needed_count', label: 'No Irrigation Needed', icon: CheckCircle2, bg: 'rgba(76, 175, 80, 0.12)', color: 'var(--c-ok)' },
  { key: 'high_priority_count', label: 'High Priority', icon: Zap, bg: 'rgba(212, 225, 87, 0.22)', color: 'var(--c-lime-deep)' },
];

export function DashboardSummary({ summary, isLoading, onSelect }) {
  if (isLoading) {
    return (
      <div className="grid-pills">
        {METRICS.map((m) => (
          <div key={m.key} className="metric-pill loading-skeleton" style={{ height: 64 }} />
        ))}
      </div>
    );
  }

  const data = summary || {};

  return (
    <div className="grid-pills">
      {METRICS.map((m) => {
        const Icon = m.icon;
        const value = data[m.key] ?? '—';
        return (
          <button type="button" key={m.key} className="metric-pill dashboard-metric-button" onClick={() => onSelect?.(m.key)}>
            <div className="metric-ico" style={{ background: m.bg, color: m.color }}>
              <Icon size={18} strokeWidth={2.2} />
            </div>
            <div className="flex flex-col">
              <span className="metric-value">{value}</span>
              <span className="metric-label">{m.label}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
}

DashboardSummary.propTypes = {
  summary: PropTypes.shape({
    total_analyses: PropTypes.number,
    irrigation_required_count: PropTypes.number,
    monitor_count: PropTypes.number,
    no_irrigation_needed_count: PropTypes.number,
    high_priority_count: PropTypes.number,
    latest_analysis_timestamp: PropTypes.string,
  }),
  isLoading: PropTypes.bool,
  onSelect: PropTypes.func,
};

export default DashboardSummary;
