import PropTypes from 'prop-types';

export function HealthBadge({ isOnline, isLoading }) {
  if (isLoading) {
    return (
      <span className="tag" style={{ background: 'rgba(249, 168, 37, 0.16)', color: 'var(--c-amber-deep)' }}>
        <span className="status-dot checking" />
        Checking status
      </span>
    );
  }

  return isOnline ? (
    <span className="tag leaf">
      <span className="status-dot online" />
      System Online
    </span>
  ) : (
    <span className="tag danger">
      <span className="status-dot offline" />
      Backend Offline
    </span>
  );
}

HealthBadge.propTypes = {
  isOnline: PropTypes.bool,
  isLoading: PropTypes.bool,
};

export default HealthBadge;
