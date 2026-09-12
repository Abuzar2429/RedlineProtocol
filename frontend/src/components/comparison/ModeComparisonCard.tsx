import React from 'react';
import { Link } from 'react-router-dom';
import { Trophy, AlertCircle, Clock, Users, ShieldAlert, ArrowUpRight, Scale } from 'lucide-react';
import type { ModeComparisonResult, SimulationMode } from '../../types';

interface ModeComparisonCardProps {
  mode: SimulationMode;
  result?: ModeComparisonResult | null;
  progressStatus?: string;
  isWinner?: boolean;
  isTie?: boolean;
  onInspect?: (mode: SimulationMode) => void;
}

const MODE_THEMES: Record<string, {
  border: string;
  bg: string;
  accent: string;
  badge: string;
  tagline: string;
}> = {
  no_coordination: {
    border: 'border-rose-900/40 hover:border-rose-700/60',
    bg: 'bg-rose-950/10',
    accent: 'text-rose-400',
    badge: 'bg-rose-950/50 text-rose-300 border-rose-800',
    tagline: 'Sovereign unilateral doctrine; zero multilateral accord',
  },
  partial: {
    border: 'border-amber-900/40 hover:border-amber-700/60',
    bg: 'bg-amber-950/10',
    accent: 'text-amber-400',
    badge: 'bg-amber-950/50 text-amber-300 border-amber-800',
    tagline: 'Regional coalition; 50% quorum & simple majority',
  },
  coordinated: {
    border: 'border-emerald-900/40 hover:border-emerald-700/60',
    bg: 'bg-emerald-950/10',
    accent: 'text-emerald-400',
    badge: 'bg-emerald-950/50 text-emerald-300 border-emerald-800',
    tagline: 'Multilateral governance; 60% qualified majority',
  },
};

