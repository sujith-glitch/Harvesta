import { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { getCrop, deleteCrop } from '../services/api';
import { ArrowLeft, Sprout, Pencil, Trash2, Loader2, AlertTriangle, StickyNote } from 'lucide-react';

const HEALTH_STYLES = {
  'healthy': 'health-healthy',
  'needs attention': 'health-attention',
  'critical': 'health-critical',
};
function healthClass(status) { return HEALTH_STYLES[(status || '').toLowerCase()] || 'health-unknown'; }

export function CropDetail({ cropId, onNavigate }) {
  const [crop, setCrop] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const loadCrop = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await getCrop(cropId);
      setCrop(data);
    } catch (err) {
      console.error('Failed to load crop:', err);
      setError(err.message || 'Could not load this crop.');
    } finally {
      setIsLoading(false);
    }
  }, [cropId]);

  useEffect(() => { loadCrop(); }, [loadCrop]);

  const handleDelete = async () => {
    if (!window.confirm(`Remove ${crop?.name} from your farm?`)) return;
    try {
      await deleteCrop(crop.id);
      onNavigate('my-farm');
    } catch (err) {
      alert(err.message || 'Could not delete this crop.');
    }
  };

  if (isLoading) {
    return (
      <div className="page-shell center-loading">
        <div className="glass-card flat" style={{ padding: 36, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, minWidth: 280 }}>
          <Loader2 size={28} className="animate-spin" style={{ color: 'var(--c-lime-deep)' }} />
          <p className="muted" style={{ fontSize: 13 }}>Loading crop details…</p>
        </div>
      </div>
    );
  }

  if (error || !crop) {
    return (
      <div className="page-shell">
        <button className="btn-back-h" onClick={() => onNavigate('my-farm')}>
          <ArrowLeft size={13} /> Back to My Farm
        </button>
        <div className="glass-card flat empty-state-h" style={{ padding: 36 }}>
          <div className="empty-ico" style={{ background: 'rgba(239,68,68,0.10)', color: '#EF4444' }}>
            <AlertTriangle size={26} />
          </div>
          <h4 style={{ fontSize: 16, fontWeight: 700 }}>Crop not found</h4>
          <p className="muted" style={{ fontSize: 13 }}>{error}</p>
          <button type="button" className="btn-pill" onClick={() => onNavigate('my-farm')}>Back to My Farm</button>
        </div>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <button className="btn-back-h" onClick={() => onNavigate('my-farm')}>
        <ArrowLeft size={13} /> Back to My Farm
      </button>

      <div className="topbar">
        <div className="topbar-left">
          <span className="eyebrow-text">Crop Detail</span>
          <h1 className="topbar-title">{crop.name}{crop.variety ? ` (${crop.variety})` : ''}</h1>
        </div>
        <div className="topbar-right">
          <span className={`health-pill ${healthClass(crop.health_status)}`}>
            <span className={`health-dot ${healthClass(crop.health_status)}`} />
            {crop.health_status || 'Unknown'}
          </span>
        </div>
      </div>

      <div className="glass-card flat" style={{ padding: 24, maxWidth: 760 }}>
        <div className="card-head">
          <h3 style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <Sprout size={16} style={{ color: 'var(--c-lime-deep)' }} /> Crop Details
          </h3>
        </div>

        {/* Hero crop banner */}
        <div className="flex items-center gap-4 p-4 rounded-2xl mb-5" style={{ background: 'linear-gradient(135deg, rgba(212,225,87,0.18), rgba(85,139,47,0.10))' }}>
          <div className="flex items-center justify-center flex-shrink-0"
               style={{ width: 64, height: 64, borderRadius: 18, background: 'linear-gradient(135deg, var(--c-leaf-300), var(--c-leaf-500))', color: '#fff', boxShadow: '0 8px 20px rgba(85,139,47,0.35)' }}>
            <Sprout size={26} />
          </div>
          <div>
            <h4 style={{ fontSize: 22, fontWeight: 700 }}>{crop.name}</h4>
            {crop.variety && <p className="muted" style={{ fontSize: 13, marginTop: 4 }}>Variety: {crop.variety}</p>}
          </div>
        </div>

        {/* Facts grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
          <Fact label="Variety" value={crop.variety || '—'} />
          <Fact label="Growth Stage" value={crop.growth_stage || '—'} />
          <Fact label="Planting Date" value={crop.planting_date || '—'} />
          <Fact label="Expected Harvest" value={crop.expected_harvest_date || '—'} />
        </div>

        {/* Notes */}
        {crop.notes && (
          <div className="p-4 rounded-2xl border border-black/5 bg-cream-50" style={{ marginBottom: 18 }}>
            <h5 style={{ fontSize: 12, fontWeight: 700, color: 'var(--c-leaf-500)', display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
              <StickyNote size={14} /> Notes
            </h5>
            <p style={{ fontSize: 13, color: 'var(--c-ink-700)', lineHeight: 1.6 }}>{crop.notes}</p>
          </div>
        )}

        <div className="action-row">
          <button type="button" className="btn-pill-outline danger" onClick={handleDelete}>
            <Trash2 size={14} /> Delete Crop
          </button>
          <button type="button" className="btn-pill" onClick={() => onNavigate('crop-form', { farmId: crop.farm_id, crop })}>
            <Pencil size={14} strokeWidth={2.4} /> Edit Crop
          </button>
        </div>
      </div>

      <p className="footer-text" style={{ marginTop: 32 }}>Smart Agriculture AI Platform &copy; 2026</p>
    </div>
  );
}

function Fact({ label, value }) {
  return (
    <div className="p-3 rounded-xl border border-black/5 bg-cream-50">
      <span className="uppercase-mini">{label}</span>
      <span style={{ display: 'block', fontFamily: 'var(--font-display)', fontSize: 15, fontWeight: 700, color: 'var(--c-ink-900)', marginTop: 2 }}>
        {value}
      </span>
    </div>
  );
}

CropDetail.propTypes = {
  cropId: PropTypes.number.isRequired,
  onNavigate: PropTypes.func.isRequired,
};

export default CropDetail;
