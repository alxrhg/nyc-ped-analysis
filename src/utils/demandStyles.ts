/**
 * Styling utilities for pedestrian demand visualization
 */

import type {
  DemandCategory,
  DemandStyleMap,
  FocusArea,
  PedestrianDemandProperties,
} from '../types/pedestrianDemand';

/**
 * Color and weight mapping for demand categories
 * Colors follow a diverging red scale for intuitive interpretation
 */
export const DEMAND_STYLES: DemandStyleMap = {
  'Very High': {
    color: '#b2182b', // Dark red
    weight: 4,
    opacity: 0.9,
    label: 'Very High',
  },
  'High': {
    color: '#ef8a62', // Orange-red
    weight: 3,
    opacity: 0.9,
    label: 'High',
  },
  'Medium': {
    color: '#fddbc7', // Light peach
    weight: 2,
    opacity: 0.85,
    label: 'Medium',
  },
  'Low': {
    color: '#d9d9d9', // Light grey
    weight: 1,
    opacity: 0.7,
    label: 'Low',
  },
};

/**
 * Default style for segments with unknown/missing category
 */
export const DEFAULT_STYLE = {
  color: '#999999',
  weight: 1,
  opacity: 0.5,
};

/**
 * Predefined focus areas for map navigation
 */
export const FOCUS_AREAS: FocusArea[] = [
  {
    name: 'Below 56th St',
    bounds: [[40.700, -74.02], [40.765, -73.97]],
    zoom: 12,
    description: 'Manhattan below 56th Street - full data extent',
  },
  {
    name: 'Lower Manhattan',
    bounds: [[40.700, -74.02], [40.74, -73.97]],
    zoom: 13,
    description: 'Below 14th Street - FiDi, Tribeca, Chinatown, LES',
  },
  {
    name: 'Chinatown / SoHo',
    bounds: [[40.715, -74.005], [40.728, -73.99]],
    zoom: 15,
    description: 'Houston St to Canal St - primary thesis study area',
  },
];

/**
 * Study area overlay definitions
 */
export const STUDY_AREAS = {
  chinatownSoho: {
    bounds: [[40.716, -74.003], [40.727, -73.992]] as [[number, number], [number, number]],
    name: 'Chinatown / SoHo Study Area',
    description: 'Houston St to Canal St - Primary LTN candidate zone',
    style: {
      color: '#e41a1c',
      weight: 2,
      fillOpacity: 0.05,
      dashArray: '5, 5',
    },
  },
  lowerManhattan: {
    bounds: [[40.700, -74.02], [40.74, -73.97]] as [[number, number], [number, number]],
    name: 'Lower Manhattan Context',
    description: 'Broader context area - FiDi to 14th Street',
    style: {
      color: '#377eb8',
      weight: 1.5,
      fillOpacity: 0.02,
      dashArray: '10, 5',
    },
  },
};

/**
 * Extract the demand category from feature properties
 * Handles multiple possible field names in the dataset
 */
export function getDemandCategory(
  properties: PedestrianDemandProperties
): DemandCategory | null {
  // Check various possible field names for the demand category
  const category =
    properties.corridor_category ||
    properties.pedestrian_demand ||
    properties.ped_demand ||
    properties.demand_category;

  if (!category) return null;

  // Normalize the category string
  const normalized = category.toString().trim();

  // Map to standard categories
  if (normalized.toLowerCase().includes('very high')) return 'Very High';
  if (normalized.toLowerCase().includes('high')) return 'High';
  if (normalized.toLowerCase().includes('medium')) return 'Medium';
  if (normalized.toLowerCase().includes('low')) return 'Low';

  return null;
}

/**
 * Get the style for a demand category
 */
export function getStyleForCategory(category: DemandCategory | null) {
  if (!category) return DEFAULT_STYLE;
  return DEMAND_STYLES[category] || DEFAULT_STYLE;
}

/**
 * Extract street name from feature properties
 * Handles multiple possible field names
 */
export function getStreetName(properties: PedestrianDemandProperties): string {
  return (
    properties.street ||
    properties.streetname ||
    properties.on_st ||
    properties.st_name ||
    properties.name ||
    'Unknown Street'
  );
}

/**
 * Extract from/to street information
 */
export function getFromToStreets(properties: PedestrianDemandProperties): {
  from: string;
  to: string;
} {
  return {
    from: properties.fromst || properties.from_st || '',
    to: properties.tost || properties.to_st || '',
  };
}

/**
 * Extract borough name from feature properties
 */
export function getBorough(properties: PedestrianDemandProperties): string {
  return properties.borough || properties.boro || 'Unknown Borough';
}

/**
 * Format tooltip content for a street segment
 */
export function formatTooltipContent(properties: PedestrianDemandProperties): string {
  const streetName = getStreetName(properties);
  const category = getDemandCategory(properties);
  const borough = getBorough(properties);
  const { from, to } = getFromToStreets(properties);

  let content = `<strong>${streetName}</strong>`;

  if (from && to) {
    content += `<br><span class="text-gray-500 text-sm">${from} to ${to}</span>`;
  }

  if (category) {
    const style = DEMAND_STYLES[category];
    content += `<br><span style="color: ${style.color}; font-weight: 600;">Demand: ${category}</span>`;
  }

  content += `<br><span class="text-gray-400 text-xs">${borough}</span>`;
  content += `<br><span class="text-gray-400 text-xs italic">Source: NYC DOT Pedestrian Mobility Plan</span>`;

  return content;
}

/**
 * Initial category visibility state (all visible)
 */
export const INITIAL_CATEGORY_VISIBILITY = {
  'Very High': true,
  'High': true,
  'Medium': true,
  'Low': true,
};
