import PropTypes from 'prop-types';
import { Sprout, ArrowRight } from 'lucide-react';

export default function FarmerPersonaCard({ user, recommendation, onSeeDetails }) {
  const userName = user?.full_name?.trim() || user?.email?.trim();
  const personaLabel = userName
    ? `${userName} · Smart farming assistant`
    : 'Smart Farming Assistant';

  const quoteText = recommendation && recommendation.trim()
    ? recommendation.trim()
    : 'Run a field analysis to get your latest farming recommendation.';

  return (
    <div className="farmer-card">
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 14 }}>
        <span className="farmer-photo">
          <Sprout size={36} />
        </span>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 0 }}>
          <span className="farmer-name">{personaLabel}</span>
          <p className="farmer-quote">
            {quoteText}
          </p>
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 2 }}>
        <button type="button" className="btn-pill" onClick={onSeeDetails} style={{ padding: '8px 14px', fontSize: 12 }}>
          See details <ArrowRight size={12} />
        </button>
      </div>
    </div>
  );
}

FarmerPersonaCard.propTypes = {
  user: PropTypes.shape({
    full_name: PropTypes.string,
    email: PropTypes.string,
  }),
  recommendation: PropTypes.string,
  onSeeDetails: PropTypes.func.isRequired,
};

