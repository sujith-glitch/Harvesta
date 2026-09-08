import PropTypes from 'prop-types';
import { Bot, Droplets, AlertTriangle, Sparkles, Lightbulb, TrendingUp, Loader2 } from 'lucide-react';
import { ResponsiveContainer, RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts';

export function AIResultCard({ result, error, isLoading }) {
  if (isLoading) {
    return (
      <div className="glass-card flat" style={{ padding: 28, minHeight: 280, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
        <Loader2 size={32} className="animate-spin" style={{ color: 'var(--c-lime-deep)' }} />
        <p className="muted" style={{ fontSize: 13 }}>Analyzing field conditions with AI model…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card flat" style={{ padding: 22 }}>
        <div className="card-head">
          <h3 style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={16} style={{ color: '#EF4444' }} /> Analysis Error
          </h3>
        </div>
        <div className="alert-h error"><p>{error}</p></div>
        <p className="muted-2" style={{ fontSize: 12, marginTop: 6 }}>
          Ensure your FastAPI server is running on <code>http://127.0.0.1:8000</code>.
        </p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="glass-card flat" style={{ padding: 28, minHeight: 280, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
        <div className="empty-ico" style={{ marginBottom: 14 }}>
          <Bot size={26} />
        </div>
        <h4 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>Ready for Field Analysis</h4>
        <p className="muted" style={{ fontSize: 13, maxWidth: 320 }}>
          Configure your crop and environmental metrics on the left panel and click <strong className="strong-600">Analyze Field</strong> to view machine learning predictions and irrigation recommendations.
        </p>
      </div>
    );
  }

  const { prediction, recommendation, crop_type } = result;
  const { status, priority, reason, factors } = recommendation || {};

  const predictedMoistureValue =
    prediction?.soil_moisture !== undefined ? Number(prediction.soil_moisture).toFixed(2) : '--';

  const getStatusConfig = (recStatus) => {
    switch (recStatus?.toUpperCase()) {
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

  const radialData = [{ name: 'moisture', value: Math.min(100, Number(predictedMoistureValue) || 0), fill: '#D4E157' }];

  return (
    <div className="glass-card flat" style={{ padding: 22 }}>
      <div className="card-head">
        <h3 style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
          <Bot size={16} style={{ color: 'var(--c-lime-deep)' }} /> AI Analysis Dashboard
        </h3>
        <span className="tag lime">{crop_type}</span>
      </div>

      <div className="grid gap-4 ai-result-grid" style={{ gridTemplateColumns: 'minmax(180px, 1fr) 1fr', marginBottom: 18 }}>
        {/* Predicted moisture radial gauge */}
        <div className="p-4 rounded-2xl border border-black/5 bg-cream-50 flex flex-col items-center justify-center">
          <span className="eyebrow-text">Predicted Soil Moisture</span>
          <div style={{ width: '100%', height: 140, position: 'relative' }}>
            <ResponsiveContainer>
              <RadialBarChart
                innerRadius="70%"
                outerRadius="100%"
                data={radialData}
                startAngle={210}
                endAngle={-30}
              >
                <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                <RadialBar dataKey="value" cornerRadius={10} background={{ fill: 'rgba(15,23,42,0.06)' }} />
              </RadialBarChart>
            </ResponsiveContainer>
            <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
              <span style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 700, color: 'var(--c-ink-900)', lineHeight: 1 }}>
                {predictedMoistureValue}<span style={{ fontSize: 14, color: 'var(--c-ink-500)' }}> %</span>
              </span>
              <span className="uppercase-mini" style={{ marginTop: 2 }}>Predicted</span>
            </div>
          </div>
        </div>

        {/* Recommendation banner */}
        <div className="flex flex-col gap-3 p-4 rounded-2xl" style={{ background: statusConfig.theme.bg, color: statusConfig.theme.color }}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: statusConfig.theme.accent, color: statusConfig.theme.color }}>
              <StatusIcon size={20} strokeWidth={2.2} />
            </div>
            <div>
              <span className="uppercase-mini" style={{ color: statusConfig.theme.color }}>Action Recommendation</span>
              <h4 style={{ fontSize: 18, fontWeight: 700, color: statusConfig.theme.color, marginTop: 2 }}>
                {statusConfig.badgeText}
              </h4>
            </div>
          </div>
          <div>{getPriorityTag(priority)}</div>
        </div>
      </div>

      {reason && (
        <div className="p-4 rounded-2xl border border-black/5 bg-cream-50" style={{ marginBottom: 14 }}>
          <h5 style={{ fontSize: 12, fontWeight: 700, color: 'var(--c-leaf-500)', display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
            <Lightbulb size={14} /> Primary Rationale
          </h5>
          <p style={{ fontSize: 13, color: 'var(--c-ink-700)', lineHeight: 1.6 }}>{reason}</p>
        </div>
      )}

      {factors && factors.length > 0 && (
        <div className="p-4 rounded-2xl border border-black/5 bg-cream-50">
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
    </div>
  );
}

AIResultCard.propTypes = {
  result: PropTypes.shape({
    crop_type: PropTypes.string,
    prediction: PropTypes.shape({ soil_moisture: PropTypes.number }),
    recommendation: PropTypes.shape({
      status: PropTypes.string,
      priority: PropTypes.string,
      reason: PropTypes.string,
      factors: PropTypes.arrayOf(PropTypes.string),
    }),
  }),
  error: PropTypes.string,
  isLoading: PropTypes.bool,
};

export default AIResultCard;
