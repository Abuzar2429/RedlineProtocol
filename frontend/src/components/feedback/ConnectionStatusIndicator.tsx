import React from 'react';
import { useConnectionStore } from '../../stores/connectionStore';
import type { ConnectionState } from '../../types';

interface Props {
  className?: string;
  showText?: boolean;
  showDetails?: boolean;
}

export const ConnectionStatusIndicator: React.FC<Props> = ({
  className = '',
  showText = true,
  showDetails = false,
}) => {
  const { state, reconnectAttempts, error } = useConnectionStore();

  const getStatusConfig = (s: ConnectionState) => {
    switch (s) {
      case 'CONNECTED':
        return {
          label: 'Live Stream Active',
          color: 'bg-emerald-400',
          border: 'border-emerald-500/30',
          bg: 'bg-emerald-950/40 text-emerald-400',
          ping: true,
        };
      case 'CONNECTING':
        return {
          label: 'Connecting...',
          color: 'bg-sky-400',
          border: 'border-sky-500/30',
          bg: 'bg-sky-950/40 text-sky-400',
          ping: true,
        };
      case 'RECONNECTING':
        return {
          label: `Reconnecting (${reconnectAttempts})...`,
          color: 'bg-amber-400',
          border: 'border-amber-500/30',
          bg: 'bg-amber-950/40 text-amber-400',
          ping: true,
        };
      case 'ERROR':
        return {
          label: error ? `Error: ${error}` : 'Connection Error',
          color: 'bg-rose-500',
          border: 'border-rose-500/30',
          bg: 'bg-rose-950/40 text-rose-400',
          ping: false,
        };
      case 'DISCONNECTED':
      default:
        return {
          label: 'Disconnected',
          color: 'bg-slate-500',
          border: 'border-slate-700',
          bg: 'bg-slate-900/60 text-slate-400',
          ping: false,
        };
    }
  };

  const config = getStatusConfig(state);

  return (
    <div
      role="status"
      aria-live="polite"
      className={`inline-flex items-center gap-2 px-2.5 py-1 rounded-full border text-xs font-mono tracking-wider ${config.border} ${config.bg} ${className}`}
      title={config.label}
    >
      <span className="relative flex h-2 w-2">
        {config.ping && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${config.color}`}
          />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${config.color}`} />
      </span>
      {showText && (
        <span>
          {config.label}
          {showDetails && reconnectAttempts > 0 && ` (retry ${reconnectAttempts})`}
        </span>
      )}
    </div>
  );
};
