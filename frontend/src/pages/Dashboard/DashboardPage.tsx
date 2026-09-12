import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, RefreshCw, AlertTriangle, ShieldCheck, Database, Layers, Radio, Scale, ChevronRight } from 'lucide-react';
import { apiClient } from '../../services/api/client';
import type { ScenarioData, RAGHealthResponse } from '../../types/api';
import type { SimulationSummary, SimulationMode } from '../../types/simulation';
import { LoadingState } from '../../components/feedback/LoadingState';
import { ErrorState } from '../../components/feedback/ErrorState';
import { EmptyState } from '../../components/feedback/EmptyState';
import { useUIStore } from '../../stores/uiStore';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { addToast } = useUIStore();

  const [scenarios, setScenarios] = useState<ScenarioData[]>([]);
  const [recentSims, setRecentSims] = useState<SimulationSummary[]>([]);
  const [ragHealth, setRagHealth] = useState<RAGHealthResponse | null>(null);

  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('');
  const [selectedMode, setSelectedMode] = useState<SimulationMode>('coordinated');

  const [loading, setLoading] = useState<boolean>(true);
  const [launching, setLaunching] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [scenariosData, simsData, ragData] = await Promise.all([
        apiClient.getScenarios().catch(() => [] as ScenarioData[]),
        apiClient.listSimulations().catch(() => [] as SimulationSummary[]),
        apiClient.getRAGHealth().catch(() => null),
      ]);

      setScenarios(scenariosData);
      setRecentSims(simsData);
      setRagHealth(ragData);

      if (scenariosData.length > 0 && !selectedScenarioId) {
        setSelectedScenarioId(scenariosData[0].id);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to connect to simulation backend';
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [selectedScenarioId]);

  useEffect(() => {
    const timer = setTimeout(() => {
      void loadDashboardData();
    }, 0);
    return () => clearTimeout(timer);
  }, [loadDashboardData]);

  const handleLaunchSimulation = async () => {
    if (!selectedScenarioId) {
      addToast({
        type: 'warning',
        title: 'Scenario Required',
        message: 'Please select a crisis scenario to initialize.',
      });
      return;
    }

    setLaunching(true);
    try {
      const res = await apiClient.createSimulation({
        scenario_id: selectedScenarioId,
        mode: selectedMode,
      });

      addToast({
        type: 'success',
        title: 'Simulation Initialized',
        message: `ID: ${res.simulation_id.slice(0, 8)} ready for command operations.`,
      });

      navigate(`/simulation/${res.simulation_id}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to initialize simulation';
      addToast({
        type: 'error',
        title: 'Launch Failed',
        message: msg,
      });
    } finally {
      setLaunching(false);
    }
  };

  if (loading) {
    return <LoadingState message="Connecting to Command Center & retrieving scenarios..." />;
  }

  if (error) {
    return (
      <ErrorState
        title="Backend Communication Error"
        message={error}
        onRetry={loadDashboardData}
        retryText="Retry Connection"
      />
    );
  }

  const selectedScenario = scenarios.find((s) => s.id === selectedScenarioId);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-4 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-wide text-slate-100 uppercase flex items-center gap-2">
            <Radio className="w-5 h-5 text-cyan-400 animate-pulse" />
            Crisis Simulator Control Center
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Global AI Governance Emergency Decision & Multilateral Coordination Environment
          </p>
        </div>

        <button
          onClick={loadDashboardData}
          className="self-start sm:self-auto flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-mono transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Data</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Launcher & Scenario Config */}
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Layers className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  Initialize New Session
                </h2>
              </div>
              <span className="text-[11px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800 px-2 py-0.5 rounded">
                PHASE 10 SHELL
              </span>
            </div>

            {/* Scenario Picker */}
            <div>
              <label htmlFor="scenario-select" className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">
                Select Crisis Scenario
              </label>
              {scenarios.length === 0 ? (
                <EmptyState
                  title="No Scenarios Loaded"
                  message="No scenarios were returned from the backend service."
                />
              ) : (
                <select
                  id="scenario-select"
                  aria-label="Select Crisis Scenario"
                  value={selectedScenarioId}
                  onChange={(e) => setSelectedScenarioId(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-200 text-sm font-sans focus:outline-none focus:ring-1 focus:ring-cyan-500"
                >
                  {scenarios.map((sc) => (
                    <option key={sc.id} value={sc.id}>
                      {sc.title} (Severity {sc.severity}/10)
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Selected Scenario Preview */}
            {selectedScenario && (
              <div className="p-4 rounded-lg bg-slate-950/60 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200">{selectedScenario.title}</span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-amber-950/80 text-amber-400 border border-amber-800">
                    Severity: {selectedScenario.severity}/10
                  </span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {selectedScenario.description}
                </p>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  <span className="text-[10px] font-mono text-slate-500 mr-1">Affected:</span>
                  {selectedScenario.affected_countries.map((c) => (
                    <span
                      key={c}
                      className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700"
                    >
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Simulation Mode Selection */}
            <div>
              <label className="block text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">
                Governance Mode
              </label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'coordinated' as SimulationMode, label: 'Coordinated' },
                  { id: 'partial' as SimulationMode, label: 'Partial HITL' },
                  { id: 'no_coordination' as SimulationMode, label: 'Autonomous' },
                ].map(({ id, label }) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setSelectedMode(id)}
                    className={`py-2 px-3 rounded-lg text-xs font-medium border text-center transition-all cursor-pointer ${
                      selectedMode === id
                        ? 'bg-cyan-950/80 border-cyan-500 text-cyan-300 ring-1 ring-cyan-500'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                    }`}
                  >
                    <div>{label}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Launch Button */}
            <button
              onClick={handleLaunchSimulation}
              disabled={launching || !selectedScenarioId}
              className="w-full py-3 px-4 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-sm tracking-wide uppercase transition-all shadow-lg shadow-cyan-950/50 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            >
              {launching ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Initializing Backend Instance...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  <span>Launch Simulation Command Shell</span>
                </>
              )}
            </button>

            {/* Phase 13 Three-Mode Comparison Banner */}
            <div className="rounded-xl border border-amber-500/40 bg-gradient-to-r from-amber-950/20 via-slate-900 to-slate-950 p-4 flex items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-amber-400 uppercase">
                  <Scale className="w-3.5 h-3.5" />
                  <span>Phase 13 Signature Feature</span>
                </div>
                <h3 className="text-sm font-bold text-slate-100 mt-0.5">
                  Three-Mode Comparative Evaluation
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Empirically test this crisis across Unilateral, Coalition, and Multilateral governance architectures side-by-side.
                </p>
              </div>
              <button
                onClick={() => navigate('/comparisons')}
                className="shrink-0 flex items-center gap-1 px-4 py-2 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs font-mono transition-colors shadow-md shadow-amber-950/40"
              >
                <span>Compare Modes</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Right 1 Col: Status & Active Sessions */}
        <div className="space-y-6">
          {/* RAG Knowledge Engine Status */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Database className="w-4 h-4 text-cyan-400" />
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                  RAG Knowledge Base
                </h2>
              </div>
              <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                Phase 9
              </span>
            </div>

            {ragHealth ? (
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                  <span className="text-slate-500">Vector Store:</span>
                  <span className="flex items-center text-emerald-400 gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" />
                    {ragHealth.status}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-500">Documents / Chunks:</span>
                  <span className="text-slate-300">
                    {ragHealth.document_count} docs / {ragHealth.chunk_count} chunks
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800/60">
                  <span className="text-slate-500">Embedding:</span>
                  <span className="text-slate-300">{ragHealth.embedding_model}</span>
                </div>
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-xs text-amber-400 py-2">
                <AlertTriangle className="w-4 h-4" />
                <span>RAG Diagnostics offline or unreachable</span>
              </div>
            )}
          </div>

          {/* Active / Recent Sessions */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                Recent Sessions
              </h2>
              <span className="text-xs font-mono text-slate-500">{recentSims.length} total</span>
            </div>

            {recentSims.length === 0 ? (
              <p className="text-xs text-slate-500 text-center py-4">
                No active or previous simulations found.
              </p>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                {recentSims.map((sim) => (
                  <div
                    key={sim.simulation_id}
                    onClick={() => navigate(`/simulation/${sim.simulation_id}`)}
                    className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 hover:border-cyan-700/60 hover:bg-slate-900/80 transition-all cursor-pointer flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs font-mono font-semibold text-slate-200">
                        {sim.simulation_id.slice(0, 8)}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {sim.scenario_id} • Tick {sim.current_tick}
                      </div>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase">
                      {sim.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
