import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { NewspaperOutcomeSummary } from '../components/outcome/NewspaperOutcomeSummary';

describe('NewspaperOutcomeSummary', () => {
  const mockScoring = {
    overall_score: 84.2,
    score_grade: 'A',
    metric_breakdown: [
      { metric_id: 'risk_reduction', display_value: '↓78.5%' },
      { metric_id: 'response_time', display_value: '18m' },
      { metric_id: 'coordination', display_value: '13/15 Nations' },
      { metric_id: 'unresolved_issues', display_value: '1' },
    ],
  };

  it('renders masthead, headline, and lede for coordinated outcome', () => {
    render(
      <NewspaperOutcomeSummary
        simulation={{ scenario_id: 'scenario_01', current_tick: 40 }}
        scoring={mockScoring}
        mode="coordinated"
        scenarioTitle="Cross-Border AI Infra Failure"
        initiallyExpanded={true}
      />
    );

    expect(screen.getByTestId('newspaper-outcome-summary')).toBeInTheDocument();
    expect(screen.getByText('The Global Dispatch')).toBeInTheDocument();
    expect(screen.getByText(/GLOBAL ACCORD REACHED/i)).toBeInTheDocument();
    expect(screen.getByText(/GENEVA —/i)).toBeInTheDocument();
    expect(screen.getByText('↓78.5%')).toBeInTheDocument();
    expect(screen.getByText('18m')).toBeInTheDocument();
  });

  it('renders coalition headline when mode is partial', () => {
    render(
      <NewspaperOutcomeSummary
        scoring={{ overall_score: 62.0, score_grade: 'C' }}
        mode="partial"
        scenarioTitle="Border Drone Incursion"
        initiallyExpanded={true}
      />
    );

    expect(screen.getByText(/REGIONAL COALITION CURBS FALLOUT/i)).toBeInTheDocument();
    expect(screen.getByText(/BRUSSELS —/i)).toBeInTheDocument();
  });

  it('renders unilateral failure headline when mode is no_coordination', () => {
    render(
      <NewspaperOutcomeSummary
        scoring={{ overall_score: 35.0, score_grade: 'F' }}
        mode="no_coordination"
        scenarioTitle="Autonomous Trading Crash"
        initiallyExpanded={true}
      />
    );

    expect(screen.getByText(/UNILATERAL MEASURES FAIL/i)).toBeInTheDocument();
    expect(screen.getByText(/WASHINGTON \/ NEW YORK —/i)).toBeInTheDocument();
  });

  it('collapses and expands article when toggled', () => {
    render(
      <NewspaperOutcomeSummary
        scoring={mockScoring}
        mode="coordinated"
        scenarioTitle="Test Crisis"
        initiallyExpanded={true}
      />
    );

    const toggleBtn = screen.getByRole('button', { name: /collapse/i });
    fireEvent.click(toggleBtn);

    expect(screen.queryByText('The Global Dispatch')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /read article/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /read article/i }));
    expect(screen.getByText('The Global Dispatch')).toBeInTheDocument();
  });
});
