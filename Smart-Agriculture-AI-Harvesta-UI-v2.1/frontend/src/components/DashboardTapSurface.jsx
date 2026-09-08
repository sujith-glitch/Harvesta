import { useState } from 'react';
import PropTypes from 'prop-types';
import { getBackgroundTap } from '../utils/dashboardDetails';

export default function DashboardTapSurface({ children, zoom = 1 }) {
  const [marker, setMarker] = useState(null);

  const showMarker = (event) => {
    const point = getBackgroundTap(event);
    if (!point) return;
    setMarker((previous) => ({ ...point, sequence: (previous?.sequence ?? 0) + 1 }));
  };

  return (
    <section className="hero-map dashboard-tap-surface" onClickCapture={showMarker} style={{ paddingTop: 24, paddingBottom: 32, '--map-background-zoom': zoom }}>
      {children}
      <div className="dashboard-tap-overlay" aria-hidden="true">
        {marker && (
          <span
            key={marker.sequence}
            className="map-marker dashboard-tap-marker"
            style={{ left: marker.x, top: marker.y }}
          />
        )}
      </div>
    </section>
  );
}

DashboardTapSurface.propTypes = {
  children: PropTypes.node.isRequired,
  zoom: PropTypes.number,
};
