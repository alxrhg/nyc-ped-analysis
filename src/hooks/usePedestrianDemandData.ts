/**
 * Custom hook for fetching pedestrian demand data from NYC Open Data
 */

import { useState, useEffect, useCallback } from 'react';
import type {
  PedestrianDemandData,
  LoadingState,
  FetchError,
} from '../types/pedestrianDemand';

/**
 * NYC Open Data SODA 2 API endpoint for Pedestrian Demand dataset
 * Dataset ID: fwpa-qxaf
 * No API key required for public read access
 */
const API_BASE_URL = 'https://data.cityofnewyork.us/resource/fwpa-qxaf.geojson';

/**
 * Default query parameters
 * - $limit: Maximum number of features to fetch (API default is 1000)
 * - $where: Optional spatial filter using within_box
 */
interface QueryParams {
  limit?: number;
  boundingBox?: {
    north: number;
    south: number;
    east: number;
    west: number;
  };
}

/**
 * Build the API URL with query parameters
 */
function buildApiUrl(params: QueryParams = {}): string {
  const { limit = 50000, boundingBox } = params;

  const queryParts: string[] = [`$limit=${limit}`];

  // Add bounding box filter if specified
  if (boundingBox) {
    const { north, south, east, west } = boundingBox;
    const withinBox = `within_box(the_geom, ${north}, ${west}, ${south}, ${east})`;
    queryParts.push(`$where=${encodeURIComponent(withinBox)}`);
  }

  return `${API_BASE_URL}?${queryParts.join('&')}`;
}

/**
 * Hook return type
 */
interface UsePedestrianDemandDataResult {
  data: PedestrianDemandData | null;
  loadingState: LoadingState;
  error: FetchError | null;
  featureCount: number;
  refetch: () => void;
}

/**
 * Custom hook to fetch and manage pedestrian demand GeoJSON data
 *
 * @param options - Query options for filtering data
 * @returns Object with data, loading state, error, and refetch function
 *
 * @example
 * ```tsx
 * const { data, loadingState, error } = usePedestrianDemandData({
 *   limit: 10000,
 *   boundingBox: { north: 40.74, south: 40.70, east: -73.97, west: -74.02 }
 * });
 * ```
 */
export function usePedestrianDemandData(
  options: QueryParams = {}
): UsePedestrianDemandDataResult {
  const [data, setData] = useState<PedestrianDemandData | null>(null);
  const [loadingState, setLoadingState] = useState<LoadingState>('idle');
  const [error, setError] = useState<FetchError | null>(null);

  const fetchData = useCallback(async () => {
    setLoadingState('loading');
    setError(null);

    const url = buildApiUrl(options);
    console.log('[PedestrianDemandData] Fetching from:', url);

    try {
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const geojson: PedestrianDemandData = await response.json();

      // Validate the response structure
      if (!geojson.features || !Array.isArray(geojson.features)) {
        throw new Error('Invalid GeoJSON response: missing features array');
      }

      console.log(
        `[PedestrianDemandData] Loaded ${geojson.features.length} features`
      );

      // Log sample properties for debugging field names
      if (geojson.features.length > 0) {
        console.log(
          '[PedestrianDemandData] Sample properties:',
          geojson.features[0].properties
        );
      }

      setData(geojson);
      setLoadingState('success');
    } catch (err) {
      console.error('[PedestrianDemandData] Fetch error:', err);

      const fetchError: FetchError = {
        message: err instanceof Error ? err.message : 'Unknown error occurred',
      };

      setError(fetchError);
      setLoadingState('error');
    }
  }, [options.limit, options.boundingBox?.north, options.boundingBox?.south, options.boundingBox?.east, options.boundingBox?.west]);

  // Fetch on mount and when options change
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loadingState,
    error,
    featureCount: data?.features?.length ?? 0,
    refetch: fetchData,
  };
}

/**
 * Default export for convenience
 */
export default usePedestrianDemandData;
