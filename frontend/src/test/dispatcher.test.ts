import { describe, it, expect, beforeEach, vi } from 'vitest';
import { dispatchEvent } from '../services/websocket/dispatcher';
import { useSimulationStore } from '../stores/simulationStore';
import { useUIStore } from '../stores/uiStore';
import { useConnectionStore } from '../stores/connectionStore';

describe('WebSocket Event Dispatcher', () => {
  beforeEach(() => {
    useSimulationStore.getState().reset();
    useConnectionStore.getState().reset();
    useUIStore.getState().clearToasts();
    useSimulationStore.getState().setActiveSimulationId('sim_target');
  });

  it('safely rejects invalid JSON without throwing', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(() => dispatchEvent('INVALID_NON_JSON{{{')).not.toThrow();
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });

  it('safely rejects messages lacking required envelope fields', () => {
    const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    expect(() => dispatchEvent(JSON.stringify({ some_other_key: 123 }))).not.toThrow();
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });

  it('dispatches valid simulation event and updates store & connection timestamp', () => {
    const envelope = {
      event_id: 'evt_test_1',
      event_type: 'tick_advanced',
      simulation_id: 'sim_target',
      tick: 5,
      timestamp: '2026-09-12T12:00:00Z',
      payload: {
        tick: 5,
        current_time: '2026-09-12T12:00:00Z',
        events: [],
      },
    };

    dispatchEvent(JSON.stringify(envelope));

    expect(useConnectionStore.getState().lastMessageTime).not.toBeNull();
    expect(useSimulationStore.getState().currentSimulation?.current_tick).toBe(5);
  });

  it('handles unknown event types without crashing', () => {
    const envelope = {
      event_id: 'evt_unknown',
      event_type: 'custom_future_telemetry_event',
      simulation_id: 'sim_target',
      tick: 2,
      timestamp: '2026-09-12T12:00:00Z',
      payload: { foo: 'bar' },
    };

    expect(() => dispatchEvent(JSON.stringify(envelope))).not.toThrow();
    // Recorded message in connection store even if event type is unknown
    expect(useConnectionStore.getState().lastMessageTime).not.toBeNull();
  });

  it('dispatches status change toast notification', () => {
    const envelope = {
      event_id: 'evt_status',
      event_type: 'simulation_status_changed',
      simulation_id: 'sim_target',
      tick: 1,
      timestamp: '2026-09-12T12:00:00Z',
      payload: {
        old_status: 'initialized',
        new_status: 'running',
      },
    };

    dispatchEvent(JSON.stringify(envelope));

    const toasts = useUIStore.getState().toasts;
    expect(toasts.length).toBeGreaterThan(0);
    expect(toasts[0].title).toBe('Simulation Running');
  });
});
