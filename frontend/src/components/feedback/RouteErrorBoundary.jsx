import React from 'react';
import { useRouteError, useNavigate } from 'react-router-dom';
import { AlertTriangle, RotateCcw, Home } from 'lucide-react';

export const RouteErrorBoundary = () => {
  const error = useRouteError();
  const navigate = useNavigate();

  const errorMessage = error instanceof Error
    ? error.message
    : (typeof error === 'object' && error && 'statusText' in error)
    ? String(error.statusText)
    : 'An unexpected application error occurred.';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
      <div className="max-w-md w-full p-6 rounded-2xl border border-rose-800/80 bg-rose-950/20 backdrop-blur-md shadow-2xl text-center space-y-4">
        <div className="w-12 h-12 rounded-xl bg-rose-900/40 border border-rose-700/60 flex items-center justify-center mx-auto text-rose-400">
          <AlertTriangle className="w-6 h-6" />
        </div>

        <div>
          <h2 className="text-lg font-bold font-mono uppercase tracking-wide text-rose-200">
            System Interface Error
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            The command module encountered an unexpected condition.
          </p>
        </div>

        <div className="p-3 rounded-lg bg-slate-950/80 border border-slate-800 font-mono text-xs text-rose-300 text-left overflow-x-auto max-h-32">
          {errorMessage}
        </div>

        <div className="flex items-center justify-center gap-3 pt-2">
          <button
            onClick={() => window.location.reload()}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-mono transition-colors cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reload</span>
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-mono font-bold text-xs transition-colors cursor-pointer"
          >
            <Home className="w-3.5 h-3.5" />
            <span>Return Home</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default RouteErrorBoundary;
