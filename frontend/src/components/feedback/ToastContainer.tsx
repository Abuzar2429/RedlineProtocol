import React from 'react';
import { useUIStore, type ToastNotification } from '../../stores/uiStore';
import { AlertCircle, CheckCircle2, Info, TriangleAlert, X } from 'lucide-react';

export const ToastContainer: React.FC = () => {
  const { toasts, removeToast } = useUIStore();

  if (toasts.length === 0) return null;

  const getToastIcon = (type: ToastNotification['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />;
      case 'warning':
        return <TriangleAlert className="w-4 h-4 text-amber-400 shrink-0" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />;
      case 'info':
      default:
        return <Info className="w-4 h-4 text-cyan-400 shrink-0" />;
    }
  };

  const getBorderColor = (type: ToastNotification['type']) => {
    switch (type) {
      case 'success':
        return 'border-emerald-500/40 bg-slate-950/90';
      case 'warning':
        return 'border-amber-500/40 bg-slate-950/90';
      case 'error':
        return 'border-rose-500/40 bg-slate-950/90';
      case 'info':
      default:
        return 'border-cyan-500/40 bg-slate-950/90';
    }
  };

  return (
    <div
      aria-live="polite"
      className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`pointer-events-auto flex items-start gap-3 p-3 rounded-lg border shadow-xl backdrop-blur-md transition-all duration-200 ${getBorderColor(
            toast.type
          )}`}
        >
          <div className="mt-0.5">{getToastIcon(toast.type)}</div>
          <div className="flex-1 min-w-0">
            <div className="text-xs font-semibold text-slate-200 tracking-wide">
              {toast.title}
            </div>
            {toast.message && (
              <div className="text-xs text-slate-400 mt-0.5 leading-relaxed break-words">
                {toast.message}
              </div>
            )}
          </div>
          <button
            onClick={() => removeToast(toast.id)}
            className="text-slate-500 hover:text-slate-300 transition-colors p-0.5"
            aria-label="Dismiss notification"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
};
