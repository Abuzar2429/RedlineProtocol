import React from 'react';
import { Radio, PlaySquare, History } from 'lucide-react';
import type { ExecutionMode } from '../../types/demo';

interface ExecutionModeBadgeProps {
  mode: ExecutionMode;
  seed?: number;
  className?: string;
  showDetails?: boolean;
}

export const ExecutionModeBadge: React.FC<ExecutionModeBadgeProps> = ({
  mode,
  seed = 42,
  className = '',
  showDetails = true,
}) => {
  if (mode === 'DEMO') {
    return (
      <div
        data-testid="execution-mode-badge"
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-mono font-medium bg-cyan-950/80 text-cyan-300 border-cyan-700/70 shadow-sm ${className}`}
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
        </span>
        <PlaySquare className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
        <span className="font-semibold tracking-wide">DEMO MODE</span>
        {showDetails && (
          <span className="bg-cyan-900/80 text-cyan-200 px-1.5 py-0.5 rounded text-[10px] border border-cyan-800">
            Seed: {seed}
          </span>
        )}
      </div>
    );
  }

  if (mode === 'REPLAY') {
    return (
      <div
        data-testid="execution-mode-badge"
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-mono font-medium bg-purple-950/80 text-purple-300 border-purple-700/70 shadow-sm ${className}`}
      >
        <History className="w-3.5 h-3.5 text-purple-400 shrink-0" />
        <span className="font-semibold tracking-wide">REPLAY MODE</span>
        {showDetails && (
          <span className="bg-purple-900/80 text-purple-200 px-1.5 py-0.5 rounded text-[10px] border border-purple-800">
            Authoritative Playback
          </span>
        )}
      </div>
    );
  }

  // LIVE mode
  return (
    <div
      data-testid="execution-mode-badge"
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full border text-xs font-mono font-medium bg-emerald-950/80 text-emerald-300 border-emerald-700/70 shadow-sm ${className}`}
    >
      <span className="relative flex h-2 w-2">
        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
        <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
      </span>
      <Radio className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
      <span className="font-semibold tracking-wide">LIVE MODE</span>
    </div>
  );
};
