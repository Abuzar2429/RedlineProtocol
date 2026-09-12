import React from 'react';
import { X, Shield, Activity, Cpu, Globe, CheckCircle2, FileText } from 'lucide-react';
import { useUIStore } from '../../stores/uiStore';
import { useSimulationStore } from '../../stores/simulationStore';
import { COUNTRY_GEO_REGISTRY, getCountryStatusPresentation } from '../../utils/geoCoordinates';
import type { CountryData } from '../../types';

interface CountryDetailPanelProps {
  countryProfiles?: Record<string, CountryData>;
}

export const CountryDetailPanel: React.FC<CountryDetailPanelProps> = ({ countryProfiles = {} }) => {
  const selectedCountryId = useUIStore((s) => s.selectedCountryId);
  const setSelectedCountryId = useUIStore((s) => s.setSelectedCountryId);
  const liveCountries = useSimulationStore((s) => s.countries);
  const decisions = useSimulationStore((s) => s.decisions);

  if (!selectedCountryId) return null;

  const geo = COUNTRY_GEO_REGISTRY[selectedCountryId] ?? {
    id: selectedCountryId,
    name: selectedCountryId,
    flag: '🌐',
    region: 'Unknown Sector',
    geopoliticalBloc: 'unassigned',
  };

  const liveState = liveCountries[selectedCountryId];
  const staticProfile = countryProfiles[selectedCountryId];

  const statusPres = getCountryStatusPresentation(liveState?.status);

  // Filter decisions taken by this country (most recent first)
  const countryDecisions = decisions.filter(
    (d) => d.country_id === selectedCountryId || d.source === selectedCountryId
  ).slice(0, 3);

  return (
    <div
      role="dialog"
      aria-label={`${geo.name} Intelligence Profile`}
      className="absolute top-4 right-4 z-[1000] w-80 sm:w-96 max-h-[calc(100%-2rem)] overflow-y-auto bg-slate-950/95 backdrop-blur-md border border-slate-700/80 rounded-xl p-4 shadow-2xl space-y-4 pointer-events-auto"
    >
      {/* Header */}
      <div className="flex items-start justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2.5">
          <span className="text-2xl" role="img" aria-label="Flag">
            {geo.flag}
          </span>
          <div>
            <h3 className="text-sm font-bold text-slate-100 leading-tight">{geo.name}</h3>
            <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">
              {geo.region}
            </span>
          </div>
        </div>

        <button
          onClick={() => setSelectedCountryId(null)}
          aria-label="Close Country Panel"
          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Live Operational Status */}
      <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/80 border border-slate-800">
        <div className="flex items-center space-x-2">
          <span className={`w-2.5 h-2.5 rounded-full ${statusPres.dotClass} animate-pulse`} />
          <span className="text-xs font-mono font-semibold text-slate-200">
            {statusPres.label}
          </span>
        </div>
        <span
          className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase font-medium ${statusPres.bgClass} ${statusPres.borderClass} ${statusPres.textClass}`}
        >
          {liveState?.coordination_status || 'Independent'}
        </span>
      </div>

      {/* Telemetry Grid */}
      <div className="grid grid-cols-2 gap-2 text-xs font-mono">
        <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
          <div className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
            <Activity className="w-3 h-3 text-cyan-400" />
            <span>Tension Index</span>
          </div>
          <div className="text-sm font-bold text-slate-200 mt-1">
            {liveState?.tension_level !== undefined ? `${liveState.tension_level}%` : 'Nominal'}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
          <div className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
            <Globe className="w-3 h-3 text-cyan-400" />
            <span>Intel Completeness</span>
          </div>
          <div className="text-sm font-bold text-cyan-400 mt-1">
            {liveState?.information_completeness !== undefined
              ? `${Math.round(liveState.information_completeness * 100)}%`
              : '0%'}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
          <div className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
            <Cpu className="w-3 h-3 text-slate-400" />
            <span>AI Capacity</span>
          </div>
          <div className="text-xs font-semibold text-slate-300 mt-1 capitalize">
            {staticProfile?.ai_capability_level || 'High'}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-900/50 border border-slate-800/80">
          <div className="text-[10px] text-slate-500 uppercase flex items-center gap-1">
            <Shield className="w-3 h-3 text-slate-400" />
            <span>Risk Tolerance</span>
          </div>
          <div className="text-xs font-semibold text-slate-300 mt-1 capitalize">
            {staticProfile?.risk_tolerance || 'Medium'}
          </div>
        </div>
      </div>

      {/* Current Committed Action */}
      {liveState?.current_action && (
        <div className="p-2.5 rounded-lg bg-cyan-950/40 border border-cyan-800/60 text-xs">
          <div className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider flex items-center gap-1 mb-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>Committed Policy Action</span>
          </div>
          <p className="text-slate-200 font-medium">{liveState.current_action}</p>
        </div>
      )}

      {/* Strategic Policy Stance (Public only) */}
      {staticProfile?.ai_policy_position && (
        <div className="space-y-1">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <FileText className="w-3 h-3 text-slate-400" />
            <span>Public Strategic Posture</span>
          </div>
          <p className="text-[11px] text-slate-300 bg-slate-900/60 p-2.5 rounded-lg border border-slate-800/80 leading-relaxed max-h-24 overflow-y-auto">
            {staticProfile.ai_policy_position}
          </p>
        </div>
      )}

      {/* Recent Decisions Committed */}
      {countryDecisions.length > 0 && (
        <div className="space-y-1.5 pt-1 border-t border-slate-800">
          <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
            Committed Actions ({countryDecisions.length})
          </div>
          <div className="space-y-1.5">
            {countryDecisions.map((dec) => (
              <div
                key={dec.decision_id}
                className="p-2 rounded bg-slate-900/60 border border-slate-800 text-[11px]"
              >
                <div className="flex justify-between items-center text-slate-300 font-medium">
                  <span className="truncate">{dec.label}</span>
                  <span className="text-[9px] font-mono text-cyan-400 shrink-0 ml-2">
                    T+{dec.tick}
                  </span>
                </div>
                {dec.reasoning && (
                  <p className="text-[10px] text-slate-400 mt-0.5 line-clamp-2">
                    {dec.reasoning}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
