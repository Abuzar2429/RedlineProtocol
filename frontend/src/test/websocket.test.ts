import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { SimulationWebSocketClient } from '../services/websocket/client';
import { useConnectionStore } from '../stores/connectionStore';

// Mock WebSocket
class MockWebSocket {
  public static instances: MockWebSocket[] = [];
  public static OPEN = 1;
  public static CLOSED = 3;

  public url: string;
  public readyState: number = MockWebSocket.OPEN;
  public onopen: (() => void) | null = null;
  public onmessage: ((event: { data: string }) => void) | null = null;
  public onerror: ((error: unknown) => void) | null = null;
  public onclose: ((event: { code: number; reason: string }) => void) | null = null;
  public send = vi.fn();
  public close = vi.fn(() => {
    this.readyState = MockWebSocket.CLOSED;
    if (this.onclose) {
      this.onclose({ code: 1000, reason: 'Normal Closure' });
    }
  });

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
    setTimeout(() => {
      if (this.onopen) this.onopen();
    }, 5);
  }
}

describe('SimulationWebSocketClient', () => {
  let originalWebSocket: typeof WebSocket;

  beforeEach(() => {
    useConnectionStore.getState().reset();
    MockWebSocket.instances = [];
    originalWebSocket = globalThis.WebSocket;
    // @ts-expect-error mock socket
    globalThis.WebSocket = MockWebSocket;
    vi.useFakeTimers();
  });

  afterEach(() => {
    globalThis.WebSocket = originalWebSocket;
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('connects to correct simulation URL and updates connection store to CONNECTED', async () => {
    const client = new SimulationWebSocketClient('ws://test-server.local');
    client.connect('sim_abc123');

    expect(useConnectionStore.getState().state).toBe('CONNECTING');

    const socketInstance = MockWebSocket.instances[0];
    expect(socketInstance).toBeDefined();
    expect(socketInstance.url).toBe('ws://test-server.local/ws/simulations/sim_abc123');

    // Fast-forward opening timer
    vi.advanceTimersByTime(10);
    expect(useConnectionStore.getState().state).toBe('CONNECTED');
    expect(useConnectionStore.getState().reconnectAttempts).toBe(0);

    client.disconnect();
  });

  it('handles incoming messages via dispatcher', () => {
    const client = new SimulationWebSocketClient('ws://test-server.local');
    client.connect('sim_abc123');
    vi.advanceTimersByTime(10);

    const socketInstance = MockWebSocket.instances[0];
    const eventPayload = {
      event_id: 'evt_1',
      event_type: 'tick_advanced',
      simulation_id: 'sim_abc123',
      tick: 2,
      timestamp: '2026-09-12T00:02:00Z',
      payload: {},
    };

    if (socketInstance.onmessage) {
      socketInstance.onmessage({ data: JSON.stringify(eventPayload) });
    }

    expect(useConnectionStore.getState().lastMessageTime).not.toBeNull();
    client.disconnect();
  });

  it('triggers exponential backoff reconnect on unexpected close', () => {
    const client = new SimulationWebSocketClient('ws://test-server.local');
    client.connect('sim_abc123');
    vi.advanceTimersByTime(10);

    const socketInstance = MockWebSocket.instances[0];
    // Simulate unexpected server crash/disconnect
    if (socketInstance.onclose) {
      socketInstance.onclose({ code: 1006, reason: 'Abnormal' });
    }

    // Should transition to RECONNECTING with attempt 1
    expect(useConnectionStore.getState().state).toBe('RECONNECTING');
    expect(useConnectionStore.getState().reconnectAttempts).toBe(1);

    // Fast-forward 1000ms delay for first retry
    vi.advanceTimersByTime(1050);

    // Second socket instance should have been spawned
    expect(MockWebSocket.instances.length).toBe(2);

    client.disconnect();
  });

  it('cleanly disconnects on intentional user/component teardown', () => {
    const client = new SimulationWebSocketClient('ws://test-server.local');
    client.connect('sim_abc123');
    vi.advanceTimersByTime(10);

    expect(useConnectionStore.getState().state).toBe('CONNECTED');

    client.disconnect();

    expect(useConnectionStore.getState().state).toBe('DISCONNECTED');
    // Ensure no reconnection attempt timer is scheduled
    vi.advanceTimersByTime(5000);
    expect(useConnectionStore.getState().state).toBe('DISCONNECTED');
    expect(MockWebSocket.instances.length).toBe(1);
  });
});
