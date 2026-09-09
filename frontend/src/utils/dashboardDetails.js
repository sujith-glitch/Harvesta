// All values come from the authenticated user's saved records.
export function formatRecordedAt(value) {
  if (!value) return 'Not recorded';
  // The backend serializes its UTC timestamps without an offset.
  const date = new Date(/[zZ]|[+-]\d{2}:?\d{2}$/.test(value) ? value : value + 'Z');
  return Number.isNaN(date.getTime()) ? 'Not recorded' : date.toLocaleString();
}

export const ANALYSIS_FILTERS = {
  total_analyses: 'All analyses',
  irrigation_required_count: 'Irrigation required',
  monitor_count: 'Monitor closely',
  no_irrigation_needed_count: 'No irrigation needed',
  high_priority_count: 'High priority',
};

export function filterAnalyses(records, filter) {
  const statuses = {
    irrigation_required_count: 'IRRIGATION_REQUIRED',
    monitor_count: 'MONITOR',
    no_irrigation_needed_count: 'NO_IRRIGATION_NEEDED',
  };
  if (filter === 'high_priority_count') {
    return records.filter((record) => record.analysis?.priority?.toUpperCase() === 'HIGH');
  }
  if (statuses[filter]) {
    return records.filter((record) => record.analysis?.status?.toUpperCase() === statuses[filter]);
  }
  return records;
}

export const MAP_FOREGROUND = 'button, a, input, select, textarea, [role="button"], .topbar, .metric-mini, .health-score-pill, .crop-scroller, .farmer-card';

export function getBackgroundTap(event) {
  if (event.detail === 0 || event.button !== 0 || event.target.closest(MAP_FOREGROUND)) return null;
  const bounds = event.currentTarget.getBoundingClientRect();
  const x = event.clientX - bounds.left;
  const y = event.clientY - bounds.top;
  if (x < 0 || y < 0 || x > bounds.width || y > bounds.height) return null;
  return { x, y };
}
