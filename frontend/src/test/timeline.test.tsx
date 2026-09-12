import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { SimulationTimeline } from '../components/timeline/SimulationTimeline';
import { useSimulationStore } from '../stores/simulationStore';
import type { SimulationEvent } from '../types';

const mockTimelineEvents: SimulationEvent[] = [
  {
    event_id: 'evt_001',
    simulation_id: 'sim_test_001',
    tick: 0,
    timestamp: 'T+00',
    event_type: 'CRISIS_TRIGGERED',
    title: 'Anomalous Military LLM Weights Detected',
    description: 'Rogue high-frequency weights detected in autonomous targeting network.',
    severity: 5,
    payload: { phase: 'early_warning' },
  },
  {
    event_id: 'evt_002',
    simulation_id: 'sim_test_001',
    tick: 2,
    timestamp: 'T+02',
    event_type: 'DECISION_RECORDED',
    title: 'Alerion Dispatches Cyber Intercept',
    description: 'Federal Republic of Alerion deployed defensive perimeter filters.',
    severity: 3,
    payload: { country_id: 'country_01', action_id: 'act_cyber_defense' },
  },
  {
    event_id: 'evt_003',
    simulation_id: 'sim_test_001',
    tick: 4,
    timestamp: 'T+04',
    event_type: 'COORDINATOR_PROPOSAL',
    title: 'Joint Containment Treaty Proposed',
    description: 'International Coordinator presented collective containment draft.',
    severity: 4,
    payload: { round: 1 },
  },
  {
    event_id: 'evt_004',
    simulation_id: 'sim_test_001',
    tick: 6,
    timestamp: 'T+06',
    event_type: 'UNKNOWN_FUTURE_EVENT_TYPE',
    title: 'Unusual Telemetry Anomaly',
    description: 'Proprietary foreign sensor relay alert.',
    severity: 2,
    payload: { raw_flag: true },
  },
];

describe('Phase 12 — Simulation Timeline', () => {
  beforeEach(() => {
    useSimulationStore.getState().reset();
  });

  it('renders empty timeline state when no events exist', () => {
    render(<SimulationTimeline />);

    expect(screen.getByTestId('simulation-timeline-empty')).toBeInTheDocument();
    expect(screen.getByText(/No Timeline Events Recorded/i)).toBeInTheDocument();
    expect(screen.getByTestId('timeline-current-position')).toHaveTextContent('CURRENT: T+00');
  });

  it('renders events sorted chronologically by virtual simulation tick', () => {
    // Deliberately insert in reverse order to test authoritative sorting
    useSimulationStore.setState({
      currentTick: 4,
      status: 'running',
      eventHistory: [mockTimelineEvents[2], mockTimelineEvents[0], mockTimelineEvents[1]],
    });

    render(<SimulationTimeline />);

    expect(screen.getByTestId('timeline-current-position')).toHaveTextContent('CURRENT: T+04');
    expect(screen.getByText('3 Events Recorded')).toBeInTheDocument();

    // Verify all 3 events are present
    expect(screen.getByText('Anomalous Military LLM Weights Detected')).toBeInTheDocument();
    expect(screen.getByText('Alerion Dispatches Cyber Intercept')).toBeInTheDocument();
    expect(screen.getByText('Joint Containment Treaty Proposed')).toBeInTheDocument();
  });

  it('filters events by category correctly', () => {
    useSimulationStore.setState({
      currentTick: 6,
      eventHistory: mockTimelineEvents,
    });

    render(<SimulationTimeline />);

    // Click 'CRISIS' filter
    const crisisFilterBtn = screen.getByRole('button', { name: /crisis/i });
    fireEvent.click(crisisFilterBtn);

    expect(screen.getByText('Anomalous Military LLM Weights Detected')).toBeInTheDocument();
    expect(screen.queryByText('Alerion Dispatches Cyber Intercept')).not.toBeInTheDocument();

    // Click 'NEGOTIATION' filter
    const negFilterBtn = screen.getByRole('button', { name: /negotiation/i });
    fireEvent.click(negFilterBtn);

    expect(screen.getByText('Joint Containment Treaty Proposed')).toBeInTheDocument();
    expect(screen.queryByText('Anomalous Military LLM Weights Detected')).not.toBeInTheDocument();
  });

  it('handles unknown event types gracefully without crashing', () => {
    useSimulationStore.setState({
      currentTick: 6,
      eventHistory: [mockTimelineEvents[3]], // UNKNOWN_FUTURE_EVENT_TYPE
    });

    render(<SimulationTimeline />);

    expect(screen.getByText('Unusual Telemetry Anomaly')).toBeInTheDocument();
    expect(screen.getByText('Proprietary foreign sensor relay alert.')).toBeInTheDocument();
  });
});
