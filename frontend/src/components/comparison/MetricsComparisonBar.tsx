import React from 'react';
import type { ModeComparisonResult, SimulationMode } from '../../types';

interface MetricsComparisonBarProps {
  results: Record<string, ModeComparisonResult>;
}

const MODES: { id: SimulationMode; label: string; color: string; barColor: string }[] = [
  { id: 'no_coordination', label: 'No Coordination', color: 'text-rose-400', barColor: 'bg-rose-500' },
  { id: 'partial', label: 'Partial Coordination', color: 'text-amber-400', barColor: 'bg-amber-500' },
  { id: 'coordinated', label: 'Full Coordinated Governance', color: 'text-emerald-400', barColor: 'bg-emerald-500' },
];

export const MetricsComparisonBar: React.FC<MetricsComparisonBarProps> = ({ results }) => {
  // Helper to extract metric values
  const getRiskReduction = (mode: string) => {
    return results[mode]?.metrics?.risk_reduction_pct ?? 0;
  };

  const getResponseScore = (mode: string) => {
    const res = results[mode];
    const m = res?.metric_breakdown?.find((item) => item.metric_id === 'response_time');
    if (m?.normalized_score !== undefined) return m.normalized_score;
    const respTime = res?.metrics?.response_time_minutes;
    return respTime !== undefined ? Math.max(0, 100 - respTime * 2) : 0;
  };

  const getCoordRatio = (mode: string) => {
    return (results[mode]?.metrics?.coordination_ratio ?? 0) * 100;
  };

  const getUnresolvedScore = (mode: string) => {
    const res = results[mode];
    const m = res?.metric_breakdown?.find((item) => item.metric_id === 'unresolved_issues');
    if (m?.normalized_score !== undefined) return m.normalized_score;
    const unres = res?.metrics?.unresolved_issues_count;
    return unres !== undefined ? Math.max(0, 100 - unres * 20) : 0;
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 uppercase tracking-wider font-mono">
            Direct Metric Comparison
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Normalized performance ratings across all three coordination architectures (0–100 scale)
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs font-mono">
          {MODES.map((m) => (
            <div key={m.id} className="flex items-center gap-1.5">
              <span className={`w-2.5 h-2.5 rounded-full ${m.barColor}`} />
              <span className={m.color}>{m.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-5">
        {/* Metric 1: Risk Reduction */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="font-semibold text-slate-300">Metric 1: Crisis Risk Reduction</span>
            <span className="text-slate-500 font-mono">Higher is better</span>
          </div>
          <div className="space-y-1">
            {MODES.map((m) => {
              const val = getRiskReduction(m.id);
              return (
                <div key={m.id} className="flex items-center gap-3 text-xs font-mono">
                  <span className="w-36 text-slate-400 truncate">{m.label}:</span>
                  <div className="flex-1 h-3 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${m.barColor}`}
                      style={{ width: `${Math.min(100, Math.max(0, val))}%` }}
                    />
                  </div>
                  <span className="w-14 text-right font-bold text-slate-200">
                    {val.toFixed(1)}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Metric 2: Response Time Efficiency */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="font-semibold text-slate-300">Metric 2: Response Timeliness & Speed</span>
            <span className="text-slate-500 font-mono">Higher is faster response</span>
          </div>
          <div className="space-y-1">
            {MODES.map((m) => {
              const score = getResponseScore(m.id);
              const mins = results[m.id]?.metrics?.response_time_minutes ?? '—';
              return (
                <div key={m.id} className="flex items-center gap-3 text-xs font-mono">
                  <span className="w-36 text-slate-400 truncate">{m.label}:</span>
                  <div className="flex-1 h-3 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${m.barColor}`}
                      style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                    />
                  </div>
                  <span className="w-14 text-right font-bold text-slate-200">
                    {mins}m
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Metric 3: Multilateral Coordination Ratio */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="font-semibold text-slate-300">Metric 3: Coordination & Consensus Ratio</span>
            <span className="text-slate-500 font-mono">Consensus percentage</span>
          </div>
          <div className="space-y-1">
            {MODES.map((m) => {
              const pct = getCoordRatio(m.id);
              const count = results[m.id]?.metrics?.countries_coordinating ?? 0;
              const total = results[m.id]?.metrics?.countries_total ?? 15;
              return (
                <div key={m.id} className="flex items-center gap-3 text-xs font-mono">
                  <span className="w-36 text-slate-400 truncate">{m.label}:</span>
                  <div className="flex-1 h-3 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${m.barColor}`}
                      style={{ width: `${Math.min(100, Math.max(0, pct))}%` }}
                    />
                  </div>
                  <span className="w-14 text-right font-bold text-slate-200">
                    {count}/{total}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Metric 4: Unresolved Issues & Deadlocks */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="font-semibold text-slate-300">Metric 4: Unresolved Deadlock Mitigation</span>
            <span className="text-slate-500 font-mono">Fewer deadlocks = higher score</span>
          </div>
          <div className="space-y-1">
            {MODES.map((m) => {
              const score = getUnresolvedScore(m.id);
              const count = results[m.id]?.metrics?.unresolved_issues_count ?? '—';
              return (
                <div key={m.id} className="flex items-center gap-3 text-xs font-mono">
                  <span className="w-36 text-slate-400 truncate">{m.label}:</span>
                  <div className="flex-1 h-3 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${m.barColor}`}
                      style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                    />
                  </div>
                  <span className="w-14 text-right font-bold text-slate-200">
                    {count} {count === 1 ? 'issue' : 'issues'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
