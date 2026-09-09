import { useState } from 'react';
import PropTypes from 'prop-types';
import { createCrop, updateCrop } from '../services/api';
import { Save, ArrowLeft, Sprout, CalendarDays, Heart, StickyNote, Loader2, AlertTriangle } from 'lucide-react';

const CROP_NAME_SUGGESTIONS = ['Rice', 'Tomato', 'Maize', 'Cotton', 'Wheat', 'Chili', 'Onion', 'Sugarcane', 'Groundnut', 'Millet'];
const GROWTH_STAGES = ['Seedling', 'Vegetative', 'Flowering', 'Fruiting', 'Maturity'];
const HEALTH_STATUSES = ['Healthy', 'Needs Attention', 'Critical'];

export function CropForm({ farmId, crop, onNavigate }) {
  const isEditMode = Boolean(crop);
  const [formData, setFormData] = useState({
    name: crop?.name || '',
    variety: crop?.variety || '',
    planting_date: crop?.planting_date || '',
    expected_harvest_date: crop?.expected_harvest_date || '',
    growth_stage: crop?.growth_stage || '',
    health_status: crop?.health_status || '',
    notes: crop?.notes || '',
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError('');
  };

  const validate = () => {
    if (!formData.name.trim()) return 'Please give your crop a name.';
    if (formData.planting_date && formData.expected_harvest_date &&
        formData.expected_harvest_date < formData.planting_date) {
      return 'Expected harvest date cannot be before the planting date.';
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
        variety: formData.variety.trim() || null,
        planting_date: formData.planting_date || null,
        expected_harvest_date: formData.expected_harvest_date || null,
        growth_stage: formData.growth_stage || null,
        health_status: formData.health_status || null,
        notes: formData.notes.trim() || null,
      };
      if (isEditMode) { await updateCrop(crop.id, payload); } else { await createCrop(farmId, payload); }
      onNavigate('my-farm');
    } catch (err) {
      console.error('Crop save failed:', err);
      setError(err.message || 'Could not save your crop. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="page-shell">
      <button className="btn-back-h" onClick={() => onNavigate('my-farm')}>
        <ArrowLeft size={13} /> Back to My Farm
      </button>

      <div className="topbar">
        <div className="topbar-left">
          <span className="eyebrow-text">{isEditMode ? 'Edit Crop' : 'Add Crop'}</span>
          <h1 className="topbar-title">{isEditMode ? 'Edit Crop' : 'Add Crop'}</h1>
          <p className="topbar-sub">Only the crop name is required — fill in the rest whenever you are ready.</p>
        </div>
      </div>

      <div className="glass-card flat" style={{ padding: 24, maxWidth: 720 }}>
        {error && (
          <div className="alert-h error" role="alert" style={{ marginBottom: 16 }}>
            <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} /> {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="form-grid-h">
            <div className="form-group-h">
              <label htmlFor="name" className="form-label-h">
                Crop Name <span className="req">*</span>
              </label>
              <div style={{ position: 'relative' }}>
                <Sprout size={15} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--c-ink-300)' }} />
                <input
                  type="text" id="name" name="name" list="crop-name-options"
                  value={formData.name} onChange={handleChange}
                  placeholder="e.g. Tomato" className="form-input-h"
                  style={{ paddingLeft: 38 }} maxLength={255} disabled={isSaving}
                />
                <datalist id="crop-name-options">
                  {CROP_NAME_SUGGESTIONS.map((c) => <option key={c} value={c} />)}
                </datalist>
              </div>
            </div>
            <div className="form-group-h">
              <label htmlFor="variety" className="form-label-h">Variety</label>
              <input
                type="text" id="variety" name="variety" value={formData.variety}
                onChange={handleChange} placeholder="e.g. Roma"
                className="form-input-h" maxLength={255} disabled={isSaving}
              />
            </div>
            <div className="form-group-h">
              <label htmlFor="planting_date" className="form-label-h">Planting Date</label>
              <input
                type="date" id="planting_date" name="planting_date"
                value={formData.planting_date} onChange={handleChange}
                className="form-input-h" disabled={isSaving}
              />
            </div>
            <div className="form-group-h">
              <label htmlFor="expected_harvest_date" className="form-label-h">Expected Harvest Date</label>
              <input
                type="date" id="expected_harvest_date" name="expected_harvest_date"
                value={formData.expected_harvest_date} onChange={handleChange}
                className="form-input-h" disabled={isSaving}
              />
            </div>
            <div className="form-group-h">
              <label htmlFor="growth_stage" className="form-label-h">Growth Stage</label>
              <select
                id="growth_stage" name="growth_stage" value={formData.growth_stage}
                onChange={handleChange} className="form-select-h" disabled={isSaving}
              >
                <option value="">Select stage (optional)</option>
                {GROWTH_STAGES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div className="form-group-h">
              <label htmlFor="health_status" className="form-label-h">Health Status</label>
              <select
                id="health_status" name="health_status" value={formData.health_status}
                onChange={handleChange} className="form-select-h" disabled={isSaving}
              >
                <option value="">Select status (optional)</option>
                {HEALTH_STATUSES.map((h) => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>
          </div>

          <div className="form-group-h full-width" style={{ marginTop: 14 }}>
            <label htmlFor="notes" className="form-label-h">Notes</label>
            <textarea
              id="notes" name="notes" rows={3} value={formData.notes}
              onChange={handleChange} placeholder="Observations, treatments, reminders... (optional)"
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
                  <Save size={16} strokeWidth={2.4} /> {isEditMode ? 'Save Changes' : 'Add Crop'}
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

CropForm.propTypes = {
  farmId: PropTypes.number,
  crop: PropTypes.object,
  onNavigate: PropTypes.func.isRequired,
};

export default CropForm;
