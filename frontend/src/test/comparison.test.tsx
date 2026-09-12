import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ModeComparisonCard } from '../components/comparison/ModeComparisonCard';
import { MetricsComparisonBar } from '../components/comparison/MetricsComparisonBar';
import { DeltasTable } from '../components/comparison/DeltasTable';
import type { ComparisonDelta, ModeComparisonResult } from '../types';

const mockCoordinatedResult: ModeComparisonResult = {
  mode: 'coordinated',
  mode_name: 'Full Coordinated Governance',
  simulation_id: 'sim_test_coord',
  status: 'COMPLETED',
  final_tick: 14,
  overall_score: 86.5,
  score_grade: 'A',
  performance_headline: 'Optimal multilateral accord achieved rapid containment.',
  is_winner: true,
  metric_breakdown: [
    {
      metric_id: 'risk_reduction',
      name: 'Risk Reduction',
      raw_value: 76.5,
      unit: '%',
      normalized_score: 76.5,
      weight: 0.25,
      weighted_score: 19.1,
      display_value: '↓76.5%',
      interpretation: 'Substantial risk reduction',
    },
    {
      metric_id: 'response_time',
      name: 'Response Time',
      raw_value: 14,
      unit: 'm',
      normalized_score: 88.0,
      weight: 0.25,
      weighted_score: 22.0,
      display_value: '14m',
      interpretation: 'Rapid response',
    },
    {
      metric_id: 'coordination',
      name: 'Coordination',
      raw_value: 0.87,
      unit: 'ratio',
      normalized_score: 86.7,
      weight: 0.25,
      weighted_score: 21.7,
      display_value: '0.87 (13/15)',
      interpretation: 'Multilateral consensus',
    },
    {
      metric_id: 'unresolved_issues',
      name: 'Unresolved Issues',
      raw_value: 1,
      unit: 'count',
      normalized_score: 80.0,
      weight: 0.25,
      weighted_score: 20.0,
      display_value: '1',
      interpretation: 'Low deadlock count',
    },
  ],
  metrics: {
    risk_initial: 100,
    risk_final: 23.5,
    risk_reduction_pct: 76.5,
    response_time_minutes: 14,
    coordination_ratio: 0.87,
    countries_coordinating: 13,
    countries_total: 15,
    unresolved_issues: ['Liability'],
    unresolved_issues_count: 1,
    negotiation_rounds: 2,
    agreement_reached: true,
    simulation_mode: 'coordinated',
  },
  negotiation_outcome: {
    negotiation_id: 'neg_1',
    simulation_id: 'sim_test_coord',
    final_status: 'ACCEPTED',
    agreement_reached: true,
    rounds_completed: 2,
    final_proposal_version: 2,
    supporting_countries: ['c1', 'c2'],
    opposing_countries: [],
    abstaining_countries: [],
    unresolved_issues: ['Liability'],
    failure_reason: null,
  },
  events_count: 18,
  decisions_count: 15,
  error: null,
};

const mockNoCoordResult: ModeComparisonResult = {
  mode: 'no_coordination',
  mode_name: 'No Coordination (Unilateral)',
  simulation_id: 'sim_test_nocoord',
  status: 'COMPLETED',
  final_tick: 31,
  overall_score: 34.0,
  score_grade: 'F',
  performance_headline: 'Unilateral fragmentation led to prolonged crisis exposure.',
  is_winner: false,
  metric_breakdown: [
    {
      metric_id: 'risk_reduction',
      name: 'Risk Reduction',
      raw_value: 28.0,
      unit: '%',
      normalized_score: 28.0,
      weight: 0.25,
      weighted_score: 7.0,
      display_value: '↓28.0%',
      interpretation: 'Low risk mitigation',
    },
    {
      metric_id: 'response_time',
      name: 'Response Time',
      raw_value: 31,
      unit: 'm',
      normalized_score: 40.0,
      weight: 0.25,
      weighted_score: 10.0,
      display_value: '31m',
      interpretation: 'Slow unilateral action',
    },
    {
      metric_id: 'coordination',
      name: 'Coordination',
      raw_value: 0.0,
      unit: 'ratio',
      normalized_score: 0.0,
      weight: 0.25,
      weighted_score: 0.0,
      display_value: '0.00 (0/15)',
      interpretation: 'Zero multilateral coordination',
    },
    {
      metric_id: 'unresolved_issues',
      name: 'Unresolved Issues',
      raw_value: 5,
      unit: 'count',
      normalized_score: 0.0,
      weight: 0.25,
      weighted_score: 0.0,
      display_value: '5',
      interpretation: 'High deadlock count',
    },
  ],
  metrics: {
    risk_initial: 100,
    risk_final: 72.0,
    risk_reduction_pct: 28.0,
    response_time_minutes: 31,
    coordination_ratio: 0.0,
    countries_coordinating: 0,
    countries_total: 15,
    unresolved_issues: ['Issue 1', 'Issue 2', 'Issue 3', 'Issue 4', 'Issue 5'],
    unresolved_issues_count: 5,
    negotiation_rounds: 0,
    agreement_reached: false,
    simulation_mode: 'no_coordination',
  },
  events_count: 8,
  decisions_count: 5,
  error: null,
};

