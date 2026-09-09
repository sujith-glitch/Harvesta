import PropTypes from 'prop-types';

/** Decorative, CSS-only depth cues that stay behind interactive dashboard content. */
export default function DashboardMotionLayer({ children }) {
  return (
    <div className="dashboard-motion-layer" aria-hidden="true">
      <span className="motion-orb motion-orb-one" />
      <span className="motion-orb motion-orb-two" />
      <span className="motion-ring motion-ring-one" />
      <span className="motion-ring motion-ring-two" />
      <div className="dashboard-motion-content">{children}</div>
    </div>
  );
}

DashboardMotionLayer.propTypes = { children: PropTypes.node };
