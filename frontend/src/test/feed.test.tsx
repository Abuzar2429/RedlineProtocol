import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { LiveEventFeed } from '../components/feed/LiveEventFeed';
import { EventCard } from '../components/feed/EventCard';
import { useSimulationStore } from '../stores/simulationStore';
import { useConnectionStore } from '../stores/connectionStore';
import type { FormattedEvent } from '../utils/eventFormatter';

describe('LiveEventFeed & EventCard', () => {
  beforeEach(() => {
    useSimulationStore.getState().reset();
    useConnectionStore.getState().reset();
  });

  describe('EventCard', () => {
    it('renders event details, actor, timestamp, and RAG citation', () => {
      const mockEvent: FormattedEvent = {
        id: 'evt_1',
        eventType: 'DECISION_RECORDED',
        category: 'decision',
        title: 'Share Sensor Feed',
        description: 'Authorized unilateral sensor disclosure.',
        tick: 3,
        timeDisplay: 'T+03',
        actor: {
          id: 'country_01',
          name: 'Federal Republic of Alerion',
          flag: '🦅',
        },
        severity: 'info',
        ragCitation: 'Geneva Framework Article 12',
        rawPayload: {},
      };

      render(<EventCard event={mockEvent} />);

      expect(screen.getByText('Share Sensor Feed')).toBeInTheDocument();
      expect(screen.getByText('Authorized unilateral sensor disclosure.')).toBeInTheDocument();
      expect(screen.getByText('Federal Republic of Alerion')).toBeInTheDocument();
      expect(screen.getByText('T+03')).toBeInTheDocument();
      expect(screen.getByText(/RAG Grounded: Geneva Framework Article 12/i)).toBeInTheDocument();
    });
  });

  describe('LiveEventFeed', () => {
    it('renders empty state when no events are present in store', () => {
      render(<LiveEventFeed />);

      expect(screen.getByText(/No Events Recorded Yet/i)).toBeInTheDocument();
      expect(screen.getByText(/Advance the simulation engine using the Step or Run buttons/i)).toBeInTheDocument();
    });

    it('renders event list when simulationStore contains events', () => {
      useSimulationStore.getState().applyEvent({
        event_id: 'evt_crisis_1',
        event_type: 'CRISIS_TRIGGERED',
        simulation_id: 'sim_test',
        tick: 1,
        timestamp: 'T+01',
        payload: {
          title: 'Swarm Deviation Detected',
          description: 'Unusual swarm flight paths observed near neutral straits.',
        },
      });

      render(<LiveEventFeed />);

      expect(screen.getByText('Swarm Deviation Detected')).toBeInTheDocument();
      expect(screen.getByText(/1 events logged/i)).toBeInTheDocument();
    });

    it('filters events by category tabs', () => {
      // Ingest 1 crisis event and 1 decision
      useSimulationStore.getState().applyEvent({
        event_id: 'evt_crisis_1',
        event_type: 'CRISIS_TRIGGERED',
        simulation_id: 'sim_test',
        tick: 1,
        timestamp: 'T+01',
        payload: { title: 'Emergency Alert' },
      });

      useSimulationStore.getState().applyEvent({
        event_id: 'evt_dec_1',
        event_type: 'DECISION_RECORDED',
        simulation_id: 'sim_test',
        tick: 2,
        timestamp: 'T+02',
        payload: {
          country_id: 'country_02',
          label: 'Deploy Interceptors',
          reasoning: 'Protect borders.',
        },
      });

      render(<LiveEventFeed />);

      expect(screen.getByText('Emergency Alert')).toBeInTheDocument();
      expect(screen.getByText('Deploy Interceptors')).toBeInTheDocument();

      // Click "decision" filter tab
      const decisionTab = screen.getByRole('button', { name: /^decision$/i });
      fireEvent.click(decisionTab);

      expect(screen.getByText('Deploy Interceptors')).toBeInTheDocument();
      expect(screen.queryByText('Emergency Alert')).not.toBeInTheDocument();
    });

    it('displays disconnected banner when WebSocket state is not CONNECTED', () => {
      useConnectionStore.getState().setConnectionState('DISCONNECTED');
      render(<LiveEventFeed />);

      expect(screen.getByText(/WebSocket disconnected/i)).toBeInTheDocument();
    });
  });
});
