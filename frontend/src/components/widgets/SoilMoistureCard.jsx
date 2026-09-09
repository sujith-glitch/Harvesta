import { useState, useMemo } from 'react';
import PropTypes from 'prop-types';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, ReferenceDot } from 'recharts';
import { Droplets } from 'lucide-react';

function CustomTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;
  const dataPoint = payload[0].payload;
  return (
    <div
      style={{
        background: '#1A1D21',
        color: '#FFFFFF',
        padding: '7px 11px',
        borderRadius: 8,
        fontSize: 11,
        fontWeight: 600,
        position: 'relative',
        boxShadow: '0 6px 16px rgba(15, 23, 42, 0.25)',
        lineHeight: 1.4,
      }}
    >
      <div>Moisture: <span style={{ color: 'var(--c-lime-soft, #D4E157)', fontWeight: 700 }}>{dataPoint.value}%</span></div>
      <div style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: 10, marginTop: 2 }}>{dataPoint.fullTimestamp || dataPoint.label}</div>
      <span
        style={{
          position: 'absolute',
          bottom: -5,
          left: '50%',
          transform: 'translateX(-50%) rotate(45deg)',
          width: 10,
          height: 10,
          background: '#1A1D21',
          borderRadius: 2,
        }}
      />
    </div>
  );
}

export default function SoilMoistureCard({ history = [], isLoading = false }) {
  const [range, setRange] = useState('24h');

  const chartData = useMemo(() => {
    if (!Array.isArray(history) || history.length === 0) return [];

    const now = Date.now();
    const cutoffMs = (range === '24h' ? 24 : 48) * 60 * 60 * 1000;

    const validPoints = [];
    for (const record of history) {
      if (!record) continue;
      const rawMoisture = record.soil?.current_soil_moisture ?? record.soil?.moisture ?? record.current_soil_moisture;
      if (rawMoisture == null || isNaN(Number(rawMoisture))) continue;

      if (!record.created_at) continue;
      const timestamp = new Date(record.created_at);
      if (isNaN(timestamp.getTime())) continue;

      const age = now - timestamp.getTime();
      // Keep only readings within the selected window (last 24h or 48h)
      if (age <= cutoffMs && age >= -60000) {
        const timeStr = timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const dateStr = timestamp.toLocaleDateString([], { month: 'short', day: 'numeric' });
        validPoints.push({
          id: record.id,
          timeMs: timestamp.getTime(),
          value: Number(Number(rawMoisture).toFixed(1)),
          label: range === '24h' ? timeStr : `${dateStr} ${timeStr}`,
          shortDate: dateStr,
          timeStr,
          fullTimestamp: timestamp.toLocaleDateString(undefined, {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          }),
        });
      }
    }

    // Sort chronologically (oldest -> newest)
    validPoints.sort((a, b) => a.timeMs - b.timeMs);

    return validPoints;
  }, [history, range]);

  const peak = useMemo(() => {
    if (!chartData || chartData.length === 0) return null;
    return chartData.reduce((max, item) => (item.value > max.value ? item : max), chartData[0]);
  }, [chartData]);

  return (
    <div className="analytic-card">
      <div className="analytic-card-head">
        <h3 className="analytic-card-title">
          <Droplets size={18} />
          Soil Moisture
        </h3>
        <div className="toggle-group" role="tablist" aria-label="Time range">
          <button
            type="button"
            className={range === '24h' ? 'active' : ''}
            onClick={() => setRange('24h')}
            role="tab"
            aria-selected={range === '24h'}
          >
            24 hours
          </button>
          <button
            type="button"
            className={range === '48h' ? 'active' : ''}
            onClick={() => setRange('48h')}
            role="tab"
            aria-selected={range === '48h'}
          >
            48 hours
          </button>
        </div>
      </div>

      <div className="soil-chart-wrap">
        {isLoading ? (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: 'var(--c-ink-400)',
              fontSize: 12.5,
            }}
          >
            Loading moisture telemetry…
          </div>
        ) : chartData.length === 0 ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              textAlign: 'center',
              padding: '16px',
              color: 'var(--c-ink-500)',
            }}
          >
            <Droplets size={22} style={{ color: 'var(--c-leaf-300)', marginBottom: 6, opacity: 0.8 }} />
            <p className="muted" style={{ fontSize: 12, margin: 0 }}>
              No soil moisture readings available for this period.
            </p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 12, right: 8, bottom: 4, left: -16 }}>
              <defs>
                <linearGradient id="soilFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="rgba(85, 139, 47, 0.32)" />
                  <stop offset="100%" stopColor="rgba(85, 139, 47, 0)" />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="label"
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 10, fill: 'var(--c-ink-400)' }}
                dy={6}
              />
              <YAxis hide domain={['dataMin - 8', 'dataMax + 8']} />
              <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(15, 23, 42, 0.1)', strokeWidth: 1 }} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#558B2F"
                strokeWidth={2.5}
                fill="url(#soilFill)"
                strokeLinecap="round"
                dot={chartData.length === 1 ? { r: 4, fill: '#558B2F' } : false}
                activeDot={{ r: 4, fill: '#558B2F', stroke: '#FFFFFF', strokeWidth: 2 }}
              />
              {peak && (
                <ReferenceDot
                  x={peak.label}
                  y={peak.value}
                  r={4}
                  fill="#1A1D21"
                  stroke="#FFFFFF"
                  strokeWidth={2}
                />
              )}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>

      <p className="muted" style={{ fontSize: 11.5, marginTop: -2 }}>
        {peak ? (
          <>
            Peak reading: <strong style={{ color: 'var(--c-ink-900)' }}>{peak.value}%</strong> on {peak.label}.
          </>
        ) : (
          <>
            Peak reading: <strong style={{ color: 'var(--c-ink-900)' }}>Not available</strong>.
          </>
        )}
      </p>
    </div>
  );
}

SoilMoistureCard.propTypes = {
  history: PropTypes.arrayOf(PropTypes.object),
  isLoading: PropTypes.bool,
};
