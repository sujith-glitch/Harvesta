import { useState } from 'react';
import PropTypes from 'prop-types';
import { Sliders, RotateCcw, Sparkles, AlertTriangle, Loader2 } from 'lucide-react';

const CROP_OPTIONS = ['Rice', 'Tomato', 'Maize', 'Cotton', 'Wheat'];

const DEFAULT_FORM_VALUES = {
  crop_type: 'Tomato',
  temperature: '32',
  humidity: '60',
  rainfall: '0',
  current_soil_moisture: '35',
  soil_ph: '6.5',
  soil_temperature: '30',
};

export function FieldInputForm({ onSubmit, isLoading }) {
  const [formData, setFormData] = useState(DEFAULT_FORM_VALUES);
  const [validationError, setValidationError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setValidationError('');
  };

  const validate = () => {
    if (!formData.crop_type) return 'Please select a crop type.';
    const temp = parseFloat(formData.temperature);
    if (isNaN(temp) || temp < -50 || temp > 70) return 'Temperature must be between -50°C and 70°C.';
    const hum = parseFloat(formData.humidity);
    if (isNaN(hum) || hum < 0 || hum > 100) return 'Humidity must be between 0% and 100%.';
    const rain = parseFloat(formData.rainfall);
    if (isNaN(rain) || rain < 0) return 'Rainfall must be 0 mm or greater.';
    const moisture = parseFloat(formData.current_soil_moisture);
    if (isNaN(moisture) || moisture < 0 || moisture > 100) return 'Current Soil Moisture must be between 0% and 100%.';
    const ph = parseFloat(formData.soil_ph);
    if (isNaN(ph) || ph < 0 || ph > 14) return 'Soil pH must be between 0 and 14.';
    const soilTemp = parseFloat(formData.soil_temperature);
    if (isNaN(soilTemp) || soilTemp < -50 || soilTemp > 70) return 'Soil Temperature must be between -50°C and 70°C.';
    return null;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    const error = validate();
    if (error) { setValidationError(error); return; }
    setValidationError('');
    onSubmit({
      crop_type: formData.crop_type,
      temperature: parseFloat(formData.temperature),
      humidity: parseFloat(formData.humidity),
      rainfall: parseFloat(formData.rainfall),
      current_soil_moisture: parseFloat(formData.current_soil_moisture),
      soil_ph: parseFloat(formData.soil_ph),
      soil_temperature: parseFloat(formData.soil_temperature),
    });
  };

  const handleReset = () => {
    setFormData(DEFAULT_FORM_VALUES);
    setValidationError('');
  };

  return (
    <div className="glass-card flat" style={{ padding: 22 }}>
      <div className="card-head">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{ background: 'rgba(85, 139, 47, 0.12)', color: 'var(--c-leaf-400)' }}>
            <Sliders size={18} strokeWidth={2.2} />
          </div>
          <div>
            <span className="eyebrow-text">Manual Mode</span>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginTop: 2 }}>Custom Parameter Recommendation</h3>
          </div>
        </div>
        <button
          type="button"
          onClick={handleReset}
          title="Reset to default values"
          className="btn-pill-outline"
          style={{ padding: '8px 14px', fontSize: 12 }}
        >
          <RotateCcw size={13} />
          Reset
        </button>
      </div>

      {validationError && (
        <div className="alert-h error" role="alert" style={{ marginBottom: 14 }}>
          <AlertTriangle size={16} style={{ flexShrink: 0, marginTop: 2 }} />
          {validationError}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group-h" style={{ marginBottom: 14 }}>
          <label htmlFor="crop_type" className="form-label-h">
            Crop Type <span className="req">*</span>
          </label>
          <select
            id="crop_type"
            name="crop_type"
            value={formData.crop_type}
            onChange={handleChange}
            className="form-select-h"
            disabled={isLoading}
          >
            {CROP_OPTIONS.map((crop) => (
              <option key={crop} value={crop}>{crop}</option>
            ))}
          </select>
        </div>

        <div className="form-grid-h">
          <div className="form-group-h">
            <label htmlFor="temperature" className="form-label-h">Air Temp (°C)</label>
            <input type="number" id="temperature" name="temperature" step="0.1" value={formData.temperature} onChange={handleChange} placeholder="e.g. 32" className="form-input-h" disabled={isLoading} />
          </div>
          <div className="form-group-h">
            <label htmlFor="humidity" className="form-label-h">Humidity (%)</label>
            <input type="number" id="humidity" name="humidity" step="0.1" value={formData.humidity} onChange={handleChange} placeholder="e.g. 60" className="form-input-h" disabled={isLoading} />
          </div>
          <div className="form-group-h">
            <label htmlFor="rainfall" className="form-label-h">Rainfall (mm)</label>
            <input type="number" id="rainfall" name="rainfall" step="0.1" value={formData.rainfall} onChange={handleChange} placeholder="e.g. 0" className="form-input-h" disabled={isLoading} />
          </div>
          <div className="form-group-h">
            <label htmlFor="current_soil_moisture" className="form-label-h">Current Moisture (%)</label>
            <input type="number" id="current_soil_moisture" name="current_soil_moisture" step="0.1" value={formData.current_soil_moisture} onChange={handleChange} placeholder="e.g. 35" className="form-input-h" disabled={isLoading} />
          </div>
          <div className="form-group-h">
            <label htmlFor="soil_ph" className="form-label-h">Soil pH</label>
            <input type="number" id="soil_ph" name="soil_ph" step="0.1" value={formData.soil_ph} onChange={handleChange} placeholder="e.g. 6.5" className="form-input-h" disabled={isLoading} />
          </div>
          <div className="form-group-h">
            <label htmlFor="soil_temperature" className="form-label-h">Soil Temp (°C)</label>
            <input type="number" id="soil_temperature" name="soil_temperature" step="0.1" value={formData.soil_temperature} onChange={handleChange} placeholder="e.g. 30" className="form-input-h" disabled={isLoading} />
          </div>
        </div>

        <div className="action-row">
          <button type="submit" className="btn-pill" disabled={isLoading}>
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Analyzing field…
              </>
            ) : (
              <>
                <Sparkles size={16} strokeWidth={2.4} />
                Analyze Field
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

FieldInputForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  isLoading: PropTypes.bool,
};

export default FieldInputForm;
