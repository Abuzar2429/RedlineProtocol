/**
 * App — root application shell for the AI Governance Crisis Simulator.
 *
 * Phase 1 renders a professional "system ready" placeholder that:
 *  - Displays the application identity
 *  - Shows frontend online status
 *  - Polls GET /health and shows backend connection status
 *
 * The three-column dashboard layout (left/center/right) is the Phase 6 target.
 */
import { useEffect, useState } from 'react';
import { StatusIndicator } from './components/StatusIndicator';
import apiService from './services/api';
import type { ConnectionStatus } from './types';

function App() {
  const [backendStatus, setBackendStatus] = useState<ConnectionStatus>('checking');

  // ── Poll /health on mount ──────────────────────────────────────────────
  useEffect(() => {
    let cancelled = false;

    const checkHealth = async () => {
      try {
        const { status } = await apiService.getHealth();
        if (!cancelled) {
          setBackendStatus(status === 'healthy' ? 'connected' : 'offline');
        }
      } catch {
        if (!cancelled) setBackendStatus('offline');
      }
    };

    checkHealth();

    // Re-check every 30 seconds
    const interval = setInterval(checkHealth, 30_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 py-12 bg-gradient-to-b from-[#03060f] to-[#0d1a38]">
      {/* ── Header ── */}
      <header className="text-center mb-12">
        {/* Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-cyan-500/30 bg-cyan-500/10 text-cyan-400 text-xs font-semibold tracking-widest uppercase mb-6">
          <span className="relative flex h-1.5 w-1.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-cyan-400" />
          </span>
          System Ready
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-white mb-4">
          AI Governance{' '}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
            Crisis Simulator
          </span>
        </h1>

        <p className="max-w-md mx-auto text-slate-400 text-base leading-relaxed">
          A multi-agent simulation platform demonstrating how governance strategy shapes
          the outcome of international AI crises.
        </p>
      </header>

      {/* ── Architecture diagram (minimal Phase-1 representation) ── */}
      <div className="mb-10 flex flex-col items-center gap-1 text-slate-600 text-xs font-mono">
        <span className="text-slate-400 font-semibold">React Frontend</span>
        <span>↓</span>
        <span className="text-slate-400 font-semibold">FastAPI Backend</span>
        <span>↓</span>
        <span className="text-slate-400 font-semibold">PostgreSQL</span>
      </div>

      {/* ── Connection status ── */}
      <div className="flex flex-col sm:flex-row gap-3">
        <StatusIndicator label="Frontend" status="connected" />
        <StatusIndicator label="Backend"  status={backendStatus} />
      </div>

      {/* ── Phase label ── */}
      <footer className="mt-16 text-slate-700 text-xs">
        Phase 1 — Foundation · v0.1.0
      </footer>
    </div>
  );
}

export default App;