const mockDeltas: ComparisonDelta[] = [
  {
    baseline_mode: 'no_coordination',
    compared_mode: 'coordinated',
    overall_score_delta: 52.5,
    risk_reduction_delta_pct: 48.5,
    response_time_delta_min: -17,
    coordination_ratio_delta: 0.87,
    unresolved_issues_delta: -4,
    final_tick_delta: -17,
  },
];

describe('ModeComparisonCard', () => {
  it('renders mode title, overall score, grade, and winner badge', () => {
    render(
      <MemoryRouter>
        <ModeComparisonCard
          mode="coordinated"
          result={mockCoordinatedResult}
          isWinner={true}
        />
      </MemoryRouter>
    );

    expect(screen.getByText('Full Coordinated Governance')).toBeInTheDocument();
    expect(screen.getByText('86.5')).toBeInTheDocument();
    expect(screen.getByText('A')).toBeInTheDocument();
    expect(screen.getByTestId('winner-badge')).toHaveTextContent('WINNER');
  });

  it('renders exact 4 Phase 7 metrics with correct display values', () => {
    render(
      <MemoryRouter>
        <ModeComparisonCard
          mode="coordinated"
          result={mockCoordinatedResult}
          isWinner={true}
        />
      </MemoryRouter>
    );

    expect(screen.getByText('1. Risk Reduction')).toBeInTheDocument();
    expect(screen.getByText('↓76.5%')).toBeInTheDocument();

    expect(screen.getByText('2. Response Time')).toBeInTheDocument();
    expect(screen.getByText('14m')).toBeInTheDocument();

    expect(screen.getByText('3. Coordination')).toBeInTheDocument();
    expect(screen.getByText('0.87 (13/15)')).toBeInTheDocument();

    expect(screen.getByText('4. Unresolved Issues')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument();
  });

  it('renders tie badge when isTie is true', () => {
    render(
      <MemoryRouter>
        <ModeComparisonCard
          mode="partial"
          result={mockCoordinatedResult}
          isWinner={false}
          isTie={true}
        />
      </MemoryRouter>
    );

    expect(screen.getByTestId('tie-badge')).toHaveTextContent('TIE');
  });

  it('renders simulation detail deep link with correct simulationId', () => {
    render(
      <MemoryRouter>
        <ModeComparisonCard
          mode="coordinated"
          result={mockCoordinatedResult}
          isWinner={true}
        />
      </MemoryRouter>
    );

    const link = screen.getByRole('link', { name: /Inspect Simulation History/i });
    expect(link).toHaveAttribute('href', '/simulation/sim_test_coord');
  });
});

describe('MetricsComparisonBar', () => {
  it('renders comparison bars for all 3 modes', () => {
    render(
      <MetricsComparisonBar
        results={{
          coordinated: mockCoordinatedResult,
          no_coordination: mockNoCoordResult,
        }}
      />
    );

    expect(screen.getByText('Direct Metric Comparison')).toBeInTheDocument();
    expect(screen.getByText('Metric 1: Crisis Risk Reduction')).toBeInTheDocument();
    expect(screen.getByText('Metric 2: Response Timeliness & Speed')).toBeInTheDocument();
    expect(screen.getByText('Metric 3: Coordination & Consensus Ratio')).toBeInTheDocument();
    expect(screen.getByText('Metric 4: Unresolved Deadlock Mitigation')).toBeInTheDocument();
  });
});

describe('DeltasTable', () => {
  it('renders quantitative variances against baseline correctly', () => {
    render(<DeltasTable deltas={mockDeltas} />);

    expect(screen.getByText('Comparative Variance Analysis')).toBeInTheDocument();
    expect(screen.getByText('+52.5 pts')).toBeInTheDocument();
    expect(screen.getByText('+48.5%')).toBeInTheDocument();
    expect(screen.getByText('-17m')).toBeInTheDocument();
  });
});
