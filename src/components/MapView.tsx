/**
 * MapView component - Leaflet map with pedestrian demand visualization
 * Uses native Leaflet for better performance with large datasets
 */

import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Rectangle, Tooltip, useMap } from 'react-leaflet';
import L from 'leaflet';

import type {
  PedestrianDemandData,
  PedestrianDemandProperties,
  CategoryVisibility,
  FocusArea,
  DemandCategory,
} from '../types/pedestrianDemand';
import { STUDY_AREAS, DEMAND_STYLES } from '../utils/demandStyles';

import 'leaflet/dist/leaflet.css';

/**
 * Map controller for focus area navigation
 */
function MapController({ focusArea }: { focusArea: FocusArea | null }) {
  const map = useMap();

  useEffect(() => {
    if (focusArea) {
      map.fitBounds(focusArea.bounds, { padding: [20, 20], maxZoom: focusArea.zoom || 16 });
    }
  }, [focusArea, map]);

  return null;
}

/**
 * Common numeric field names that might contain demand values
 */
const NUMERIC_DEMAND_FIELDS = [
  'demand', 'score', 'index', 'ped_vol', 'volume', 'count',
  'demand_score', 'demand_index', 'ped_demand', 'pedestrian_demand',
  'total', 'value', 'rank', 'priority', 'weight'
];

/**
 * Extract numeric demand value from feature properties
 */
function getNumericDemand(props: PedestrianDemandProperties): number | null {
  if (!props) return null;

  // Try each known numeric field name
  for (const field of NUMERIC_DEMAND_FIELDS) {
    const val = props[field] ?? props[field.toUpperCase()] ?? props[field.charAt(0).toUpperCase() + field.slice(1)];
    if (val !== undefined && val !== null) {
      const num = typeof val === 'number' ? val : parseFloat(String(val));
      if (!isNaN(num)) return num;
    }
  }

  // Fallback: look for any numeric field
  for (const [key, val] of Object.entries(props)) {
    if (typeof val === 'number' && !key.toLowerCase().includes('id') && !key.toLowerCase().includes('code')) {
      return val;
    }
  }

  return null;
}

/**
 * Calculate quartile thresholds from an array of numbers
 */
function calculateQuartiles(values: number[]): { q25: number; q50: number; q75: number } {
  const sorted = [...values].sort((a, b) => a - b);
  const n = sorted.length;

  const q25 = sorted[Math.floor(n * 0.25)];
  const q50 = sorted[Math.floor(n * 0.50)];
  const q75 = sorted[Math.floor(n * 0.75)];

  return { q25, q50, q75 };
}

/**
 * Quantile thresholds for demand categorization
 */
interface QuantileThresholds {
  q25: number;
  q50: number;
  q75: number;
}

/**
 * Get demand category based on quantile thresholds
 */
function getCategoryFromQuantile(value: number, thresholds: QuantileThresholds): DemandCategory {
  if (value >= thresholds.q75) return 'Very High';
  if (value >= thresholds.q50) return 'High';
  if (value >= thresholds.q25) return 'Medium';
  return 'Low';
}

/**
 * Fallback: Get demand category from NYC DOT Category field
 */
function getCategoryFromField(props: PedestrianDemandProperties): DemandCategory | null {
  if (!props) return null;

  const category = (props.Category || props.category || '') as string;
  if (!category) return null;

  const str = category.toLowerCase().trim();
  if (str === 'regional') return 'Very High';
  if (str === 'community') return 'High';
  if (str === 'baseline') return 'Medium';
  return 'Low';
}

/**
 * Component that adds GeoJSON layer using native Leaflet
 * Uses quantile-based coloring for even distribution
 */
