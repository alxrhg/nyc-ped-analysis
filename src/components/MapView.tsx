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
import Legend from './Legend';

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
 * Get demand category from properties
 * Tries multiple possible field names from NYC Open Data
 */
function getDemandCategory(props: PedestrianDemandProperties): DemandCategory | null {
  // Try known field names first
  let value = props.corridor_category || props.pedestrian_demand ||
              props.ped_demand || props.demand_category || props.category ||
              props.demand || props.ped_level;

  // If not found, search for any field containing 'demand' or 'category'
  if (!value) {
    for (const key of Object.keys(props)) {
      const keyLower = key.toLowerCase();
      if (keyLower.includes('demand') || keyLower.includes('category') || keyLower.includes('level')) {
        const v = props[key];
        if (typeof v === 'string' && v.length > 0) {
          value = v;
          break;
        }
      }
    }
  }

  if (!value) return null;

  const str = String(value).toLowerCase().trim();
  if (str.includes('very') && str.includes('high')) return 'Very High';
  if (str === 'high' || str.includes('high')) return 'High';
  if (str === 'medium' || str.includes('medium') || str.includes('mod')) return 'Medium';
  if (str === 'low' || str.includes('low')) return 'Low';

  return null;
}

/**
 * Component that adds GeoJSON layer using native Leaflet
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

    console.log('[DemandLayer] Adding', data.features.length, 'features');
    console.log('[DemandLayer] Sample properties:', data.features[0].properties);
    console.log('[DemandLayer] Available fields:', Object.keys(data.features[0].properties || {}));

    // Test category detection on first feature
    const testCategory = getDemandCategory(data.features[0].properties as PedestrianDemandProperties);
    console.log('[DemandLayer] Detected category for first feature:', testCategory);

    // Remove existing layer
    if (layerRef.current) {
      map.removeLayer(layerRef.current);
    }

    // Create new GeoJSON layer with native Leaflet
    const layer = L.geoJSON(data as GeoJSON.GeoJsonObject, {
      style: (feature) => {
        if (!feature?.properties) {
          return { color: '#888', weight: 1, opacity: 0.5 };
        }

        const category = getDemandCategory(feature.properties as PedestrianDemandProperties);

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
        const category = getDemandCategory(props);
        const color = category ? DEMAND_STYLES[category].color : '#888';

        featureLayer.bindTooltip(
          `<strong>${name}</strong><br/><span style="color:${color}">Demand: ${category || 'N/A'}</span>`,
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

      <div className="absolute bottom-4 right-4 z-[1000]">
        <Legend />
      </div>
    </div>
  );
}

export default MapView;
