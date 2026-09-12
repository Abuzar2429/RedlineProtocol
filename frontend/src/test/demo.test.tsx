import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ExecutionModeBadge } from '../components/replay/ExecutionModeBadge';
import { ReplayControls } from '../components/replay/ReplayControls';
import { useDemoStore } from '../stores/demoStore';
import type { ReplaySession } from '../types/demo';

const mockReplay: ReplaySession = {
  replay_id: 'rep_test_001',
  source_type: 'comparison',
  source_id: 'comp_test_001',
  scenario_id: 'scenario_01',
  scenario_title: 'Cross-Border AI Infra Failure',
  seed: 42,
  execution_mode: 'REPLAY',
  created_at: '2026-09-12T18:00:00Z',
  total_ticks: 10,
  total_events: 4,
  metadata: {},
  events: [
    {
      sequence_number: 1,
      tick: 0,
      timestamp: '2026-09-12T18:00:01Z',
      event_type: 'SCENARIO_TRIGGERED',
      source: 'SIMULATION',
      description: 'Initial incident',
      affected_countries: ['US', 'CN'],
      payload: { desc: 'Initial incident' },
      mode: 'uncoordinated',
    },
    {
      sequence_number: 2,
      tick: 3,
      timestamp: '2026-09-12T18:00:02Z',
      event_type: 'PROPOSAL_SUBMITTED',
      source: 'AGENT',
      description: 'Subgroup proposal',
      affected_countries: ['US'],
      payload: { desc: 'Subgroup proposal' },
      mode: 'fragmented',
    },
    {
      sequence_number: 3,
      tick: 7,
      timestamp: '2026-09-12T18:00:03Z',
      event_type: 'VOTE_TALLIED',
      source: 'VOTING_ENGINE',
      description: 'Consensus reached',
      affected_countries: ['US', 'CN', 'EU'],
      payload: { passed: true },
      mode: 'coordinated',
    },
    {
      sequence_number: 4,
      tick: 10,
      timestamp: '2026-09-12T18:00:04Z',
      event_type: 'SIMULATION_COMPLETED',
      source: 'SIMULATION',
      description: 'Crisis contained',
      affected_countries: [],
      payload: { winner: 'coordinated' },
      mode: 'coordinated',
    },
  ],
};

describe('Phase 14 — ExecutionModeBadge', () => {
  it('renders DEMO mode with seed', () => {
    render(<ExecutionModeBadge mode="DEMO" seed={42} />);
    const badge = screen.getByTestId('execution-mode-badge');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('DEMO MODE');
    expect(badge).toHaveTextContent('Seed: 42');
  });

  it('renders LIVE mode indicator', () => {
    render(<ExecutionModeBadge mode="LIVE" />);
    const badge = screen.getByTestId('execution-mode-badge');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('LIVE MODE');
  });

  it('renders REPLAY mode indicator', () => {
    render(<ExecutionModeBadge mode="REPLAY" />);
    const badge = screen.getByTestId('execution-mode-badge');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('REPLAY MODE');
    expect(badge).toHaveTextContent('Authoritative Playback');
  });
});

describe('Phase 14 — ReplayControls', () => {
  beforeEach(() => {
    useDemoStore.setState({
      activeReplay: mockReplay,
      replayTick: 3,
      isPlayingReplay: false,
      playbackSpeed: 1,
      visibleReplayEvents: mockReplay.events.filter((e) => e.tick <= 3),
    });
  });

  it('renders timeline scrubber and current tick info', () => {
    render(<ReplayControls />);
    expect(screen.getByTestId('replay-controls')).toBeInTheDocument();
    expect(screen.getByText('scenario_01')).toBeInTheDocument();
    expect(screen.getByText('T+03')).toBeInTheDocument();
  });

  it('toggles playback when Play button is clicked', () => {
    render(<ReplayControls />);
    const playBtn = screen.getByTestId('replay-play-btn');
    expect(playBtn).toBeInTheDocument();
    fireEvent.click(playBtn);
    expect(useDemoStore.getState().isPlayingReplay).toBe(true);
  });

  it('cycles playback speed on speed button click', () => {
    render(<ReplayControls />);
    const speedBtn = screen.getByTestId('replay-speed-btn');
    expect(speedBtn).toHaveTextContent('1x');
    fireEvent.click(speedBtn);
    expect(useDemoStore.getState().playbackSpeed).toBe(2);
  });

  it('steps forward and backward on tick controls', () => {
    render(<ReplayControls />);
    // Step forward
    const stepForwardBtn = screen.getByTitle('Step Forward 1 Tick');
    fireEvent.click(stepForwardBtn);
    expect(useDemoStore.getState().replayTick).toBe(4);

    // Step backward
    const stepBackBtn = screen.getByTitle('Step Back 1 Tick');
    fireEvent.click(stepBackBtn);
    expect(useDemoStore.getState().replayTick).toBe(3);
  });

  it('scrubs timeline when slider changes', () => {
    render(<ReplayControls />);
    const scrubber = screen.getByTestId('replay-scrubber');
    fireEvent.change(scrubber, { target: { value: '7' } });
    expect(useDemoStore.getState().replayTick).toBe(7);
  });
});

describe('Phase 14 — useDemoStore', () => {
  it('updates executionMode and demoSeed correctly', () => {
    useDemoStore.getState().setExecutionMode('DEMO');
    expect(useDemoStore.getState().executionMode).toBe('DEMO');

    useDemoStore.getState().setDemoSeed(999);
    expect(useDemoStore.getState().demoSeed).toBe(999);
  });

  it('resets replay to start upon resetReplay', () => {
    useDemoStore.setState({
      activeReplay: mockReplay,
      replayTick: 8,
      isPlayingReplay: true,
      playbackSpeed: 1,
      visibleReplayEvents: mockReplay.events,
    });

    useDemoStore.getState().resetReplay();
    expect(useDemoStore.getState().replayTick).toBe(0);
    expect(useDemoStore.getState().isPlayingReplay).toBe(false);
    expect(useDemoStore.getState().executionMode).toBe('LIVE');
  });
});