function DemandLayer({
  data,
  categoryVisibility
}: {
  data: PedestrianDemandData;
  categoryVisibility: CategoryVisibility;
}) {
  const map = useMap();
  const layerRef = useRef<L.GeoJSON | null>(null);

  useEffect(() => {
    if (!data?.features?.length) return;

    const sample = data.features[0].properties;
    console.log('[DemandLayer] Adding', data.features.length, 'features');
    console.log('[DemandLayer] Sample properties:', sample);

    // Extract all numeric demand values for quantile calculation
    const numericValues: number[] = [];
    let numericFieldUsed: string | null = null;

    for (const feature of data.features) {
      const props = feature.properties as PedestrianDemandProperties;
      if (!props) continue;

      const numVal = getNumericDemand(props);
      if (numVal !== null) {
        numericValues.push(numVal);
        // Track which field we're using
        if (!numericFieldUsed) {
          for (const [key, val] of Object.entries(props)) {
            if (typeof val === 'number' || (typeof val === 'string' && !isNaN(parseFloat(val)))) {
              const parsed = typeof val === 'number' ? val : parseFloat(val);
              if (parsed === numVal) {
                numericFieldUsed = key;
                break;
              }
            }
          }
        }
      }
    }

    // Calculate quantile thresholds if we have numeric data
    let thresholds: QuantileThresholds | null = null;
    const useQuantiles = numericValues.length > 10;

    if (useQuantiles) {
      thresholds = calculateQuartiles(numericValues);
      console.log('[DemandLayer] Using QUANTILE-based coloring');
      console.log(`[DemandLayer] Numeric field: "${numericFieldUsed}"`);
      console.log(`[DemandLayer] Values: ${numericValues.length} features with numeric data`);
      console.log(`[DemandLayer] Quartiles: Q25=${thresholds.q25.toFixed(2)}, Q50=${thresholds.q50.toFixed(2)}, Q75=${thresholds.q75.toFixed(2)}`);
      console.log(`[DemandLayer] Range: ${Math.min(...numericValues).toFixed(2)} - ${Math.max(...numericValues).toFixed(2)}`);
    } else {
      console.log('[DemandLayer] Using CATEGORY-based coloring (no numeric data found)');
    }

    // Remove existing layer
    if (layerRef.current) {
      map.removeLayer(layerRef.current);
    }

    // Helper to get category for a feature
    const getCategory = (props: PedestrianDemandProperties): DemandCategory | null => {
      if (thresholds) {
        const numVal = getNumericDemand(props);
        if (numVal !== null) {
          return getCategoryFromQuantile(numVal, thresholds);
        }
      }
      return getCategoryFromField(props);
    };

    // Create new GeoJSON layer with native Leaflet
    const layer = L.geoJSON(data as GeoJSON.GeoJsonObject, {
      style: (feature) => {
        if (!feature?.properties) {
          return { color: '#888', weight: 1, opacity: 0.5 };
        }

        const props = feature.properties as PedestrianDemandProperties;
        const category = getCategory(props);

        // Hide if toggled off
        if (category && !categoryVisibility[category]) {
          return { opacity: 0, weight: 0 };
        }

        if (!category) {
          return { color: '#888', weight: 1, opacity: 0.5 };
        }

        const style = DEMAND_STYLES[category];
        return {
          color: style.color,
          weight: style.weight,
          opacity: style.opacity,
        };
      },
      onEachFeature: (feature, featureLayer) => {
        const props = feature.properties as PedestrianDemandProperties;
        if (!props) return;

        const name = props.street || props.streetname || props.on_st || props.name || 'Street';
        const category = getCategory(props);
        const numVal = getNumericDemand(props);
        const color = category ? DEMAND_STYLES[category].color : '#888';

        const demandText = numVal !== null
          ? `${category} (${numVal.toFixed(1)})`
          : (category || 'N/A');

        featureLayer.bindTooltip(
          `<strong>${name}</strong><br/><span style="color:${color}">Demand: ${demandText}</span>`,
          { sticky: true }
        );
      },
    });

    layer.addTo(map);
    layerRef.current = layer;

    console.log('[DemandLayer] Layer added successfully');

    return () => {
      if (layerRef.current) {
        map.removeLayer(layerRef.current);
      }
    };
  }, [data, categoryVisibility, map]);

  return null;
}

interface MapViewProps {
  data: PedestrianDemandData | null;
  categoryVisibility: CategoryVisibility;
  focusArea: FocusArea | null;
  className?: string;
}

export function MapView({
  data,
  categoryVisibility,
  focusArea,
  className = '',
}: MapViewProps) {
  const defaultCenter: [number, number] = [40.72, -73.998];
  const defaultZoom = 14;

  const manhattanBounds: L.LatLngBoundsExpression = [
    [40.695, -74.025],
    [40.77, -73.965],
  ];

  return (
    <div className={`relative ${className}`}>
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        minZoom={12}
        maxZoom={18}
        maxBounds={manhattanBounds}
        maxBoundsViscosity={1.0}
        className="w-full h-full rounded-lg"
        style={{ background: '#f5f5f5' }}
      >
        <MapController focusArea={focusArea} />

        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          subdomains="abcd"
        />

        {/* Study area rectangles */}
        <Rectangle
          bounds={STUDY_AREAS.lowerManhattan.bounds}
          pathOptions={{ color: '#377eb8', weight: 1.5, fillOpacity: 0.02, dashArray: '10, 5' }}
        >
          <Tooltip permanent direction="center" className="study-area-label">
            Lower Manhattan
          </Tooltip>
        </Rectangle>

        <Rectangle
          bounds={STUDY_AREAS.chinatownSoho.bounds}
          pathOptions={{ color: '#e41a1c', weight: 2, fillOpacity: 0.05, dashArray: '5, 5' }}
        >
          <Tooltip permanent direction="center" className="study-area-label">
            Chinatown / SoHo
          </Tooltip>
        </Rectangle>

        {/* Native Leaflet GeoJSON layer */}
        {data && data.features && data.features.length > 0 && (
          <DemandLayer data={data} categoryVisibility={categoryVisibility} />
        )}
      </MapContainer>
    </div>
  );
}

export default MapView;
