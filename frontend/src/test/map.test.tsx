import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MapLegend } from '../components/map/MapLegend';
import { CountryDetailPanel } from '../components/map/CountryDetailPanel';
import { WorldMap } from '../components/map/WorldMap';
import { getCountryStatusPresentation } from '../utils/geoCoordinates';
import { useUIStore } from '../stores/uiStore';
import { useSimulationStore } from '../stores/simulationStore';
import type { CountryData } from '../types';

describe('World Map & Country Visualizations', () => {
  beforeEach(() => {
    useUIStore.getState().setSelectedCountryId(null);
    useSimulationStore.getState().reset();
  });

  describe('getCountryStatusPresentation', () => {
    it('maps standard backend country statuses correctly', () => {
      expect(getCountryStatusPresentation('Unaware').label).toBe('Unaware');
      expect(getCountryStatusPresentation('Investigating').label).toBe('Investigating');
      expect(getCountryStatusPresentation('Notified').label).toBe('Notified');
      expect(getCountryStatusPresentation('Coordinating').label).toBe('Coordinating');
    });

    it('handles case-insensitive and alternative terminology safely', () => {
      expect(getCountryStatusPresentation('aligned').label).toBe('Coordinating');
      expect(getCountryStatusPresentation('monitoring').label).toBe('Investigating');
      expect(getCountryStatusPresentation('UNKNOWN_STATUS').label).toBe('Unaware');
    });
  });

  describe('MapLegend', () => {
    it('renders all four country posture legend items', () => {
      render(<MapLegend />);

      expect(screen.getByText(/Country Posture/i)).toBeInTheDocument();
      expect(screen.getByText('Unaware')).toBeInTheDocument();
      expect(screen.getByText('Investigating')).toBeInTheDocument();
      expect(screen.getByText('Notified')).toBeInTheDocument();
      expect(screen.getByText('Coordinating')).toBeInTheDocument();
    });
  });

  describe('CountryDetailPanel', () => {
    const mockProfiles: Record<string, CountryData> = {
      country_01: {
        id: 'country_01',
        name: 'Federal Republic of Alerion',
        code: 'ALR',
        region: 'Boreal Alliance / Northern Continent',
        strategic_priorities: ['security', 'leadership'],
        risk_tolerance: 'medium',
        coordination_willingness: 0.85,
        ai_capability_level: 'high',
        ai_policy_position: 'Advocates for self-regulatory safety baselines and international transparency.',
        allies: ['country_04'],
        rivals: ['country_03'],
      },
    };

    it('does not render when no country is selected in UI store', () => {
      const { container } = render(<CountryDetailPanel countryProfiles={mockProfiles} />);
      expect(container).toBeEmptyDOMElement();
    });

    it('renders full intelligence panel when a country is selected', () => {
      useUIStore.getState().setSelectedCountryId('country_01');

      // Set live simulation state in store
      useSimulationStore.getState().applyEvent({
        event_id: 'evt_c1',
        event_type: 'country_status_changed',
        simulation_id: 'sim_test',
        tick: 2,
        timestamp: 'T+02',
        payload: {
          country_id: 'country_01',
          status: 'Investigating',
          tension_level: 45,
          information_completeness: 0.8,
          current_action: 'Transmit Radar Telemetry',
        },
      });

      render(<CountryDetailPanel countryProfiles={mockProfiles} />);

      expect(screen.getByText('Federal Republic of Alerion')).toBeInTheDocument();
      expect(screen.getByText('Investigating')).toBeInTheDocument();
      expect(screen.getByText('45%')).toBeInTheDocument(); // Tension index
      expect(screen.getByText('80%')).toBeInTheDocument(); // Intel completeness
      expect(screen.getByText('Transmit Radar Telemetry')).toBeInTheDocument();
      expect(screen.getByText(/Advocates for self-regulatory safety baselines/i)).toBeInTheDocument();
    });

    it('closes panel when close button is clicked', () => {
      useUIStore.getState().setSelectedCountryId('country_01');

      render(<CountryDetailPanel countryProfiles={mockProfiles} />);
      expect(screen.getByText('Federal Republic of Alerion')).toBeInTheDocument();

      const closeButton = screen.getByRole('button', { name: /close country panel/i });
      fireEvent.click(closeButton);

      expect(useUIStore.getState().selectedCountryId).toBeNull();
    });
  });

  describe('WorldMap', () => {
    it('renders map container and status banner without crashing', () => {
      render(<WorldMap />);

      expect(screen.getByText(/GLOBAL CRISIS THEATER/i)).toBeInTheDocument();
      expect(screen.getByText(/15 SOVEREIGN NATIONS/i)).toBeInTheDocument();
    });
  });
});
