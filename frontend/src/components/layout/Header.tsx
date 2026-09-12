import React from 'react';
import { Menu, ShieldAlert, Activity, Clock } from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';
import { useSimulationStore } from '../../stores/simulationStore';
import { ConnectionStatusIndicator } from '../feedback/ConnectionStatusIndicator';
import { Link } from 'react-router-dom';

export const Header: React.FC = () => {
  const { toggleSidebar } = useUIStore();
  const activeSim = useSimulationStore((s) => s.currentSimulation);
  const activeSimId = useSimulationStore((s) => s.activeSimulationId);

  return (
    <header className="h-14 border-b border-slate-800 bg-slate-950/90 backdrop-blur px-4 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center space-x-3">
        <button
          onClick={toggleSidebar}
          aria-label="Toggle Navigation Sidebar"
          className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors focus:outline-none focus:ring-1 focus:ring-cyan-500"
        >
          <Menu className="w-5 h-5" />
        </button>

        <Link to="/" className="flex items-center space-x-2 text-decoration-none">
          <div className="p-1 rounded bg-cyan-950 border border-cyan-800 text-cyan-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <span className="text-sm font-bold tracking-wider text-slate-100 uppercase">
              AI Crisis Simulator
            </span>
            <span className="hidden sm:inline-block ml-2 text-[10px] font-mono tracking-widest px-1.5 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
              COMMAND SHELL
            </span>
          </div>
        </Link>
      </div>

      {/* Center simulation active status if loaded */}
      {activeSim && (
        <div className="hidden md:flex items-center space-x-4 px-3 py-1 rounded bg-slate-900/80 border border-slate-800 text-xs font-mono">
          <div className="flex items-center space-x-1.5 text-slate-400">
            <span className="text-slate-500">SIM:</span>
            <span className="text-slate-200 font-semibold">{activeSimId?.slice(0, 8)}</span>
          </div>
          <div className="h-3 w-px bg-slate-700" />
          <div className="flex items-center space-x-1.5 text-slate-400">
            <Clock className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-cyan-300 font-bold">T+{activeSim.current_tick}</span>
          </div>
          <div className="h-3 w-px bg-slate-700" />
          <div className="flex items-center space-x-1.5">
            <Activity className="w-3.5 h-3.5 text-amber-400" />
            <span className="uppercase text-amber-300 font-medium">{activeSim.status}</span>
          </div>
        </div>
      )}

      {/* Right side connection indicator */}
      <div className="flex items-center space-x-3">
        <ConnectionStatusIndicator showDetails={true} />
      </div>
    </header>
  );
};
