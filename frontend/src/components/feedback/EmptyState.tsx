import React from 'react';
import { Database } from 'lucide-react';

interface EmptyStateProps {
  title?: string;
  message?: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'No Data Available',
  message = 'There is currently no simulation data or events to display.',
  actionText,
  onAction,
  icon,
}) => {
  return (
    <div
      role="region"
      aria-label={title}
      className="flex flex-col items-center justify-center p-8 rounded-lg border border-dashed border-slate-700 bg-slate-900/40 text-center"
    >
      <div className="p-3 rounded-full bg-slate-800 text-slate-400 mb-4">
        {icon ?? <Database className="w-8 h-8" />}
      </div>
      <h3 className="text-base font-semibold text-slate-200 mb-1">{title}</h3>
      <p className="text-sm text-slate-400 max-w-sm mb-4">{message}</p>
      {actionText && onAction && (
        <button
          onClick={onAction}
          className="px-4 py-1.5 text-xs font-medium rounded bg-cyan-600 hover:bg-cyan-500 text-white transition-colors cursor-pointer"
        >
          {actionText}
        </button>
      )}
    </div>
  );
};
