import { create } from 'zustand';
import { apiClient } from '../services/api/client';
import type {
  ComparisonRun,
  CreateComparisonRequest,
  SimulationMode,
} from '../types';

interface ComparisonStoreState {
  // State
  comparisons: ComparisonRun[];
  activeComparison: ComparisonRun | null;
  selectedComparisonId: string | null;
  activeModeInspection: SimulationMode | null;
  isLoading: boolean;
  isExecuting: boolean;
  error: string | null;

  // Real-time progress map for running comparisons: mode -> status / headline
  modeProgress: Record<string, {
    status: string;
    mode_name?: string;
    score?: number | null;
    grade?: string | null;
  }>;

  // Actions
  setSelectedComparisonId: (id: string | null) => void;
  setActiveModeInspection: (mode: SimulationMode | null) => void;
  fetchComparisons: () => Promise<void>;
  fetchComparison: (id: string) => Promise<ComparisonRun | null>;
  createAndRunComparison: (request: CreateComparisonRequest) => Promise<ComparisonRun | null>;
  handleWebSocketEvent: (event: { event_type: string; payload: Record<string, unknown> }) => void;
  reset: () => void;
}

export const useComparisonStore = create<ComparisonStoreState>((set, get) => ({
  comparisons: [],
  activeComparison: null,
  selectedComparisonId: null,
  activeModeInspection: null,
  isLoading: false,
  isExecuting: false,
  error: null,
  modeProgress: {},

  setSelectedComparisonId: (id) => {
    set({ selectedComparisonId: id });
    if (id) {
      void get().fetchComparison(id);
    }
  },

  setActiveModeInspection: (mode) => {
    set({ activeModeInspection: mode });
  },

  fetchComparisons: async () => {
    set({ isLoading: true, error: null });
    try {
      const list = await apiClient.listComparisons();
      set({ comparisons: list, isLoading: false });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch comparisons';
      set({ error: msg, isLoading: false });
    }
  },

  fetchComparison: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      const run = await apiClient.getComparison(id);
      set({ activeComparison: run, selectedComparisonId: id, isLoading: false });
      return run;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load comparison';
      set({ error: msg, isLoading: false });
      return null;
    }
  },

  createAndRunComparison: async (request: CreateComparisonRequest) => {
    set({ isExecuting: true, error: null, modeProgress: {
      no_coordination: { status: 'WAITING', mode_name: 'No Coordination' },
      partial: { status: 'WAITING', mode_name: 'Partial Coordination' },
      coordinated: { status: 'WAITING', mode_name: 'Full Coordinated Governance' },
    } });

    try {
      const result = await apiClient.createComparison(request, false);
      set((state) => ({
        activeComparison: result,
        selectedComparisonId: result.comparison_id,
        comparisons: [result, ...state.comparisons.filter((c) => c.comparison_id !== result.comparison_id)],
        isExecuting: false,
      }));
      return result;
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Comparison execution failed';
      set({ error: msg, isExecuting: false });
      return null;
    }
  },

  handleWebSocketEvent: (event) => {
    const { event_type, payload } = event;

    if (event_type === 'COMPARISON_SNAPSHOT') {
      const snapshot = payload as unknown as ComparisonRun;
      set({ activeComparison: snapshot });
    } else if (event_type === 'COMPARISON_MODE_STARTED') {
      const mode = payload.mode as string;
      set((state) => ({
        modeProgress: {
          ...state.modeProgress,
          [mode]: {
            ...state.modeProgress[mode],
            status: 'RUNNING',
            mode_name: (payload.mode_name as string) || mode,
          },
        },
      }));
    } else if (event_type === 'COMPARISON_MODE_COMPLETED') {
      const mode = payload.mode as string;
      set((state) => ({
        modeProgress: {
          ...state.modeProgress,
          [mode]: {
            status: 'COMPLETED',
            score: typeof payload.overall_score === 'number' ? payload.overall_score : null,
            grade: (payload.score_grade as string) || null,
          },
        },
      }));
    } else if (event_type === 'COMPARISON_COMPLETED') {
      const compId = payload.comparison_id as string;
      if (get().activeComparison?.comparison_id === compId) {
        void get().fetchComparison(compId);
      }
    }
  },

  reset: () => {
    set({
      activeComparison: null,
      selectedComparisonId: null,
      activeModeInspection: null,
      error: null,
      modeProgress: {},
    });
  },
}));
