import PropTypes from 'prop-types';
import { MapPin, Plus, Sprout, Sparkles, Camera, ArrowRight } from 'lucide-react';

const HEALTH_DOT = {
  healthy: 'health-healthy',
  'needs attention': 'health-attention',
  critical: 'health-critical',
};

function getGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

export function FarmHomeCard({ home, isLoading, onNavigate }) {
  if (isLoading) {
    return (
      <div className="glass-card loading-skeleton" style={{ height: 220, borderRadius: 18 }} />
    );
  }

  if (!home) return null;

  const { farm, total_crops, overall_health_percent, recent_crops } = home;
  const greeting = `${getGreeting()}, Farmer`;

  if (!farm) {
    return (
      <div className="glass-card" style={{ padding: 28, display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div className="flex items-center justify-between gap-3 flex-wrap">
          <div>
            <span className="eyebrow-text">Your Farm</span>
            <h3 style={{ fontSize: 22, fontWeight: 700, marginTop: 4 }}>{greeting}</h3>
            <p className="muted" style={{ fontSize: 13, marginTop: 4 }}>
              You have not set up a farm yet. Create one to begin tracking crops, growth and harvests.
            </p>
          </div>
          <button type="button" className="btn-pill" onClick={() => onNavigate('my-farm')}>
            <Plus size={16} strokeWidth={2.4} />
            Set Up My Farm
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ padding: 24 }}>
      {/* Header row */}
      <div className="flex items-start justify-between gap-3 flex-wrap">
        <div className="flex items-start gap-3">
          {/* Photo / avatar */}
          <div
            className="flex items-center justify-center flex-shrink-0"
            style={{
              width: 64,
              height: 64,
              borderRadius: 18,
              background: 'linear-gradient(135deg, var(--c-leaf-300), var(--c-leaf-500))',
              color: '#FFFFFF',
              boxShadow: '0 8px 20px rgba(85, 139, 47, 0.35)',
            }}
          >
            <Sprout size={26} />
          </div>
          <div>
            <span className="eyebrow-text">{greeting}</span>
            <h3 style={{ fontSize: 22, fontWeight: 700, marginTop: 2 }}>{farm.name}</h3>
            {farm.location && (
              <p className="muted" style={{ fontSize: 13, marginTop: 4, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <MapPin size={13} />
                {[farm.location, farm.state].filter(Boolean).join(', ')}
              </p>
            )}
          </div>
        </div>

        {/* Stats */}
        <div className="flex gap-3">
          <div className="flex flex-col items-center justify-center px-4 py-3 rounded-2xl" style={{ background: 'rgba(212, 225, 87, 0.18)', minWidth: 96 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, color: 'var(--c-ink-900)', lineHeight: 1 }}>
              {total_crops}
            </span>
            <span className="uppercase-mini" style={{ marginTop: 4, color: 'var(--c-leaf-500)' }}>
              {total_crops === 1 ? 'Crop' : 'Crops'}
            </span>
          </div>
          <div className="flex flex-col items-center justify-center px-4 py-3 rounded-2xl" style={{ background: 'rgba(76, 175, 80, 0.12)', minWidth: 96 }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 26, fontWeight: 700, color: 'var(--c-leaf-500)', lineHeight: 1 }}>
              {overall_health_percent != null ? `${overall_health_percent}%` : '—'}
            </span>
            <span className="uppercase-mini" style={{ marginTop: 4, color: 'var(--c-leaf-500)' }}>Health</span>
          </div>
        </div>
      </div>

      <div className="divider-h" />

      {/* Recent crops quick row */}
      {recent_crops && recent_crops.length > 0 && (
        <div style={{ marginBottom: 14 }}>
          <div className="flex items-center justify-between mb-3">
            <h4 style={{ fontSize: 13, fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: 8 }}>
              <Sparkles size={14} style={{ color: 'var(--c-leaf-400)' }} />
              Recent Crop Activity
            </h4>
            <button className="btn-ghost" onClick={() => onNavigate('my-farm')}>
              View all <ArrowRight size={12} />
            </button>
          </div>
          <div className="scroll-x" style={{ display: 'flex', gap: 10 }}>
            {recent_crops.map((crop) => (
              <button
                key={crop.id}
                type="button"
                onClick={() => onNavigate('crop-detail', { cropId: crop.id })}
                className="flex items-center gap-2 px-3 py-2 rounded-xl border border-black/5 bg-white hover:shadow-soft transition-all whitespace-nowrap"
                style={{ fontSize: 13 }}
              >
                <span className={`health-dot ${HEALTH_DOT[(crop.health_status || '').toLowerCase()] || 'health-unknown'}`} />
                <span className="font-semibold text-ink-800">{crop.name}</span>
                <span className="muted-2" style={{ fontSize: 11 }}>
                  {crop.health_status || 'Unknown'}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-3 flex-wrap">
        <button type="button" className="btn-pill" onClick={() => onNavigate('dashboard', { askAi: true })}>
          <Sparkles size={16} strokeWidth={2.4} />
          Ask AI
        </button>
        <button
          type="button"
          className="btn-pill-outline"
          onClick={() => window.alert('Plant photo scanning is coming soon in a future update!')}
        >
          <Camera size={16} />
          Scan Plant
        </button>
      </div>
    </div>
  );
}

FarmHomeCard.propTypes = {
  home: PropTypes.shape({
    farm: PropTypes.shape({
      name: PropTypes.string,
      location: PropTypes.string,
      state: PropTypes.string,
    }),
    total_crops: PropTypes.number.isRequired,
    overall_health_percent: PropTypes.number,
    recent_crops: PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.number.isRequired,
        name: PropTypes.string.isRequired,
        health_status: PropTypes.string,
      })
    ),
  }),
  isLoading: PropTypes.bool,
  onNavigate: PropTypes.func.isRequired,
};

export default FarmHomeCard;
