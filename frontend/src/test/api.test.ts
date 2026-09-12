import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ApiClient, ApiError } from '../services/api/client';

describe('ApiClient', () => {
  let client: ApiClient;
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    client = new ApiClient('http://test-api.local');
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('successfully fetches scenarios', async () => {
    const mockScenarios = [
      {
        id: 'scenario_01',
        title: 'Autonomous Weapons Escalation',
        description: 'Crisis description',
        severity: 8,
        affected_countries: ['US', 'CN'],
        initial_detection: 'US-CYBERCOM',
        information_delay: { US: 0, CN: 1 },
        available_actions: [],
      },
    ];

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockScenarios,
    } as unknown as Response);

    const result = await client.getScenarios();
    expect(result).toEqual(mockScenarios);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      'http://test-api.local/api/scenarios',
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('handles HTTP error responses with structured ApiError', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: async () => ({ detail: 'Simulation instance not found' }),
    } as unknown as Response);

    await expect(client.getSimulation('nonexistent-id')).rejects.toThrow(ApiError);

    try {
      await client.getSimulation('nonexistent-id');
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(404);
      expect(apiErr.detail).toBe('Simulation instance not found');
    }
  });

  it('handles network failure or abort', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch'));

    await expect(client.getHealth()).rejects.toThrow('Failed to fetch');
  });

  it('posts commands properly with correct headers and payload', async () => {
    const mockCreated = {
      simulation_id: 'sim_123',
      scenario_id: 'scenario_01',
      mode: 'autonomous' as const,
      status: 'initialized' as const,
      current_tick: 0,
      current_time: '2026-09-12T00:00:00Z',
      message: 'Created',
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 201,
      json: async () => mockCreated,
    } as unknown as Response);

    const result = await client.createSimulation({
      scenario_id: 'scenario_01',
      mode: 'autonomous',
    });

    expect(result).toEqual(mockCreated);
    expect(globalThis.fetch).toHaveBeenCalledWith(
      'http://test-api.local/api/simulations',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ scenario_id: 'scenario_01', mode: 'autonomous' }),
      })
    );
  });
});
