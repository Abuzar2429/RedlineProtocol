import React from 'react';
import { Shield } from 'lucide-react';

export const MapLegend: React.FC = () => {
  const items = [
    { label: 'Unaware', color: 'bg-rose-500', border: 'border-rose-400/50', desc: 'No crisis telemetry' },
    { label: 'Investigating', color: 'bg-amber-400', border: 'border-amber-400/50', desc: 'Assessing anomaly' },
    { label: 'Notified', color: 'bg-blue-400', border: 'border-blue-400/50', desc: 'Alert confirmed' },
    { label: 'Coordinating', color: 'bg-emerald-400', border: 'border-emerald-400/50', desc: 'Treaty / Action aligned' },
  ];

  return (
    <div
      aria-label="Map Status Legend"
      className="absolute bottom-4 left-4 z-[1000] bg-slate-950/85 backdrop-blur-md border border-slate-800 rounded-lg p-3 shadow-xl pointer-events-auto"
    >
      <div className="flex items-center space-x-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2 pb-1.5 border-b border-slate-800/80">
        <Shield className="w-3 h-3 text-cyan-400" />
        <span>Country Posture</span>
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-1.5 text-xs">
        {items.map((item) => (
          <div key={item.label} className="flex items-center space-x-2">
            <span className={`w-2.5 h-2.5 rounded-full ${item.color} ${item.border} border shrink-0`} />
            <span className="text-[11px] font-mono text-slate-300">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
