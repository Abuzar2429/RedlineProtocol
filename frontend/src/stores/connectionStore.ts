import { create } from 'zustand';
import type { ConnectionState } from '../types';

interface ConnectionStoreState {
  state: ConnectionState;
  simulationId: string | null;
  lastConnectedAt: string | null;
  lastMessageAt: string | null;
  lastConnectedTime: string | null;
  lastMessageTime: string | null;
  reconnectAttempts: number;
  error: string | null;

  setConnectionState: (state: ConnectionState) => void;
  setConnecting: (simulationId?: string) => void;
  setConnected: () => void;
  setReconnecting: (attempt: number) => void;
  recordReconnectAttempt: (error?: string) => void;
  setDisconnected: () => void;
  setError: (error: string) => void;
  recordMessage: () => void;
  recordMessageReceived: () => void;
  reset: () => void;
}

export const useConnectionStore = create<ConnectionStoreState>((set) => ({
  state: 'DISCONNECTED',
  simulationId: null,
  lastConnectedAt: null,
  lastMessageAt: null,
  lastConnectedTime: null,
  lastMessageTime: null,
  reconnectAttempts: 0,
  error: null,

  setConnectionState: (state: ConnectionState) => {
    const now = new Date().toISOString();
    set((s) => ({
      state,
      lastConnectedTime: state === 'CONNECTED' ? now : s.lastConnectedTime,
      lastConnectedAt: state === 'CONNECTED' ? now : s.lastConnectedAt,
      reconnectAttempts: state === 'CONNECTED' ? 0 : s.reconnectAttempts,
    }));
  },

  setConnecting: (simulationId?: string) =>
    set((s) => ({
      state: 'CONNECTING',
      simulationId: simulationId !== undefined ? simulationId : s.simulationId,
      error: null,
    })),

  setConnected: () => {
    const now = new Date().toISOString();
    set({
      state: 'CONNECTED',
      reconnectAttempts: 0,
      lastConnectedAt: now,
      lastConnectedTime: now,
      error: null,
    });
  },

  setReconnecting: (attempt: number) =>
    set({
      state: 'RECONNECTING',
      reconnectAttempts: attempt,
    }),

  recordReconnectAttempt: (error?: string) =>
    set((state) => ({
      state: 'RECONNECTING',
      reconnectAttempts: state.reconnectAttempts + 1,
      error: error || state.error,
    })),

  setDisconnected: () =>
    set({
      state: 'DISCONNECTED',
      reconnectAttempts: 0,
    }),

  setError: (error: string) =>
    set({
      state: 'ERROR',
      error,
    }),

  recordMessage: () => {
    const now = new Date().toISOString();
    set({
      lastMessageAt: now,
      lastMessageTime: now,
    });
  },

  recordMessageReceived: () => {
    const now = new Date().toISOString();
    set({
      lastMessageAt: now,
      lastMessageTime: now,
    });
  },

  reset: () =>
    set({
      state: 'DISCONNECTED',
      simulationId: null,
      lastConnectedAt: null,
      lastMessageAt: null,
      lastConnectedTime: null,
      lastMessageTime: null,
      reconnectAttempts: 0,
      error: null,
    }),
}));
