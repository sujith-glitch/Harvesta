import { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import {
  MapPin,
  Ruler,
  FlaskConical,
  Cloud,
  Clock,
  Plus,
  ZoomIn,
  ZoomOut,
  Sparkles,
  Sliders,
  Satellite,
  AlertTriangle,
  ArrowLeft,
} from 'lucide-react';
import HealthBadge from '../components/HealthStatus';
import UserProfile from '../components/UserProfile';
import NotificationBell from '../components/NotificationBell';
import DashboardSummary from '../components/DashboardSummary';
import DashboardTapSurface from '../components/DashboardTapSurface';
import DashboardDetailDialog from '../components/DashboardDetailDialog';
import DashboardDetails from '../components/DashboardDetails';
import { ANALYSIS_FILTERS, filterAnalyses } from '../utils/dashboardDetails';
import NPKLevelsCard from '../components/widgets/NPKLevelsCard';
import LostAreaIndexCard from '../components/widgets/LostAreaIndexCard';
import SoilMoistureCard from '../components/widgets/SoilMoistureCard';
import FarmerPersonaCard from '../components/widgets/FarmerPersonaCard';
import ChatWidget from '../components/widgets/ChatWidget';
import DashboardMotionLayer from '../components/DashboardMotionLayer';
import RealWeatherForm from '../components/RealWeatherForm';
import FieldInputForm from '../components/FieldInputForm';
import FieldAnalysisResultCard from '../components/FieldAnalysisResultCard';
import AIResultCard from '../components/AIResultCard';
import AnalysisHistory from '../components/AnalysisHistory';
import Disclaimer from '../components/Disclaimer';
import {
  checkHealth,
  getFieldAnalysis,
  getIrrigationRecommendation,
  getAnalysisHistory,
  deleteAnalysis,
  getDashboardHome,
  getDashboardSummary,
  getSensorReadings,
} from '../services/api';
import { usePreferences } from '../context/PreferencesContext';

const CROP_EMOJIS = {
  corn: '🌽',
  maize: '🌽',
  carrot: '🥕',
  potato: '🥔',
  wheat: '🌾',
  rice: '🌾',
  'basmati rice': '🌾',
  paddy: '🌾',
  tomato: '🍅',
  cotton: '🌱',
  lettuce: '🥬',
  soybean: '🫘',
  barley: '🌾',
  sugarcane: '🎋',
  onion: '🧅',
  chilli: '🌶️',
  pepper: '🫑',
  garlic: '🧄',
  groundnut: '🥜',
  peanut: '🥜',
};

function getCropEmoji(name = '') {
  return CROP_EMOJIS[name.trim().toLowerCase()] || '🌱';
}

function formatHoursAgo(dateString) {
  if (!dateString) return 'Not available';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return 'Not available';
    const diffMs = Date.now() - d.getTime();
    if (diffMs < 0) return 'Just now';
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    if (diffHours < 1) return '<1h ago';
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  } catch {
    return 'Not available';
  }
}

