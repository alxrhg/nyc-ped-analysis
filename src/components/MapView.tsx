/**
 * MapView component - Leaflet map with pedestrian demand visualization
 * Simplified version for better performance
 */

import { useEffect, useRef, useMemo } from 'react';
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Rectangle,
  Tooltip,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import type { PathOptions } from 'leaflet';
import type { Feature, Geometry } from 'geojson';

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
      const bounds = L.latLngBounds(focusArea.bounds);
      map.fitBounds(bounds, { padding: [20, 20], maxZoom: focusArea.zoom || 16 });
    }
  }, [focusArea, map]);

  return null;
}

/**
 * Get demand category from properties - inline detection
 */
function getDemandCategory(props: PedestrianDemandProperties): DemandCategory | null {
  // Try different possible field names
  const value = props.corridor_category ||
                props.pedestrian_demand ||
                props.ped_demand ||
                props.demand_category ||
                props.category ||
                props.demand;

  if (!value) return null;

  const str = String(value).toLowerCase();
  if (str.includes('very') && str.includes('high')) return 'Very High';
  if (str.includes('high')) return 'High';
  if (str.includes('medium') || str.includes('med')) return 'Medium';
  if (str.includes('low')) return 'Low';

  return null;
}

/**
 * Get style for a feature
 */
function getFeatureStyle(
  feature: Feature<Geometry, PedestrianDemandProperties> | undefined,
  categoryVisibility: CategoryVisibility
): PathOptions {
  if (!feature?.properties) {
    return { color: '#888', weight: 1, opacity: 0.5 };
  }

  const category = getDemandCategory(feature.properties);

  // Hide if category is toggled off
  if (category && !categoryVisibility[category]) {
    return { opacity: 0, fillOpacity: 0, weight: 0 };
  }

  // No category = default grey
  if (!category) {
    return { color: '#888', weight: 1, opacity: 0.5 };
  }

  const style = DEMAND_STYLES[category];
  return {
    color: style.color,
    weight: style.weight,
    opacity: style.opacity,
  };
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
  const geoJsonRef = useRef<L.GeoJSON | null>(null);

  const defaultCenter: [number, number] = [40.72, -73.998];
  const defaultZoom = 14;

  const manhattanBounds: L.LatLngBoundsExpression = [
    [40.695, -74.025],
    [40.77, -73.965],
  ];

  // Log data on load
  useEffect(() => {
    if (data?.features?.length) {
      console.log('[MapView] Features:', data.features.length);
      console.log('[MapView] Sample:', data.features[0].properties);
      console.log('[MapView] Geometry:', data.features[0].geometry?.type);
    }
  }, [data]);

  // Style function
  const styleFunction = useMemo(() => {
    return (feature: Feature<Geometry, PedestrianDemandProperties> | undefined) => {
      return getFeatureStyle(feature, categoryVisibility);
    };
  }, [categoryVisibility]);

  // Tooltip handler
  const onEachFeature = useMemo(() => {
    return (feature: Feature<Geometry, PedestrianDemandProperties>, layer: L.Layer) => {
      const props = feature.properties;
      if (!props) return;

      const name = props.street || props.streetname || props.on_st || props.name || 'Street';
      const category = getDemandCategory(props);
      const categoryColor = category ? DEMAND_STYLES[category].color : '#888';

      const tooltip = `
        <strong>${name}</strong><br/>
        <span style="color:${categoryColor}">Demand: ${category || 'N/A'}</span>
      `;

      layer.bindTooltip(tooltip, { sticky: true });
    };
  }, []);

  // Key to force re-render when visibility changes
  const geoJsonKey = useMemo(() => {
    const vis = Object.values(categoryVisibility).join('-');
    return `geojson-${vis}`;
  }, [categoryVisibility]);

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

        {/* Pedestrian demand layer */}
        {data && data.features && data.features.length > 0 && (
          <GeoJSON
            key={geoJsonKey}
            ref={geoJsonRef as React.Ref<L.GeoJSON>}
            data={data}
            style={styleFunction}
            onEachFeature={onEachFeature}
          />
        )}
      </MapContainer>

      <div className="absolute bottom-4 right-4 z-[1000]">
        <Legend />
      </div>
    </div>
  );
}

export default MapView;
