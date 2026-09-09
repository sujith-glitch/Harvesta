import { useCallback, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { ArrowLeft, RefreshCw, Radio, Tractor } from 'lucide-react';
import { getSensorDevices, getSensorReadings, getInventory } from '../services/api';
import { usePreferences } from '../context/PreferencesContext';
import DashboardDetailDialog from '../components/DashboardDetailDialog';
import { formatRecordedAt } from '../utils/dashboardDetails';

export default function EquipmentPage({ onNavigate }) {
  const { t } = usePreferences();
  const [devices, setDevices] = useState([]);
  const [items, setItems] = useState([]);
  const [readings, setReadings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selected, setSelected] = useState(null);
  const [readingError, setReadingError] = useState('');
  const [readingLoading, setReadingLoading] = useState(false);
  const load = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const [deviceData, inventoryData] = await Promise.all([getSensorDevices(), getInventory()]);
      setDevices(deviceData.devices || []);
      setItems((inventoryData.items || []).filter((item) => ['Equipment', 'Tools'].includes(item.category)));
    } catch (err) { setError(err.message || 'Equipment could not be loaded. Please try again.'); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!selected) return;
    let cancelled = false;
    setReadings([]); setReadingError(''); setReadingLoading(true);
    getSensorReadings({ device_id: selected.id, limit: 10 })
      .then((result) => { if (!cancelled) setReadings(result.readings || []); })
      .catch((err) => { if (!cancelled) setReadingError(err.message || 'Could not load readings.'); })
      .finally(() => { if (!cancelled) setReadingLoading(false); });
    return () => { cancelled = true; };
  }, [selected]);
  return <section className="page-shell utility-page">
    <button type="button" className="btn-back-h" onClick={() => onNavigate('dashboard')}><ArrowLeft size={16} /> {t('backDashboard')}</button>
    <div className="topbar">
      <div><h1 className="topbar-title">{t('equipment')}</h1><p className="topbar-sub">Your registered sensors, tools and farm equipment.</p></div>
      <button type="button" className="btn-pill-outline" onClick={load} disabled={loading}><RefreshCw size={16} /> Refresh</button>
    </div>
    {error && <p className="alert-h error" role="alert">{error}</p>}
    {loading ? <p role="status">{t('loading')}</p> : !error && <>
      <div className="analytic-card">
        <h2 className="analytic-card-title"><Radio size={20} /> Sensor gateways</h2>
        {devices.length ? <div className="equipment-grid">{devices.map((device) => (
          <button type="button" className="equipment-device" key={device.id} onClick={() => setSelected(device)} aria-haspopup="dialog">
            <strong>{device.name}</strong><span>{device.device_type}</span>
            <span>Recorded status: {device.status}</span>
            <span>Last received: {formatRecordedAt(device.last_seen_at)}</span>
            <span className="equipment-device-action">View readings →</span>
          </button>
        ))}</div> : <p>No sensor gateways are registered yet. When your hardware is connected, its saved readings will appear here.</p>}
        <p className="muted">A registered device is not necessarily online. Check its last received time. No sensor readings are simulated here.</p>
      </div>
      <div className="analytic-card" style={{ marginTop: 20 }}>
        <h2 className="analytic-card-title"><Tractor size={20} /> Tools & equipment</h2>
        {items.length ? <div className="equipment-grid">{items.map((item) => (
          <button type="button" className="equipment-device" key={item.id} onClick={() => onNavigate('inventory')}>
            <strong>{item.name}</strong><span>{item.quantity} {item.unit}</span>
            <span>{item.notes || item.category}</span><span className="equipment-device-action">Manage in Inventory →</span>
          </button>
        ))}</div> : <p>No tools or equipment saved. Add items under the Tools or Equipment category in Inventory.</p>}
        <button type="button" className="btn-pill" onClick={() => onNavigate('inventory')}>Open Inventory</button>
      </div>
    </>}
    {selected && <DashboardDetailDialog title={selected.name} onClose={() => setSelected(null)}>
      <div className="dashboard-detail-body">
        <p>Latest 10 saved readings for this gateway.</p>
        {readingLoading ? <p role="status">{t('loading')}</p> : readingError ? <p role="alert">{readingError}</p> : readings.length ? readings.map((reading) => (
          <div key={reading.id}>
            <h3>{formatRecordedAt(reading.recorded_at)}</h3>
            <dl className="dashboard-detail-facts">
              {[['soil_moisture', 'Soil moisture', '%'], ['soil_temperature', 'Soil temperature', ' °C'],
                ['soil_ph', 'Soil pH', ''], ['air_humidity', 'Humidity', '%'], ['air_temperature', 'Air temperature', ' °C'],
                ['nitrogen', 'Nitrogen', ' mg/kg'], ['phosphorus', 'Phosphorus', ' mg/kg'], ['potassium', 'Potassium', ' mg/kg'],
              ].map(([key, label, unit]) => <div key={key}><dt>{label}</dt><dd>{reading[key] == null ? 'Not available' : `${reading[key]}${unit}`}</dd></div>)}
            </dl>
          </div>
        )) : <p>No readings have been received from this gateway yet.</p>}
      </div>
    </DashboardDetailDialog>}
  </section>;
}
EquipmentPage.propTypes = { onNavigate: PropTypes.func.isRequired };
