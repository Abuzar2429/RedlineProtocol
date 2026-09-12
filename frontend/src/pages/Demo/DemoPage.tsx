import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PlaySquare,
  RotateCcw,
  Trophy,
  History,
  ShieldCheck,
  Zap,
  Activity,
  CheckCircle,
  AlertCircle,
  Clock,
} from 'lucide-react';
import { useDemoStore } from '../../stores/demoStore';
import { ExecutionModeBadge } from '../../components/replay/ExecutionModeBadge';
import { ReplayControls } from '../../components/replay/ReplayControls';
import { ModeComparisonCard } from '../../components/comparison/ModeComparisonCard';
import { MetricsComparisonBar } from '../../components/comparison/MetricsComparisonBar';
import { DeltasTable } from '../../components/comparison/DeltasTable';
import type { SimulationMode } from '../../types';

export const DemoPage: React.FC = () => {
  const navigate = useNavigate();

  const {
    executionMode,
    demoSeed,
    activeDemo,
    activeReplay,
    replays,
    isDemoRunning,
    demoError,
    replayTick,
    visibleReplayEvents,
    setExecutionMode,
    setDemoSeed,
    launchDemo,
    restartDemo,
    fetchReplays,
    loadReplay,
  } = useDemoStore();

  const [seedInput, setSeedInput] = useState<number>(demoSeed);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('scenario_01');
  const [activeTab, setActiveTab] = useState<'comparison' | 'replay'>('comparison');
  const [replayFilterMode, setReplayFilterMode] = useState<string>('all');

  // Load recorded replays list on mount
  useEffect(() => {
    void fetchReplays();
  }, [fetchReplays]);

  // Sync seed input with store demoSeed
  useEffect(() => {
    const timer = setTimeout(() => {
      setSeedInput(demoSeed);
    }, 0);
    return () => clearTimeout(timer);
  }, [demoSeed]);

  const handleLaunch = async () => {
    setDemoSeed(seedInput);
    await launchDemo(selectedScenarioId, seedInput);
    setActiveTab('comparison');
    void fetchReplays();
  };

  const handleRestart = async () => {
    if (activeDemo) {
      await restartDemo(activeDemo.demo_id, seedInput);
      setActiveTab('comparison');
      void fetchReplays();
    }
  };

  const handleSelectReplay = async (replayId: string) => {
    await loadReplay(replayId);
    setActiveTab('replay');
  };

  // Helper for comparison data from active demo run
  const comparison = activeDemo?.comparison;
  const results = comparison?.results;
  const winner = comparison?.winner;
  const deltas = comparison?.deltas;

  // Filtered replay events
  const replayedEvents = (visibleReplayEvents.length > 0 ? visibleReplayEvents : (activeReplay?.events ?? [])).filter((evt) => {
    if (replayFilterMode === 'all') return true;
    return evt.mode === replayFilterMode;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Banner: Mode Indicator & Deterministic Engine Status */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl border border-slate-800 bg-slate-950/70 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-cyan-950/60 border border-cyan-800/80 text-cyan-400">
            <PlaySquare className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight flex items-center gap-2">
              Seeded Demo & Replay Center
              <ExecutionModeBadge
                mode={executionMode}
                seed={activeDemo?.seed ?? demoSeed}
              />
            </h1>
            <p className="text-xs text-slate-400 font-mono">
              Deterministic offline execution · 100% reproducible · Zero network dependencies
            </p>
          </div>
        </div>

        {/* Global Fallback & Engine Readiness */}
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 text-slate-300">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Deterministic Fallback: Active</span>
          </span>
          <button
            onClick={() => {
              setExecutionMode(executionMode === 'LIVE' ? 'DEMO' : 'LIVE');
            }}
            className="text-[11px] px-2 py-1 rounded border border-slate-800 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
          >
            Switch to {executionMode === 'LIVE' ? 'DEMO' : 'LIVE'}
          </button>
        </div>
      </div>

      {/* Control Panel: Scenario, Seed & Action Buttons */}
      <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 shadow-md">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          {/* Scenario Selection */}
          <div>
            <label className="block text-xs font-mono font-medium text-slate-300 uppercase tracking-wider mb-1.5">
              Fictional Demo Scenario
            </label>
            <select
              value={selectedScenarioId}
              onChange={(e) => setSelectedScenarioId(e.target.value)}
              disabled={isDemoRunning}
              aria-label="Fictional Demo Scenario"
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 font-mono"
            >
              <option value="scenario_01">
                Scenario 01: Cross-Border AI Infra Failure
              </option>
            </select>
          </div>

          {/* Seed Input */}
          <div>
            <label className="block text-xs font-mono font-medium text-slate-300 uppercase tracking-wider mb-1.5">
              Deterministic Seed
            </label>
            <div className="flex items-center">
              <input
                type="number"
                value={seedInput}
                onChange={(e) => setSeedInput(parseInt(e.target.value, 10) || 0)}
                disabled={isDemoRunning}
                aria-label="Deterministic Seed"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-cyan-500 font-mono"
              />
            </div>
          </div>

          {/* Launch / Running Buttons */}
          <div className="flex items-center gap-2 md:col-span-2">
            <button
              onClick={handleLaunch}
              disabled={isDemoRunning}
              data-testid="launch-demo-btn"
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold text-sm shadow-md transition-colors cursor-pointer"
            >
              {isDemoRunning ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin" />
                  <span>Executing 3 Modes...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 fill-current" />
                  <span>Run Seeded Demo (3 Modes)</span>
                </>
              )}
            </button>

            {activeDemo && (
              <button
                onClick={handleRestart}
                disabled={isDemoRunning}
                data-testid="restart-demo-btn"
                title="Restart fresh simulation with same seed"
                className="flex items-center gap-1.5 px-3 py-2 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition-colors cursor-pointer"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Restart</span>
              </button>
            )}
          </div>
        </div>

        {/* Error message if any */}
        {demoError && (
          <div className="mt-3 p-3 rounded-lg bg-red-950/60 border border-red-800 text-red-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
            <span>{demoError}</span>
          </div>
        )}
      </div>

      {/* Real-time Progress Bar During Demo Execution */}
      {isDemoRunning && (
        <div className="p-4 rounded-xl border border-cyan-800/80 bg-cyan-950/40 animate-pulse">
          <div className="flex items-center justify-between text-xs font-mono text-cyan-300 mb-2">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 animate-spin" />
              <span>Simulating All 3 Governance Modes via Real Engine Pipeline...</span>
            </div>
            <span>Deterministic Seed: {demoSeed}</span>
          </div>
          <div className="grid grid-cols-3 gap-2 font-mono text-[11px] text-center">
            <div className="py-1 px-2 rounded bg-cyan-900/60 border border-cyan-700 text-cyan-200">
              1. Uncoordinated Mode
            </div>
            <div className="py-1 px-2 rounded bg-cyan-900/60 border border-cyan-700 text-cyan-200">
              2. Fragmented Mode
            </div>
            <div className="py-1 px-2 rounded bg-cyan-900/60 border border-cyan-700 text-cyan-200">
              3. Coordinated Mode
            </div>
          </div>
        </div>
      )}

      {/* Navigation Tabs: Comparison Results vs Authoritative Replay */}
      {activeDemo && (
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('comparison')}
              className={`px-4 py-2 rounded-lg text-xs font-semibold font-mono tracking-wider uppercase transition-colors cursor-pointer ${
                activeTab === 'comparison'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              1. Three-Mode Results & Scoring
            </button>
            <button
              onClick={() => setActiveTab('replay')}
              data-testid="tab-authoritative-replay"
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold font-mono tracking-wider uppercase transition-colors cursor-pointer ${
                activeTab === 'replay'
                  ? 'bg-purple-950 text-purple-300 border border-purple-800'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>2. Authoritative Replay ({activeReplay?.events.length ?? 0} Events)</span>
            </button>
          </div>

          <div className="text-xs font-mono text-slate-400">
            Demo ID: <span className="text-cyan-300">{activeDemo.demo_id.slice(0, 8)}</span>
          </div>
        </div>
      )}

      {/* TAB 1: COMPARISON VIEW & WINNER */}
      {activeTab === 'comparison' && activeDemo && (
        <div className="space-y-6">
          {/* Winner Showcase Banner */}
          {winner && (
            <div
              data-testid="demo-winner-banner"
              className="rounded-xl border border-amber-500/40 bg-gradient-to-r from-amber-950/40 via-slate-900 to-amber-950/40 p-5 backdrop-blur shadow-lg shadow-amber-950/20"
            >
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-full bg-amber-500/20 border border-amber-500/40 text-amber-400">
                    <Trophy className="w-8 h-8" />
                  </div>
                  <div>
                    <div className="text-xs font-mono uppercase tracking-wider text-amber-400 font-semibold">
                      Authoritative Winner (Phase 7 Scoring)
                    </div>
                    <h2 className="text-2xl font-bold text-white capitalize">
                      {winner} Coordination Protocol
                    </h2>
                    <p className="text-xs text-slate-300 max-w-2xl mt-1">
                      {comparison?.summary_headline ??
                        'Deterministic comparative analysis across all four governance pillars.'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      if (activeDemo.comparison_id) {
                        navigate(`/comparisons/${activeDemo.comparison_id}`);
                      }
                    }}
                    className="px-3.5 py-2 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-xs font-mono text-slate-200 transition-colors cursor-pointer"
                  >
                    Open in Full Comparison View &rarr;
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Three Mode Comparison Cards */}
          {results && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {(['uncoordinated', 'fragmented', 'coordinated'] as SimulationMode[]).map((modeKey) => {
                const modeResult = results[modeKey];
                const isWinner = winner === modeKey;
                return (
                  <ModeComparisonCard
                    key={modeKey}
                    mode={modeKey}
                    result={modeResult}
                    isWinner={isWinner}
                    onInspect={() => {
                      if (modeResult?.simulation_id) {
                        navigate(`/simulation/${modeResult.simulation_id}`);
                      }
                    }}
                  />
                );
              })}
            </div>
          )}

          {/* Comparative Metrics Bar */}
          {results && (
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 shadow-md">
              <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" />
                Cross-Mode Scoring Metrics (Phase 7 Engine)
              </h3>
              <MetricsComparisonBar results={results} />
            </div>
          )}

          {/* Metric Deltas Table */}
          {deltas && deltas.length > 0 && (
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 shadow-md">
              <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 mb-4 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-emerald-400" />
                Comparative Pillar Deltas
              </h3>
              <DeltasTable deltas={deltas} />
            </div>
          )}
        </div>
      )}

      {/* TAB 2: AUTHORITATIVE REPLAY VIEW */}
      {activeTab === 'replay' && activeReplay && (
        <div className="space-y-6">
          {/* Replay Controls Component */}
          <ReplayControls />

          {/* Replay Event Feed Filter & Stats */}
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
            <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-purple-400" />
                <span className="text-xs font-mono font-semibold text-slate-200">
                  Authoritative Event Sequence (Recorded)
                </span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-950 text-purple-200 border border-purple-800">
                  {replayedEvents.length} events (Tick T+{String(replayTick).padStart(2, '0')})
                </span>
              </div>

              {/* Filter by Mode */}
              <div className="flex items-center gap-1.5 text-xs font-mono">
                <span className="text-slate-400 mr-1">Filter Mode:</span>
                {['all', 'uncoordinated', 'fragmented', 'coordinated'].map((m) => (
                  <button
                    key={m}
                    onClick={() => setReplayFilterMode(m)}
                    className={`px-2 py-1 rounded capitalize transition-colors cursor-pointer ${
                      replayFilterMode === m
                        ? 'bg-purple-900 text-purple-200 border border-purple-700'
                        : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-slate-200'
                    }`}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            {/* Event Timeline Feed */}
            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {replayedEvents.map((evt, idx) => {
                return (
                  <div
                    key={`${evt.sequence_number}-${idx}`}
                    className="p-3 rounded-lg border border-purple-900/60 bg-purple-950/40 text-xs font-mono transition-colors shadow-sm"
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-2">
                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300">
                          #{evt.sequence_number || idx + 1}
                        </span>
                        <span className="text-purple-400 font-semibold">
                          T+{String(evt.tick).padStart(2, '0')}
                        </span>
                        <span className="text-slate-500">|</span>
                        <span className="text-cyan-300 font-medium">
                          {evt.event_type}
                        </span>
                      </div>

                      {evt.mode && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800 capitalize">
                          {evt.mode}
                        </span>
                      )}
                    </div>

                    <div className="text-slate-300 text-[11px]">
                      {evt.description || JSON.stringify(evt.payload)}
                    </div>
                  </div>
                );
              })}

              {replayedEvents.length === 0 && (
                <div className="text-center py-8 text-xs font-mono text-slate-500">
                  No events recorded at or before current tick. Scrub or step forward to reveal events.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Historical Recorded Replays List */}
      <div className="p-5 rounded-xl border border-slate-800 bg-slate-950/60">
        <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-300 mb-3 flex items-center gap-2">
          <History className="w-4 h-4 text-purple-400" />
          Recorded Authoritative Replay Sessions
        </h3>

        {replays.length === 0 ? (
          <p className="text-xs font-mono text-slate-500">
            No saved replay recordings yet. Launch a seeded demo above to create one.
          </p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {replays.map((rep) => (
              <div
                key={rep.replay_id}
                className="p-3.5 rounded-lg border border-slate-800 bg-slate-900/50 hover:border-purple-800/80 transition-colors flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between text-xs font-mono mb-1.5">
                    <span className="font-semibold text-purple-300">
                      Seed: {rep.seed ?? 'N/A'}
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {new Date(rep.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-xs text-slate-300 font-medium">
                    {rep.scenario_title || rep.scenario_id}
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono mt-1">
                    {rep.total_events} events · {rep.total_ticks} ticks
                  </div>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-end">
                  <button
                    onClick={() => handleSelectReplay(rep.replay_id)}
                    className="text-xs font-mono text-purple-400 hover:text-purple-300 font-medium transition-colors cursor-pointer"
                  >
                    Open Replay &rarr;
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
