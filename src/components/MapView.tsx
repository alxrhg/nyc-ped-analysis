/**
 * MapView component - Leaflet map with pedestrian demand visualization
 */

import { useEffect, useRef, useState, useCallback } from 'react';
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

import type {
  PedestrianDemandData,
  PedestrianDemandFeature,
  CategoryVisibility,
  FocusArea,
} from '../types/pedestrianDemand';
import {
  getDemandCategory,
  getStyleForCategory,
  getStreetName,
  getBorough,
  formatTooltipContent,
  STUDY_AREAS,
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

  // Default view: Lower Manhattan / Chinatown-SoHo area
  const defaultCenter: [number, number] = [40.72, -73.998];
  const defaultZoom = 14;

  // NYC bounds to restrict panning
  const nycBounds: L.LatLngBoundsExpression = [
    [40.68, -74.04],
    [40.82, -73.90],
  ];

  /**
   * Style function for GeoJSON features
   * Returns appropriate color/weight based on demand category and visibility
   */
  const getFeatureStyle = useCallback(
    (feature: PedestrianDemandFeature | undefined): PathOptions => {
      if (!feature?.properties) {
        return { opacity: 0, weight: 0 };
      }

      const category = getDemandCategory(feature.properties);

      // Hide if category is toggled off
      if (category && !categoryVisibility[category]) {
        return { opacity: 0, fillOpacity: 0, weight: 0 };
      }

      const style = getStyleForCategory(category);

      return {
        color: style.color,
        weight: style.weight,
        opacity: style.opacity,
        fillOpacity: style.opacity * 0.5,
      };
    },
    [categoryVisibility]
  );

  /**
   * Handle feature hover - show tooltip and highlight
   */
  const onEachFeature = useCallback(
    (feature: PedestrianDemandFeature, layer: Layer) => {
      const props = feature.properties;
      if (!props) return;

      // Create tooltip content
      const tooltipContent = formatTooltipContent(props);

      // Bind tooltip
      layer.bindTooltip(tooltipContent, {
        sticky: true,
        direction: 'top',
        offset: [0, -10],
        className: 'demand-tooltip',
      });

      // Create popup for click
      const streetName = getStreetName(props);
      const category = getDemandCategory(props);
      const borough = getBorough(props);
      const style = getStyleForCategory(category);

      const popupContent = `
        <div class="p-2 min-w-[200px]">
          <h3 class="font-semibold text-gray-800 mb-1">${streetName}</h3>
          ${category ? `
            <p class="mb-1">
              <span class="text-gray-600">Demand:</span>
              <span style="color: ${style.color}; font-weight: 600;">${category}</span>
            </p>
          ` : ''}
          <p class="text-gray-500 text-sm">${borough}</p>
          <p class="text-gray-400 text-xs mt-2 italic">Source: NYC DOT Pedestrian Mobility Plan</p>
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
          // Reset previous highlight
          if (highlightedLayer && geoJsonRef.current) {
            geoJsonRef.current.resetStyle(highlightedLayer);
          }

          // Set new highlight
          const targetLayer = e.target;
          setHighlightedLayer(targetLayer);

          if (targetLayer.setStyle) {
            targetLayer.setStyle({
              weight: (targetLayer.options?.weight || 2) + 3,
              opacity: 1,
            });
            targetLayer.bringToFront();
          }

          // Call callback if provided
          if (onFeatureClick) {
            onFeatureClick(feature);
          }
        },
      });
    },
    [highlightedLayer, onFeatureClick]
  );

  /**
   * Update styles when category visibility changes
   */
  useEffect(() => {
    if (geoJsonRef.current && data) {
      geoJsonRef.current.eachLayer((layer) => {
        const geoLayer = layer as L.GeoJSON;
        if (geoLayer.feature) {
          const newStyle = getFeatureStyle(geoLayer.feature as PedestrianDemandFeature);
          if ((layer as L.Path).setStyle) {
            (layer as L.Path).setStyle(newStyle);
          }
        }
      });
    }
  }, [categoryVisibility, data, getFeatureStyle]);

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
        {data && (
          <GeoJSON
            ref={geoJsonRef as React.Ref<L.GeoJSON>}
            data={data}
            style={getFeatureStyle}
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
