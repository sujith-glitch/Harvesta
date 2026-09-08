import { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { getFarms, getFarmCrops, deleteCrop } from '../services/api';
import { MapPin, Sprout, Plus, Pencil, Trash2, ArrowRight, Home, Ruler, Layers, Leaf, Loader2, AlertTriangle } from 'lucide-react';
import { usePreferences } from '../context/PreferencesContext';

const HEALTH_STYLES = {
  'healthy': 'health-healthy',
  'needs attention': 'health-attention',
  'critical': 'health-critical',
};
function healthClass(status) { return HEALTH_STYLES[(status || '').toLowerCase()] || 'health-unknown'; }

export function MyFarm({ onNavigate }) {
  const { t } = usePreferences();
  const [farm, setFarm] = useState(null);
  const [crops, setCrops] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [deletingCropId, setDeletingCropId] = useState(null);

  const loadFarmData = useCallback(async () => {
    setIsLoading(true);
    setError('');
    try {
      const farms = await getFarms();
      if (!farms || farms.length === 0) {
        setFarm(null);
        setCrops([]);
        setIsLoading(false);
        return;
      }
      const primaryFarm = farms[0];
      const farmCrops = await getFarmCrops(primaryFarm.id);
      setFarm(primaryFarm);
      setCrops(farmCrops || []);
    } catch (err) {
      console.error('Failed to load farm data:', err);
      setError(err.message || 'Unable to load your farm.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => { loadFarmData(); }, [loadFarmData]);

  const handleViewCrop = (crop) => onNavigate('crop-detail', { cropId: crop.id });
  const handleEditCrop = (crop) => onNavigate('crop-form', { farmId: crop.farm_id, crop });

  const handleDeleteCrop = async (crop) => {
    if (!window.confirm(`Remove ${crop.name} from your farm?`)) return;
    setDeletingCropId(crop.id);
    try {
      await deleteCrop(crop.id);
      setCrops((prev) => prev.filter((c) => c.id !== crop.id));
    } catch (err) {
      alert(err.message || 'Could not delete crop.');
    } finally {
      setDeletingCropId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="page-shell center-loading">
        <div className="glass-card flat" style={{ padding: 36, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, minWidth: 280 }}>
          <Loader2 size={28} className="animate-spin" style={{ color: 'var(--c-lime-deep)' }} />
          <p className="muted" style={{ fontSize: 13 }}>{t('loading')}</p>
        </div>
      </div>
    );
  }

  if (!farm) {
    return (
      <div className="page-shell">
        <button className="btn-back-h" onClick={() => onNavigate('dashboard')}>
          <Home size={13} /> {t('backDashboard')}
        </button>
        <div className="topbar">
          <div className="topbar-left">
            <span className="eyebrow-text">{t('yourFarm')}</span>
            <h1 className="topbar-title">{t('myFarm')}</h1>
          </div>
        </div>
        {error && (
          <div className="alert-h error" role="alert">
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} /> {error}
          </div>
        )}
        <div className="glass-card flat empty-state-h" style={{ padding: 48 }}>
          <div className="empty-ico"><Sprout size={28} /></div>
          <h3 style={{ fontSize: 18, fontWeight: 700 }}>Welcome! Set up your farm</h3>
          <p>Add your farm details and start tracking crops, growth stages, harvest dates and crop health — all in one place.</p>
          <button type="button" className="btn-pill" onClick={() => onNavigate('farm-form')}>
            <Plus size={16} strokeWidth={2.4} /> {t('myFarm')}
          </button>
        </div>
        <p className="footer-text mt-6">Smart Agriculture AI Platform &copy; 2026</p>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <button className="btn-back-h" onClick={() => onNavigate('dashboard')}>
        <Home size={13} /> {t('backDashboard')}
      </button>

      <div className="topbar">
        <div className="topbar-left">
          <span className="eyebrow-text">{t('yourFarm')}</span>
          <h1 className="topbar-title">{t('myFarm')}</h1>
          <p className="topbar-sub">{t('manageCrops')}</p>
        </div>
        <div className="topbar-right">
          <button type="button" className="btn-pill" onClick={() => onNavigate('crop-form', { farmId: farm.id })}>
            <Plus size={16} strokeWidth={2.4} /> {t('addCrop')}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert-h error" role="alert" style={{ marginBottom: 16 }}>
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} /> {error}
        </div>
      )}

      {/* Farm overview */}
      <section className="glass-card flat" style={{ padding: 24, marginBottom: 24 }}>
        <div className="card-head">
          <h3 style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <Home size={16} style={{ color: 'var(--c-lime-deep)' }} /> {t('farmOverview')}
          </h3>
          <button type="button" className="btn-pill-outline" onClick={() => onNavigate('farm-form', { farmId: farm.id })}>
            <Pencil size={14} /> {t('editFarm')}
          </button>
        </div>

        <div className="flex items-start gap-4 mb-4 flex-wrap">
          <div className="flex items-center justify-center flex-shrink-0"
               style={{ width: 56, height: 56, borderRadius: 18, background: 'linear-gradient(135deg, var(--c-leaf-300), var(--c-leaf-500))', color: '#fff', boxShadow: '0 8px 20px rgba(85,139,47,0.35)' }}>
            <Leaf size={22} />
          </div>
          <div>
            <h4 style={{ fontSize: 22, fontWeight: 700 }}>{farm.name}</h4>
            <p className="muted" style={{ fontSize: 13, marginTop: 4, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <MapPin size={13} />
              {[farm.location, farm.district, farm.state, farm.country].filter(Boolean).join(', ') || 'Location not set'}
            </p>
            {farm.description && <p className="muted" style={{ fontSize: 13, marginTop: 6, maxWidth: 600 }}>{farm.description}</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Fact icon={Ruler} label={t('farmSize')} value={farm.size != null ? `${farm.size} acres` : '—'} />
          <Fact icon={Layers} label={t('soilType')} value={farm.soil_type || '—'} />
          <Fact icon={Leaf} label={t('farmingMethod')} value={farm.farming_method || '—'} />
          <Fact icon={Sprout} label={t('totalCrops')} value={crops.length} />
        </div>
      </section>

      {/* My crops */}
      <section>
        <div className="flex items-center justify-between gap-3 flex-wrap mb-4">
          <h2 style={{ fontSize: 18, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <Sprout size={18} style={{ color: 'var(--c-lime-deep)' }} /> {t('myCrops')}
          </h2>
          <button type="button" className="btn-pill" onClick={() => onNavigate('crop-form', { farmId: farm.id })}>
            <Plus size={14} strokeWidth={2.4} /> {t('addCrop')}
          </button>
        </div>

        {crops.length === 0 ? (
          <div className="glass-card flat empty-state-h" style={{ padding: 36 }}>
            <div className="empty-ico"><Sprout size={26} /></div>
            <h4 style={{ fontSize: 16, fontWeight: 700 }}>{t('noCropsYet')}</h4>
            <p className="muted" style={{ fontSize: 13 }}>{t('noCropsHint')}</p>
            <button type="button" className="btn-pill" onClick={() => onNavigate('crop-form', { farmId: farm.id })}>
              <Plus size={16} strokeWidth={2.4} /> {t('addCrop')}
            </button>
          </div>
        ) : (
          <div className="grid-cards">
            {crops.map((crop) => (
              <div key={crop.id} className="glass-card flat" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                         style={{ background: 'rgba(212,225,87,0.22)', color: 'var(--c-lime-deep)' }}>
                      <Sprout size={18} />
                    </div>
                    <h4 style={{ fontSize: 16, fontWeight: 700 }}>{crop.name}</h4>
                  </div>
                  <span className={`health-pill ${healthClass(crop.health_status)}`}>
                    <span className={`health-dot ${healthClass(crop.health_status)}`} />
                    {crop.health_status || 'Unknown'}
                  </span>
                </div>

                <dl className="grid grid-cols-2 gap-2">
                  <Meta label={t('variety')} value={crop.variety || '—'} />
                  <Meta label={t('growthStage')} value={crop.growth_stage || '—'} />
                  <Meta label={t('plantingDate')} value={crop.planting_date || '—'} />
                  <Meta label={t('expectedHarvest')} value={crop.expected_harvest_date || '—'} />
                </dl>

                <div className="flex items-center justify-between gap-2 pt-2">
                  <button type="button" className="btn-pill-outline" style={{ fontSize: 12, padding: '6px 12px' }} onClick={() => handleViewCrop(crop)}>
                    {t('viewCrop')} <ArrowRight size={11} />
                  </button>
                  <div className="flex items-center gap-1">
                    <button type="button" className="btn-ghost" onClick={() => handleEditCrop(crop)}>
                      <Pencil size={12} /> Edit
                    </button>
                    <button
                      type="button"
                      className="w-8 h-8 rounded-lg flex items-center justify-center text-ink-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                      title="Delete this crop"
                      disabled={deletingCropId === crop.id}
                      onClick={() => handleDeleteCrop(crop)}
                    >
                      {deletingCropId === crop.id ? <span className="spinner" style={{ width: 12, height: 12 }} /> : <Trash2 size={14} />}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <p className="footer-text mt-8" style={{ marginTop: 32 }}>Smart Agriculture AI Platform &copy; 2026</p>
    </div>
  );
}

function Fact({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-xl border border-black/5 bg-cream-50">
      <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(212,225,87,0.22)', color: 'var(--c-lime-deep)' }}>
        <Icon size={14} />
      </div>
      <div className="flex flex-col leading-tight">
        <span className="uppercase-mini">{label}</span>
        <span style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, color: 'var(--c-ink-900)' }}>{value}</span>
      </div>
    </div>
  );
}

function Meta({ label, value }) {
  return (
    <div>
      <dt className="uppercase-mini">{label}</dt>
      <dd style={{ fontSize: 13, fontWeight: 600, color: 'var(--c-ink-800)', marginTop: 2 }}>{value}</dd>
    </div>
  );
}

MyFarm.propTypes = {
  onNavigate: PropTypes.func.isRequired,
};

export default MyFarm;
