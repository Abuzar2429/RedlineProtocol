import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, ArrowLeft } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
      <div className="p-4 rounded-full bg-rose-950/60 border border-rose-800 text-rose-400 mb-4">
        <ShieldAlert className="w-10 h-10" />
      </div>
      <div className="text-xs font-mono text-rose-400 uppercase tracking-widest mb-1">
        404 — UNKNOWN SECTOR
      </div>
      <h1 className="text-xl font-bold text-slate-100 mb-2">
        Command Route Not Found
      </h1>
      <p className="text-xs text-slate-400 max-w-sm mb-6">
        The requested crisis simulator interface or resource does not exist or has been relocated.
      </p>
      <button
        onClick={() => navigate('/')}
        className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Return to Dashboard</span>
      </button>
    </div>
  );
};
