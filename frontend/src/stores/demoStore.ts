import { create } from 'zustand';
import { apiClient } from '../services/api/client';
import type {
  DemoRun,
  ExecutionMode,
  ReplayEvent,
  ReplaySession,
} from '../types';

interface DemoStoreState {
  executionMode: ExecutionMode;
  demoSeed: number;
  demoRuns: DemoRun[];
  activeDemo: DemoRun | null;
  isDemoRunning: boolean;
  demoError: string | null;

  // Replay
  replays: ReplaySession[];
  activeReplay: ReplaySession | null;
  isPlayingReplay: boolean;
  replayTick: number;
  playbackSpeed: number; // 1, 2, 4
  visibleReplayEvents: ReplayEvent[];

  // Actions
  setExecutionMode: (mode: ExecutionMode) => void;
  setDemoSeed: (seed: number) => void;
  fetchDemoRuns: () => Promise<void>;
  launchDemo: (scenarioId?: string, seed?: number, maxTicks?: number) => Promise<DemoRun | null>;
  restartDemo: (demoId: string, newSeed?: number) => Promise<DemoRun | null>;
  fetchReplays: () => Promise<void>;
  loadReplay: (replayId: string) => Promise<ReplaySession | null>;
  playReplay: () => void;
  pauseReplay: () => void;
  stepReplay: (forward?: boolean) => void;
  seekReplayTick: (tick: number) => void;
  setPlaybackSpeed: (speed: number) => void;
  resetReplay: () => void;
}

export const useDemoStore = create<DemoStoreState>((set, get) => ({
  executionMode: 'LIVE',
  demoSeed: 42,
  demoRuns: [],
  activeDemo: null,
  isDemoRunning: false,
  demoError: null,

  replays: [],
  activeReplay: null,
  isPlayingReplay: false,
  replayTick: 0,
  playbackSpeed: 1,
  visibleReplayEvents: [],

  setExecutionMode: (mode) => set({ executionMode: mode }),
  setDemoSeed: (seed) => set({ demoSeed: seed }),

  fetchDemoRuns: async () => {
    try {
      const runs = await apiClient.listDemoRuns();
      set({ demoRuns: runs });
    } catch {
      // Ignore network errors on initial poll
    }
  },

  launchDemo: async (scenarioId = 'scenario_01', seed = 42, maxTicks = 60) => {
    set({ isDemoRunning: true, demoError: null, executionMode: 'DEMO', demoSeed: seed });
    try {
      const run = await apiClient.launchDemo({
        scenario_id: scenarioId,
        seed,
        max_ticks: maxTicks,
      });
      set((state) => ({
        activeDemo: run,
        demoRuns: [run, ...state.demoRuns.filter((d) => d.demo_id !== run.demo_id)],
        isDemoRunning: false,
      }));
      return run;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Demo execution failed';
      set({ demoError: msg, isDemoRunning: false });
      return null;
    }
  },

  restartDemo: async (demoId: string, newSeed?: number) => {
    set({ isDemoRunning: true, demoError: null });
    try {
      const run = await apiClient.restartDemo(demoId, newSeed);
      set((state) => ({
        activeDemo: run,
        demoSeed: run.seed,
        demoRuns: [run, ...state.demoRuns.filter((d) => d.demo_id !== run.demo_id)],
        isDemoRunning: false,
      }));
      return run;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Restart failed';
      set({ demoError: msg, isDemoRunning: false });
      return null;
    }
  },

  fetchReplays: async () => {
    try {
      const list = await apiClient.listReplays();
      set({ replays: list });
    } catch {
      // Ignore
    }
  },

  loadReplay: async (replayId: string) => {
    try {
      const replay = await apiClient.getReplay(replayId);
      set({
        activeReplay: replay,
        executionMode: 'REPLAY',
        replayTick: 0,
        isPlayingReplay: false,
        visibleReplayEvents: replay.events.filter((e) => e.tick === 0),
      });
      return replay;
    } catch {
      return null;
    }
  },

  playReplay: () => {
    const { activeReplay, replayTick } = get();
    if (!activeReplay) return;
    if (replayTick >= activeReplay.total_ticks) {
      // Restart from 0 if at end
      set({ replayTick: 0, visibleReplayEvents: activeReplay.events.filter((e) => e.tick === 0) });
    }
    set({ isPlayingReplay: true });
  },

  pauseReplay: () => {
    set({ isPlayingReplay: false });
  },

  stepReplay: (forward = true) => {
    const { activeReplay, replayTick } = get();
    if (!activeReplay) return;

    const nextTick = forward
      ? Math.min(activeReplay.total_ticks, replayTick + 1)
      : Math.max(0, replayTick - 1);

    set({
      replayTick: nextTick,
      visibleReplayEvents: activeReplay.events.filter((e) => e.tick <= nextTick),
    });
  },

  seekReplayTick: (tick: number) => {
    const { activeReplay } = get();
    if (!activeReplay) return;

    const target = Math.max(0, Math.min(tick, activeReplay.total_ticks));
    set({
      replayTick: target,
      visibleReplayEvents: activeReplay.events.filter((e) => e.tick <= target),
    });
  },

  setPlaybackSpeed: (speed: number) => {
    set({ playbackSpeed: speed });
  },

  resetReplay: () => {
    set({
      activeReplay: null,
      replayTick: 0,
      isPlayingReplay: false,
      visibleReplayEvents: [],
      executionMode: 'LIVE',
    });
  },
}));
