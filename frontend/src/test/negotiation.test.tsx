import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NegotiationPanel } from '../components/negotiation/NegotiationPanel';
import { useSimulationStore } from '../stores/simulationStore';
import type {
  CoordinatorProposal,
  NegotiationSession,
  NegotiationRound,
} from '../types';

const mockProposal: CoordinatorProposal = {
  proposal_id: 'prop_001',
  simulation_id: 'sim_test_001',
  tick: 4,
  round: 1,
  proposal_type: 'JOINT_RESPONSE',
  title: 'Global Autonomous Containment Pact',
  summary: 'Multilateral technical quarantine and real-time telemetry exchange agreement.',
  items: [
    'Immediate quarantine of affected server clusters',
    'Bilateral cryptographic telemetry streaming to the Coordinator',
    'Joint verification inspection teams deployed within 24 hours',
  ],
  rationale: 'Preserves national data sovereignty while neutralizing collective escalation risks.',
  supporting_countries: ['country_01', 'country_02', 'country_03'],
  opposing_countries: ['country_06'],
  confidence: 0.85,
  source: 'llm_coordinator',
  status: 'PROPOSED',
  rag_sources: ['International AI Safety Accord 2025 §4.2'],
};

const mockRound1: NegotiationRound = {
  round_number: 1,
  proposal_version: {
    version: 1,
    proposal_id: 'prop_001',
    title: 'Global Autonomous Containment Pact',
    summary: 'Initial multilateral technical quarantine protocol.',
    items: ['Immediate quarantine of affected server clusters'],
    rationale: 'Initial collective response balancing sovereignty.',
    unresolved_issues: ['Inspection access jurisdiction'],
    created_at_tick: 4,
    source: 'llm_coordinator',
    created_at: '2026-09-12T12:00:00Z',
  },
  voting_result: {
    round: 1,
    proposal_version: 1,
    eligible_voters: 15,
    votes_cast: 15,
    votes_for: 9,
    votes_against: 4,
    abstentions: 2,
    participation_rate: 1.0,
    is_quorum_met: true,
    required_threshold: 0.67,
    achieved_threshold: 0.60,
    passed: false,
    status: 'INSUFFICIENT_SUPPORT',
    failure_reason: 'Supermajority of 67% not reached (achieved 60%).',
    approving_countries: ['country_01', 'country_02', 'country_03', 'country_04'],
    opposing_countries: ['country_06', 'country_07', 'country_08', 'country_09'],
    abstaining_countries: ['country_05', 'country_10'],
  },
  unresolved_issues: ['Inspection access jurisdiction'],
  status: 'COMPLETED',
  started_at_tick: 4,
  completed_at_tick: 8,
};

const mockRound2: NegotiationRound = {
  round_number: 2,
  proposal_version: {
    version: 2,
    proposal_id: 'prop_001',
    title: 'Revised Autonomous Containment Protocol',
    summary: 'Compromise text limiting inspections to mutual consent zones.',
    items: [
      'Immediate quarantine of affected server clusters',
      'Mutual-consent telemetry verification',
    ],
    rationale: 'Addressed sovereignty objections raised by dissenting nations.',
    unresolved_issues: [],
    created_at_tick: 8,
    source: 'llm_coordinator',
    created_at: '2026-09-12T12:15:00Z',
  },
  voting_result: {
    round: 2,
    proposal_version: 2,
    eligible_voters: 15,
    votes_cast: 15,
    votes_for: 12,
    votes_against: 2,
    abstentions: 1,
    participation_rate: 1.0,
    is_quorum_met: true,
    required_threshold: 0.67,
    achieved_threshold: 0.80,
    passed: true,
    status: 'PASSED',
    approving_countries: ['country_01', 'country_02', 'country_03', 'country_04', 'country_05', 'country_06'],
    opposing_countries: ['country_08', 'country_09'],
    abstaining_countries: ['country_10'],
  },
  unresolved_issues: [],
  status: 'COMPLETED',
  started_at_tick: 8,
  completed_at_tick: 12,
};

