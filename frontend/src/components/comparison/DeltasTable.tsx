import React from 'react';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import type { ComparisonDelta } from '../../types';

interface DeltasTableProps {
  deltas: ComparisonDelta[];
}

export const DeltasTable: React.FC<DeltasTableProps> = ({ deltas }) => {
  if (!deltas || deltas.length === 0) {
    return null;
  }

  const formatDelta = (val: number, unit = '', invert = false) => {
    if (val === 0) {
      return (
        <span className="flex items-center gap-1 text-slate-400 font-mono">
          <Minus className="w-3 h-3" />
          <span>0{unit}</span>
        </span>
      );
    }
    const isPositive = val > 0;
    const isGood = invert ? !isPositive : isPositive;
    const color = isGood ? 'text-emerald-400' : 'text-rose-400';
    const Icon = isPositive ? ArrowUp : ArrowDown;

    return (
      <span className={`flex items-center gap-1 font-mono font-semibold ${color}`}>
        <Icon className="w-3 h-3" />
        <span>
          {isPositive ? '+' : ''}
          {val}
          {unit}
        </span>
      </span>
    );
  };

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 backdrop-blur p-5">
      <h3 className="text-sm font-semibold text-slate-100 uppercase tracking-wider font-mono mb-1">
        Comparative Variance Analysis
      </h3>
      <p className="text-xs text-slate-400 mb-4">
        Direct quantitative deltas evaluated against the unilateral baseline (<span className="text-rose-400 font-mono">No Coordination</span>)
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400 font-mono uppercase text-[10px]">
              <th className="py-2.5 px-3">Compared Strategy</th>
              <th className="py-2.5 px-3">Overall Score</th>
              <th className="py-2.5 px-3">Risk Reduction</th>
              <th className="py-2.5 px-3">Response Time</th>
              <th className="py-2.5 px-3">Consensus Ratio</th>
              <th className="py-2.5 px-3">Deadlock Issues</th>
              <th className="py-2.5 px-3">Duration (Ticks)</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {deltas.map((d) => (
              <tr key={d.compared_mode} className="hover:bg-slate-800/30 transition-colors">
                <td className="py-3 px-3 font-medium text-slate-200 capitalize">
                  {d.compared_mode.replace('_', ' ')}
                </td>
                <td className="py-3 px-3">
                  {formatDelta(d.overall_score_delta, ' pts')}
                </td>
                <td className="py-3 px-3">
                  {formatDelta(d.risk_reduction_delta_pct, '%')}
                </td>
                <td className="py-3 px-3">
                  {formatDelta(d.response_time_delta_min, 'm', true)}
                </td>
                <td className="py-3 px-3">
                  {formatDelta(Math.round(d.coordination_ratio_delta * 100), '%')}
                </td>
                <td className="py-3 px-3">
                  {formatDelta(d.unresolved_issues_delta, '', true)}
                </td>
                <td className="py-3 px-3">
                  {formatDelta(d.final_tick_delta, ' ticks', true)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
