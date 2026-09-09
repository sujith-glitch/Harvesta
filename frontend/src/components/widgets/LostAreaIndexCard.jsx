import { Download, Satellite } from 'lucide-react';
import PropTypes from 'prop-types';

export default function LostAreaIndexCard({ onDetails }) {
  return (
    <div className="analytic-card">
      <div className="analytic-card-head">
        <h3 className="analytic-card-title">Lost area index</h3>
        <button
          type="button"
          onClick={onDetails}
          title="Why is the crop-loss report unavailable?"
          aria-label="View crop-loss report details"
          style={{
            background: 'transparent',
            border: '1px solid rgba(15, 23, 42, 0.08)',
            color: 'var(--c-ink-400)',
            cursor: 'pointer',
            padding: '5px 10px',
            borderRadius: 8,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            fontSize: 11,
            fontWeight: 600,
          }}
        >
          <Download size={13} />
          Report details
        </button>
      </div>

      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          textAlign: 'center',
          padding: '24px 16px',
          background: 'rgba(15, 23, 42, 0.02)',
          borderRadius: 16,
          border: '1px dashed rgba(15, 23, 42, 0.1)',
          minHeight: 140,
          gap: 8,
        }}
      >
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: 'rgba(212, 225, 87, 0.18)',
            color: 'var(--c-leaf-500)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Satellite size={20} />
        </div>
        <p style={{ fontSize: 13, fontWeight: 700, color: 'var(--c-ink-800)', margin: 0 }}>
          Crop-loss index data is not available yet.
        </p>
        <p className="muted" style={{ fontSize: 11.5, margin: 0, maxWidth: 280, lineHeight: 1.45 }}>
          Satellite or field-monitoring data is required to calculate crop-loss trends.
        </p>
      </div>

      <p className="muted" style={{ fontSize: 11.5, marginTop: -2 }}>
        Vegetation anomaly and crop loss telemetry will display here when connected.
      </p>
    </div>
  );
}
LostAreaIndexCard.propTypes = { onDetails: PropTypes.func };