export const ModeComparisonCard: React.FC<ModeComparisonCardProps> = ({
  mode,
  result,
  progressStatus,
  isWinner = false,
  isTie = false,
}) => {
  const theme = MODE_THEMES[mode] || MODE_THEMES.coordinated;
  const status = result?.status || progressStatus || 'WAITING';

  // Get metric by ID helper
  const getMetric = (id: string) => {
    return result?.metric_breakdown?.find((m) => m.metric_id === id);
  };

  const riskMetric = getMetric('risk_reduction');
  const responseMetric = getMetric('response_time');
  const coordMetric = getMetric('coordination');
  const unresolvedMetric = getMetric('unresolved_issues');

  return (
    <div
      data-testid={`mode-card-${mode}`}
      className={`relative flex flex-col rounded-xl border ${
        isWinner
          ? 'border-amber-500/80 ring-1 ring-amber-500/50 shadow-lg shadow-amber-950/30'
          : theme.border
      } ${theme.bg} bg-slate-900/80 backdrop-blur p-5 transition-all duration-200`}
    >
      {/* Top Banner: Winner / Tie / Mode Badge */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <span className={`text-[11px] font-mono px-2.5 py-0.5 rounded border uppercase font-semibold ${theme.badge}`}>
          {mode.replace('_', ' ')}
        </span>

        {isWinner && (
          <div
            data-testid="winner-badge"
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500 text-slate-950 font-mono text-xs font-bold shadow-md shadow-amber-500/20 animate-pulse"
          >
            <Trophy className="w-3.5 h-3.5" />
            <span>WINNER</span>
          </div>
        )}

        {isTie && !isWinner && (
          <div
            data-testid="tie-badge"
            className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-600 text-slate-950 font-mono text-xs font-bold"
          >
            <Scale className="w-3.5 h-3.5" />
            <span>TIE</span>
          </div>
        )}

        {!isWinner && !isTie && (
          <span className="text-[10px] font-mono text-slate-500 uppercase">
            {status}
          </span>
        )}
      </div>

      {/* Title & Tagline */}
      <div className="mb-4">
        <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
          {result?.mode_name || mode}
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">{theme.tagline}</p>
      </div>

      {/* Score Hero Section */}
      <div className="rounded-lg bg-slate-950/60 border border-slate-800/80 p-4 mb-4">
        <div className="flex items-baseline justify-between">
          <div>
            <div className="text-[10px] font-mono uppercase text-slate-500 tracking-wider">
              Phase 7 Composite Score
            </div>
            <div className="flex items-baseline gap-2 mt-1">
              {result?.overall_score !== null && result?.overall_score !== undefined ? (
                <>
                  <span className="text-3xl font-bold font-mono text-slate-100">
                    {result.overall_score.toFixed(1)}
                  </span>
                  <span className="text-xs text-slate-500 font-mono">/ 100</span>
                </>
              ) : (
                <span className="text-xl font-mono text-slate-600">
                  {status === 'RUNNING' ? 'EVALUATING...' : 'PENDING'}
                </span>
              )}
            </div>
          </div>

          {result?.score_grade && (
            <div
              className={`w-11 h-11 rounded-lg flex items-center justify-center font-mono text-xl font-bold border ${
                result.score_grade === 'A'
                  ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                  : result.score_grade === 'B'
                  ? 'bg-cyan-950 text-cyan-400 border-cyan-800'
                  : result.score_grade === 'C'
                  ? 'bg-amber-950 text-amber-400 border-amber-800'
                  : 'bg-rose-950 text-rose-400 border-rose-800'
              }`}
            >
              {result.score_grade}
            </div>
          )}
        </div>

        {result?.performance_headline && (
          <p className="text-xs text-slate-300 mt-2.5 pt-2 border-t border-slate-800/60 line-clamp-2">
            {result.performance_headline}
          </p>
        )}
      </div>

      {/* Exact 4 Phase 7 Metrics Grid */}
      <div className="space-y-2 mb-4 flex-1">
        <div className="text-[10px] font-mono uppercase text-slate-400 tracking-wider mb-1">
          Exact Four Governance Metrics
        </div>

        {/* 1. Risk Reduction */}
        <div className="flex items-center justify-between p-2 rounded bg-slate-950/40 border border-slate-800/50 text-xs">
          <div className="flex items-center gap-2 text-slate-400">
            <ShieldAlert className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="truncate">1. Risk Reduction</span>
          </div>
          <span className="font-mono font-semibold text-slate-200">
            {riskMetric ? riskMetric.display_value : (result?.metrics?.risk_reduction_pct !== undefined ? `↓${result.metrics.risk_reduction_pct.toFixed(1)}%` : '—')}
          </span>
        </div>

        {/* 2. Response Time */}
        <div className="flex items-center justify-between p-2 rounded bg-slate-950/40 border border-slate-800/50 text-xs">
          <div className="flex items-center gap-2 text-slate-400">
            <Clock className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="truncate">2. Response Time</span>
          </div>
          <span className="font-mono font-semibold text-slate-200">
            {responseMetric ? responseMetric.display_value : (result?.metrics?.response_time_minutes !== undefined ? `${result.metrics.response_time_minutes}m` : '—')}
          </span>
        </div>

        {/* 3. Coordination Ratio */}
        <div className="flex items-center justify-between p-2 rounded bg-slate-950/40 border border-slate-800/50 text-xs">
          <div className="flex items-center gap-2 text-slate-400">
            <Users className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="truncate">3. Coordination</span>
          </div>
          <span className="font-mono font-semibold text-slate-200">
            {coordMetric ? coordMetric.display_value : (result?.metrics?.coordination_ratio !== undefined ? `${result.metrics.coordination_ratio.toFixed(2)} (${result.metrics.countries_coordinating ?? 0}/${result.metrics.countries_total ?? 15})` : '—')}
          </span>
        </div>

        {/* 4. Unresolved Issues */}
        <div className="flex items-center justify-between p-2 rounded bg-slate-950/40 border border-slate-800/50 text-xs">
          <div className="flex items-center gap-2 text-slate-400">
            <AlertCircle className="w-3.5 h-3.5 text-slate-500 shrink-0" />
            <span className="truncate">4. Unresolved Issues</span>
          </div>
          <span className="font-mono font-semibold text-slate-200">
            {unresolvedMetric ? unresolvedMetric.display_value : (result?.metrics ? `${result.metrics.unresolved_issues_count}` : '—')}
          </span>
        </div>
      </div>

      {/* Negotiation & Virtual Duration Breakdown */}
      <div className="pt-3 border-t border-slate-800/80 space-y-1.5 text-xs text-slate-400 mb-4 font-mono">
        <div className="flex justify-between">
          <span className="text-slate-500">Negotiation Status:</span>
          <span className={`font-semibold ${
            result?.negotiation_outcome?.agreement_reached ? 'text-emerald-400' : 'text-slate-300'
          }`}>
            {result?.negotiation_outcome?.final_status || (mode === 'no_coordination' ? 'UNILATERAL' : 'NONE')}
          </span>
        </div>

        <div className="flex justify-between">
          <span className="text-slate-500">Virtual Duration:</span>
          <span className="text-slate-200">
            {result?.final_tick !== undefined ? `T+${result.final_tick} min` : '—'}
          </span>
        </div>
      </div>

      {/* Deep Link to Single-Mode Simulation Detail */}
      {result?.simulation_id && (
        <Link
          to={`/simulation/${result.simulation_id}`}
          className="w-full flex items-center justify-center gap-1.5 py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors border border-slate-700/60"
        >
          <span>Inspect Simulation History</span>
          <ArrowUpRight className="w-3.5 h-3.5" />
        </Link>
      )}
    </div>
  );
};
