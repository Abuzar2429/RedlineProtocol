import React from 'react';
import { Loader2 } from 'lucide-react';

interface Props {
  message?: string;
  submessage?: string;
  className?: string;
}

export const LoadingState: React.FC<Props> = ({
  message = 'Loading simulation intelligence...',
  submessage = 'Synchronizing with crisis operational state machine',
  className = '',
}) => {
  return (
    <div
      role="status"
      className={`flex flex-col items-center justify-center p-8 text-center rounded-xl border border-slate-800 bg-slate-950/50 backdrop-blur-sm ${className}`}
    >
      <Loader2 className="w-8 h-8 text-cyan-400 animate-spin mb-4" />
      <div className="text-sm font-semibold text-slate-200 tracking-wide font-mono">
        {message}
      </div>
      {submessage && (
        <div className="text-xs text-slate-400 mt-1 max-w-sm">
          {submessage}
        </div>
      )}
    </div>
  );
};
