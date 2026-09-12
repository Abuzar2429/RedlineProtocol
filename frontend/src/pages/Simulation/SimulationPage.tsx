import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Play,
  Pause,
  SkipForward,
  Square,
  Clock,
  TrendingUp,
  GitCompare,
  ArrowLeft,
} from 'lucide-react';
import { apiClient } from '../../services/api/client';
import { getWebSocketClient } from '../../services/websocket/client';
import { useSimulationStore } from '../../stores/simulationStore';
import { useUIStore } from '../../stores/uiStore';
import { LoadingState } from '../../components/feedback/LoadingState';
import { ErrorState } from '../../components/feedback/ErrorState';
import { EmptyState } from '../../components/feedback/EmptyState';
import { WorldMap } from '../../components/map/WorldMap';
import { LiveEventFeed } from '../../components/feed/LiveEventFeed';
import type { CountryData } from '../../types';

export const SimulationPage: React.FC = () => {
  const { simulationId } = useParams<{ simulationId: string }>();
  const navigate = useNavigate();
  const { addToast } = useUIStore();

  const currentSimulation = useSimulationStore((s) => s.currentSimulation);
  const setActiveSimulationId = useSimulationStore((s) => s.setActiveSimulationId);
  const loadInitialState = useSimulationStore((s) => s.loadInitialState);
  const setError = useSimulationStore((s) => s.setError);
  const storeError = useSimulationStore((s) => s.error);

  const [countryProfiles, setCountryProfiles] = useState<Record<string, CountryData>>({});
  const [loading, setLoading] = useState<boolean>(true);
  const [controlActionInProgress, setControlActionInProgress] = useState<string | null>(null);

  // Initialize and synchronize simulation session
  const initializeSession = useCallback(async (simId: string) => {
    setLoading(true);
    setError(null);
    try {
      setActiveSimulationId(simId);

      // 1. Fetch authoritative initial state and country profiles via REST
      const [initialState, countriesList] = await Promise.all([
        apiClient.getFullSimulationState(simId),
        apiClient.getCountries().catch(() => [] as CountryData[]),
      ]);

      loadInitialState(simId, initialState);

      const profilesMap: Record<string, CountryData> = {};
      countriesList.forEach((c) => {
        profilesMap[c.id] = c;
      });
      setCountryProfiles(profilesMap);

      // 2. Connect WebSocket client for real-time live events
      const wsClient = getWebSocketClient(simId);
      wsClient.connect();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load simulation state';
      setError(msg);
      addToast({
        type: 'error',
        title: 'Simulation Load Error',
        message: msg,
      });
    } finally {
      setLoading(false);
    }
  }, [setActiveSimulationId, loadInitialState, setError, addToast]);

  useEffect(() => {
    if (!simulationId) {
      navigate('/');
      return;
    }

    const timer = setTimeout(() => {
      void initializeSession(simulationId);
    }, 0);

    // Cleanup on unmount or navigation away from this simulation
    return () => {
      clearTimeout(timer);
      const wsClient = getWebSocketClient(simulationId);
      wsClient.disconnect();
    };
  }, [simulationId, initializeSession, navigate]);

  // Command handlers delegating strictly to backend
  const handleStep = async () => {
    if (!simulationId) return;
    setControlActionInProgress('step');
    try {
      await apiClient.stepSimulation(simulationId);
      addToast({
        type: 'info',
        title: 'Step Dispatched',
        message: 'Engine executing next tick step.',
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Step command failed';
      addToast({ type: 'error', title: 'Step Error', message: msg });
    } finally {
      setControlActionInProgress(null);
    }
  };

  const handleRun = async () => {
    if (!simulationId) return;
    setControlActionInProgress('run');
    try {
      await apiClient.runSimulation(simulationId);
      addToast({
        type: 'success',
        title: 'Continuous Execution',
        message: 'Simulation run started.',
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Run command failed';
      addToast({ type: 'error', title: 'Run Error', message: msg });
    } finally {
      setControlActionInProgress(null);
    }
  };

  const handlePause = async () => {
    if (!simulationId) return;
    setControlActionInProgress('pause');
    try {
      await apiClient.pauseSimulation(simulationId);
      addToast({
        type: 'info',
        title: 'Simulation Paused',
        message: 'Execution paused by operator.',
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Pause command failed';
      addToast({ type: 'error', title: 'Pause Error', message: msg });
    } finally {
      setControlActionInProgress(null);
    }
  };

  const handleResume = async () => {
    if (!simulationId) return;
    setControlActionInProgress('resume');
    try {
      await apiClient.resumeSimulation(simulationId);
      addToast({
        type: 'info',
        title: 'Simulation Resumed',
        message: 'Resumed continuous execution.',
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Resume command failed';
      addToast({ type: 'error', title: 'Resume Error', message: msg });
    } finally {
      setControlActionInProgress(null);
    }
  };

  const handleStop = async () => {
    if (!simulationId) return;
    setControlActionInProgress('stop');
    try {
      await apiClient.stopSimulation(simulationId);
      addToast({
        type: 'warning',
        title: 'Simulation Stopped',
        message: 'Engine session terminated.',
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Stop command failed';
      addToast({ type: 'error', title: 'Stop Error', message: msg });
    } finally {
      setControlActionInProgress(null);
    }
  };

  if (!simulationId) {
    return (
      <EmptyState
        title="No Simulation Selected"
        message="Please select or launch a simulation from the dashboard."
        actionText="Return to Dashboard"
        onAction={() => navigate('/')}
      />
    );
  }

  if (loading) {
    return <LoadingState message={`Connecting to simulation instance ${simulationId.slice(0, 8)}...`} />;
  }

  if (storeError) {
    return (
      <ErrorState
        title="Simulation Communication Error"
        message={storeError}
        onRetry={() => initializeSession(simulationId)}
        retryText="Retry Session"
      />
    );
  }

  const isRunning = currentSimulation?.status === 'running' || currentSimulation?.status === 'RUNNING';
  const isPaused = currentSimulation?.status === 'paused' || currentSimulation?.status === 'PAUSED';
  const isCompleted = currentSimulation?.status === 'completed' || currentSimulation?.status === 'COMPLETED';

  return (
    <div className="space-y-6">
      {/* Back button & Control Bar Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between pb-4 border-b border-slate-800 gap-4">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => navigate('/')}
            aria-label="Return to Dashboard"
            className="p-1.5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold tracking-wide text-slate-100 uppercase font-mono">
                SESSION {simulationId.slice(0, 8)}
              </h1>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 text-cyan-300 border border-cyan-800 uppercase">
                {currentSimulation?.mode ?? 'autonomous'}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Scenario: <span className="text-slate-300 font-medium">{currentSimulation?.scenario_id}</span>
            </p>
          </div>
        </div>

        {/* Engine Telemetry & Controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Status Badges */}
          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 font-mono text-xs">
            <div className="flex items-center space-x-1.5">
              <Clock className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-cyan-300 font-bold">T+{currentSimulation?.current_tick ?? 0}</span>
            </div>
            <div className="h-3 w-px bg-slate-700" />
            <div className="flex items-center space-x-1.5">
              <span className="text-slate-500">PHASE:</span>
              <span className="capitalize text-slate-300 font-medium">
                {currentSimulation?.crisis_phase ?? 'early_warning'}
              </span>
            </div>
            <div className="h-3 w-px bg-slate-700" />
            <div className="flex items-center space-x-1.5">
              <span className="text-slate-500">STATUS:</span>
              <span
                className={`font-semibold uppercase ${
                  isRunning
                    ? 'text-emerald-400'
                    : isPaused
                    ? 'text-amber-400'
                    : isCompleted
                    ? 'text-purple-400'
                    : 'text-slate-300'
                }`}
              >
                {currentSimulation?.status ?? 'initialized'}
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-1.5">
            <button
              onClick={handleStep}
              disabled={controlActionInProgress !== null || isRunning || isCompleted}
              aria-label="Advance Simulation by 1 Tick"
              title="Step 1 Tick"
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium flex items-center space-x-1.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
            >
              <SkipForward className="w-3.5 h-3.5 text-cyan-400" />
              <span>Step</span>
            </button>

            {isRunning ? (
              <button
                onClick={handlePause}
                disabled={controlActionInProgress !== null}
                aria-label="Pause Continuous Execution"
                title="Pause Simulation"
                className="px-3 py-1.5 rounded-lg bg-amber-950/80 hover:bg-amber-900/80 text-amber-300 border border-amber-800 text-xs font-medium flex items-center space-x-1.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </button>
            ) : isPaused ? (
              <button
                onClick={handleResume}
                disabled={controlActionInProgress !== null}
                aria-label="Resume Execution"
                title="Resume Simulation"
                className="px-3 py-1.5 rounded-lg bg-emerald-950/80 hover:bg-emerald-900/80 text-emerald-300 border border-emerald-800 text-xs font-medium flex items-center space-x-1.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Resume</span>
              </button>
            ) : (
              <button
                onClick={handleRun}
                disabled={controlActionInProgress !== null || isCompleted}
                aria-label="Run Continuous Execution"
                title="Continuous Run"
                className="px-3 py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900/80 text-cyan-300 border border-cyan-800 text-xs font-medium flex items-center space-x-1.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run</span>
              </button>
            )}

            <button
              onClick={handleStop}
              disabled={controlActionInProgress !== null || isCompleted}
              aria-label="Stop Simulation Session"
              title="Stop Simulation"
              className="px-3 py-1.5 rounded-lg bg-rose-950/80 hover:bg-rose-900/80 text-rose-300 border border-rose-800 text-xs font-medium flex items-center space-x-1.5 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              <span>Stop</span>
            </button>
          </div>
        </div>
      </div>

      {/* Phase 11 Visual Simulation Layer: Interactive World Map & Live Multilateral Event Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* World Map with Country Markers and Slide-Out Intelligence Panel */}
        <div className="lg:col-span-2">
          <WorldMap countryProfiles={countryProfiles} />
        </div>

        {/* Live Multilateral Event Feed */}
        <div className="lg:col-span-1">
          <LiveEventFeed />
        </div>
      </div>

      {/* Modular Shell Placeholder Areas for Subsequent Phases (Phases 12 & 13) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
        {/* Metrics & Scoring Slot (Phase 12 Foundation) */}
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/40 p-5 flex flex-col items-center justify-center text-center">
          <div className="p-2 rounded-full bg-slate-900 text-slate-400 mb-2">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">
            Phase 12 Foundation Slot
          </div>
          <h3 className="text-xs font-semibold text-slate-300 mb-1">
            Deterministic Governance Metrics
          </h3>
          <p className="text-xs text-slate-500 max-w-sm">
            Cooperation Index, Stability Index, Escalation Rate, and Regulatory Compliance gauges.
          </p>
        </div>

        {/* Negotiation & Voting Slot (Phase 12 & 13 Foundation) */}
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/40 p-5 flex flex-col items-center justify-center text-center">
          <div className="p-2 rounded-full bg-slate-900 text-slate-400 mb-2">
            <GitCompare className="w-5 h-5" />
          </div>
          <div className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-1">
            Phase 12 & 13 Foundation Slots
          </div>
          <h3 className="text-xs font-semibold text-slate-300 mb-1">
            Multilateral Negotiation & Mode Comparison
          </h3>
          <p className="text-xs text-slate-500 max-w-sm">
            Coordinator treaty proposals, treaty voting rounds, and comparative telemetry across Autonomous, HITL, and Hybrid modes.
          </p>
        </div>
      </div>
    </div>
  );
};
