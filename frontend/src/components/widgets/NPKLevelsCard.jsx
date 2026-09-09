import { BarChart3, Plus, CircleDot } from 'lucide-react';
import PropTypes from 'prop-types';

const NPK_ROWS = [
  { key: 'nitrogen', label: 'Nitrogen (N)', dotClass: 'n' },
  { key: 'phosphorus', label: 'Phosphorus (P)', dotClass: 'p' },
  { key: 'potassium', label: 'Potassium (K)', dotClass: 'k' },
];

export default function NPKLevelsCard({ reading = null, onAnalyze, onSensorFeed }) {
  const handleScrollToWorkspace = () => {
    document.getElementById('ai-workspace')?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="analytic-card">
      <div className="analytic-card-head">
        <h3 className="analytic-card-title">
          <BarChart3 size={18} />
          NPK Levels
        </h3>
        <div style={{ display: 'inline-flex', gap: 8 }}>
          <button
            type="button"
            className="badge-pill outline"
            onClick={onAnalyze || handleScrollToWorkspace}
            title="Go to AI Analysis Workspace"
          >
            <CircleDot size={11} /> AI Analysis
          </button>
          <button
            type="button"
            className="badge-pill outline"
            onClick={onSensorFeed}
            title="Open equipment and sensor readings"
          >
            <Plus size={11} /> Sensor feed
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        {NPK_ROWS.map((row) => (
          <div key={row.key} className="npk-bar-row">
            <div className="npk-bar-head">
              <span className="npk-bar-label">
                <span className={`npk-bar-dot ${row.dotClass}`} />
                {row.label}
              </span>
              <span className="npk-bar-value" style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--c-ink-400)' }}>
                {reading?.[row.key] != null ? `${reading[row.key]} mg/kg` : 'Not available'}
              </span>
            </div>
            <div className="npk-bar-track">
              <div
                className={`npk-bar-fill ${row.dotClass}`}
                style={{ width: '0%', opacity: 0.3 }}
              />
            </div>
          </div>
        ))}
      </div>

      <p className="muted" style={{ fontSize: 11.5, marginTop: 2, lineHeight: 1.45 }}>
        {reading
          ? 'Latest connected sensor values. Confirm calibration and laboratory units before nutrient decisions.'
          : 'NPK sensor data is not available yet. Register a calibrated sensor gateway to enable readings.'}
      </p>
    </div>
  );
}

NPKLevelsCard.propTypes = {
  reading: PropTypes.shape({
    nitrogen: PropTypes.number,
    phosphorus: PropTypes.number,
    potassium: PropTypes.number,
  }),
  onAnalyze: PropTypes.func,
  onSensorFeed: PropTypes.func,
};
