import React from 'react';
import { Award, CheckCircle2, Clock, Info } from 'lucide-react';
import { useSimulationStore } from '../../stores/simulationStore';
import { MetricCard } from './MetricCard';
import type { MetricResult } from '../../types';

const getGradeColorClass = (grade?: string) => {
  switch (grade) {
    case 'A':
      return 'text-emerald-400 bg-emerald-950/80 border-emerald-700/80 shadow-emerald-950/50';
    case 'B':
      return 'text-cyan-400 bg-cyan-950/80 border-cyan-700/80 shadow-cyan-950/50';
    case 'C':
      return 'text-amber-400 bg-amber-950/80 border-amber-700/80 shadow-amber-950/50';
    case 'D':
    case 'F':
      return 'text-rose-400 bg-rose-950/80 border-rose-700/80 shadow-rose-950/50';
    default:
      return 'text-slate-300 bg-slate-800 border-slate-700';
  }
};

export const MetricsBar: React.FC = () => {
  const scoring = useSimulationStore((s) => s.scoring);
  const currentTick = useSimulationStore((s) => s.currentTick);
  const status = useSimulationStore((s) => s.status);

  // If scoring is not yet available, render informative pending state with the 4 target metrics
  if (!scoring) {
    return (
      <div
        data-testid="metrics-bar-pending"
        className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-md p-4 shadow-lg"
      >
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 pb-3 border-b border-slate-800/80">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-slate-800/80 border border-slate-700/60 text-cyan-400">
              <Award className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-100 uppercase tracking-wider font-mono">
                Multilateral Crisis Governance Performance
              </h2>
              <p className="text-xs text-slate-400">
                Awaiting scoring evaluation • Spec §6.5 & §7.1 Deterministic Engine
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono bg-slate-950/60 px-3 py-1.5 rounded-lg border border-slate-800">
            <Clock className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
            <span>Telemetry Active • Current Tick: T+{currentTick}</span>
            <span className="text-slate-600">|</span>
            <span className="uppercase text-slate-400 font-semibold">{status}</span>
          </div>
        </div>

        {/* 4 Skeleton Cards representing the exact 4 Phase 7 metrics */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
          {[
            { id: 'risk_reduction', name: 'Risk Reduction', weight: '35%', desc: 'Peak to final risk mitigation percentage' },
            { id: 'response_time', name: 'Response Time', weight: '25%', desc: 'Virtual minutes from detection to coordinated action' },
            { id: 'coordination', name: 'International Coordination', weight: '25%', desc: 'Ratio of endorsing nations to total nations' },
            { id: 'unresolved_issues', name: 'Unresolved Issues', weight: '15%', desc: 'Contested policy issues remaining in deadlock' },
          ].map((item) => (
            <div
              key={item.id}
              className="p-3.5 rounded-xl bg-slate-950/40 border border-dashed border-slate-800 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs font-semibold text-slate-300">{item.name}</span>
                <span className="text-[10px] font-mono text-slate-500">Weight: {item.weight}</span>
              </div>
              <div className="text-sm font-mono text-slate-500 my-1 flex items-center space-x-1.5">
                <span className="inline-block w-2 h-2 rounded-full bg-slate-600 animate-ping" />
                <span>Pending evaluation...</span>
              </div>
              <p className="text-[10px] text-slate-500">{item.desc}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Authoritative Scoring Result Available
  const overallScore = Math.round(scoring.overall_score * 10) / 10;
  const grade = scoring.score_grade || scoring.letter_grade || 'C';
  const breakdown: MetricResult[] = scoring.metric_breakdown ?? [];

  return (
    <div
      data-testid="metrics-bar"
      className="rounded-2xl border border-slate-800 bg-slate-900/80 backdrop-blur-md p-4 shadow-lg space-y-4"
    >
      {/* Top Banner: Composite Score + Letter Grade + Provenance */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 pb-3 border-b border-slate-800">
        <div className="flex items-center space-x-4">
          {/* Grade Badge */}
          <div
            data-testid="metrics-grade-badge"
            className={`flex flex-col items-center justify-center w-14 h-14 rounded-2xl border font-mono font-black text-2xl shadow-md ${getGradeColorClass(
              grade
            )}`}
          >
            {grade}
            <span className="text-[9px] font-sans font-normal uppercase tracking-widest text-slate-400 -mt-1">
              GRADE
            </span>
          </div>

          {/* Overall Score & Headline */}
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-lg font-bold text-slate-100 font-mono tracking-tight">
                COMPOSITE SCORE: <span className="text-cyan-300">{overallScore}</span>
                <span className="text-xs text-slate-400 font-normal"> / 100</span>
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                T+{scoring.calculated_at_tick ?? currentTick}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5 font-medium">
              {scoring.performance_headline || 'Deterministic crisis response outcome calculated.'}
            </p>
          </div>
        </div>

        {/* Provenance & Audit Info */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-mono text-slate-400">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-950/60 border border-slate-800">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Deterministic Engine v{scoring.formula_version || '1.0'}</span>
          </div>
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-950/60 border border-slate-800">
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span>Authoritative • Zero LLM Score Authority</span>
          </div>
        </div>
      </div>

      {/* Grid of the 4 Exact Project-Defined Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {breakdown.map((metric) => (
          <MetricCard key={metric.metric_id} metric={metric} />
        ))}
      </div>
    </div>
  );
};
