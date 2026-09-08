import { Info } from 'lucide-react';

export function Disclaimer() {
  return (
    <div className="alert-h info">
      <Info size={16} style={{ flexShrink: 0, marginTop: 2 }} />
      <p>
        <strong className="strong-600">Disclaimer:</strong> Prototype AI recommendation based on development/synthetic data. Not professional agronomic advice.
      </p>
    </div>
  );
}

export default Disclaimer;
