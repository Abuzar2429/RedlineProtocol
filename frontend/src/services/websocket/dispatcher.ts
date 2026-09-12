/**
 * Centralized WebSocket event dispatcher.
 * Validates inbound frames and dispatches them to Zustand stores.
 */
import { useConnectionStore } from '../../stores/connectionStore';
import { useSimulationStore } from '../../stores/simulationStore';
import { useUIStore } from '../../stores/uiStore';
import type { WebSocketEventEnvelope } from '../../types';

export function dispatchWebSocketMessage(rawData: string): boolean {
  try {
    const envelope = JSON.parse(rawData) as WebSocketEventEnvelope;

    if (!envelope || typeof envelope !== 'object' || !envelope.event_type) {
      console.warn('Malformed WebSocket message received (missing event_type):', rawData);
      return false;
    }

    // Record incoming message in connection store
    useConnectionStore.getState().recordMessage();

    // Pass to authoritative simulation store
    useSimulationStore.getState().applyEvent(envelope);

    // Contextual UI toast alerts for key milestones
    const eventTypeUpper = envelope.event_type.toUpperCase();
    switch (eventTypeUpper) {
      case 'SIMULATION_STARTED':
        useUIStore.getState().addToast({
          type: 'info',
          title: 'Simulation Started',
          message: `Simulation ${envelope.simulation_id} is now running.`,
        });
        break;

      case 'SIMULATION_STATUS_CHANGED':
        useUIStore.getState().addToast({
          type: 'info',
          title: 'Simulation Running',
          message: 'Simulation status updated.',
        });
        break;

      case 'COORDINATOR_PROPOSAL':
        useUIStore.getState().addToast({
          type: 'info',
          title: 'New Joint Proposal',
          message: 'International Coordinator drafted a new multilateral proposal.',
        });
        break;

      case 'SIMULATION_COMPLETED':
        useUIStore.getState().addToast({
          type: 'success',
          title: 'Simulation Complete',
          message: 'All scenario events and crisis actions resolved.',
        });
        break;
    }

    return true;
  } catch (err) {
    console.warn('Failed to parse WebSocket event JSON:', err, rawData);
    return false;
  }
}

export const dispatchEvent = dispatchWebSocketMessage;
export default dispatchWebSocketMessage;
