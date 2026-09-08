import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { createFarm, updateFarm, getFarm } from '../services/api';
import { Save, ArrowLeft, Home, MapPin, Ruler, Layers, Leaf, Loader2, AlertTriangle } from 'lucide-react';

const SOIL_TYPES = ['Loamy', 'Clay', 'Sandy', 'Silty', 'Peaty', 'Chalky', 'Black Soil', 'Red Soil', 'Alluvial'];
const FARMING_METHODS = ['Organic', 'Conventional', 'Mixed', 'Natural Farming', 'Hydroponic', 'Permaculture'];

const EMPTY_FORM = {
  name: '', location: '', district: '', state: '', country: '',
  size: '', soil_type: '', farming_method: '', description: '',
};

export function FarmForm({ farmId, onNavigate }) {
  const isEditMode = Boolean(farmId);
  const [formData, setFormData] = useState(EMPTY_FORM);
  const [isLoading, setIsLoading] = useState(isEditMode);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    if (!isEditMode) return undefined;
    getFarm(farmId)
      .then((farm) => {
        if (cancelled) return;
        setFormData({
          name: farm.name || '',
          location: farm.location || '',
          district: farm.district || '',
          state: farm.state || '',
          country: farm.country || '',
          size: farm.size ?? '',
          soil_type: farm.soil_type || '',
          farming_method: farm.farming_method || '',
          description: farm.description || '',
        });
      })
      .catch((err) => setError(err.message || 'Could not load farm details.'))
      .finally(() => !cancelled && setIsLoading(false));
    return () => { cancelled = true; };
  }, [farmId, isEditMode]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const validate = () => {
    if (!formData.name.trim()) return 'Please give your farm a name.';
    if (formData.size !== '' && (isNaN(Number(formData.size)) || Number(formData.size) <= 0)) {
      return 'Farm size must be a positive number.';
    }
    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) { setError(validationError); return; }
    setIsSaving(true);
    setError('');
    try {
      const payload = {
        name: formData.name.trim(),
        location: formData.location.trim() || null,
        district: formData.district.trim() || null,
        state: formData.state.trim() || null,
        country: formData.country.trim() || null,
        size: formData.size === '' ? null : Number(formData.size),
        soil_type: formData.soil_type || null,
        farming_method: formData.farming_method || null,
        description: formData.description.trim() || null,
      };
      if (isEditMode) { await updateFarm(farmId, payload); } else { await createFarm(payload); }
      onNavigate('my-farm');
    } catch (err) {
      console.error('Farm save failed:', err);
      setError(err.message || 'Could not save your farm. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="page-shell center-loading">
        <div className="glass-card flat" style={{ padding: 36, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 14, minWidth: 280 }}>
          <Loader2 size={28} className="animate-spin" style={{ color: 'var(--c-lime-deep)' }} />
          <p className="muted" style={{ fontSize: 13 }}>Loading farm details…</p>
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
          <span className="eyebrow-text">{isEditMode ? 'Edit Farm' : 'Add Farm'}</span>
          <h1 className="topbar-title">{isEditMode ? 'Edit Farm' : 'Add Farm'}</h1>
          <p className="topbar-sub">Tell us about your land in simple terms — no technical details or coordinates needed.</p>
        </div>
      </div>

      <div className="glass-card flat" style={{ padding: 24, maxWidth: 720 }}>
        {error && (
          <div className="alert-h error" role="alert" style={{ marginBottom: 16 }}>
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-group-h" style={{ marginBottom: 14 }}>
            <label htmlFor="name" className="form-label-h">
              Farm Name <span className="req">*</span>
            </label>
            <div style={{ position: 'relative' }}>
              <Home size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
              <input
                type="text" id="name" name="name" value={formData.name}
                onChange={handleChange} placeholder="e.g. Green Valley Farm"
                className="form-input-h" style={{ paddingLeft: 38 }} maxLength={255} disabled={isSaving}
              />
            </div>
          </div>

          <div className="form-grid-h">
            <div className="form-group-h">
              <label htmlFor="location" className="form-label-h">Farm Location</label>
              <div style={{ position: 'relative' }}>
                <MapPin size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
                <input
                  type="text" id="location" name="location" value={formData.location}
                  onChange={handleChange} placeholder="Village / Town"
                  className="form-input-h" style={{ paddingLeft: 38 }} maxLength={255} disabled={isSaving}
                />
              </div>
            </div>
            <div className="form-group-h">
              <label htmlFor="district" className="form-label-h">District</label>
              <input
                type="text" id="district" name="district" value={formData.district}
                onChange={handleChange} placeholder="e.g. Salem"
                className="form-input-h" maxLength={255} disabled={isSaving}
              />
            </div>
            <div className="form-group-h">
              <label htmlFor="state" className="form-label-h">State</label>
              <input
                type="text" id="state" name="state" value={formData.state}
                onChange={handleChange} placeholder="e.g. Tamil Nadu"
                className="form-input-h" maxLength={255} disabled={isSaving}
              />
            </div>
            <div className="form-group-h">
              <label htmlFor="country" className="form-label-h">Country</label>
              <input
                type="text" id="country" name="country" value={formData.country}
                onChange={handleChange} placeholder="e.g. India"
                className="form-input-h" maxLength={255} disabled={isSaving}
              />
            </div>
            <div className="form-group-h">
              <label htmlFor="size" className="form-label-h">Farm Size (acres)</label>
              <div style={{ position: 'relative' }}>
                <Ruler size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
                <input
                  type="number" id="size" name="size" step="0.1" min="0"
                  value={formData.size} onChange={handleChange}
                  placeholder="e.g. 12.5" className="form-input-h" style={{ paddingLeft: 38 }} disabled={isSaving}
                />
              </div>
            </div>
            <div className="form-group-h">
              <label htmlFor="soil_type" className="form-label-h">Soil Type</label>
              <div style={{ position: 'relative' }}>
                <Layers size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
                <input
                  type="text" id="soil_type" name="soil_type" list="soil-type-options"
                  value={formData.soil_type} onChange={handleChange}
                  placeholder="e.g. Loamy" className="form-input-h" style={{ paddingLeft: 38 }} maxLength={100} disabled={isSaving}
                />
                <datalist id="soil-type-options">
                  {SOIL_TYPES.map((t) => <option key={t} value={t} />)}
                </datalist>
              </div>
            </div>
            <div className="form-group-h">
              <label htmlFor="farming_method" className="form-label-h">Farming Method</label>
              <div style={{ position: 'relative' }}>
                <Leaf size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
                <input
                  type="text" id="farming_method" name="farming_method" list="farming-method-options"
                  value={formData.farming_method} onChange={handleChange}
                  placeholder="e.g. Organic" className="form-input-h" style={{ paddingLeft: 38 }} maxLength={100} disabled={isSaving}
                />
                <datalist id="farming-method-options">
                  {FARMING_METHODS.map((m) => <option key={m} value={m} />)}
                </datalist>
              </div>
            </div>
          </div>

          <div className="form-group-h full-width" style={{ marginTop: 14 }}>
            <label htmlFor="description" className="form-label-h">Description</label>
            <textarea
              id="description" name="description" rows={3}
              value={formData.description} onChange={handleChange}
              placeholder="Anything special about your farm? (optional)"
              className="form-textarea-h" maxLength={2000} disabled={isSaving}
            />
          </div>

          <div className="action-row">
            <button type="button" className="btn-pill-outline" onClick={() => onNavigate('my-farm')} disabled={isSaving}>
              Cancel
            </button>
            <button type="submit" className="btn-pill" disabled={isSaving}>
              {isSaving ? (
                <>
                  <Loader2 size={16} className="animate-spin" /> Saving…
                </>
              ) : (
                <>
                  <Save size={16} strokeWidth={2.4} /> {isEditMode ? 'Save Changes' : 'Create Farm'}
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      <p className="footer-text" style={{ marginTop: 32 }}>Smart Agriculture AI Platform &copy; 2026</p>
    </div>
  );
}

FarmForm.propTypes = {
  farmId: PropTypes.number,
  onNavigate: PropTypes.func.isRequired,
};

export default FarmForm;
