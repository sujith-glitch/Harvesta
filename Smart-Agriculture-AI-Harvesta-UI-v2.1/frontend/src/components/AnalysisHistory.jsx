import { useState } from 'react';
import PropTypes from 'prop-types';
import AnalysisHistoryCard from './AnalysisHistoryCard';
import { History, RotateCw, Leaf, Loader2 } from 'lucide-react';

export function AnalysisHistory({ history, isLoading, onDelete, onRefresh }) {
  const [selectedRecord, setSelectedRecord] = useState(null);

  if (isLoading) {
    return (
      <div className="glass-card flat" style={{ padding: 28, minHeight: 200, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
        <Loader2 size={28} className="animate-spin" style={{ color: 'var(--c-lime-deep)' }} />
        <p className="muted" style={{ fontSize: 13 }}>Loading previous field analysis records…</p>
      </div>
    );
  }

  return (
    <div className="glass-card flat" style={{ padding: 22 }}>
      <div className="card-head">
        <h3 style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <History size={16} style={{ color: 'var(--c-lime-deep)' }} />
          Recent Field Analyses
        </h3>
        <button
          type="button"
          onClick={onRefresh}
          title="Refresh analysis history"
          className="btn-pill-outline"
          style={{ padding: '8px 14px', fontSize: 12 }}
        >
          <RotateCw size={13} />
          Refresh
        </button>
      </div>

      {!history || history.length === 0 ? (
        <div className="empty-state-h">
          <div className="empty-ico"><Leaf size={26} /></div>
          <h4>No Field Analyses Saved Yet</h4>
          <p>
            Perform an <strong className="strong-600">AI Field Analysis</strong> above to automatically record real-time weather, soil metrics, and irrigation recommendations.
          </p>
        </div>
      ) : (
        <div className="grid-cards">
          {history.map((item) => (
            <AnalysisHistoryCard
              key={item.id}
              item={item}
              onViewDetails={(record) => setSelectedRecord(record)}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}

      {selectedRecord && (
        <div className="modal-overlay" onClick={() => setSelectedRecord(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <HistoryModal record={selectedRecord} onClose={() => setSelectedRecord(null)} />
          </div>
        </div>
      )}
    </div>
  );
}

function HistoryModal({ record, onClose }) {
  const { id, crop_type, location, weather, soil, analysis } = record;
  return (
    <>
      <div className="card-head" style={{ marginBottom: 14 }}>
        <h3 style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <Leaf size={16} style={{ color: 'var(--c-lime-deep)' }} />
          Analysis #{id} · {crop_type}
        </h3>
        <button onClick={onClose} className="btn-pill-outline" style={{ padding: '6px 10px', fontSize: 12 }}>✕</button>
      </div>

      <div className="alert-h info" style={{ marginBottom: 14 }}>
        <p style={{ fontSize: 13 }}>
          <span className="uppercase-mini" style={{ marginRight: 8 }}>Historic Recommendation</span>
          <strong className="strong-600">{analysis?.status?.replace(/_/g, ' ') || 'UNKNOWN'}</strong> · {analysis?.priority || 'LOW'} priority
        </p>
      </div>

      <h5 style={{ fontSize: 12, fontWeight: 700, color: 'var(--c-leaf-500)', marginBottom: 8 }}>Recorded Weather Metrics</h5>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <Stat label="Air Temp" value={`${weather?.temperature ?? '--'}°C`} />
        <Stat label="Humidity" value={`${weather?.humidity ?? '--'}%`} />
        <Stat label="Precip" value={`${weather?.precipitation ?? '--'} mm`} />
        <Stat label="Wind" value={`${weather?.wind_speed ?? '--'} km/h`} />
      </div>

      <h5 style={{ fontSize: 12, fontWeight: 700, color: 'var(--c-leaf-500)', marginBottom: 8 }}>Recorded Soil Conditions</h5>
      <div className="grid grid-cols-3 gap-3 mb-4">
        <Stat label="Moisture" value={`${soil?.current_soil_moisture ?? '--'}%`} />
        <Stat label="pH" value={soil?.soil_ph ?? '--'} />
        <Stat label="Soil Temp" value={`${soil?.soil_temperature ?? '--'}°C`} />
      </div>

      {analysis?.reason && (
        <>
          <h5 style={{ fontSize: 12, fontWeight: 700, color: 'var(--c-leaf-500)', marginBottom: 6 }}>Primary Rationale</h5>
          <p style={{ fontSize: 13, color: 'var(--c-ink-700)', lineHeight: 1.6, marginBottom: 14, padding: 14, background: 'var(--c-cream-50)', borderRadius: 12, border: '1px solid rgba(15,23,42,0.05)' }}>
            {analysis.reason}
          </p>
        </>
      )}

      {analysis?.factors && analysis.factors.length > 0 && (
        <>
          <h5 style={{ fontSize: 12, fontWeight: 700, color: 'var(--c-leaf-500)', marginBottom: 8 }}>Key Influencing Factors</h5>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 14 }}>
            {analysis.factors.map((factor, index) => (
              <li key={index} className="flex items-start gap-2" style={{ fontSize: 13, color: 'var(--c-ink-700)' }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--c-lime-deep)', flexShrink: 0, marginTop: 6 }} />
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </>
      )}

      <div className="action-row">
        <button type="button" className="btn-pill-outline" onClick={onClose}>Close Record</button>
      </div>
    </>
  );
}

function Stat({ label, value }) {
  return (
    <div className="p-3 rounded-xl border border-black/5 bg-white">
      <span className="uppercase-mini">{label}</span>
      <span style={{ display: 'block', fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, color: 'var(--c-ink-900)', marginTop: 2 }}>
        {value}
      </span>
    </div>
  );
}

AnalysisHistory.propTypes = {
  history: PropTypes.arrayOf(PropTypes.object),
  isLoading: PropTypes.bool,
  onDelete: PropTypes.func.isRequired,
  onRefresh: PropTypes.func.isRequired,
};

export default AnalysisHistory;
