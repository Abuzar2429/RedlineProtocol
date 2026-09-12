/**
 * StatusIndicator — shows a pulsing dot + label for a connection status.
 */
import type { ConnectionStatus } from '../../types';

interface StatusIndicatorProps {
  label: string;
  status: ConnectionStatus;
}

const STATUS_STYLES: Record<ConnectionStatus, { dot: string; text: string; pulse: boolean }> = {
  checking: { dot: 'bg-amber-400',   text: 'text-amber-300',  pulse: true },
  connected: { dot: 'bg-emerald-400', text: 'text-emerald-300', pulse: true },
  offline:   { dot: 'bg-red-500',     text: 'text-red-400',    pulse: false },
};

const STATUS_LABEL: Record<ConnectionStatus, string> = {
  checking:  'Checking…',
  connected: 'Connected',
  offline:   'Offline',
};

export function StatusIndicator({ label, status }: StatusIndicatorProps) {
  const styles = STATUS_STYLES[status];

  return (
    <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-white/5 border border-white/10">
      {/* Pulsing dot */}
      <span className="relative flex h-2.5 w-2.5">
        {styles.pulse && (
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full ${styles.dot} opacity-60`}
          />
        )}
        <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${styles.dot}`} />
      </span>

      <span className="text-sm font-medium text-slate-300">{label}:</span>
      <span className={`text-sm font-semibold ${styles.text}`}>
        {STATUS_LABEL[status]}
      </span>
    </div>
  );
}
