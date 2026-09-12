import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppShell } from '../components/layout/AppShell';
import { DashboardPage } from '../pages/Dashboard/DashboardPage';
import { SimulationPage } from '../pages/Simulation/SimulationPage';
import { ComparisonPage } from '../pages/Comparison/ComparisonPage';
import { NotFoundPage } from '../pages/NotFound/NotFoundPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'simulation/:simulationId',
        element: <SimulationPage />,
      },
      {
        path: 'simulation',
        element: <Navigate to="/" replace />,
      },
      {
        path: 'comparisons',
        element: <ComparisonPage />,
      },
      {
        path: 'comparisons/:comparisonId',
        element: <ComparisonPage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
]);
