import PropTypes from 'prop-types';
import { formatRecordedAt } from '../utils/dashboardDetails';

const value = (number, unit = '') => number == null ? 'Not available' : `${number}${unit}`;

function Facts({ items }) {
  return <dl className="dashboard-detail-facts">{items.map(([label, content]) => (
    <div key={label}><dt>{label}</dt><dd>{content ?? 'Not available'}</dd></div>
  ))}</dl>;
}
Facts.propTypes = { items: PropTypes.array.isRequired };

export default function DashboardDetails({ type, farm, homeData, location, sensor, analysis, onLocate, onNavigate }) {
  const farmAddress = [farm?.location, farm?.district, farm?.state, farm?.country].filter(Boolean).join(', ');
  const go = (view, params) => () => onNavigate(view, params);
  const equipmentButton = <button type="button" className="btn-pill" onClick={go('equipment')}>Open equipment & sensors</button>;
  const analysisButton = <button type="button" className="btn-pill" onClick={go('analysis')}>Open AI analysis</button>;

  if (type === 'location') {
    const messages = {
      locating: 'Finding your device location…',
      denied: 'Location permission is blocked. Allow Location in your browser site settings, then try again.',
      insecure: 'This browser requires HTTPS for device location. On your laptop, localhost works too. On your phone, a plain HTTP Wi-Fi address cannot request GPS.',
      unsupported: 'This browser does not provide device location.',
      unavailable: 'Your device could not provide a location. Check location services and try again.',
      timeout: 'The location request timed out. Move somewhere with a better signal and try again.',
      ready: 'This is your device location, not necessarily the location of your farm.',
    };
    return <div className="dashboard-detail-body">
      <p>{messages[location.status] || messages.unavailable}</p>
      <Facts items={[
        ['Device coordinates', location.label || 'Not available'],
        ['Estimated accuracy', location.accuracy == null ? 'Not available' : `Within about ${location.accuracy} metres`],
        ['Location checked', formatRecordedAt(location.checkedAt)],
        ['Saved farm address', farmAddress || 'No farm address saved'],
      ]} />
      <div className="dashboard-detail-actions">
        <button type="button" className="btn-pill" disabled={location.status === 'locating'} onClick={onLocate}>Refresh device location</button>
        {Number.isFinite(location.latitude) && Number.isFinite(location.longitude) &&
          <a className="btn-pill-outline" href={`https://www.google.com/maps/search/?api=1&query=${location.latitude},${location.longitude}`} target="_blank" rel="noopener noreferrer">View on Google Maps</a>}
        <button type="button" className="btn-pill-outline" onClick={go('my-farm')}>View saved farm</button>
      </div>
    </div>;
  }
  if (type === 'area') return <div className="dashboard-detail-body">
    <p>This shows the farm area you saved. It is not a satellite measurement or a calculation of planted crop coverage.</p>
    <Facts items={[
      ['Farm', farm?.name || 'No farm added'],
      ['Saved area', value(farm?.size ?? farm?.size_acres, ' acres')],
      ['Soil type', farm?.soil_type], ['Farming method', farm?.farming_method],
      ['Saved crops', homeData?.total_crops ?? 'Not available'],
    ]} />
    <button type="button" className="btn-pill" onClick={go('farm-form', farm?.id ? { farmId: farm.id } : {})}>{farm ? 'Edit farm details' : 'Add your farm'}</button>
  </div>;
  if (type === 'npk') return <div className="dashboard-detail-body">
    <p>NPK means nitrogen, phosphorus and potassium. These are measured nutrient readings, not values inferred from your irrigation analysis.</p>
    <Facts items={[
      ['Nitrogen (N)', value(sensor?.nitrogen, ' mg/kg')],
      ['Phosphorus (P)', value(sensor?.phosphorus, ' mg/kg')],
      ['Potassium (K)', value(sensor?.potassium, ' mg/kg')],
      ['Sensor reading recorded', formatRecordedAt(sensor?.recorded_at)],
    ]} />
    <p className="muted">Missing values mean no corresponding measurement was received. Confirm sensor calibration and units before making nutrient decisions.</p>
    {equipmentButton}
  </div>;
  if (type === 'humidity' || type === 'climate') return <div className="dashboard-detail-body">
    <p>Saved weather and sensor measurements are shown below. They are not a live forecast. Run a new Live Weather analysis for updated weather.</p>
    <Facts items={[
      ['Sensor humidity', value(sensor?.air_humidity, '%')],
      ['Sensor air temperature', value(sensor?.air_temperature, ' °C')],
      ['Sensor recorded', formatRecordedAt(sensor?.recorded_at)],
      ['Weather humidity', value(analysis?.weather?.humidity, '%')],
      ['Weather air temperature', value(analysis?.weather?.temperature, ' °C')],
      ['Precipitation', value(analysis?.weather?.precipitation ?? analysis?.weather?.rainfall, ' mm')],
      ['Wind speed', value(analysis?.weather?.wind_speed, ' km/h')],
      ['Weather saved with analysis', formatRecordedAt(analysis?.created_at)],
    ]} />
    <p className="muted">Weather values belong to the location used for that saved analysis; they do not automatically follow your device GPS.</p>
    {analysisButton}
  </div>;
  if (type === 'soil') return <div className="dashboard-detail-body">
    <p>Sensor readings and manually entered analysis values are shown separately.</p>
    <Facts items={[
      ['Sensor soil moisture', value(sensor?.soil_moisture, '%')],
      ['Sensor soil temperature', value(sensor?.soil_temperature, ' °C')],
      ['Sensor soil pH', sensor?.soil_ph],
      ['Sensor recorded', formatRecordedAt(sensor?.recorded_at)],
      ['Analysis input moisture', value(analysis?.soil?.current_soil_moisture, '%')],
      ['Analysis input soil pH', analysis?.soil?.soil_ph],
      ['Analysis saved', formatRecordedAt(analysis?.created_at)],
    ]} />
    <div className="dashboard-detail-actions">{equipmentButton}{analysisButton}</div>
  </div>;
  if (type === 'health') return <div className="dashboard-detail-body">
    <Facts items={[
      ['Crop health summary', value(homeData?.overall_health_percent, '%')],
      ['Saved crops', homeData?.total_crops ?? 'Not available'],
    ]} />
    <p>This is a summary of saved crop health statuses, not a verified land-suitability score. It stays unavailable until crop health information is saved.</p>
    <button type="button" className="btn-pill" onClick={go('my-farm')}>View crops & health</button>
  </div>;
  if (type === 'recommendation') return <div className="dashboard-detail-body">
    <Facts items={[
      ['Crop', analysis?.crop_type], ['Recorded', formatRecordedAt(analysis?.created_at)],
      ['Status', analysis?.analysis?.status?.replaceAll('_', ' ')],
      ['Priority', analysis?.analysis?.priority],
    ]} />
    <p>{analysis?.analysis?.reason || analysis?.analysis?.recommendation || 'Run a field analysis to create your first recommendation.'}</p>
    <p className="muted">This is a saved AI recommendation, not a live sensor reading or professional diagnosis.</p>
    {analysisButton}
  </div>;
  return <div className="dashboard-detail-body">
    <p>No satellite or crop-loss telemetry is connected yet, so a crop-loss report cannot be calculated.</p>
    <p>You can still open your existing field analyses and other available reports.</p>
    <button type="button" className="btn-pill" onClick={go('reports')}>Open available reports</button>
  </div>;
}
DashboardDetails.propTypes = {
  type: PropTypes.string.isRequired,
  farm: PropTypes.object,
  homeData: PropTypes.object,
  location: PropTypes.object.isRequired,
  sensor: PropTypes.object,
  analysis: PropTypes.object,
  onLocate: PropTypes.func.isRequired,
  onNavigate: PropTypes.func.isRequired,
};
