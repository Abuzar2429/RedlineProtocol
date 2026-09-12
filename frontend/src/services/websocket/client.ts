/**
 * Resilient WebSocket client for real-time simulation streaming.
 * Supports auto-reconnect with exponential backoff and cleanup.
 */
import { useConnectionStore } from '../../stores/connectionStore';
import type { WebSocketClientMessage } from '../../types';
import { dispatchWebSocketMessage } from './dispatcher';

export class SimulationWebSocketClient {
  private socket: WebSocket | null = null;
  private simulationId: string | null = null;
  private isIntentionallyClosed = false;
  private reconnectTimer: number | null = null;
  private pingInterval: number | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private wsBaseUrl?: string;

  constructor(wsBaseUrl?: string) {
    this.wsBaseUrl = wsBaseUrl;
  }

  public connect(simulationId?: string): void {
    const targetSimId = simulationId || this.simulationId;
    if (!targetSimId) return;

    // If already connected to this simulation, ignore
    if (this.socket && this.simulationId === targetSimId && this.socket.readyState === WebSocket.OPEN) {
      return;
    }

    // Clean up previous socket if switching simulations
    this.disconnect();

    this.simulationId = targetSimId;
    this.isIntentionallyClosed = false;
    useConnectionStore.getState().setConnecting(targetSimId);

    const url = this.buildWebSocketUrl(targetSimId);

    try {
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        this.reconnectAttempts = 0;
        useConnectionStore.getState().setConnected();
        this.startHeartbeat();
      };

      this.socket.onmessage = (event: MessageEvent) => {
        if (typeof event.data === 'string') {
          dispatchWebSocketMessage(event.data);
        }
      };

      this.socket.onerror = (error) => {
        console.warn('WebSocket encountered error:', error);
        useConnectionStore.getState().setError('Connection error');
      };

      this.socket.onclose = (event: CloseEvent) => {
        this.stopHeartbeat();
        this.socket = null;

        if (this.isIntentionallyClosed) {
          useConnectionStore.getState().setDisconnected();
          return;
        }

        // Bounded reconnection with exponential backoff
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts += 1;
          useConnectionStore.getState().setReconnecting(this.reconnectAttempts);

          const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts - 1), 10000);
          this.reconnectTimer = window.setTimeout(() => {
            if (!this.isIntentionallyClosed && this.simulationId) {
              this.connect(this.simulationId);
            }
          }, delay);
        } else {
          useConnectionStore.getState().setError(
            `Disconnected from simulation (code ${event.code})`
          );
        }
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'WebSocket initialization failed';
      useConnectionStore.getState().setError(msg);
    }
  }

  public disconnect(): void {
    this.isIntentionallyClosed = true;
    this.stopHeartbeat();

    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.socket) {
      // Remove event handlers to avoid unwanted state updates during intentional tear-down
      this.socket.onopen = null;
      this.socket.onmessage = null;
      this.socket.onerror = null;
      this.socket.onclose = null;
      this.socket.close();
      this.socket = null;
    }

    this.reconnectAttempts = 0;
    this.simulationId = null;
    useConnectionStore.getState().setDisconnected();
  }

  public send(action: WebSocketClientMessage['action'], payload?: Record<string, unknown>): boolean {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      console.warn('Cannot send WebSocket message: socket not open');
      return false;
    }

    try {
      const msg: WebSocketClientMessage = { action, payload };
      this.socket.send(JSON.stringify(msg));
      return true;
    } catch (err) {
      console.error('Failed to send WebSocket message:', err);
      return false;
    }
  }

  public ping(): void {
    this.send('ping');
  }

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.pingInterval = window.setInterval(() => {
      this.ping();
    }, 25000);
  }

  private stopHeartbeat(): void {
    if (this.pingInterval !== null) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private buildWebSocketUrl(simulationId: string): string {
    if (this.wsBaseUrl) {
      return `${this.wsBaseUrl}/ws/simulations/${simulationId}`;
    }

    const envWs = import.meta.env.VITE_WS_BASE_URL;
    if (envWs) {
      return `${envWs}/ws/simulations/${simulationId}`;
    }

    const loc = window.location;
    const protocol = loc.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${loc.host}/ws/simulations/${simulationId}`;
  }
}

const clientPool = new Map<string, SimulationWebSocketClient>();

export function getWebSocketClient(simulationId?: string): SimulationWebSocketClient {
  const key = simulationId || 'default';
  if (!clientPool.has(key)) {
    clientPool.set(key, new SimulationWebSocketClient());
  }
  return clientPool.get(key)!;
}

export const wsClient = getWebSocketClient();
export default wsClient;
