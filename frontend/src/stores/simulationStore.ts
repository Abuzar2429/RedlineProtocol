import { create } from 'zustand';
import type {
  CoordinatorProposal,
  CountryState,
  DecisionRecord,
  ScoringResult,
  SimulationEvent,
  SimulationMode,
  SimulationSnapshotPayload,
  SimulationStatus,
  WebSocketEventEnvelope,
} from '../types';
import type { FullSimulationStateResponse } from '../types/api';

export interface CurrentSimulationView {
  simulation_id: string;
  scenario_id: string;
  mode: SimulationMode;
  status: SimulationStatus;
  current_tick: number;
  current_time: string;
  crisis_phase: string;
  crisis_title?: string;
  crisis_severity?: number;
}

interface SimulationStoreState {
  // Primary state fields
  simulationId: string | null;
  activeSimulationId: string | null;
  scenarioId: string | null;
  mode: SimulationMode;
  status: SimulationStatus;
  currentTick: number;
  currentTime: string;
  crisisTitle: string;
  crisisSeverity: number;
  crisisPhase: string;
  countries: Record<string, CountryState>;
  events: SimulationEvent[];
  eventHistory: SimulationEvent[];
  decisions: DecisionRecord[];
  proposals: CoordinatorProposal[];
  negotiations: Array<Record<string, unknown>>;
  scoring: ScoringResult | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: string | null;

  // Computed summary view
  currentSimulation: CurrentSimulationView | null;

  // Actions
  setActiveSimulationId: (id: string | null) => void;
  loadInitialState: (simulationId: string, data: FullSimulationStateResponse) => void;
  setSnapshot: (snapshot: SimulationSnapshotPayload) => void;
  applyEvent: (envelope: WebSocketEventEnvelope) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearSimulation: (id?: string) => void;
  reset: () => void;
}

const buildCurrentSimulation = (
  simId: string | null,
  scenarioId: string | null,
  mode: SimulationMode,
  status: SimulationStatus,
  tick: number,
  time: string,
  phase: string,
  title?: string,
  severity?: number
): CurrentSimulationView | null => {
  if (!simId) return null;
  return {
    simulation_id: simId,
    scenario_id: scenarioId ?? '',
    mode,
    status,
    current_tick: tick,
    current_time: time,
    crisis_phase: phase,
    crisis_title: title,
    crisis_severity: severity,
  };
};

const initialValues = {
  simulationId: null,
  activeSimulationId: null,
  scenarioId: null,
  mode: 'autonomous' as SimulationMode,
  status: 'initialized' as SimulationStatus,
  currentTick: 0,
  currentTime: 'T+00:00',
  crisisTitle: '',
  crisisSeverity: 0,
  crisisPhase: 'early_warning',
  countries: {},
  events: [],
  eventHistory: [],
  decisions: [],
  proposals: [],
  negotiations: [],
  scoring: null,
  isLoading: false,
  error: null,
  lastUpdated: null,
  currentSimulation: null,
};

