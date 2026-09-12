import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Scale,
  Play,
  RotateCcw,
  Trophy,
  AlertTriangle,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { useComparisonStore } from '../../stores/comparisonStore';
import { apiClient } from '../../services/api/client';
import { ModeComparisonCard } from '../../components/comparison/ModeComparisonCard';
import { MetricsComparisonBar } from '../../components/comparison/MetricsComparisonBar';
import { DeltasTable } from '../../components/comparison/DeltasTable';
import type { ScenarioData, SimulationMode } from '../../types';

export const ComparisonPage: React.FC = () => {
  const { comparisonId } = useParams<{ comparisonId: string }>();
  const navigate = useNavigate();

  const {
    activeComparison,
    comparisons,
    isLoading,
    isExecuting,
    error,
    modeProgress,
    fetchComparisons,
    fetchComparison,
    createAndRunComparison,
  } = useComparisonStore();

  const [scenarios, setScenarios] = useState<ScenarioData[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('scenario_01');
  const [maxTicks, setMaxTicks] = useState<number>(60);

  // Load scenarios and comparison runs list on mount
  useEffect(() => {
    void fetchComparisons();
    void apiClient.getScenarios().then((list) => {
      setScenarios(list);
      if (list.length > 0 && !selectedScenarioId) {
        setSelectedScenarioId(list[0].id);
      }
    });
  }, [fetchComparisons, selectedScenarioId]);

  // Load active comparison if ID parameter in URL changes
  useEffect(() => {
    if (comparisonId) {
      void fetchComparison(comparisonId);
    }
  }, [comparisonId, fetchComparison]);

  // Handle launch new comparison
  const handleLaunchComparison = async () => {
    const result = await createAndRunComparison({
      scenario_id: selectedScenarioId,
      max_ticks: maxTicks,
    });
    if (result) {
      navigate(`/comparisons/${result.comparison_id}`);
    }
  };

  const currentRun = activeComparison;
  const modesList: SimulationMode[] = ['no_coordination', 'partial', 'coordinated'];

  return (
    <div className="space-y-6 pb-12" data-testid="comparison-page">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-400 uppercase tracking-wider mb-1">
            <Scale className="w-4 h-4" />
            <span>Phase 13 • Three-Mode Comparison Engine</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            Governance Strategy Comparison View
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Empirically evaluate the exact same fictional crisis scenario across three distinct
            governance architectures: <span className="text-rose-400">No Coordination</span>,{' '}
            <span className="text-amber-400">Partial Coordination</span>, and{' '}
            <span className="text-emerald-400">Full Coordinated Governance</span>.
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 flex-wrap">
          {comparisons.length > 0 && (
            <select
              value={comparisonId || currentRun?.comparison_id || ''}
              onChange={(e) => {
                if (e.target.value) {
                  navigate(`/comparisons/${e.target.value}`);
                }
              }}
              className="bg-slate-900 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-2 font-mono"
            >
              <option value="" disabled>Select Previous Comparison</option>
              {comparisons.map((c) => (
                <option key={c.comparison_id} value={c.comparison_id}>
                  {c.scenario_title} ({c.comparison_id.slice(-6)}) - {c.status}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Launcher Bar (if no active comparison or to run another) */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/50 backdrop-blur p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex flex-col">
            <label className="text-[10px] font-mono uppercase text-slate-400 mb-1">Target Scenario</label>
            <select
              value={selectedScenarioId}
              onChange={(e) => setSelectedScenarioId(e.target.value)}
              disabled={isExecuting}
              className="bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 font-mono"
            >
              {scenarios.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title} ({s.severity} Severity)
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-[10px] font-mono uppercase text-slate-400 mb-1">Max Simulation Ticks</label>
            <input
              type="number"
              min={20}
              max={180}
              value={maxTicks}
              onChange={(e) => setMaxTicks(Number(e.target.value))}
              disabled={isExecuting}
              className="w-24 bg-slate-950 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 font-mono"
            />
          </div>
        </div>

        <button
          onClick={handleLaunchComparison}
          disabled={isExecuting}
          className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-slate-950 font-semibold text-xs font-mono transition-colors shadow-lg shadow-cyan-950/40"
        >
          {isExecuting ? (
            <>
              <RotateCcw className="w-4 h-4 animate-spin" />
              <span>Orchestrating 3 Runs...</span>
            </>
          ) : (
            <>
              <Play className="w-4 h-4 fill-current" />
              <span>Run 3-Mode Comparison</span>
            </>
          )}
        </button>
      </div>

      {/* Real-time Execution Progress Tracker */}
      {isExecuting && (
        <div className="rounded-xl border border-cyan-800/80 bg-cyan-950/20 p-4 space-y-3">
          <div className="flex items-center gap-2 text-xs font-mono text-cyan-300">
            <RotateCcw className="w-4 h-4 animate-spin text-cyan-400" />
            <span className="font-semibold">Sequential Execution in Progress:</span>
            <span className="text-slate-400">Executing same scenario through all three modes</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {modesList.map((m) => {
              const prog = modeProgress[m];
              const isWaiting = !prog || prog.status === 'WAITING';
              const isRunning = prog?.status === 'RUNNING';
              const isDone = prog?.status === 'COMPLETED';

              return (
                <div
                  key={m}
                  className={`p-3 rounded-lg border text-xs font-mono flex items-center justify-between ${
                    isRunning
                      ? 'border-cyan-500 bg-cyan-950/40 text-cyan-200'
                      : isDone
                      ? 'border-emerald-700 bg-emerald-950/30 text-emerald-300'
                      : 'border-slate-800 bg-slate-950/30 text-slate-500'
                  }`}
                >
                  <span className="capitalize">{m.replace('_', ' ')}</span>
                  <span className="flex items-center gap-1.5 font-bold">
                    {isRunning && <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />}
                    {isDone && <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />}
                    {isWaiting && <Clock className="w-3.5 h-3.5 text-slate-600" />}
                    <span>{prog?.status || 'WAITING'}</span>
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="rounded-xl border border-rose-800 bg-rose-950/30 p-4 flex items-start gap-3 text-xs text-rose-300">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold font-mono">Execution Error</div>
            <p className="mt-0.5 text-rose-200/80">{error}</p>
          </div>
        </div>
      )}

      {/* Current Comparison Results View */}
      {currentRun && (
        <div className="space-y-6">
          {/* Winner Banner / Synthesis Narrative */}
          <div
            data-testid="winner-banner"
            className={`rounded-xl border p-6 backdrop-blur ${
              currentRun.winner === 'TIE'
                ? 'border-cyan-800/80 bg-gradient-to-r from-cyan-950/40 via-slate-900 to-slate-950'
                : currentRun.winner === 'FAILED'
                ? 'border-rose-800/80 bg-rose-950/20'
                : 'border-amber-500/60 bg-gradient-to-r from-amber-950/30 via-slate-900/90 to-slate-950'
            }`}
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400">
                  <Trophy className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-[10px] font-mono uppercase tracking-wider text-amber-400 font-semibold">
                    Deterministic Winner (Phase 7 Rule: Highest Overall Score)
                  </div>
                  <h2 className="text-xl font-bold text-slate-100 mt-0.5">
                    {currentRun.winner === 'TIE'
                      ? 'Evaluation Result: TIE'
                      : currentRun.winner
                      ? currentRun.results[currentRun.winner]?.mode_name || currentRun.winner
                      : 'Comparison In Progress'}
                  </h2>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300">
                  Scenario: {currentRun.scenario_title}
                </span>
                <span className="text-xs font-mono px-3 py-1 rounded-full bg-emerald-950 border border-emerald-800 text-emerald-300">
                  Authoritative (Code-Driven)
                </span>
              </div>
            </div>

            {/* Headline and Narrative */}
            <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-2">
              <p className="text-sm font-semibold text-slate-200">
                {currentRun.summary_headline}
              </p>
              <div className="text-xs text-slate-300 leading-relaxed whitespace-pre-line bg-slate-950/40 p-4 rounded-lg border border-slate-800/60 font-sans">
                {currentRun.summary_narrative}
              </div>
            </div>
          </div>

          {/* 3-Column Side-by-Side Comparison Grid */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider font-mono flex items-center gap-2">
                <span>Side-by-Side Mode Breakdown</span>
                <span className="text-[10px] text-slate-500 font-normal">
                  (Same Crisis Scenario: {currentRun.scenario_id})
                </span>
              </h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {modesList.map((m) => {
                const res = currentRun.results[m];
                return (
                  <ModeComparisonCard
                    key={m}
                    mode={m}
                    result={res}
                    progressStatus={modeProgress[m]?.status}
                    isWinner={currentRun.winner === m}
                    isTie={currentRun.winner === 'TIE' && res?.is_winner}
                  />
                );
              })}
            </div>
          </div>

          {/* Direct Metric Comparison Bars */}
          <MetricsComparisonBar results={currentRun.results} />

          {/* Deltas Table */}
          {currentRun.deltas && currentRun.deltas.length > 0 && (
            <DeltasTable deltas={currentRun.deltas} />
          )}
        </div>
      )}

      {/* Empty State when no comparison loaded */}
      {!currentRun && !isLoading && !isExecuting && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center mx-auto text-slate-400">
            <Scale className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-200">No Active Comparison Selected</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
              Select a target crisis scenario above and click &quot;Run 3-Mode Comparison&quot; to
              orchestrate runs across all three governance architectures.
            </p>
          </div>
          <button
            onClick={handleLaunchComparison}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-slate-950 font-semibold text-xs font-mono transition-colors"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Launch Comparison Now</span>
          </button>
        </div>
      )}
    </div>
  );
};
