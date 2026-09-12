import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Radio, Cpu, BookOpen, ChevronLeft, ChevronRight, Scale } from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';
import { useSimulationStore } from '../../stores/simulationStore';

export const Sidebar: React.FC = () => {
  const { sidebarCollapsed, toggleSidebar } = useUIStore();
  const activeSimId = useSimulationStore((s) => s.activeSimulationId);
  const currentSim = useSimulationStore((s) => s.currentSimulation);

  const navItems = [
    {
      to: '/',
      label: 'Control Dashboard',
      icon: LayoutDashboard,
      badge: null,
    },
    {
      to: activeSimId ? `/simulation/${activeSimId}` : '/simulation',
      label: 'Active Simulation',
      icon: Radio,
      badge: activeSimId ? 'LIVE' : null,
      badgeColor: 'bg-cyan-900 text-cyan-300 border-cyan-700',
    },
    {
      to: '/comparisons',
      label: '3-Mode Comparison',
      icon: Scale,
      badge: 'P13',
      badgeColor: 'bg-amber-950 text-amber-300 border-amber-800',
    },
  ];

  return (
    <aside
      aria-label="Sidebar Navigation"
      className={`relative border-r border-slate-800 bg-slate-950/60 backdrop-blur transition-all duration-200 flex flex-col justify-between shrink-0 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="py-4">
        {/* Navigation list */}
        <nav className="space-y-1 px-2" aria-label="Main Navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center px-3 py-2.5 rounded-lg text-xs font-medium transition-colors ${
                  isActive
                    ? 'bg-cyan-950/60 text-cyan-300 border border-cyan-800/60'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                } ${sidebarCollapsed ? 'justify-center' : 'justify-between'}`
              }
              title={sidebarCollapsed ? item.label : undefined}
            >
              <div className="flex items-center space-x-3">
                <item.icon className="w-4 h-4 shrink-0" />
                {!sidebarCollapsed && <span>{item.label}</span>}
              </div>
              {!sidebarCollapsed && item.badge && (
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-mono font-semibold border ${item.badgeColor}`}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Phase Scope / Future Modules indicator */}
        {!sidebarCollapsed && (
          <div className="mt-6 px-4">
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 mb-2">
              Future Modules
            </div>
            <div className="space-y-1 text-xs text-slate-400">
              <div className="flex items-center space-x-2 py-1 px-2 rounded hover:bg-slate-900/30">
                <BookOpen className="w-3.5 h-3.5 text-slate-400" />
                <span>World Map (P11)</span>
              </div>
              <div className="flex items-center space-x-2 py-1 px-2 rounded hover:bg-slate-900/30">
                <Cpu className="w-3.5 h-3.5 text-slate-400" />
                <span>Negotiation (P12)</span>
              </div>
            </div>
          </div>
        )}

        {/* Simulation Quick Stats if loaded */}
        {!sidebarCollapsed && currentSim && (
          <div className="mt-6 mx-3 p-3 rounded-lg bg-slate-900/50 border border-slate-800 text-xs">
            <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider mb-2">
              Active Session
            </div>
            <div className="space-y-1 font-mono text-[11px] text-slate-300">
              <div className="flex justify-between">
                <span className="text-slate-500">Scenario:</span>
                <span className="truncate max-w-[120px]" title={currentSim.scenario_id}>
                  {currentSim.scenario_id}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Phase:</span>
                <span className="capitalize">{currentSim.crisis_phase}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Tick:</span>
                <span>{currentSim.current_tick}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Collapse Toggle Footer */}
      <div className="p-3 border-t border-slate-800 flex justify-end">
        <button
          onClick={toggleSidebar}
          aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors w-full flex items-center justify-center"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <div className="flex items-center space-x-2 text-xs">
              <ChevronLeft className="w-4 h-4" />
              <span>Collapse</span>
            </div>
          )}
        </button>
      </div>
    </aside>
  );
};
