import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { MetricsBar } from '../components/metrics/MetricsBar';
import { MetricCard } from '../components/metrics/MetricCard';
import { useSimulationStore } from '../stores/simulationStore';
import type { MetricResult, ScoringResult } from '../types';

const mockMetricBreakdown: MetricResult[] = [
  {
    metric_id: 'risk_reduction',
    name: 'Risk Reduction',
    raw_value: 63.5,
    unit: '%',
    display_value: '↓63.5%',
    normalized_score: 63.5,
    weight: 0.35,
    weighted_score: 22.2,
    interpretation: 'Moderate risk elimination achieved via multilateral containment.',
    evidence: { baseline: 100, final: 36.5 },
  },
  {
    metric_id: 'response_time',
    name: 'Response Time',
    raw_value: 14,
    unit: 'minutes',
    display_value: '14 min',
    normalized_score: 86.0,
    weight: 0.25,
    weighted_score: 21.5,
    interpretation: 'Rapid multilateral notification and consensus within 15 minutes.',
    evidence: { detection_tick: 2, action_tick: 4 },
  },
  {
    metric_id: 'coordination',
    name: 'International Coordination',
    raw_value: 0.73,
    unit: 'ratio',
    display_value: '11/15',
    normalized_score: 73.3,
    weight: 0.25,
    weighted_score: 18.3,
    interpretation: 'Substantial coalition achieved supermajority consensus.',
    evidence: { approving: 11, total: 15 },
  },
  {
    metric_id: 'unresolved_issues',
    name: 'Unresolved Issues',
    raw_value: 1,
    unit: 'count',
    display_value: '1 issue',
    normalized_score: 66.7,
    weight: 0.15,
    weighted_score: 10.0,
    interpretation: 'Minor sovereignty stipulations remain unresolved.',
    evidence: { count: 1 },
  },
];

const mockScoringResult: ScoringResult = {
  scoring_id: 'score_test_001',
  simulation_id: 'sim_test_001',
  overall_score: 72.0,
  score_grade: 'B',
  performance_headline: 'Effective coordinated containment with minor regulatory friction.',
  formula_version: '1.0',
  calculated_at_tick: 20,
  is_authoritative: true,
  metric_breakdown: mockMetricBreakdown,
};

describe('Phase 12 — Metrics Bar & MetricCard', () => {
  beforeEach(() => {
    useSimulationStore.getState().reset();
  });

  it('renders pending state when scoring is not yet available', () => {
    render(<MetricsBar />);

    expect(screen.getByTestId('metrics-bar-pending')).toBeInTheDocument();
    expect(screen.getByText(/Awaiting scoring evaluation/i)).toBeInTheDocument();
    expect(screen.getByText('Risk Reduction')).toBeInTheDocument();
    expect(screen.getByText('Response Time')).toBeInTheDocument();
    expect(screen.getByText('International Coordination')).toBeInTheDocument();
    expect(screen.getByText('Unresolved Issues')).toBeInTheDocument();
  });

  it('renders authoritative ScoringResult with exact 4 metrics and overall score', () => {
    useSimulationStore.getState().setScoring(mockScoringResult);
    render(<MetricsBar />);

    // Top banner
    expect(screen.getByTestId('metrics-bar')).toBeInTheDocument();
    expect(screen.getByText('72')).toBeInTheDocument();
    expect(screen.getByTestId('metrics-grade-badge')).toHaveTextContent('B');
    expect(screen.getByText(/Effective coordinated containment/i)).toBeInTheDocument();
    expect(screen.getByText(/Deterministic Engine v1.0/i)).toBeInTheDocument();

    // 4 exact metrics
    expect(screen.getByTestId('metric-card-risk_reduction')).toBeInTheDocument();
    expect(screen.getByTestId('metric-card-response_time')).toBeInTheDocument();
    expect(screen.getByTestId('metric-card-coordination')).toBeInTheDocument();
    expect(screen.getByTestId('metric-card-unresolved_issues')).toBeInTheDocument();

    // Values displayed unchanged from backend
    expect(screen.getByText('↓63.5%')).toBeInTheDocument();
    expect(screen.getByText('14 min')).toBeInTheDocument();
    expect(screen.getByText('11/15')).toBeInTheDocument();
    expect(screen.getByText('1 issue')).toBeInTheDocument();
  });

  it('renders single MetricCard with normalized progress and weight', () => {
    render(<MetricCard metric={mockMetricBreakdown[0]} />);

    expect(screen.getByText('Risk Reduction')).toBeInTheDocument();
    expect(screen.getByText('Weight: 35%')).toBeInTheDocument();
    expect(screen.getByText('64/100')).toBeInTheDocument();
    expect(screen.getByText('+22.2 pts')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '64');
  });

  it('updates reactively when scoring arrives via WebSocket event', async () => {
    // Set active simulation first
    useSimulationStore.getState().setActiveSimulationId('sim_test_001');

    render(<MetricsBar />);
    expect(screen.getByTestId('metrics-bar-pending')).toBeInTheDocument();

    // Dispatch WebSocket event inside act
    await React.act(async () => {
      useSimulationStore.getState().applyEvent({
        event_type: 'SCORING_COMPLETED',
        simulation_id: 'sim_test_001',
        tick: 20,
        timestamp: 'T+20',
        payload: mockScoringResult as unknown as Record<string, unknown>,
      });
    });

    // Verify UI updated reactively
    expect(screen.getByTestId('metrics-bar')).toBeInTheDocument();
    expect(screen.getByText('72')).toBeInTheDocument();
  });
});
