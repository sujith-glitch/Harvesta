import { useState, useEffect, useRef, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  Camera,
  Upload,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  ShieldAlert,
  Bug,
  Leaf,
  Trash2,
  Loader2,
  RefreshCw,
  Info,
  Layers,
  ArrowRight,
} from 'lucide-react';
import {
  scanCropDisease,
  getDiseaseScans,
  deleteDiseaseScan,
  getFarms,
  getFarmCrops,
} from '../services/api';

function formatScanDate(dateString) {
  if (!dateString) return '';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return '';
    return d.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return '';
  }
}

export function DiseaseScan({ onNavigate }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [farms, setFarms] = useState([]);
  const [selectedFarmId, setSelectedFarmId] = useState('');
  const [crops, setCrops] = useState([]);
  const [selectedCropId, setSelectedCropId] = useState('');

  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [scanError, setScanError] = useState(null);

  const [history, setHistory] = useState([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [deletingId, setDeletingId] = useState(null);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  // Load farms
  useEffect(() => {
    async function loadFarms() {
      try {
        const farmList = await getFarms();
        setFarms(farmList || []);
      } catch (err) {
        console.error('Failed to load farms:', err);
      }
    }
    loadFarms();
  }, []);

  // Load crops when farm changes
  useEffect(() => {
    async function loadCrops() {
      if (!selectedFarmId) {
        setCrops([]);
        setSelectedCropId('');
        return;
      }
      try {
        const cropList = await getFarmCrops(selectedFarmId);
        setCrops(cropList || []);
      } catch (err) {
        console.error('Failed to load crops:', err);
      }
    }
    loadCrops();
  }, [selectedFarmId]);

  // Load scan history
  const loadHistory = useCallback(async () => {
    setIsHistoryLoading(true);
    try {
      const res = await getDiseaseScans({ limit: 20 });
      setHistory(res?.scans || []);
    } catch (err) {
      console.error('Failed to load scan history:', err);
    } finally {
      setIsHistoryLoading(false);
    }
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleFileChange = (file) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      setScanError('Please select a valid image file (JPEG, PNG, or WebP).');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setScanError('Image file size exceeds the 5.0 MB maximum limit.');
      return;
    }

    setScanError(null);
    setSelectedFile(file);

    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleScanSubmit = async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      setScanError('Please upload or capture a crop leaf photograph to scan.');
      return;
    }

    setIsScanning(true);
    setScanError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    if (selectedFarmId) formData.append('farm_id', selectedFarmId);
    if (selectedCropId) formData.append('crop_id', selectedCropId);

    try {
      const result = await scanCropDisease(formData);
      setScanResult(result);
      await loadHistory();
    } catch (err) {
      console.error('Disease scan error:', err);
      setScanError(err.message || 'Image screening failed. Please ensure the leaf is clearly visible and try again.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleDeleteScan = async (scanId) => {
    if (!window.confirm('Delete this disease scan record?')) return;
    setDeletingId(scanId);
    try {
      await deleteDiseaseScan(scanId);
      setHistory((prev) => prev.filter((s) => s.id !== scanId));
      if (scanResult && scanResult.id === scanId) {
        setScanResult(null);
      }
    } catch (err) {
      console.error('Failed to delete scan:', err);
      alert(err.message || 'Failed to delete scan record.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setScanResult(null);
    setScanError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  const urgencyColor = (urgency) => {
    switch (urgency?.toUpperCase()) {
      case 'HIGH':
        return { bg: '#fee2e2', text: '#dc2626', border: '#fecaca' };
      case 'MEDIUM':
        return { bg: '#fef3c7', text: '#d97706', border: '#fde68a' };
      case 'LOW':
      default:
        return { bg: '#dcfce7', text: '#15803d', border: '#bbf7d0' };
    }
  };

  return (
    <div className="page-shell" style={{ maxWidth: 1080, margin: '0 auto', paddingTop: 28, paddingBottom: 48 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <span className="eyebrow-text">Computer Vision Diagnostics</span>
        <h1 style={{ fontSize: 24, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 10, margin: '4px 0 0' }}>
          <Sparkles size={24} style={{ color: 'var(--c-leaf-500)' }} />
          Crop Disease Vision AI
        </h1>
        <p className="muted" style={{ fontSize: 13, marginTop: 4 }}>
          Upload or capture a close-up photograph of affected crop foliage for immediate symptom classification and management guidance.
        </p>
      </div>

      {/* Main Grid: Upload/Scan Form on Left, Diagnostic Result on Right */}
      <div className="grid gap-6 grid-cols-1 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]" style={{ marginBottom: 32 }}>
        {/* Left Column: Image Upload Card */}
        <div className="analytic-card" style={{ padding: 22, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <Camera size={18} style={{ color: 'var(--c-leaf-600)' }} />
              Leaf Photograph Upload
            </h2>
            {selectedFile && (
              <button
                type="button"
                className="btn-text"
                onClick={handleReset}
                style={{ fontSize: 12, color: 'var(--c-ink-400)' }}
              >
                Clear
              </button>
            )}
          </div>

          <form onSubmit={handleScanSubmit} style={{ display: 'flex', flexDirection: 'column', flex: 1, gap: 16 }}>
            {/* Dropzone */}
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onClick={() => fileInputRef.current?.click()}
              style={{
                border: '2px dashed',
                borderColor: previewUrl ? 'var(--c-leaf-400)' : 'var(--c-border)',
                borderRadius: 12,
                padding: previewUrl ? 12 : 28,
                background: previewUrl ? 'rgba(240, 253, 244, 0.4)' : 'var(--c-ink-50)',
                textAlign: 'center',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: 190,
              }}
            >
              {previewUrl ? (
                <div style={{ position: 'relative', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <img
                    src={previewUrl}
                    alt="Leaf Preview"
                    style={{
                      maxHeight: 180,
                      maxWidth: '100%',
                      borderRadius: 8,
                      objectFit: 'contain',
                      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                    }}
                  />
                  <span style={{ fontSize: 11, color: 'var(--c-leaf-700)', marginTop: 8, fontWeight: 600 }}>
                    Click or drag new image to replace
                  </span>
                </div>
              ) : (
                <>
                  <div
                    style={{
                      width: 44,
                      height: 44,
                      borderRadius: '50%',
                      background: 'var(--c-leaf-100)',
                      color: 'var(--c-leaf-600)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginBottom: 10,
                    }}
                  >
                    <Upload size={20} />
                  </div>
                  <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--c-ink-800)' }}>
                    Drop leaf photo here or browse
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--c-ink-400)', marginTop: 4 }}>
                    Supports JPEG, PNG, WebP up to 5 MB
                  </span>
                </>
              )}
            </div>

            {/* Hidden File Inputs */}
            <input
              type="file"
              ref={fileInputRef}
              accept="image/*"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
            />
            <input
              type="file"
              ref={cameraInputRef}
              accept="image/*"
              capture="environment"
              style={{ display: 'none' }}
              onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
            />

            {/* Action Buttons for Upload / Camera */}
            <div style={{ display: 'flex', gap: 10 }}>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => fileInputRef.current?.click()}
                style={{ flex: 1, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: 13 }}
              >
                <Upload size={14} /> Browse Files
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => cameraInputRef.current?.click()}
                style={{ flex: 1, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: 6, fontSize: 13 }}
              >
                <Camera size={14} /> Take Photo
              </button>
            </div>

            {/* Optional Farm & Crop Association */}
            <div className="disease-scan-field-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 4 }}>
              <div>
                <label className="field-label" style={{ fontSize: 12 }}>
                  Farm (Optional)
                </label>
                <select
                  className="harvesta-input"
                  value={selectedFarmId}
                  onChange={(e) => setSelectedFarmId(e.target.value)}
                  style={{ fontSize: 13 }}
                >
                  <option value="">-- General Scan --</option>
                  {farms.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="field-label" style={{ fontSize: 12 }}>
                  Crop (Optional)
                </label>
                <select
                  className="harvesta-input"
                  value={selectedCropId}
                  onChange={(e) => setSelectedCropId(e.target.value)}
                  disabled={!selectedFarmId || crops.length === 0}
                  style={{ fontSize: 13 }}
                >
                  <option value="">-- Select Crop --</option>
                  {crops.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} ({c.growth_stage || 'Planted'})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Scan Submit Button */}
            <button
              type="submit"
              className="btn-primary"
              disabled={isScanning || !selectedFile}
              style={{
                marginTop: 8,
                padding: '12px 18px',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                fontSize: 14,
                fontWeight: 700,
              }}
            >
              {isScanning ? (
                <>
                  <Loader2 size={16} className="animate-spin" />
                  Analyzing Foliage Patterns…
                </>
              ) : (
                <>
                  <Sparkles size={16} />
                  Run AI Disease Screening
                </>
              )}
            </button>
          </form>

          {scanError && (
            <div
              style={{
                marginTop: 14,
                padding: '10px 14px',
                borderRadius: 8,
                background: '#fef2f2',
                border: '1px solid #fecaca',
                color: '#991b1b',
                display: 'flex',
                alignItems: 'flex-start',
                gap: 8,
                fontSize: 12,
              }}
            >
              <AlertTriangle size={15} style={{ color: '#dc2626', flexShrink: 0, marginTop: 1 }} />
              <span>{scanError}</span>
            </div>
          )}
        </div>

        {/* Right Column: Diagnostic Result Card */}
        <div className="analytic-card" style={{ padding: 22, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <Layers size={18} style={{ color: 'var(--c-leaf-600)' }} />
              Diagnostic Screening Report
            </h2>
            {scanResult && (
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: 6,
                  background: urgencyColor(scanResult.urgency).bg,
                  color: urgencyColor(scanResult.urgency).text,
                  border: `1px solid ${urgencyColor(scanResult.urgency).border}`,
                }}
              >
                {scanResult.urgency} URGENCY
              </span>
            )}
          </div>

          {!scanResult && !isScanning && (
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 32,
                textAlign: 'center',
                background: 'var(--c-ink-50)',
                borderRadius: 12,
                border: '1px dashed var(--c-border)',
              }}
            >
              <Leaf size={36} style={{ color: 'var(--c-ink-300)', marginBottom: 12, strokeWidth: 1.5 }} />
              <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--c-ink-700)' }}>
                No active scan result
              </span>
              <p className="muted" style={{ fontSize: 12, maxWidth: 320, marginTop: 4 }}>
                Upload or capture a leaf photo on the left to view computer vision analysis, disease confidence, and agronomic management steps.
              </p>
            </div>
          )}

          {isScanning && (
            <div
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 40,
                textAlign: 'center',
              }}
            >
              <Loader2 size={32} className="animate-spin" style={{ color: 'var(--c-leaf-500)', marginBottom: 16 }} />
              <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--c-ink-900)' }}>
                Extracting Spatial-Spectral Features…
              </span>
              <p className="muted" style={{ fontSize: 13, marginTop: 6, maxWidth: 280 }}>
                Matching color moments, lesion morphology, and texture gradients against benchmark crop profiles.
              </p>
            </div>
          )}

          {scanResult && !isScanning && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Primary Match Banner */}
              <div
                style={{
                  padding: 16,
                  borderRadius: 10,
                  background: scanResult.is_healthy ? '#f0fdf4' : '#fffbeb',
                  border: '1px solid',
                  borderColor: scanResult.is_healthy ? '#bbf7d0' : '#fef3c7',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--c-ink-500)', textTransform: 'uppercase' }}>
                    Identified Condition
                  </span>
                  <span style={{ fontSize: 13, fontWeight: 800, color: scanResult.is_healthy ? '#15803d' : '#b45309' }}>
                    {Math.round(scanResult.confidence * 100)}% Match
                  </span>
                </div>

                <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--c-ink-950)' }}>
                  {scanResult.display_name}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 12, fontWeight: 600, padding: '2px 8px', borderRadius: 4, background: 'var(--c-card-bg)', border: '1px solid var(--c-border)' }}>
                    Crop: <strong>{scanResult.predicted_crop}</strong>
                  </span>
                  <span style={{ fontSize: 12, fontWeight: 600, padding: '2px 8px', borderRadius: 4, background: 'var(--c-card-bg)', border: '1px solid var(--c-border)' }}>
                    Status: {scanResult.screening_status === 'review_required'
                      ? '🔎 Human Review Needed'
                      : (scanResult.is_healthy ? '🌿 Healthy' : '⚠️ Candidate Anomaly')}
                  </span>
                </div>

                {scanResult.description && (
                  <p style={{ fontSize: 12, color: 'var(--c-ink-600)', margin: '10px 0 0', lineHeight: 1.45 }}>
                    {scanResult.description}
                  </p>
                )}
              </div>

              {/* Confidence Meter Bar */}
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4, fontWeight: 600, color: 'var(--c-ink-600)' }}>
                  <span>Screening Confidence</span>
                  <span>{Math.round(scanResult.confidence * 100)}%</span>
                </div>
                <div style={{ height: 8, borderRadius: 4, background: 'var(--c-ink-100)', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${Math.min(100, Math.max(5, scanResult.confidence * 100))}%`,
                      background: scanResult.is_healthy ? 'var(--c-leaf-500)' : 'var(--c-amber-500)',
                      borderRadius: 4,
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>

              {/* Agronomic Recommendations */}
              {scanResult.recommendations && scanResult.recommendations.length > 0 && (
                <div>
                  <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--c-ink-900)', display: 'block', marginBottom: 8 }}>
                    Recommended Agronomic Next Steps
                  </span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                    {scanResult.recommendations.map((rec, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 8,
                          fontSize: 12,
                          color: 'var(--c-ink-700)',
                          background: 'var(--c-ink-50)',
                          padding: '8px 12px',
                          borderRadius: 8,
                          lineHeight: 1.4,
                        }}
                      >
                        <ArrowRight size={14} style={{ color: 'var(--c-leaf-600)', flexShrink: 0, marginTop: 2 }} />
                        <span>{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Candidate Matches Breakdown */}
              {scanResult.top_predictions && scanResult.top_predictions.length > 1 && (
                <div>
                  <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--c-ink-500)', display: 'block', marginBottom: 6, textTransform: 'uppercase' }}>
                    Candidate Predictions
                  </span>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {scanResult.top_predictions.map((item, idx) => (
                      <div
                        key={idx}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          fontSize: 12,
                          padding: '4px 8px',
                          background: idx === 0 ? 'var(--c-leaf-50)' : 'transparent',
                          borderRadius: 4,
                        }}
                      >
                        <span style={{ color: 'var(--c-ink-800)', fontWeight: idx === 0 ? 600 : 400 }}>
                          {item.label}
                        </span>
                        <span style={{ color: 'var(--c-ink-500)', fontWeight: 600 }}>
                          {Math.round(item.confidence * 100)}%
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Disclaimer */}
              <div
                style={{
                  padding: '10px 12px',
                  borderRadius: 8,
                  background: 'rgba(212, 225, 87, 0.08)',
                  border: '1px solid var(--c-border)',
                  fontSize: 11,
                  color: 'var(--c-ink-500)',
                  lineHeight: 1.4,
                }}
              >
                <strong>Notice:</strong> {scanResult.disclaimer}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* History Section */}
      <div className="analytic-card" style={{ padding: 22 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <Leaf size={20} style={{ color: 'var(--c-leaf-600)' }} />
              Recent Field Scans
            </h2>
            <p className="muted" style={{ fontSize: 13, margin: '2px 0 0' }}>
              Historical crop disease screening records for your account.
            </p>
          </div>

          <button
            type="button"
            className="btn-secondary"
            onClick={loadHistory}
            disabled={isHistoryLoading}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12 }}
          >
            <RefreshCw size={13} className={isHistoryLoading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>

        {isHistoryLoading ? (
          <div style={{ padding: 32, textAlign: 'center' }}>
            <Loader2 size={24} className="animate-spin" style={{ color: 'var(--c-leaf-500)', margin: '0 auto 8px' }} />
            <span style={{ fontSize: 13, color: 'var(--c-ink-500)' }}>Loading scan history…</span>
          </div>
        ) : history.length === 0 ? (
          <div style={{ padding: 32, textAlign: 'center', color: 'var(--c-ink-400)', fontSize: 13 }}>
            No previous crop disease scans recorded. Run your first leaf screening above.
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 14 }}>
            {history.map((scan) => {
              const isHealthy = scan.predicted_disease?.toLowerCase() === 'healthy';
              return (
                <div
                  key={scan.id}
                  style={{
                    padding: 14,
                    borderRadius: 10,
                    border: '1px solid var(--c-border)',
                    background: 'var(--c-card-bg)',
                    boxShadow: 'var(--c-shadow-sm)',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: 10,
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: 4,
                          background: isHealthy ? '#dcfce7' : '#fee2e2',
                          color: isHealthy ? '#15803d' : '#dc2626',
                        }}
                      >
                        {scan.predicted_crop || 'Crop'}
                      </span>
                      <span style={{ fontSize: 11, color: 'var(--c-ink-400)' }}>
                        {formatScanDate(scan.created_at)}
                      </span>
                    </div>

                    <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--c-ink-900)' }}>
                      {scan.predicted_disease || 'Diagnosis'}
                    </div>

                    {scan.confidence != null && (
                      <span style={{ fontSize: 12, color: 'var(--c-ink-500)', fontWeight: 600, marginTop: 2, display: 'block' }}>
                        Confidence: {Math.round(scan.confidence * 100)}%
                      </span>
                    )}

                    {scan.recommendation && (
                      <p
                        style={{
                          fontSize: 12,
                          color: 'var(--c-ink-600)',
                          margin: '6px 0 0',
                          lineHeight: 1.4,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                        }}
                      >
                        {scan.recommendation}
                      </p>
                    )}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: 8, borderTop: '1px solid var(--c-ink-100)' }}>
                    <button
                      type="button"
                      onClick={() => handleDeleteScan(scan.id)}
                      disabled={deletingId === scan.id}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        color: 'var(--c-ink-400)',
                        cursor: 'pointer',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        fontSize: 12,
                        transition: 'color 0.15s ease',
                      }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = '#dc2626')}
                      onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--c-ink-400)')}
                    >
                      {deletingId === scan.id ? <Loader2 size={12} className="animate-spin" /> : <Trash2 size={12} />}
                      Delete
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

DiseaseScan.propTypes = {
  onNavigate: PropTypes.func,
};

export default DiseaseScan;
