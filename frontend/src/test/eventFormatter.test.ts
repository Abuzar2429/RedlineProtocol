import { describe, it, expect } from 'vitest';
import { formatSimulationEvent } from '../utils/eventFormatter';

describe('formatSimulationEvent', () => {
  it('formats CRISIS_TRIGGERED events correctly', () => {
    const raw = {
      event_id: 'evt_crisis_1',
      event_type: 'CRISIS_TRIGGERED',
      tick: 2,
      timestamp: 'T+02',
      payload: {
        title: 'Autonomous Weapons Swarm Anomaly',
        description: 'Unscheduled swarm convergence detected in international airspace.',
        severity: 9,
      },
    };

    const formatted = formatSimulationEvent(raw);
    expect(formatted.id).toBe('evt_crisis_1');
    expect(formatted.category).toBe('crisis');
    expect(formatted.severity).toBe('critical');
    expect(formatted.title).toBe('Autonomous Weapons Swarm Anomaly');
    expect(formatted.timeDisplay).toBe('T+02');
  });

  it('formats DECISION_RECORDED with country actor and RAG grounding', () => {
    const raw = {
      event_id: 'dec_1',
      event_type: 'DECISION_RECORDED',
      tick: 3,
      timestamp: 'T+03',
      payload: {
        country_id: 'country_01',
        label: 'Share Telemetry Stream',
        reasoning: 'Reduces miscalculation risk.',
        rag_sources: ['International AI Safety Framework Article 4'],
      },
    };

    const formatted = formatSimulationEvent(raw);
    expect(formatted.category).toBe('decision');
    expect(formatted.title).toBe('Share Telemetry Stream');
    expect(formatted.actor?.id).toBe('country_01');
    expect(formatted.actor?.name).toBe('Federal Republic of Alerion');
    expect(formatted.actor?.flag).toBe('🦅');
    expect(formatted.ragCitation).toBe('International AI Safety Framework Article 4');
  });

  it('formats COORDINATOR_PROPOSAL events with diplomat actor', () => {
    const raw = {
      event_id: 'prop_99',
      event_type: 'COORDINATOR_PROPOSAL',
      tick: 5,
      timestamp: 'T+05',
      payload: {
        title: 'Joint Verification Accord',
        summary: 'Requires bilateral sensor sharing.',
      },
    };

    const formatted = formatSimulationEvent(raw);
    expect(formatted.category).toBe('negotiation');
    expect(formatted.severity).toBe('warning');
    expect(formatted.actor?.name).toBe('International Coordinator');
    expect(formatted.actor?.flag).toBe('🏛️');
  });

  it('safely handles unknown or novel event types without crashing', () => {
    const raw = {
      event_id: 'evt_future_unknown',
      event_type: 'CUSTOM_ORBITAL_TELEMETRY',
      tick: 10,
      timestamp: 'T+10',
      payload: {
        foo: 'bar',
        detail: 'Deep satellite alert received.',
      },
    };

    const formatted = formatSimulationEvent(raw);
    expect(formatted.id).toBe('evt_future_unknown');
    expect(formatted.category).toBe('general');
    expect(formatted.description).toBe('Deep satellite alert received.');
  });

  it('safely handles malformed null payload', () => {
    const raw = {
      event_id: 'evt_empty',
      event_type: 'RANDOM',
      payload: null,
    };

    const formatted = formatSimulationEvent(raw);
    expect(formatted.id).toBe('evt_empty');
    expect(formatted.category).toBe('general');
  });
});
