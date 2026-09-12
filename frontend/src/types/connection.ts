/**
 * WebSocket and HTTP connection state types.
 */
export type ConnectionState =
  | 'DISCONNECTED'
  | 'CONNECTING'
  | 'CONNECTED'
  | 'RECONNECTING'
  | 'ERROR';

export type ConnectionStatus = 'checking' | 'connected' | 'offline';

export interface ConnectionInfo {
  state: ConnectionState;
  simulationId: string | null;
  lastConnectedAt: string | null;
  lastMessageAt: string | null;
  reconnectAttempts: number;
  error: string | null;
}