export function Dashboard({ user, onLogout, onNavigate, view = 'overview', analysisFilter = 'total_analyses' }) {
  const { t } = usePreferences();
  const [detail, setDetail] = useState(null);
  const [mapZoom, setMapZoom] = useState(1);
  const [loadError, setLoadError] = useState('');
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const [isHealthLoading, setIsHealthLoading] = useState(true);
  const [deviceLocation, setDeviceLocation] = useState({
    status: 'locating',
    label: null,
    accuracy: null,
  });

  // Home farm overview data
  const [homeData, setHomeData] = useState(null);
  const [isHomeLoading, setIsHomeLoading] = useState(true);

  // Operational dashboard summary metrics
  const [summaryData, setSummaryData] = useState(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(true);
  const [sensorReadings, setSensorReadings] = useState([]);
  const [isSensorsLoading, setIsSensorsLoading] = useState(true);

  // AI Workspace (kept below the Harvesta widget grid)
  const [activeTab, setActiveTab] = useState('field_analysis');
  const [historyData, setHistoryData] = useState([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(true);
  const [fieldResult, setFieldResult] = useState(null);
  const [isFieldAnalyzing, setIsFieldAnalyzing] = useState(false);
  const [fieldError, setFieldError] = useState(null);
  const [manualResult, setManualResult] = useState(null);
  const [isManualAnalyzing, setIsManualAnalyzing] = useState(false);
  const [manualError, setManualError] = useState(null);

  const verifyHealth = useCallback(async () => {
    setIsHealthLoading(true);
    try {
      const data = await checkHealth();
      setIsBackendOnline(data && data.status === 'ok');
    } catch {
      setIsBackendOnline(false);
    } finally {
      setIsHealthLoading(false);
    }
  }, []);

  const detectDeviceLocation = useCallback(() => {
    if (!window.isSecureContext || !navigator.geolocation) {
      setDeviceLocation({ status: !window.isSecureContext ? 'insecure' : 'unsupported', label: null, accuracy: null });
      return;
    }

    setDeviceLocation((current) => ({ ...current, status: 'locating' }));
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const latitude = Number(coords.latitude).toFixed(4);
        const longitude = Number(coords.longitude).toFixed(4);
        setDeviceLocation({
          status: 'ready',
          label: `GPS ${latitude}, ${longitude}`,
          accuracy: Math.round(coords.accuracy || 0),
          latitude: coords.latitude,
          longitude: coords.longitude,
          checkedAt: new Date().toISOString(),
        });
      },
      (error) => {
        setDeviceLocation({
          status: error?.code === 1 ? 'denied' : error?.code === 3 ? 'timeout' : 'unavailable',
          label: null,
          accuracy: null,
        });
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000,
      },
    );
  }, []);

  const fetchHistory = useCallback(async () => {
    setIsHistoryLoading(true);
    try {
      const hist = await getAnalysisHistory(50, 0);
      setHistoryData(hist);
    } catch (err) {
      console.error('History load error:', err);
      setLoadError('Some saved analyses could not be loaded. Try refreshing the page.');
      if (err.isAuthError) onLogout();
      setHistoryData([]);
    } finally {
      setIsHistoryLoading(false);
    }
  }, [onLogout]);

  const fetchHomeData = useCallback(async () => {
    setIsHomeLoading(true);
    try {
      const data = await getDashboardHome();
      setHomeData(data);
    } catch (err) {
      console.error('Home data load error:', err);
      setLoadError('Your farm overview could not be loaded. Try refreshing the page.');
      if (err.isAuthError) onLogout();
      setHomeData(null);
    } finally {
      setIsHomeLoading(false);
    }
  }, [onLogout]);

  const fetchSummary = useCallback(async () => {
    setIsSummaryLoading(true);
    try {
      const summary = await getDashboardSummary();
      setSummaryData(summary);
    } catch (err) {
      console.error('Summary load error:', err);
      setLoadError('Your analysis totals could not be loaded. Try refreshing the page.');
      if (err.isAuthError) onLogout();
      setSummaryData(null);
    } finally {
      setIsSummaryLoading(false);
    }
  }, [onLogout]);

  const fetchSensorReadings = useCallback(async () => {
    setIsSensorsLoading(true);
    try {
      const data = await getSensorReadings({ limit: 100 });
      setSensorReadings(data?.readings || []);
    } catch (err) {
      console.error('Sensor history load error:', err);
      setLoadError('Sensor readings could not be loaded. Try refreshing the page.');
      if (err.isAuthError) onLogout();
      setSensorReadings([]);
    } finally {
      setIsSensorsLoading(false);
    }
  }, [onLogout]);

  useEffect(() => {
    verifyHealth();
    fetchHistory();
    fetchHomeData();
    fetchSummary();
    fetchSensorReadings();
  }, [verifyHealth, fetchHistory, fetchHomeData, fetchSummary, fetchSensorReadings]);

  useEffect(() => {
    detectDeviceLocation();
  }, [detectDeviceLocation]);

  const handleRealWeatherAnalysis = async (formData) => {
    setIsFieldAnalyzing(true);
    setFieldError(null);
    try {
      const result = await getFieldAnalysis(formData);
      setFieldResult(result);
      await Promise.all([fetchHistory(), fetchHomeData(), fetchSummary()]);
    } catch (err) {
      if (err.isAuthError) { onLogout(); return; }
      setFieldError(err.message || 'Field analysis failed.');
      setFieldResult(null);
    } finally {
      setIsFieldAnalyzing(false);
    }
  };

  const handleManualAnalysis = async (formData) => {
    setIsManualAnalyzing(true);
    setManualError(null);
    try {
      const result = await getIrrigationRecommendation(formData);
      setManualResult(result);
    } catch (err) {
      if (err.isAuthError) { onLogout(); return; }
      setManualError(err.message || 'Irrigation recommendation failed.');
      setManualResult(null);
    } finally {
      setIsManualAnalyzing(false);
    }
  };

  const handleDeleteHistory = async (analysisId) => {
    try {
      await deleteAnalysis(analysisId);
      await Promise.all([fetchHistory(), fetchSummary()]);
    } catch (err) {
      console.error('Failed to delete history record:', err);
      alert(err.message || 'Unable to delete analysis record.');
    }
  };

  const userName = user?.full_name || user?.email || 'Farmer';
  const firstName = userName.split(' ')[0];

  const handleSeeDetails = () => {
    setDetail('recommendation');
  };

  const farm = homeData?.farm;
  const cropsList = homeData?.recent_crops || [];
  const overallHealth = homeData?.overall_health_percent;

  const farmSizeVal = farm?.size != null
    ? `${farm.size} acres`
    : (farm?.size_acres != null ? `${farm.size_acres} acres` : null);

  const farmLocationParts = [farm?.location, farm?.district, farm?.state, farm?.country].filter(Boolean);
  const farmLocationFull = farmLocationParts.length > 0 ? farmLocationParts.join(', ') : null;

  const currentLocationLabel = deviceLocation.status === 'ready'
    ? deviceLocation.label
    : (deviceLocation.status === 'locating'
      ? 'Detecting current location…'
      : (farmLocationFull || (deviceLocation.status === 'denied'
        ? 'Allow location permission'
        : deviceLocation.status === 'insecure' ? 'Current location needs HTTPS' : 'Current location unavailable')));

  const topbarLocationSubtitle = isHomeLoading
    ? 'Loading location…'
    : ([currentLocationLabel, farmSizeVal].filter(Boolean).join(' · '));

  const farmAreaStr = isHomeLoading ? '…' : (farmSizeVal || 'Not available');

  const farmLocationStr = isHomeLoading
    ? '…'
    : currentLocationLabel;

  const latestAnalysis = historyData?.[0] || fieldResult;
  const latestSensor = sensorReadings?.[0];
  const humidityVal = isHistoryLoading || isSensorsLoading
    ? '…'
    : (latestSensor?.air_humidity != null
      ? `${Math.round(latestSensor.air_humidity)}%`
      : (latestAnalysis?.weather?.humidity != null ? `${Math.round(latestAnalysis.weather.humidity)}%` : 'Not available'));

  const latestRecordDate = latestSensor?.recorded_at || historyData?.[0]?.created_at;
  const soilMonitoringStr = isHistoryLoading || isSensorsLoading
    ? '…'
    : (latestRecordDate ? formatHoursAgo(latestRecordDate) : 'Not available');

  const moistureHistory = [
    ...historyData,
    ...sensorReadings.map((reading) => ({
      id: `sensor-${reading.id}`,
      created_at: reading.recorded_at,
      current_soil_moisture: reading.soil_moisture,
    })),
  ];

  const latestRecommendation =
    latestAnalysis?.analysis?.recommendation ||
    latestAnalysis?.analysis?.reason ||
    latestAnalysis?.recommendation?.reason ||
    null;

  const detailTitles = {
    location: t('location'), area: t('plantedArea'), npk: t('currentNpk'),
    humidity: t('humidity'), soil: t('soilMonitoring'), health: 'Crop health',
    recommendation: 'Farming recommendation', loss: 'Crop-loss report',
  };
  const navigateFromDetail = (nextView, params) => { setDetail(null); onNavigate?.(nextView, params); };
  const detailsContent = (type) => <DashboardDetails type={type} farm={farm} homeData={homeData}
    location={deviceLocation} sensor={latestSensor} analysis={latestAnalysis}
    onLocate={detectDeviceLocation} onNavigate={navigateFromDetail} />;

  return (
    <>
      {loadError && <div className="page-shell"><p className="alert-h error" role="alert">{loadError}</p></div>}
      {view === 'overview' && <>
      {/* ============ HERO AERIAL MAP SECTION ============ */}
      <DashboardMotionLayer>
      <DashboardTapSurface zoom={mapZoom}>
        <div className="page-shell" style={{ paddingTop: 0, paddingBottom: 0, position: 'relative', zIndex: 2 }}>
          {/* Top bar */}
          <div className="topbar">
            <div className="topbar-left">
              <span className="eyebrow-text">
                Harvesta · {isHomeLoading ? t('loading') : (farm?.name || t('notAvailable'))}
              </span>
              <h1 className="topbar-title" style={{ display: 'inline-flex', alignItems: 'center', gap: 10 }}>
                <MapPin size={20} style={{ color: 'var(--c-leaf-400)' }} />
                {isHomeLoading ? t('loading') : (farm?.name || t('notAvailable'))}
              </h1>
              <button
                type="button"
                className="topbar-sub dashboard-text-button"
                onClick={() => setDetail('location')}
                aria-haspopup="dialog"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}
                title={deviceLocation.accuracy ? `Current device location, accurate to about ${deviceLocation.accuracy} metres` : undefined}
              >
                <MapPin size={13} /> {topbarLocationSubtitle}
              </button>
            </div>
            <div className="topbar-right">
              <div className="topbar-health"><HealthBadge isOnline={isBackendOnline} isLoading={isHealthLoading} /></div>
              <div className="topbar-account-actions">
                <NotificationBell onNavigate={onNavigate} />
                <UserProfile user={user} onLogout={onLogout} onNavigate={onNavigate} />
              </div>
            </div>
          </div>

          {/* Hero row: metric pills + health pill + farmer persona */}
          <div className="hero-row" style={{ marginTop: 14 }}>
            {/* Left: mini metric pills + crop scroller */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div className="mini-pill-row">
                <button type="button" className="metric-mini dashboard-metric-button" onClick={() => setDetail('area')} aria-haspopup="dialog">
                  <Ruler size={14} /> {t('plantedArea')} · <span className="metric-mini-value">{farmAreaStr}</span>
                </button>
                <button type="button" className="metric-mini dashboard-metric-button" onClick={() => setDetail('npk')} aria-haspopup="dialog">
                  <FlaskConical size={14} /> {t('currentNpk')} · <span className="metric-mini-value">{['nitrogen', 'phosphorus', 'potassium'].some((key) => latestSensor?.[key] != null) ? 'View readings' : t('notAvailable')}</span>
                </button>
                <button type="button" className="metric-mini dashboard-metric-button" onClick={() => setDetail('humidity')} aria-haspopup="dialog">
                  <Cloud size={14} /> {t('humidity')} · <span className="metric-mini-value">{humidityVal}</span>
                </button>
              </div>

              <div className="health-monitoring-row" style={{ display: 'inline-flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
                <button type="button" className="health-score-pill dashboard-metric-button" onClick={() => setDetail('health')} aria-haspopup="dialog">
                  <span
                    className="health-score-value"
                    style={overallHealth == null && !isHomeLoading ? { fontSize: 13, fontWeight: 700, textAlign: 'center', lineHeight: '1.2' } : undefined}
                  >
                    {isHomeLoading ? '…' : (overallHealth != null ? `${overallHealth}%` : 'Not available')}
                  </span>
                  <span className="health-score-label">{t('forCultivation')}</span>
                </button>

                <div className="monitoring-pills" style={{ display: 'flex', flexDirection: 'column', gap: 10, minWidth: 200, flex: 1 }}>
                  <button type="button" className="metric-mini dashboard-metric-button" style={{ alignSelf: 'flex-start' }} onClick={() => setDetail('soil')} aria-haspopup="dialog">
                    <Clock size={14} /> {t('soilMonitoring')} · <span className="metric-mini-value">{soilMonitoringStr}</span>
                  </button>
                  <button type="button" className="metric-mini dashboard-metric-button" style={{ alignSelf: 'flex-start' }} onClick={() => setDetail('location')} aria-haspopup="dialog">
                    <MapPin size={14} /> {t('location')} · <span className="metric-mini-value">{farmLocationStr}</span>
                  </button>
                </div>
              </div>

              {/* Crop scroller */}
              <div className="crop-scroller">
                {cropsList.length > 0 ? (
                  cropsList.map((c) => (
                    <button
                      key={c.id || c.name}
                      type="button"
                      className="crop-icon-pill"
                      onClick={() => onNavigate?.('my-farm')}
                    >
                      <span className="crop-emoji">{getCropEmoji(c.name)}</span>
                      {c.name}
                    </button>
                  ))
                ) : (
                  <span className="muted" style={{ fontSize: 12, padding: '6px 12px', display: 'inline-flex', alignItems: 'center' }}>
                    {isHomeLoading ? t('loadingCrops') : t('noCropsAdded')}
                  </span>
                )}
                <button
                  type="button"
                  className="crop-icon-pill add"
                  onClick={() => onNavigate?.(farm?.id ? 'crop-form' : 'farm-form', farm?.id ? { farmId: farm.id } : {})}
                >
                  <Plus size={14} strokeWidth={2.6} />
                  {t('addCrop')}
                </button>
              </div>
            </div>

            {/* Middle: empty space for map visibility */}
            <div className="hero-map-spacer" style={{ minHeight: 180 }} />

            {/* Right: Farmer persona card */}
            <div className="farmer-card-wrap" style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'flex-end' }}>
              <FarmerPersonaCard
                user={user}
                recommendation={latestRecommendation}
                onSeeDetails={handleSeeDetails}
              />
            </div>
          </div>
        </div>

        {/* Map zoom controls (floating on map) */}
        <div className="map-zoom">
          <button type="button" aria-label="Zoom background in" disabled={mapZoom >= 2} onClick={() => setMapZoom((zoom) => Math.min(2, zoom + 0.25))}><ZoomIn size={16} /></button>
          <button type="button" aria-label="Zoom background out" disabled={mapZoom <= 1} onClick={() => setMapZoom((zoom) => Math.max(1, zoom - 0.25))}><ZoomOut size={16} /></button>
        </div>
      </DashboardTapSurface>
      </DashboardMotionLayer>

      {/* ============ ANALYTICS GRID — 3 cards ============ */}
      <section className="page-shell" style={{ paddingTop: 28, paddingBottom: 32 }}>
        {/* Operational summary ribbon */}
        <div style={{ marginBottom: 20 }}>
          <DashboardSummary summary={summaryData} isLoading={isSummaryLoading} onSelect={(filter) => onNavigate?.('analysis', { filter })} />
        </div>

        <div className="analytics-grid">
          <NPKLevelsCard reading={latestSensor} onAnalyze={() => onNavigate?.('analysis')} onSensorFeed={() => onNavigate?.('equipment')} />
          <LostAreaIndexCard onDetails={() => setDetail('loss')} />
          <SoilMoistureCard history={moistureHistory} isLoading={isHistoryLoading || isSensorsLoading} />
        </div>
      </section>
      </>}

      {view === 'analysis' && <section className="page-shell">
        <button type="button" className="btn-back-h" onClick={() => onNavigate?.('dashboard')}><ArrowLeft size={16} /> {t('backDashboard')}</button>
        {/* Analysis tools open separately, leaving the overview uncluttered. */}
        <div id="ai-workspace">
          <div className="flex items-center justify-between gap-3 flex-wrap" style={{ marginBottom: 14 }}>
            <div>
              <h2 style={{ fontSize: 22, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 10 }}>
                <Sparkles size={20} style={{ color: 'var(--c-lime-deep)' }} />
                {t('aiWorkspace')}
              </h2>
              <p className="muted" style={{ fontSize: 13, marginTop: 2 }}>
                {firstName}, {t('aiWorkspaceIntro')}
              </p>
            </div>
            <div className="segmented" role="tablist" aria-label="Analysis mode">
              <button
                type="button"
                role="tab"
                className={activeTab === 'field_analysis' ? 'active' : ''}
                onClick={() => setActiveTab('field_analysis')}
                aria-selected={activeTab === 'field_analysis'}
              >
                <Satellite size={13} /> {t('liveWeather')}
              </button>
              <button
                type="button"
                role="tab"
                className={activeTab === 'manual_input' ? 'active' : ''}
                onClick={() => setActiveTab('manual_input')}
                aria-selected={activeTab === 'manual_input'}
              >
                <Sliders size={13} /> {t('manual')}
              </button>
            </div>
          </div>

          <div className="grid gap-5 grid-cols-1 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]" style={{ marginBottom: 24 }}>
            {activeTab === 'field_analysis' ? (
              <>
                <RealWeatherForm onSubmit={handleRealWeatherAnalysis} isLoading={isFieldAnalyzing} />
                <FieldAnalysisResultCard result={fieldResult} error={fieldError} isLoading={isFieldAnalyzing} />
              </>
            ) : (
              <>
                <FieldInputForm onSubmit={handleManualAnalysis} isLoading={isManualAnalyzing} />
                <AIResultCard result={manualResult} error={manualError} isLoading={isManualAnalyzing} />
              </>
            )}
          </div>

          <div style={{ marginBottom: 20 }}>
            <label className="dashboard-history-filter">Show saved analyses
              <select value={analysisFilter} onChange={(event) => onNavigate?.('analysis', { filter: event.target.value })}>
                {Object.entries(ANALYSIS_FILTERS).map(([key, label]) => <option key={key} value={key}>{label}</option>)}
              </select>
            </label>
            <p className="muted" style={{ marginBottom: 12 }}>Showing matches from your latest 50 analyses. Open Reports for downloadable records.</p>
            <AnalysisHistory
              history={filterAnalyses(historyData, analysisFilter)}
              isLoading={isHistoryLoading}
              onDelete={handleDeleteHistory}
              onRefresh={() => {
                fetchHistory();
                fetchSummary();
              }}
            />
          </div>

          <div className="analytic-card" style={{ background: 'rgba(212, 225, 87, 0.06)', padding: 16, gap: 8 }}>
            <Disclaimer />
            <p className="footer-text" style={{ fontSize: 11, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <AlertTriangle size={11} style={{ color: 'var(--c-amber-deep)' }} />
              Smart Agriculture AI Platform &copy; 2026 — Harvesta Dashboard v2
            </p>
          </div>
        </div>
      </section>}

      {view === 'climate' && <section className="page-shell">
        <button type="button" className="btn-back-h" onClick={() => onNavigate?.('dashboard')}><ArrowLeft size={16} /> {t('backDashboard')}</button>
        <div className="topbar"><h1 className="topbar-title">{t('climate')}</h1></div>
        <div className="analytic-card">{isHistoryLoading || isSensorsLoading ? <p>{t('loading')}</p> : detailsContent('climate')}</div>
      </section>}

      {detail && <DashboardDetailDialog title={detailTitles[detail]} onClose={() => setDetail(null)}>
        {isHomeLoading || isHistoryLoading || isSensorsLoading ? <p>{t('loading')}</p> : detailsContent(detail)}
      </DashboardDetailDialog>}

      {/* ============ FLOATING CHAT WIDGET ============ */}
      <ChatWidget />
    </>
  );
}

Dashboard.propTypes = {
  user: PropTypes.object.isRequired,
  onLogout: PropTypes.func.isRequired,
  onNavigate: PropTypes.func,
  view: PropTypes.oneOf(['overview', 'analysis', 'climate']),
  analysisFilter: PropTypes.string,
};

export default Dashboard;
