/**
 * Type definitions for NYC DOT Pedestrian Mobility Plan - Pedestrian Demand dataset
 * Dataset ID: fwpa-qxaf
 * Source: https://data.cityofnewyork.us/Transportation/Pedestrian-Mobility-Plan-Pedestrian-Demand/fwpa-qxaf
 */

import type { FeatureCollection, Feature, Geometry } from 'geojson';

/**
 * Demand category levels from the NYC DOT dataset
 * These represent relative pedestrian volume/demand on street segments
 */
export type DemandCategory = 'Very High' | 'High' | 'Medium' | 'Low';

/**
 * Properties of each street segment feature in the GeoJSON
 * Field names are based on the NYC Open Data schema - adjust as needed
 */
export interface PedestrianDemandProperties {
  // Primary demand classification field
  // Note: The actual field name may vary - check API response and adjust
  corridor_category?: DemandCategory;
  pedestrian_demand?: DemandCategory;
  ped_demand?: DemandCategory;
  demand_category?: DemandCategory;

  // Street identification fields
  street?: string;
  streetname?: string;
  on_st?: string;
  st_name?: string;
  name?: string;
  fromst?: string;
  from_st?: string;
  tost?: string;
  to_st?: string;

  // Location fields
  borough?: string;
  boro?: string;
  borocode?: string;

  // Numeric demand value (if available)
  ped_vol?: number;
  demand_index?: number;

  // Any additional fields from the dataset
  [key: string]: unknown;
}

/**
 * A single pedestrian demand feature (street segment)
 */
export type PedestrianDemandFeature = Feature<Geometry, PedestrianDemandProperties>;

/**
 * The full GeoJSON FeatureCollection from the API
 */
export type PedestrianDemandData = FeatureCollection<Geometry, PedestrianDemandProperties>;

/**
 * Style configuration for demand categories
 */
export interface DemandCategoryStyle {
  color: string;
  weight: number;
  opacity: number;
  label: string;
}

/**
 * Map of demand categories to their visual styles
 */
export type DemandStyleMap = Record<DemandCategory, DemandCategoryStyle>;

/**
 * Focus area presets for map navigation
 */
export interface FocusArea {
  name: string;
  bounds: [[number, number], [number, number]]; // [[south, west], [north, east]]
  zoom?: number;
  description?: string;
}

/**
 * State for category visibility toggles
 */
export type CategoryVisibility = Record<DemandCategory, boolean>;

/**
 * Loading states for data fetching
 */
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';

/**
 * Error information from API fetch
 */
export interface FetchError {
  message: string;
  status?: number;
}
