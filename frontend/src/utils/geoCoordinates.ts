/**
 * Geographic registry and visual presentation tokens for the 15 fictional simulator countries.
 * Coordinates are distributed across global operational sectors corresponding to fictional regions.
 */

export interface CountryGeoData {
  id: string;
  name: string;
  lat: number;
  lng: number;
  region: string;
  flag: string;
  geopoliticalBloc: string;
}

export const COUNTRY_GEO_REGISTRY: Record<string, CountryGeoData> = {
  country_01: {
    id: 'country_01',
    name: 'Federal Republic of Alerion',
    lat: 52.0,
    lng: -95.0,
    region: 'Boreal Alliance / Northern Continent',
    flag: '🦅',
    geopoliticalBloc: 'bloc_a',
  },
  country_02: {
    id: 'country_02',
    name: 'Kingdom of Bavari',
    lat: 48.0,
    lng: 15.0,
    region: 'Central Continent / Continental Union',
    flag: '🦁',
    geopoliticalBloc: 'bloc_b',
  },
  country_03: {
    id: 'country_03',
    name: 'Republic of Coris',
    lat: 35.0,
    lng: 105.0,
    region: 'Eastern Continent / Orient Pact',
    flag: '🐉',
    geopoliticalBloc: 'bloc_c',
  },
  country_04: {
    id: 'country_04',
    name: 'Federation of Danuvia',
    lat: 62.0,
    lng: -20.0,
    region: 'Northern Archipelago / Boreal Alliance',
    flag: '⚓',
    geopoliticalBloc: 'bloc_a',
  },
  country_05: {
    id: 'country_05',
    name: 'Elysian Union',
    lat: 58.0,
    lng: 30.0,
    region: 'Northern Rim / Boreal League',
    flag: '🛡️',
    geopoliticalBloc: 'bloc_b',
  },
  country_06: {
    id: 'country_06',
    name: 'State of Fenwick',
    lat: 20.0,
    lng: -40.0,
    region: 'Maritime Strait / Central Island',
    flag: '🌊',
    geopoliticalBloc: 'bloc_a',
  },
  country_07: {
    id: 'country_07',
    name: 'Commonwealth of Gallia',
    lat: 42.0,
    lng: -5.0,
    region: 'Western Peninsula / Continental Union',
    flag: '⚔️',
    geopoliticalBloc: 'bloc_a',
  },
  country_08: {
    id: 'country_08',
    name: 'United Hesperia',
    lat: -15.0,
    lng: -55.0,
    region: 'Southern Hemisphere / Equatorial Basin',
    flag: '☀️',
    geopoliticalBloc: 'global_south_coalition',
  },
  country_09: {
    id: 'country_09',
    name: 'Illyrian Republic',
    lat: -10.0,
    lng: 150.0,
    region: 'Pelagic Ocean / Island Arc',
    flag: '🌴',
    geopoliticalBloc: 'maritime_neutral',
  },
  country_10: {
    id: 'country_10',
    name: 'Jovian Confederation',
    lat: 46.0,
    lng: 8.0,
    region: 'Alpine Central / Non-Aligned Zone',
    flag: '🏔️',
    geopoliticalBloc: 'neutral',
  },
  country_11: {
    id: 'country_11',
    name: 'Kalmar Republic',
    lat: 68.0,
    lng: 25.0,
    region: 'Polar Fjords / Arctic Shield',
    flag: '❄️',
    geopoliticalBloc: 'bloc_b',
  },
  country_12: {
    id: 'country_12',
    name: 'Maritime Union of Lucania',
    lat: 8.0,
    lng: -80.0,
    region: 'Pelagic Crossroad / Southern Isthmus',
    flag: '🚢',
    geopoliticalBloc: 'maritime_neutral',
  },
  country_13: {
    id: 'country_13',
    name: 'Novaria Sovereign State',
    lat: 5.0,
    lng: 25.0,
    region: 'Savanna Plains / Interior Basin',
    flag: '🌾',
    geopoliticalBloc: 'global_south_coalition',
  },
  country_14: {
    id: 'country_14',
    name: 'Republic of Oakhaven',
    lat: 50.0,
    lng: 75.0,
    region: 'Steppe Frontier / Inland Union',
    flag: '🌲',
    geopoliticalBloc: 'bloc_c',
  },
  country_15: {
    id: 'country_15',
    name: 'Principality of Pelagia',
    lat: -22.0,
    lng: 60.0,
    region: 'Pelagic Archipelago / Sovereign Atolls',
    flag: '🐚',
    geopoliticalBloc: 'maritime_neutral',
  },
};

export interface StatusPresentation {
  label: 'Unaware' | 'Investigating' | 'Notified' | 'Coordinating' | 'Unknown';
  color: string;
  bgClass: string;
  borderClass: string;
  textClass: string;
  pingClass: string;
  dotClass: string;
}

export function getCountryStatusPresentation(status?: string): StatusPresentation {
  const normalized = (status || '').toLowerCase();

  switch (normalized) {
    case 'coordinating':
    case 'coordinated':
    case 'aligned':
    case 'compliant':
      return {
        label: 'Coordinating',
        color: '#22c55e', // Emerald
        bgClass: 'bg-emerald-950/60',
        borderClass: 'border-emerald-500/50',
        textClass: 'text-emerald-400',
        pingClass: 'bg-emerald-400',
        dotClass: 'bg-emerald-500',
      };

    case 'notified':
    case 'aware':
      return {
        label: 'Notified',
        color: '#3b82f6', // Blue
        bgClass: 'bg-blue-950/60',
        borderClass: 'border-blue-500/50',
        textClass: 'text-blue-400',
        pingClass: 'bg-blue-400',
        dotClass: 'bg-blue-500',
      };

    case 'investigating':
    case 'responding':
    case 'monitoring':
      return {
        label: 'Investigating',
        color: '#f59e0b', // Amber
        bgClass: 'bg-amber-950/60',
        borderClass: 'border-amber-500/50',
        textClass: 'text-amber-400',
        pingClass: 'bg-amber-400',
        dotClass: 'bg-amber-500',
      };

    case 'unaware':
    default:
      return {
        label: normalized === 'unaware' ? 'Unaware' : 'Unaware',
        color: '#ef4444', // Red / Warning
        bgClass: 'bg-rose-950/60',
        borderClass: 'border-rose-500/50',
        textClass: 'text-rose-400',
        pingClass: 'bg-rose-400',
        dotClass: 'bg-rose-500',
      };
  }
}
