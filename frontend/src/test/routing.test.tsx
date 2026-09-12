import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { DashboardPage } from '../pages/Dashboard/DashboardPage';
import { SimulationPage } from '../pages/Simulation/SimulationPage';
import { NotFoundPage } from '../pages/NotFound/NotFoundPage';
import { apiClient } from '../services/api/client';

describe('Frontend Routing & AppShell', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(apiClient, 'getScenarios').mockResolvedValue([]);
    vi.spyOn(apiClient, 'listSimulations').mockResolvedValue([]);
    vi.spyOn(apiClient, 'getRAGHealth').mockResolvedValue({
      status: 'healthy',
      rag_enabled: true,
      collection_name: 'test',
      document_count: 5,
      chunk_count: 20,
      embedding_provider: 'mock',
      embedding_model: 'mock',
      embedding_dimension: 384,
      last_ingestion_time: null,
    });
  });

  it('renders AppShell and Dashboard on root path "/"', async () => {
    const routes = [
      {
        path: '/',
        element: <AppShell />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: 'simulation/:simulationId', element: <SimulationPage /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ];

    const router = createMemoryRouter(routes, { initialEntries: ['/'] });
    render(<RouterProvider router={router} />);

    // Header title check
    expect(screen.getByText(/AI CRISIS SIMULATOR/i)).toBeInTheDocument();

    // Sidebar navigation check
    expect(screen.getByText(/Control Dashboard/i)).toBeInTheDocument();

    // Dashboard heading check
    await waitFor(() => {
      expect(screen.getByText(/Crisis Simulator Control Center/i)).toBeInTheDocument();
    });
  });

  it('renders 404 NotFoundPage on unknown route', async () => {
    const routes = [
      {
        path: '/',
        element: <AppShell />,
        children: [
          { index: true, element: <DashboardPage /> },
          { path: 'simulation/:simulationId', element: <SimulationPage /> },
          { path: '*', element: <NotFoundPage /> },
        ],
      },
    ];

    const router = createMemoryRouter(routes, { initialEntries: ['/unrecognized-path-sector-99'] });
    render(<RouterProvider router={router} />);

    expect(screen.getByText(/404 — UNKNOWN SECTOR/i)).toBeInTheDocument();
    expect(screen.getByText(/Command Route Not Found/i)).toBeInTheDocument();
  });
});
