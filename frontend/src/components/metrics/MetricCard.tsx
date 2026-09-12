import React from 'react';
import { ShieldCheck, Clock, Users, AlertTriangle } from 'lucide-react';
import type { MetricResult } from '../../types';

interface MetricCardProps {
  metric: MetricResult;
}

const getMetricIcon = (metricId: string) => {
  switch (metricId) {
    case 'risk_reduction':
      return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
    case 'response_time':
      return <Clock className="w-4 h-4 text-cyan-400" />;
    case 'coordination':
      return <Users className="w-4 h-4 text-indigo-400" />;
    case 'unresolved_issues':
      return <AlertTriangle className="w-4 h-4 text-amber-400" />;
    default:
      return <ShieldCheck className="w-4 h-4 text-slate-400" />;
  }
};

const getScoreColorClass = (score: number) => {
  if (score >= 80) return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
  if (score >= 65) return 'text-cyan-400 bg-cyan-500/10 border-cyan-500/20';
  if (score >= 45) return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
  return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
};

const getProgressBarColor = (score: number) => {
  if (score >= 80) return 'bg-emerald-500 shadow-emerald-500/30';
  if (score >= 65) return 'bg-cyan-500 shadow-cyan-500/30';
  if (score >= 45) return 'bg-amber-500 shadow-amber-500/30';
  return 'bg-rose-500 shadow-rose-500/30';
};

export const MetricCard: React.FC<MetricCardProps> = ({ metric }) => {
  const normScore = Math.min(100, Math.max(0, Math.round(metric.normalized_score)));
  const weightPct = Math.round(metric.weight * 100);

  return (
    <div
      data-testid={`metric-card-${metric.metric_id}`}
      className="flex flex-col justify-between p-3.5 rounded-xl bg-slate-900/90 border border-slate-800/80 hover:border-slate-700/80 transition-all duration-200 shadow-sm relative overflow-hidden group"
    >
      {/* Subtle top indicator line */}
      <div
        className={`absolute top-0 left-0 right-0 h-[2px] ${
          normScore >= 80
            ? 'bg-emerald-500/60'
            : normScore >= 65
            ? 'bg-cyan-500/60'
            : normScore >= 45
            ? 'bg-amber-500/60'
            : 'bg-rose-500/60'
        }`}
      />

      {/* Header: Title + Icon + Weight */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-slate-800/80 border border-slate-700/50">
            {getMetricIcon(metric.metric_id)}
          </div>
          <div>
            <h4 className="text-xs font-semibold text-slate-200 tracking-wide">
              {metric.name}
            </h4>
            <div className="text-[10px] text-slate-400 font-mono">
              Weight: {weightPct}%
            </div>
          </div>
        </div>

        {/* Normalized score badge */}
        <div
          className={`px-2 py-0.5 rounded-md border text-[11px] font-mono font-bold ${getScoreColorClass(
            normScore
          )}`}
        >
          {normScore}/100
        </div>
      </div>

      {/* Value Display */}
      <div className="flex items-baseline justify-between my-1">
        <div className="text-xl font-bold font-mono tracking-tight text-slate-100">
          {metric.display_value || `${metric.raw_value} ${metric.unit}`}
        </div>
        <div className="text-[11px] font-mono text-slate-400">
          +{metric.weighted_score.toFixed(1)} pts
        </div>
      </div>

      {/* Progress Bar */}
      <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden my-1.5">
        <div
          role="progressbar"
          aria-valuenow={normScore}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${metric.name} normalized score`}
          className={`h-full rounded-full transition-all duration-500 shadow-sm ${getProgressBarColor(
            normScore
          )}`}
          style={{ width: `${normScore}%` }}
        />
      </div>

      {/* Interpretation Footer */}
      <p className="text-[11px] text-slate-400 line-clamp-1 mt-0.5" title={metric.interpretation}>
        {metric.interpretation}
      </p>
    </div>
  );
};
