import { useState } from 'react';
import PropTypes from 'prop-types';
import { Trash2, Clock, MapPin, ArrowRight } from 'lucide-react';

const STATUS_THEME = {
  IRRIGATION_REQUIRED: { bg: 'rgba(239, 68, 68, 0.10)', color: '#EF4444', label: 'Irrigation Required' },
  'IRRIGATION REQUIRED': { bg: 'rgba(239, 68, 68, 0.10)', color: '#EF4444', label: 'Irrigation Required' },
  MONITOR: { bg: 'rgba(249, 168, 37, 0.14)', color: 'var(--c-amber-deep)', label: 'Monitor Closely' },
  NO_IRRIGATION_NEEDED: { bg: 'rgba(76, 175, 80, 0.12)', color: 'var(--c-ok)', label: 'No Irrigation Needed' },
  'NO IRRIGATION NEEDED': { bg: 'rgba(76, 175, 80, 0.12)', color: 'var(--c-ok)', label: 'No Irrigation Needed' },
};

export function AnalysisHistoryCard({ item, onViewDetails, onDelete }) {
  const [isDeleting, setIsDeleting] = useState(false);

  const { id, crop_type, location, weather, soil, analysis, created_at } = item;

  const formatDate = (isoString) => {
    if (!isoString) return '--';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  const getPriorityTagClass = (prio) => {
    const p = prio?.toUpperCase() || 'LOW';
    if (p === 'HIGH') return 'tag danger';
    if (p === 'MEDIUM') return 'tag amber';
    return 'tag leaf';
  };

  const theme = STATUS_THEME[analysis?.status?.toUpperCase()] || {
    bg: 'rgba(15, 23, 42, 0.05)',
    color: 'var(--c-ink-700)',
    label: analysis?.status?.replace(/_/g, ' ') || 'Unknown',
  };

  const handleDeleteClick = async (e) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete analysis #${id} for ${crop_type}?`)) {
      setIsDeleting(true);
      try { await onDelete(id); } finally { setIsDeleting(false); }
    }
  };

  return (
    <div
      onClick={() => onViewDetails(item)}
      className="card-solid p-4 cursor-pointer transition-all"
      style={{ display: 'flex', flexDirection: 'column', gap: 12 }}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onViewDetails(item); } }}
    >
      {/* Top row: crop + actions */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="tag lime">{crop_type}</span>
          <span className="muted-2 inline-flex items-center gap-1" style={{ fontSize: 11 }}>
            <Clock size={11} />
            {formatDate(created_at)}
          </span>
        </div>
        <button
          type="button"
          onClick={handleDeleteClick}
          disabled={isDeleting}
          title="Delete this analysis"
          aria-label="Delete"
          className="w-8 h-8 rounded-lg flex items-center justify-center text-ink-400 hover:text-red-600 hover:bg-red-50 transition-colors"
        >
          {isDeleting ? <span className="spinner" style={{ width: 12, height: 12 }} /> : <Trash2 size={14} />}
        </button>
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-3 gap-2">
        <Stat label="Location" value={location?.location_text?.trim() || 'N/A'} icon={MapPin} />
        <Stat label="Moisture" value={`${soil?.current_soil_moisture ?? '--'}%`} />
        <Stat label="Air Temp" value={`${weather?.temperature ?? '--'}°C`} />
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between gap-2 flex-wrap pt-1">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="tag" style={{ background: theme.bg, color: theme.color }}>{theme.label}</span>
          <span className={getPriorityTagClass(analysis?.priority)}>{analysis?.priority || 'LOW'} Priority</span>
        </div>
        <button type="button" className="btn-ghost" onClick={(e) => { e.stopPropagation(); onViewDetails(item); }}>
          View Details <ArrowRight size={12} />
        </button>
      </div>
    </div>
  );
}

function Stat({ label, value, icon: Icon }) {
  return (
    <div className="p-2 rounded-lg" style={{ background: 'var(--c-cream-50)', border: '1px solid rgba(15,23,42,0.04)' }}>
      <span className="uppercase-mini" style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>{Icon && <Icon size={10} />}{label}</span>
      <span style={{ display: 'block', fontSize: 12, fontWeight: 700, color: 'var(--c-ink-800)', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {value}
      </span>
    </div>
  );
}

AnalysisHistoryCard.propTypes = {
  item: PropTypes.shape({
    id: PropTypes.number.isRequired,
    crop_type: PropTypes.string.isRequired,
    location: PropTypes.shape({ location_text: PropTypes.string }),
    weather: PropTypes.shape({
      temperature: PropTypes.number,
      humidity: PropTypes.number,
      precipitation: PropTypes.number,
      wind_speed: PropTypes.number,
    }),
    soil: PropTypes.shape({
      current_soil_moisture: PropTypes.number,
      soil_ph: PropTypes.number,
      soil_temperature: PropTypes.number,
    }),
    analysis: PropTypes.shape({
      status: PropTypes.string,
      priority: PropTypes.string,
      reason: PropTypes.string,
      factors: PropTypes.arrayOf(PropTypes.string),
    }),
    created_at: PropTypes.string,
  }).isRequired,
  onViewDetails: PropTypes.func.isRequired,
  onDelete: PropTypes.func.isRequired,
};

export default AnalysisHistoryCard;