export const useSimulationStore = create<SimulationStoreState>((set) => ({
  ...initialValues,

  setActiveSimulationId: (id: string | null) =>
    set((state) => ({
      activeSimulationId: id,
      simulationId: id,
      currentSimulation: id ? buildCurrentSimulation(
        id,
        state.scenarioId,
        state.mode,
        state.status,
        state.currentTick,
        state.currentTime,
        state.crisisPhase,
        state.crisisTitle,
        state.crisisSeverity
      ) : null,
    })),

  loadInitialState: (simId: string, data: FullSimulationStateResponse) => {
    const countriesMap: Record<string, CountryState> = { ...data.countries };
    const phase = data.crisis_state?.phase ?? 'early_warning';
    const title = data.crisis_state?.title ?? '';
    const severity = data.crisis_state?.severity ?? 0;

    set({
      simulationId: simId,
      activeSimulationId: simId,
      scenarioId: data.scenario_id,
      mode: data.mode,
      status: data.status,
      currentTick: data.current_tick,
      currentTime: data.current_time,
      crisisTitle: title,
      crisisSeverity: severity,
      crisisPhase: phase,
      countries: countriesMap,
      events: data.active_events ?? [],
      eventHistory: data.event_history ?? [],
      decisions: data.decisions ?? [],
      proposals: data.proposals ?? [],
      negotiations: data.negotiations ?? [],
      isLoading: false,
      error: null,
      lastUpdated: new Date().toISOString(),
      currentSimulation: buildCurrentSimulation(
        simId,
        data.scenario_id,
        data.mode,
        data.status,
        data.current_tick,
        data.current_time,
        phase,
        title,
        severity
      ),
    });
  },

  setSnapshot: (snapshot: SimulationSnapshotPayload) => {
    const countriesMap: Record<string, CountryState> = {};
    if (Array.isArray(snapshot.countries)) {
      for (const c of snapshot.countries) {
        countriesMap[c.country_id] = c;
      }
    }

    set({
      simulationId: snapshot.simulation_id,
      activeSimulationId: snapshot.simulation_id,
      scenarioId: snapshot.scenario_id,
      mode: snapshot.mode,
      status: snapshot.status,
      currentTick: snapshot.tick,
      currentTime: snapshot.timestamp,
      crisisTitle: snapshot.title,
      crisisSeverity: snapshot.severity,
      countries: countriesMap,
      events: snapshot.recent_events ?? [],
      eventHistory: snapshot.recent_events ?? [],
      proposals: snapshot.proposals ?? [],
      negotiations: snapshot.negotiations ?? [],
      scoring: snapshot.scoring_summary ?? null,
      isLoading: false,
      error: null,
      lastUpdated: new Date().toISOString(),
      currentSimulation: buildCurrentSimulation(
        snapshot.simulation_id,
        snapshot.scenario_id,
        snapshot.mode,
        snapshot.status,
        snapshot.tick,
        snapshot.timestamp,
        'active',
        snapshot.title,
        snapshot.severity
      ),
    });
  },

  applyEvent: (envelope: WebSocketEventEnvelope) => {
    set((state) => {
      // Strict multi-simulation isolation check:
      // If envelope has a simulation_id and active state is tracking another simulation, ignore!
      const activeId = state.simulationId || state.activeSimulationId;
      if (envelope.simulation_id && activeId && envelope.simulation_id !== activeId) {
        return state;
      }

      const simId = activeId || envelope.simulation_id;
      const type = (envelope.event_type || '').toLowerCase();
      const payload = (envelope.payload ?? {}) as Record<string, unknown>;
      const timestamp = envelope.timestamp || envelope.emitted_at || new Date().toISOString();

      let newStatus = state.status;
      let newTick = envelope.tick !== undefined ? envelope.tick : state.currentTick;
      let newPhase = state.crisisPhase;
      const newCountries = { ...state.countries };
      const newEvents = [...state.events];
      const newHistory = [...state.eventHistory];
      const newDecisions = [...state.decisions];
      const newProposals = [...state.proposals];
      let newScoring = state.scoring;

      if (type === 'tick_advanced' || type === 'step_completed') {
        newTick = typeof payload.tick === 'number' ? payload.tick : envelope.tick;
        if (payload.status) newStatus = payload.status as SimulationStatus;
      } else if (type === 'simulation_started') {
        newStatus = 'running';
        newTick = envelope.tick ?? newTick;
      } else if (type === 'simulation_paused') {
        newStatus = 'paused';
      } else if (type === 'simulation_resumed') {
        newStatus = 'running';
      } else if (type === 'simulation_stopped') {
        newStatus = 'stopped';
      } else if (type === 'simulation_completed') {
        newStatus = 'completed';
      } else if (type === 'simulation_status_changed') {
        if (payload.new_status) newStatus = payload.new_status as SimulationStatus;
      } else if (type === 'country_status_changed' || type === 'country_state_updated') {
        const cId = String(payload.country_id ?? '');
        if (cId) {
          const existing = newCountries[cId] ?? {
            country_id: cId,
            country_name: String(payload.country_name ?? cId),
            defcon_level: 5,
            tension_level: 0,
            compliance_status: 'compliant',
            decision_history: [],
            current_strategy: 'deterrence',
            capabilities_score: 50,
          };
          newCountries[cId] = {
            ...existing,
            ...payload,
          } as CountryState;
        }
      } else if (type === 'decision_recorded' || type === 'country_decision') {
        const dec = payload as unknown as DecisionRecord;
        if (dec && dec.decision_id) {
          newDecisions.unshift(dec);
        }
      } else if (type === 'coordinator_proposal') {
        const prop = payload as unknown as CoordinatorProposal;
        if (prop && prop.proposal_id) {
          newProposals.unshift(prop);
          newPhase = 'negotiation';
        }
      } else if (type === 'crisis_event_triggered' || type === 'crisis_escalated') {
        const ev = payload as unknown as SimulationEvent;
        if (ev && ev.event_id) {
          newEvents.unshift(ev);
          newHistory.unshift(ev);
        }
        if (payload.phase) newPhase = String(payload.phase);
      } else if (type === 'scoring_completed' || type === 'score_update') {
        newScoring = payload as unknown as ScoringResult;
      }

      return {
        ...state,
        status: newStatus,
        currentTick: newTick,
        crisisPhase: newPhase,
        countries: newCountries,
        events: newEvents,
        eventHistory: newHistory,
        decisions: newDecisions,
        proposals: newProposals,
        scoring: newScoring,
        lastUpdated: timestamp,
        currentSimulation: buildCurrentSimulation(
          simId,
          state.scenarioId,
          state.mode,
          newStatus,
          newTick,
          timestamp,
          newPhase,
          state.crisisTitle,
          state.crisisSeverity
        ),
      };
    });
  },

  setLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  clearSimulation: (id?: string) =>
    set((state) => {
      if (!id || state.simulationId === id) {
        return initialValues;
      }
      return state;
    }),
  reset: () => set(initialValues),
}));
