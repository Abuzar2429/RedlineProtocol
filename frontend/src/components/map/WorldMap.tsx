import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { useSimulationStore } from '../../stores/simulationStore';
import { useUIStore } from '../../stores/uiStore';
import {
  COUNTRY_GEO_REGISTRY,
  getCountryStatusPresentation,
} from '../../utils/geoCoordinates';
import { MapLegend } from './MapLegend';
import { CountryDetailPanel } from './CountryDetailPanel';
import type { CountryData } from '../../types';

interface WorldMapProps {
  countryProfiles?: Record<string, CountryData>;
}

export const WorldMap: React.FC<WorldMapProps> = ({ countryProfiles = {} }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<Map<string, L.Marker>>(new Map());

  const liveCountries = useSimulationStore((s) => s.countries);
  const selectedCountryId = useUIStore((s) => s.selectedCountryId);
  const setSelectedCountryId = useUIStore((s) => s.setSelectedCountryId);

  // Initialize Leaflet Map once
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    try {
      const map = L.map(mapContainerRef.current, {
        center: [25, 10],
        zoom: 2,
        minZoom: 1.5,
        maxZoom: 7,
        zoomControl: true,
        attributionControl: false,
      });

      // CartoDB Dark Matter tile layer for command center aesthetic
      L.tileLayer(
        'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
        {
          subdomains: 'abcd',
          maxZoom: 19,
        }
      ).addTo(map);

      // Deselect country when clicking on empty map canvas
      map.on('click', () => {
        setSelectedCountryId(null);
      });

      mapInstanceRef.current = map;
    } catch (err) {
      console.warn('Leaflet map initialization notice:', err);
    }

    const markers = markersRef.current;
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        markers.clear();
      }
    };
  }, [setSelectedCountryId]);

  // Synchronize Country Markers with Live Simulation State
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    Object.entries(COUNTRY_GEO_REGISTRY).forEach(([countryId, geo]) => {
      const liveState = liveCountries[countryId];
      const statusPres = getCountryStatusPresentation(liveState?.status);
      const isSelected = selectedCountryId === countryId;

      // Custom command center HTML marker
      const customHtml = `
        <div class="relative flex items-center justify-center cursor-pointer group" style="transform: translate(-50%, -50%);">
          <!-- Outer Pulsing Radar Ring -->
          <div class="absolute w-10 h-10 rounded-full ${statusPres.pingClass} opacity-25 animate-ping"></div>
          
          <!-- Middle Halo / Selection Ring -->
          <div class="absolute w-8 h-8 rounded-full border ${
            isSelected ? 'border-cyan-400 bg-cyan-950/60 ring-2 ring-cyan-400/80 scale-125' : `${statusPres.borderClass} ${statusPres.bgClass}`
          } transition-transform duration-300"></div>

          <!-- Center Marker Pin -->
          <div class="relative z-10 w-6 h-6 rounded-full flex items-center justify-center text-xs shadow-lg border border-slate-700 bg-slate-950">
            <span class="text-xs select-none">${geo.flag}</span>
          </div>

          <!-- Bottom Label Tag -->
          <div class="absolute -bottom-5 px-1.5 py-0.5 rounded bg-slate-950/90 border border-slate-800 text-[9px] font-mono whitespace-nowrap text-slate-300 pointer-events-none shadow">
            ${geo.name.split(' ').pop()}
          </div>
        </div>
      `;

      const icon = L.divIcon({
        className: 'custom-country-marker',
        html: customHtml,
        iconSize: [24, 24],
        iconAnchor: [12, 12],
      });

      let marker = markersRef.current.get(countryId);
      if (!marker) {
        marker = L.marker([geo.lat, geo.lng], { icon }).addTo(map);

        marker.on('click', (e) => {
          L.DomEvent.stopPropagation(e);
          setSelectedCountryId(countryId);
        });

        // Hover tooltip
        marker.bindTooltip(
          `<strong>${geo.name}</strong><br/><span style="color:${statusPres.color}">${statusPres.label}</span>`,
          { direction: 'top', offset: [0, -12], className: 'map-tooltip' }
        );

        markersRef.current.set(countryId, marker);
      } else {
        // Update marker icon and tooltip dynamically without re-creating marker
        marker.setIcon(icon);
        marker.setTooltipContent(
          `<strong>${geo.name}</strong><br/><span style="color:${statusPres.color}">${statusPres.label}</span>`
        );
      }
    });
  }, [liveCountries, selectedCountryId, setSelectedCountryId]);

  return (
    <div
      role="region"
      aria-label="Interactive Global Crisis Map"
      className="relative w-full h-[460px] lg:h-[540px] rounded-xl overflow-hidden border border-slate-800 bg-slate-950 shadow-inner flex flex-col"
    >
      {/* Map Header Status Bar */}
      <div className="absolute top-3 left-3 z-[1000] px-3 py-1.5 rounded-lg bg-slate-950/85 backdrop-blur-md border border-slate-800 text-xs font-mono flex items-center space-x-2 text-slate-300 pointer-events-none shadow">
        <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
        <span className="font-semibold text-slate-200">GLOBAL CRISIS THEATER</span>
        <span className="text-slate-600">|</span>
        <span className="text-[10px] text-slate-400">15 SOVEREIGN NATIONS</span>
      </div>

      {/* Leaflet Canvas Container */}
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Map Legend in Bottom Left */}
      <MapLegend />

      {/* Detail Slide-out when a Country is Selected */}
      <CountryDetailPanel countryProfiles={countryProfiles} />
    </div>
  );
};