const mockSession: NegotiationSession = {
  negotiation_id: 'neg_001',
  simulation_id: 'sim_test_001',
  coordination_mode: 'coordinated',
  status: 'ACCEPTED',
  current_round: 2,
  max_rounds: 3,
  participating_countries: ['country_01', 'country_02'],
  proposal_versions: [mockRound1.proposal_version, mockRound2.proposal_version],
  rounds: [mockRound1, mockRound2],
  outcome: {
    negotiation_id: 'neg_001',
    simulation_id: 'sim_test_001',
    final_status: 'ACCEPTED',
    agreement_reached: true,
    rounds_completed: 2,
    final_proposal_version: 2,
    final_vote_result: mockRound2.voting_result,
    supporting_countries: ['country_01', 'country_02', 'country_03', 'country_04', 'country_05', 'country_06'],
    opposing_countries: ['country_08', 'country_09'],
    abstaining_countries: ['country_10'],
    unresolved_issues: [],
    completed_at_tick: 12,
  },
  created_at_tick: 4,
};

describe('Phase 12 — Negotiation Panel', () => {
  beforeEach(() => {
    useSimulationStore.getState().reset();
  });

  it('renders empty chamber state when no negotiation or proposal exists', () => {
    render(<NegotiationPanel />);

    expect(screen.getByTestId('negotiation-panel-empty')).toBeInTheDocument();
    expect(screen.getByText(/No Negotiation Session Active/i)).toBeInTheDocument();
    expect(screen.getByText(/Standing by for Coordinator Treaty Draft/i)).toBeInTheDocument();
  });

  it('renders coordinator proposal information cleanly', () => {
    useSimulationStore.setState({ proposals: [mockProposal] });
    render(<NegotiationPanel />);

    expect(screen.getByTestId('negotiation-panel')).toBeInTheDocument();
    expect(screen.getByText('Global Autonomous Containment Pact')).toBeInTheDocument();
    expect(screen.getByText(/Multilateral technical quarantine and real-time/i)).toBeInTheDocument();
    expect(screen.getByText(/Immediate quarantine of affected server clusters/i)).toBeInTheDocument();
    expect(screen.getByText(/85%/)).toBeInTheDocument(); // Confidence
    expect(screen.getByText(/International AI Safety Accord 2025/i)).toBeInTheDocument();
  });

  it('renders voting results, quorum, threshold meters and country alignment', () => {
    useSimulationStore.getState().setNegotiationSessions([mockSession]);
    render(<NegotiationPanel />);

    expect(screen.getByTestId('negotiation-voting-result')).toBeInTheDocument();
    expect(screen.getByText('ACCEPTED')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument(); // Votes for
    expect(screen.getByText('2')).toBeInTheDocument();  // Votes against
    expect(screen.getByText('1')).toBeInTheDocument();  // Abstentions
    expect(screen.getByText(/Quorum Met/i)).toBeInTheDocument();
    expect(screen.getByText(/Threshold Achieved/i)).toBeInTheDocument();
  });

  it('supports round switching between Round 1 and Round 2', () => {
    useSimulationStore.getState().setNegotiationSessions([mockSession]);
    render(<NegotiationPanel />);

    // Click Round 1 tab
    const round1Btn = screen.getByText('Round 1');
    fireEvent.click(round1Btn);

    // Verify Round 1 details display
    expect(screen.getByText('INSUFFICIENT_SUPPORT')).toBeInTheDocument();
    expect(screen.getByText('9')).toBeInTheDocument(); // Round 1 approvals
    expect(screen.getByText(/Supermajority of 67% not reached/i)).toBeInTheDocument();
    expect(screen.getByText(/Inspection access jurisdiction/i)).toBeInTheDocument();
  });
});
