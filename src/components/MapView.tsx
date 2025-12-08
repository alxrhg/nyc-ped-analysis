/**
 * MapView component - Leaflet map with pedestrian demand visualization
 */

import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Rectangle,
  Tooltip,
  useMap,
} from 'react-leaflet';
import L from 'leaflet';
import type { Layer, LeafletMouseEvent, PathOptions } from 'leaflet';
import type { Feature, Geometry } from 'geojson';

import type {
  PedestrianDemandData,
  PedestrianDemandFeature,
  PedestrianDemandProperties,
  CategoryVisibility,
  FocusArea,
  DemandCategory,
} from '../types/pedestrianDemand';
import {
  getStreetName,
  getBorough,
  STUDY_AREAS,
  DEMAND_STYLES,
} from '../utils/demandStyles';
import Legend from './Legend';

// Fix Leaflet default icon paths for Vite
import 'leaflet/dist/leaflet.css';

/**
 * Component to handle map view changes from focus area selection
 */
interface MapControllerProps {
  focusArea: FocusArea | null;
}

function MapController({ focusArea }: MapControllerProps) {
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
 * Detect the demand category field from feature properties
 * NYC Open Data field names can vary
 */
function detectDemandField(properties: PedestrianDemandProperties): string | null {
  // List of possible field names for demand category
  const possibleFields = [
    'corridor_category',
    'pedestrian_demand',
    'ped_demand',
    'demand_category',
    'demand',
    'category',
    'ped_level',
    'level',
  ];

  for (const field of possibleFields) {
    if (properties[field] !== undefined && properties[field] !== null) {
      return field;
    }
  }

  return null;
}

/**
 * Parse a demand category value to a standard category
 */
function parseDemandCategory(value: unknown): DemandCategory | null {
  if (!value) return null;

  const str = String(value).toLowerCase().trim();

  if (str.includes('very') && str.includes('high')) return 'Very High';
  if (str.includes('high')) return 'High';
  if (str.includes('medium') || str.includes('med')) return 'Medium';
  if (str.includes('low')) return 'Low';

  return null;
}

interface MapViewProps {
  data: PedestrianDemandData | null;
  categoryVisibility: CategoryVisibility;
  focusArea: FocusArea | null;
  onFeatureClick?: (feature: PedestrianDemandFeature) => void;
  className?: string;
}

/**
 * Main map component with pedestrian demand visualization
 */
export function MapView({
  data,
  categoryVisibility,
  focusArea,
  onFeatureClick,
  className = '',
}: MapViewProps) {
  const geoJsonRef = useRef<L.GeoJSON | null>(null);
  const [highlightedLayer, setHighlightedLayer] = useState<Layer | null>(null);
  const [demandField, setDemandField] = useState<string | null>(null);

  // Default view: Lower Manhattan / Chinatown-SoHo area
  const defaultCenter: [number, number] = [40.72, -73.998];
  const defaultZoom = 14;

  // NYC bounds to restrict panning
  const nycBounds: L.LatLngBoundsExpression = [
    [40.68, -74.04],
    [40.82, -73.90],
  ];

  // Detect demand field from data on load
  useEffect(() => {
    if (data && data.features && data.features.length > 0) {
      const firstFeature = data.features[0];
      const props = firstFeature.properties;

      console.log('[MapView] Data loaded, sample properties:', props);
      console.log('[MapView] Feature count:', data.features.length);
      console.log('[MapView] Sample geometry type:', firstFeature.geometry?.type);

      const field = detectDemandField(props);
      console.log('[MapView] Detected demand field:', field);

      if (field) {
        console.log('[MapView] Sample demand value:', props[field]);
        setDemandField(field);
      } else {
        console.warn('[MapView] Could not detect demand field. Available fields:', Object.keys(props));
      }
    }
  }, [data]);

  /**
   * Get demand category for a feature
   */
  const getDemandCategory = useCallback((properties: PedestrianDemandProperties): DemandCategory | null => {
    if (!demandField) return null;
    const value = properties[demandField];
    return parseDemandCategory(value);
  }, [demandField]);

  /**
   * Style function for GeoJSON features
   */
  const styleFunction = useCallback(
    (feature: Feature<Geometry, PedestrianDemandProperties> | undefined): PathOptions => {
      if (!feature?.properties) {
        return { color: '#999', weight: 1, opacity: 0.3 };
      }

      const category = getDemandCategory(feature.properties);

      // Hide if category is toggled off
      if (category && !categoryVisibility[category]) {
        return { opacity: 0, fillOpacity: 0, weight: 0 };
      }

      // If no category detected, show with default style
      if (!category) {
        return { color: '#666', weight: 1, opacity: 0.5 };
      }

      const style = DEMAND_STYLES[category];

      return {
        color: style.color,
        weight: style.weight,
        opacity: style.opacity,
        fillOpacity: style.opacity * 0.5,
      };
    },
    [categoryVisibility, getDemandCategory]
  );

  /**
   * Format tooltip content
   */
  const formatTooltip = useCallback((props: PedestrianDemandProperties): string => {
    const streetName = getStreetName(props);
    const category = getDemandCategory(props);
    const borough = getBorough(props);
    const style = category ? DEMAND_STYLES[category] : null;

    let content = `<strong>${streetName}</strong>`;
    if (category && style) {
      content += `<br><span style="color: ${style.color}; font-weight: 600;">Demand: ${category}</span>`;
    }
    content += `<br><span style="color: #888; font-size: 11px;">${borough}</span>`;
    content += `<br><span style="color: #aaa; font-size: 10px; font-style: italic;">Source: NYC DOT</span>`;

    return content;
  }, [getDemandCategory]);

  /**
   * Handle feature interactions
   */
  const onEachFeature = useCallback(
    (feature: Feature<Geometry, PedestrianDemandProperties>, layer: Layer) => {
      const props = feature.properties;
      if (!props) return;

      // Bind tooltip
      layer.bindTooltip(formatTooltip(props), {
        sticky: true,
        direction: 'top',
        offset: [0, -10],
        className: 'demand-tooltip',
      });

      // Bind popup
      const streetName = getStreetName(props);
      const category = getDemandCategory(props);
      const borough = getBorough(props);
      const style = category ? DEMAND_STYLES[category] : null;

      const popupContent = `
        <div style="padding: 8px; min-width: 180px; font-family: sans-serif;">
          <h3 style="margin: 0 0 8px 0; font-size: 14px; font-weight: 600;">${streetName}</h3>
          ${category && style ? `
            <p style="margin: 0 0 4px 0;">
              <span style="color: #666;">Demand:</span>
              <span style="color: ${style.color}; font-weight: 600;">${category}</span>
            </p>
          ` : ''}
          <p style="margin: 0; color: #888; font-size: 12px;">${borough}</p>
          <p style="margin: 8px 0 0 0; color: #aaa; font-size: 10px; font-style: italic;">
            Source: NYC DOT Pedestrian Mobility Plan
          </p>
        </div>
      `;

      layer.bindPopup(popupContent, { maxWidth: 300 });

      // Event handlers
      layer.on({
        mouseover: (e: LeafletMouseEvent) => {
          const targetLayer = e.target;
          if (targetLayer.setStyle) {
            targetLayer.setStyle({
              weight: (targetLayer.options?.weight || 2) + 2,
              opacity: 1,
            });
            targetLayer.bringToFront();
          }
        },
        mouseout: (e: LeafletMouseEvent) => {
          const targetLayer = e.target;
          if (geoJsonRef.current && targetLayer !== highlightedLayer) {
            geoJsonRef.current.resetStyle(targetLayer);
          }
        },
        click: (e: LeafletMouseEvent) => {
          if (highlightedLayer && geoJsonRef.current) {
            geoJsonRef.current.resetStyle(highlightedLayer);
          }

          const targetLayer = e.target;
          setHighlightedLayer(targetLayer);

          if (targetLayer.setStyle) {
            targetLayer.setStyle({
              weight: (targetLayer.options?.weight || 2) + 3,
              opacity: 1,
            });
            targetLayer.bringToFront();
          }

          if (onFeatureClick) {
            onFeatureClick(feature as PedestrianDemandFeature);
          }
        },
      });
    },
    [formatTooltip, getDemandCategory, highlightedLayer, onFeatureClick]
  );

  // Create a unique key for the GeoJSON layer to force re-render
  const geoJsonKey = useMemo(() => {
    if (!data) return 'no-data';
    const visKey = Object.entries(categoryVisibility)
      .map(([k, v]) => `${k}:${v}`)
      .join(',');
    return `geojson-${data.features.length}-${demandField}-${visKey}`;
  }, [data, demandField, categoryVisibility]);

  return (
    <div className={`relative ${className}`}>
      <MapContainer
        center={defaultCenter}
        zoom={defaultZoom}
        minZoom={11}
        maxZoom={18}
        maxBounds={nycBounds}
        maxBoundsViscosity={1.0}
        className="w-full h-full rounded-lg"
        style={{ background: '#f0f0f0' }}
      >
        {/* Map controller for focus area navigation */}
        <MapController focusArea={focusArea} />

        {/* Muted Carto Light basemap */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          subdomains="abcd"
          maxZoom={20}
          className="grayscale-basemap"
        />

        {/* Study area overlays */}
        <Rectangle
          bounds={STUDY_AREAS.lowerManhattan.bounds}
          pathOptions={STUDY_AREAS.lowerManhattan.style}
        >
          <Tooltip permanent direction="center" className="study-area-label">
            Lower Manhattan Context
          </Tooltip>
        </Rectangle>

        <Rectangle
          bounds={STUDY_AREAS.chinatownSoho.bounds}
          pathOptions={STUDY_AREAS.chinatownSoho.style}
        >
          <Tooltip permanent direction="center" className="study-area-label">
            Chinatown / SoHo Study Area
          </Tooltip>
        </Rectangle>

        {/* Pedestrian demand data layer */}
        {data && data.features.length > 0 && (
          <GeoJSON
            key={geoJsonKey}
            ref={geoJsonRef as React.Ref<L.GeoJSON>}
            data={data}
            style={styleFunction}
            onEachFeature={onEachFeature}
          />
        )}
      </MapContainer>

      {/* Floating legend */}
      <div className="absolute bottom-4 right-4 z-[1000]">
        <Legend />
      </div>
    </div>
  );
}

export default MapView;
