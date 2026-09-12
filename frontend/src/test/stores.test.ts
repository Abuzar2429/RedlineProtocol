import { describe, it, expect, beforeEach } from 'vitest';
import { useConnectionStore } from '../stores/connectionStore';
import { useSimulationStore } from '../stores/simulationStore';
import { useUIStore } from '../stores/uiStore';
import type { FullSimulationStateResponse } from '../types/api';
import type { WebSocketEventEnvelope } from '../types/events';

describe('Zustand Stores & Multi-Simulation Isolation', () => {
  beforeEach(() => {
    useConnectionStore.getState().reset();
    useSimulationStore.getState().reset();
    useUIStore.getState().clearToasts();
    useUIStore.getState().setSidebarCollapsed(false);
  });

  describe('connectionStore', () => {
    it('initializes with default disconnected state', () => {
      const state = useConnectionStore.getState();
      expect(state.state).toBe('DISCONNECTED');
      expect(state.reconnectAttempts).toBe(0);
      expect(state.error).toBeNull();
      expect(state.lastMessageTime).toBeNull();
    });

    it('updates connection state and timestamps properly', () => {
      useConnectionStore.getState().setConnectionState('CONNECTING');
      expect(useConnectionStore.getState().state).toBe('CONNECTING');

      useConnectionStore.getState().setConnectionState('CONNECTED');
      expect(useConnectionStore.getState().state).toBe('CONNECTED');
      expect(useConnectionStore.getState().lastConnectedTime).not.toBeNull();
      expect(useConnectionStore.getState().reconnectAttempts).toBe(0);
    });

    it('tracks reconnection attempts and errors', () => {
      useConnectionStore.getState().recordReconnectAttempt('Socket timeout');
      expect(useConnectionStore.getState().state).toBe('RECONNECTING');
      expect(useConnectionStore.getState().reconnectAttempts).toBe(1);
      expect(useConnectionStore.getState().error).toBe('Socket timeout');

      useConnectionStore.getState().recordReconnectAttempt();
      expect(useConnectionStore.getState().reconnectAttempts).toBe(2);
    });

    it('records received message timestamp', () => {
      expect(useConnectionStore.getState().lastMessageTime).toBeNull();
      useConnectionStore.getState().recordMessageReceived();
      expect(useConnectionStore.getState().lastMessageTime).not.toBeNull();
    });
  });

  describe('uiStore', () => {
    it('toggles sidebar collapse state', () => {
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);
      useUIStore.getState().toggleSidebar();
      expect(useUIStore.getState().sidebarCollapsed).toBe(true);
      useUIStore.getState().toggleSidebar();
      expect(useUIStore.getState().sidebarCollapsed).toBe(false);
    });

    it('adds and dismisses toast notifications, bounding at 5 items', () => {
      for (let i = 1; i <= 7; i++) {
        useUIStore.getState().addToast({
          type: 'info',
          title: `Toast ${i}`,
        });
      }

      const toasts = useUIStore.getState().toasts;
      expect(toasts.length).toBe(5);
      expect(toasts[toasts.length - 1].title).toBe('Toast 7');

      const firstToastId = toasts[0].id;
      useUIStore.getState().removeToast(firstToastId);
      expect(useUIStore.getState().toasts.length).toBe(4);
    });
  });

  describe('simulationStore & Multi-Simulation Isolation', () => {
    const mockFullState: FullSimulationStateResponse = {
      simulation_id: 'sim_ALPHA',
      scenario_id: 'scenario_01',
      mode: 'autonomous',
      status: 'initialized',
      current_tick: 0,
      current_time: '2026-09-12T00:00:00Z',
      crisis_state: {
        crisis_id: 'scenario_01',
        title: 'Weapons Escalation',
        severity: 8,
        phase: 'early_warning',
        escalation_level: 2,
        resolved: false,
      },
      countries: {
        US: {
          country_id: 'US',
          defcon_level: 4,
          tension_level: 3,
          compliance_status: 'compliant',
          decision_history: [],
          current_strategy: 'deterrence',
          capabilities_score: 95,
        },
      },
      decisions: [],
      active_events: [],
      event_history: [],
      proposals: [],
      negotiations: [],
      metadata: {},
    };

    it('loads initial state and sets active simulation', () => {
      useSimulationStore.getState().loadInitialState('sim_ALPHA', mockFullState);

      const state = useSimulationStore.getState();
      expect(state.activeSimulationId).toBe('sim_ALPHA');
      expect(state.currentSimulation?.simulation_id).toBe('sim_ALPHA');
      expect(state.currentSimulation?.crisis_phase).toBe('early_warning');
      expect(state.countries['US']?.defcon_level).toBe(4);
    });

    it('applies tick and event updates for active simulation', () => {
      useSimulationStore.getState().loadInitialState('sim_ALPHA', mockFullState);

      const tickEvent: WebSocketEventEnvelope = {
        event_id: 'evt_1',
        event_type: 'tick_advanced',
        simulation_id: 'sim_ALPHA',
        tick: 1,
        timestamp: '2026-09-12T00:01:00Z',
        payload: {
          tick: 1,
          current_time: '2026-09-12T00:01:00Z',
          events: [],
        },
      };

      useSimulationStore.getState().applyEvent(tickEvent);
      expect(useSimulationStore.getState().currentSimulation?.current_tick).toBe(1);
    });

    it('CRITICAL: Enforces multi-simulation isolation (Simulation A vs Simulation B)', () => {
      // 1. Mount simulation ALPHA
      useSimulationStore.getState().loadInitialState('sim_ALPHA', mockFullState);
      expect(useSimulationStore.getState().currentSimulation?.current_tick).toBe(0);

      // 2. An event arrives belonging to simulation BETA
      const foreignEvent: WebSocketEventEnvelope = {
        event_id: 'evt_foreign_99',
        event_type: 'tick_advanced',
        simulation_id: 'sim_BETA', // Mismatched ID!
        tick: 42,
        timestamp: '2026-09-12T00:42:00Z',
        payload: {
          tick: 42,
          current_time: '2026-09-12T00:42:00Z',
          events: [],
        },
      };

      // 3. Apply the foreign event
      useSimulationStore.getState().applyEvent(foreignEvent);

      // 4. Verify simulation ALPHA state was NOT mutated!
      const currentSim = useSimulationStore.getState().currentSimulation;
      expect(currentSim?.simulation_id).toBe('sim_ALPHA');
      expect(currentSim?.current_tick).toBe(0); // Tick remains 0! Not 42!
      expect(useSimulationStore.getState().eventHistory.length).toBe(0);
    });
  });
});
