import PropTypes from 'prop-types';
import { Satellite, MapPin, CloudRain, Droplets, Wind, Sparkles, AlertTriangle, Lightbulb, TrendingUp, Loader2, Radio, ThermometerSun } from 'lucide-react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';

export function FieldAnalysisResultCard({ result, error, isLoading }) {
  if (isLoading) {
    return (
      <div className="glass-card flat" style={{ padding: 28, minHeight: 280, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
        <Loader2 size={32} className="animate-spin" style={{ color: 'var(--c-lime-deep)' }} />
        <p className="muted" style={{ fontSize: 13 }}>Fetching real-time weather & computing field analysis…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card flat" style={{ padding: 22 }}>
        <div className="card-head">
          <h3 style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={16} style={{ color: '#EF4444' }} />
            Field Analysis Error
          </h3>
        </div>
        <div className="alert-h error">
          <p>{error}</p>
        </div>
        <p className="muted-2" style={{ fontSize: 12, marginTop: 6 }}>
          Ensure the backend server is active and your soil readings are within valid ranges.
        </p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="glass-card flat" style={{ padding: 28, minHeight: 280, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
        <div className="empty-ico" style={{ marginBottom: 14 }}>
          <Satellite size={26} />
        </div>
        <h4 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>Ready for Real-Time Weather Field Analysis</h4>
        <p className="muted" style={{ fontSize: 13, maxWidth: 320 }}>
          Enter your crop type and soil measurements on the left panel and click <strong className="strong-600">Analyze Field</strong> to fetch real-time weather and explainable irrigation advice.
        </p>
      </div>
    );
  }

  const { location, weather, soil, analysis, prototype_notice } = result;
  const { status, priority, reason, factors } = analysis || {};

  const getStatusConfig = (recStatus) => {
    switch (recStatus?.toUpperCase()) {
      case 'IRRIGATION_REQUIRED':
      case 'IRRIGATION REQUIRED':
        return {
          theme: { bg: 'rgba(239, 68, 68, 0.10)', color: '#EF4444', accent: '#FEE2E2' },
          icon: Droplets,
          badgeText: 'Irrigation Required',
        };
      case 'MONITOR':
        return {
          theme: { bg: 'rgba(249, 168, 37, 0.14)', color: 'var(--c-amber-deep)', accent: '#FEF3C7' },
          icon: AlertTriangle,
          badgeText: 'Monitor Closely',
        };
      case 'NO_IRRIGATION_NEEDED':
      case 'NO IRRIGATION NEEDED':
      default:
        return {
          theme: { bg: 'rgba(76, 175, 80, 0.12)', color: 'var(--c-ok)', accent: '#DCFCE7' },
          icon: Sparkles,
          badgeText: 'No Irrigation Needed',
        };
    }
  };

  const getPriorityTag = (prio) => {
    const p = prio?.toUpperCase() || 'LOW';
    const cls = p === 'HIGH' ? 'tag danger' : p === 'MEDIUM' ? 'tag amber' : 'tag leaf';
    return <span className={cls}>Priority · {p}</span>;
  };

  const statusConfig = getStatusConfig(status);
  const StatusIcon = statusConfig.icon;
  const locationLabel = location?.location_text?.trim();

  // Build a synthetic 24h moisture trend from the current soil moisture
  const moistureNow = soil?.current_soil_moisture ?? 35;
  const trendData = Array.from({ length: 12 }, (_, i) => {
    const hour = i * 2;
    const wave = Math.sin((i / 12) * Math.PI * 2) * 6;
    return { hour: `${hour}h`, moisture: Math.max(0, Math.min(100, moistureNow + wave + (Math.random() * 2 - 1))) };
  });

  return (
    <div className="glass-card flat" style={{ padding: 22 }}>
      <div className="card-head">
        <h3 style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <Satellite size={16} style={{ color: 'var(--c-lime-deep)' }} />
          AI Field Analysis
        </h3>
        {locationLabel ? (
          <span className="tag leaf"><MapPin size={11} />{locationLabel}</span>
        ) : (
          <span className="tag"><Radio size={11} />Live Weather</span>
        )}
      </div>

      {/* Recommendation banner */}
      <div
        className="flex items-center justify-between gap-3 p-4 rounded-2xl flex-wrap"
        style={{ background: statusConfig.theme.bg, color: statusConfig.theme.color, marginBottom: 18 }}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: statusConfig.theme.accent, color: statusConfig.theme.color }}>
            <StatusIcon size={20} strokeWidth={2.2} />
          </div>
          <div>
            <span className="uppercase-mini" style={{ color: statusConfig.theme.color }}>Irrigation Recommendation</span>
            <h4 style={{ fontSize: 18, fontWeight: 700, color: statusConfig.theme.color, marginTop: 2 }}>
              {statusConfig.badgeText}
            </h4>
          </div>
        </div>
        {getPriorityTag(priority)}
      </div>

      {/* Weather conditions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <WeatherTile icon={ThermometerSun} label="Air Temp" value={`${weather?.temperature ?? '--'}°C`} />
        <WeatherTile icon={Droplets} label="Humidity" value={`${weather?.humidity ?? '--'}%`} />
        <WeatherTile icon={CloudRain} label="Precip" value={`${weather?.precipitation ?? '--'} mm`} />
        <WeatherTile icon={Wind} label="Wind" value={`${weather?.wind_speed ?? '--'} km/h`} />
      </div>

      {/* Soil moisture chart — Harvesta-style area chart */}
      <div className="p-4 rounded-2xl border border-black/5 bg-cream-50" style={{ marginBottom: 18 }}>
        <div className="flex items-center justify-between mb-2">
          <div>
            <span className="eyebrow-text">Soil Moisture · 24h</span>
            <h5 style={{ fontSize: 14, fontWeight: 700, marginTop: 2 }}>High level · {Math.max(...trendData.map(d => d.moisture)).toFixed(0)}</h5>
          </div>
          <span className="tag lime">Current · {moistureNow}%</span>
        </div>
        <div style={{ width: '100%', height: 140 }}>
          <ResponsiveContainer>
            <AreaChart data={trendData} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
              <defs>
                <linearGradient id="moistureFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#D4E157" stopOpacity={0.7} />
                  <stop offset="95%" stopColor="#D4E157" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(15,23,42,0.04)" vertical={false} />
              <XAxis dataKey="hour" tick={{ fontSize: 10, fill: '#8590A0' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10, fill: '#8590A0' }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  background: '#1A1D21',
                  border: 'none',
                  borderRadius: 10,
                  color: '#fff',
                  fontSize: 12,
                  padding: '8px 12px',
                }}
                labelStyle={{ color: '#A8B2BD' }}
                formatter={(v) => [`${Number(v).toFixed(1)}%`, 'Moisture']}
              />
              <Area type="monotone" dataKey="moisture" stroke="#A6BC12" strokeWidth={2} fill="url(#moistureFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Soil conditions row */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <SoilTile label="Soil Moisture" value={`${soil?.current_soil_moisture ?? '--'}%`} icon={Droplets} />
        <SoilTile label="Soil pH" value={soil?.soil_ph ?? '--'} icon={Sparkles} />
        <SoilTile label="Soil Temp" value={`${soil?.soil_temperature ?? '--'}°C`} icon={ThermometerSun} />
      </div>

      {/* Reason */}
      {reason && (
        <div className="p-4 rounded-2xl border border-black/5 bg-cream-50" style={{ marginBottom: 14 }}>
          <h5 style={{ fontSize: 12, fontWeight: 700, color: 'var(--c-leaf-500)', display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <Lightbulb size={14} /> Primary Rationale
          </h5>
          <p style={{ fontSize: 13, color: 'var(--c-ink-700)', lineHeight: 1.6 }}>{reason}</p>
        </div>
      )}

      {/* Factors */}
      {factors && factors.length > 0 && (
        <div className="p-4 rounded-2xl border border-black/5 bg-cream-50" style={{ marginBottom: 14 }}>
          <h5 style={{ fontSize: 12, fontWeight: 700, color: 'var(--c-leaf-500)', display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 8 }}>
            <TrendingUp size={14} /> Key Influencing Factors
          </h5>
          <ul style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            {factors.map((factor, index) => (
              <li key={index} className="flex items-start gap-2" style={{ fontSize: 13, color: 'var(--c-ink-700)' }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--c-lime-deep)', flexShrink: 0, marginTop: 6 }} />
                <span>{factor}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {prototype_notice && (
        <div className="alert-h info">
          <AlertTriangle size={14} style={{ flexShrink: 0, marginTop: 2 }} />
          <p style={{ fontSize: 12 }}>{prototype_notice}</p>
        </div>
      )}
    </div>
  );
}

function WeatherTile({ icon: Icon, label, value }) {
  return (
    <div className="flex items-center gap-2 p-3 rounded-xl border border-black/5 bg-white">
      <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(85, 139, 47, 0.10)', color: 'var(--c-leaf-400)' }}>
        <Icon size={14} />
      </div>
      <div className="flex flex-col leading-tight">
        <span className="uppercase-mini">{label}</span>
        <span style={{ fontFamily: 'var(--font-display)', fontSize: 14, fontWeight: 700, color: 'var(--c-ink-900)' }}>{value}</span>
      </div>
    </div>
  );
}

function SoilTile({ icon: Icon, label, value }) {
  return (
    <div className="p-3 rounded-xl border border-black/5 bg-white text-center">
      <div className="w-8 h-8 rounded-lg flex items-center justify-center mx-auto mb-2" style={{ background: 'rgba(212, 225, 87, 0.22)', color: 'var(--c-lime-deep)' }}>
        <Icon size={14} />
      </div>
      <span className="uppercase-mini" style={{ display: 'block', marginBottom: 2 }}>{label}</span>
      <span style={{ fontFamily: 'var(--font-display)', fontSize: 16, fontWeight: 700, color: 'var(--c-ink-900)' }}>{value}</span>
    </div>
  );
}

FieldAnalysisResultCard.propTypes = {
  result: PropTypes.shape({
    location: PropTypes.shape({ location_text: PropTypes.string }),
    weather: PropTypes.shape({
      temperature: PropTypes.number,
      humidity: PropTypes.number,
      precipitation: PropTypes.number,
      wind_speed: PropTypes.number,
    }),
    soil: PropTypes.shape({
      current_soil_moisture: PropTypes.number,
      soil_ph: PropTypes.number,
      soil_temperature: PropTypes.number,
    }),
    analysis: PropTypes.shape({
      status: PropTypes.string,
      priority: PropTypes.string,
      reason: PropTypes.string,
      factors: PropTypes.arrayOf(PropTypes.string),
    }),
    prototype_notice: PropTypes.string,
  }),
  error: PropTypes.string,
  isLoading: PropTypes.bool,
};

export default FieldAnalysisResultCard;
