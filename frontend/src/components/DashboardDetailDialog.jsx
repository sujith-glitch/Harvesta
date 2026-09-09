import { useEffect, useId, useRef } from 'react';
import PropTypes from 'prop-types';
import { X } from 'lucide-react';

export default function DashboardDetailDialog({ title, onClose, children }) {
  const ref = useRef(null);
  const titleId = useId();
  useEffect(() => {
    const dialog = ref.current;
    const trigger = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    dialog.showModal();
    document.body.style.overflow = 'hidden';
    return () => {
      dialog.close();
      document.body.style.overflow = previousOverflow;
      if (trigger?.isConnected) trigger.focus();
    };
  }, []);

  return (
    <dialog ref={ref} className="dashboard-detail-dialog" aria-labelledby={titleId}
      onCancel={(event) => { event.preventDefault(); onClose(); }}
      onClick={(event) => {
        if (event.target !== event.currentTarget) return;
        const bounds = event.currentTarget.getBoundingClientRect();
        if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) onClose();
      }}>
      <div className="dashboard-detail-head">
        <h2 id={titleId}>{title}</h2>
        <button type="button" className="btn-pill-outline" onClick={onClose} aria-label="Close details" autoFocus><X size={18} /></button>
      </div>
      {children}
    </dialog>
  );
}

DashboardDetailDialog.propTypes = {
  title: PropTypes.string.isRequired,
  onClose: PropTypes.func.isRequired,
  children: PropTypes.node.isRequired,
};
