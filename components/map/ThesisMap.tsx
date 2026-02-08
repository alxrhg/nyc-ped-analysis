"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import mapboxgl from "mapbox-gl";
import "mapbox-gl/dist/mapbox-gl.css";
import { STUDY_AREA } from "@/lib/nyc-open-data";
import type {
  TrafficVolumeRecord,
  PedestrianCountRecord,
  CrashRecord,
} from "@/lib/nyc-open-data";
import {
  isInStudyArea,
  parseWktPoint,
  parseWktLineString,
  parseWktMultiLineString,
} from "@/lib/nyc-open-data";
import ltnBoundary from "@/data/ltn-boundary";
import subwayStations from "@/data/subway-stations.json";

// Use Mapbox's public demo token — users should replace with their own
const MAPBOX_TOKEN =
  process.env.NEXT_PUBLIC_MAPBOX_TOKEN ||
  "pk.eyJ1IjoibWFwYm94IiwiYSI6ImNpejY4NXVycTA2emYycXBndHRqcmZ3N3gifQ.rJcFIG214AriISLbB6B5aw";

const CENTER: [number, number] = [
  (STUDY_AREA.west + STUDY_AREA.east) / 2,
  (STUDY_AREA.south + STUDY_AREA.north) / 2,
];

export interface LayerVisibility {
  traffic: boolean;
  pedestrian: boolean;
  crashes: boolean;
  transit: boolean;
  ltn: boolean;
}

export interface CrashFilters {
  pedestrian: boolean;
  cyclist: boolean;
  motorist: boolean;
}

interface ThesisMapProps {
  layers: LayerVisibility;
  crashFilters: CrashFilters;
  trafficData: TrafficVolumeRecord[] | undefined;
  pedestrianData: PedestrianCountRecord[] | undefined;
  crashData: CrashRecord[] | undefined;
  onStatsUpdate: (updater: MapStats | ((prev: MapStats) => MapStats)) => void;
}

export interface MapStats {
  crashCount: number;
  pedestrianLocations: number;
  totalPedVolume: number;
  trafficSegments: number;
  subwayStations: number;
}

export default function ThesisMap({
  layers,
  crashFilters,
  trafficData,
  pedestrianData,
  crashData,
  onStatsUpdate,
}: ThesisMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const [mapLoaded, setMapLoaded] = useState(false);
  const popupRef = useRef<mapboxgl.Popup | null>(null);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;

    map.current = new mapboxgl.Map({
      container: mapContainer.current,
      style: "mapbox://styles/mapbox/dark-v11",
      center: CENTER,
      zoom: 15,
      minZoom: 13,
      maxZoom: 19,
      attributionControl: false,
    });

    map.current.addControl(
      new mapboxgl.NavigationControl({ showCompass: false }),
      "top-right"
    );
    map.current.addControl(
      new mapboxgl.AttributionControl({ compact: true }),
      "bottom-right"
    );

    map.current.on("load", () => {
      setMapLoaded(true);
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // ----- LTN Boundary Layer -----
  useEffect(() => {
    if (!mapLoaded || !map.current) return;
    const m = map.current;

    if (!m.getSource("ltn-boundary")) {
      m.addSource("ltn-boundary", {
        type: "geojson",
        data: ltnBoundary as GeoJSON.FeatureCollection,
      });

      // Boundary fill
      m.addLayer({
        id: "ltn-fill",
        type: "fill",
        source: "ltn-boundary",
        filter: ["==", ["get", "type"], "boundary"],
        paint: {
          "fill-color": "#3b82f6",
          "fill-opacity": 0.08,
        },
      });

      // Boundary roads (dashed)
      m.addLayer({
        id: "ltn-boundary-roads",
        type: "line",
        source: "ltn-boundary",
        filter: ["==", ["get", "type"], "boundary_road"],
        paint: {
          "line-color": "#3b82f6",
          "line-width": 3,
          "line-dasharray": [4, 3],
          "line-opacity": 0.8,
        },
      });

      // Modal filter markers (diamonds)
      m.addLayer({
        id: "ltn-modal-filters",
        type: "symbol",
        source: "ltn-boundary",
        filter: ["==", ["get", "type"], "modal_filter"],
        layout: {
          "icon-image": "diamond",
          "icon-size": 0.8,
          "icon-allow-overlap": true,
          "text-field": ["get", "name"],
          "text-size": 10,
          "text-offset": [0, 1.5],
          "text-anchor": "top",
          "text-optional": true,
        },
        paint: {
          "text-color": "#93c5fd",
          "text-halo-color": "#0a0a0a",
          "text-halo-width": 1,
        },
      });

      // Click handler for modal filters
      m.on("click", "ltn-modal-filters", (e) => {
        if (!e.features?.[0]) return;
        const props = e.features[0].properties;
        const coords = (e.features[0].geometry as GeoJSON.Point).coordinates;

        showPopup(
          coords as [number, number],
          `<div>
            <div style="font-weight:600;color:#93c5fd;margin-bottom:4px">
              ${props?.name || "Modal Filter"}
            </div>
            <div style="color:#9ca3af;font-size:12px">
              ${props?.description || "Proposed modal filter location"}
            </div>
            <div style="margin-top:6px;padding-top:6px;border-top:1px solid #2a2a2a;color:#f59e0b;font-size:11px">
              PROPOSED — Not existing infrastructure
            </div>
          </div>`
        );
      });

      // Click handler for boundary roads
      m.on("click", "ltn-boundary-roads", (e) => {
        if (!e.features?.[0]) return;
        const props = e.features[0].properties;

        showPopup(
          e.lngLat.toArray() as [number, number],
          `<div>
            <div style="font-weight:600;color:#93c5fd;margin-bottom:4px">
              ${props?.name || "Boundary Road"}
            </div>
            <div style="color:#9ca3af;font-size:12px">
              ${props?.role || "Through traffic corridor"}
            </div>
          </div>`
        );
      });

      // Cursor changes
      m.on("mouseenter", "ltn-modal-filters", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "ltn-modal-filters", () => {
        m.getCanvas().style.cursor = "";
      });
      m.on("mouseenter", "ltn-boundary-roads", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "ltn-boundary-roads", () => {
        m.getCanvas().style.cursor = "";
      });
    }

    // Add diamond icon if not present
    if (!m.hasImage("diamond")) {
      const size = 24;
      const canvas = document.createElement("canvas");
      canvas.width = size;
      canvas.height = size;
      const ctx = canvas.getContext("2d")!;
      ctx.fillStyle = "#f59e0b";
      ctx.beginPath();
      ctx.moveTo(size / 2, 2);
      ctx.lineTo(size - 2, size / 2);
      ctx.lineTo(size / 2, size - 2);
      ctx.lineTo(2, size / 2);
      ctx.closePath();
      ctx.fill();
      ctx.strokeStyle = "#0a0a0a";
      ctx.lineWidth = 1;
      ctx.stroke();
      m.addImage("diamond", {
        width: size,
        height: size,
        data: ctx.getImageData(0, 0, size, size).data,
      });
    }
  }, [mapLoaded]);

  // ----- Subway Stations Layer -----
  useEffect(() => {
    if (!mapLoaded || !map.current) return;
    const m = map.current;

    if (!m.getSource("subway-stations")) {
      const geojson: GeoJSON.FeatureCollection = {
        type: "FeatureCollection",
        features: subwayStations.map((s) => ({
          type: "Feature" as const,
          properties: {
            name: s.name,
            lines: s.lines.join("/"),
            color: s.color,
            cross_street: s.cross_street,
          },
          geometry: {
            type: "Point" as const,
            coordinates: s.coordinates,
          },
        })),
      };

      m.addSource("subway-stations", { type: "geojson", data: geojson });

      m.addLayer({
        id: "subway-circles",
        type: "circle",
        source: "subway-stations",
        paint: {
          "circle-radius": 7,
          "circle-color": ["get", "color"],
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
        },
      });

      m.addLayer({
        id: "subway-labels",
        type: "symbol",
        source: "subway-stations",
        layout: {
          "text-field": ["get", "lines"],
          "text-size": 9,
          "text-font": ["DIN Pro Bold", "Arial Unicode MS Bold"],
          "text-offset": [0, -1.5],
          "text-anchor": "bottom",
        },
        paint: {
          "text-color": "#ffffff",
          "text-halo-color": "#0a0a0a",
          "text-halo-width": 1,
        },
      });

      m.on("click", "subway-circles", (e) => {
        if (!e.features?.[0]) return;
        const props = e.features[0].properties;
        const coords = (e.features[0].geometry as GeoJSON.Point).coordinates;

        showPopup(
          coords as [number, number],
          `<div>
            <div style="font-weight:600;margin-bottom:4px">
              <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${props?.color};margin-right:6px"></span>
              ${props?.name} Station
            </div>
            <div style="color:#9ca3af;font-size:12px">
              Lines: <strong>${props?.lines}</strong><br/>
              at ${props?.cross_street}
            </div>
          </div>`
        );
      });

      m.on("mouseenter", "subway-circles", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "subway-circles", () => {
        m.getCanvas().style.cursor = "";
      });
    }
  }, [mapLoaded]);

  // ----- Traffic Volume Layer -----
  useEffect(() => {
    if (!mapLoaded || !map.current || !trafficData) return;
    const m = map.current;

    // Aggregate traffic volumes by segment
    const segmentMap = new Map<
      string,
      {
        coords: [number, number][] | [number, number][][];
        totalVol: number;
        count: number;
        street: string;
        fromst: string;
        tost: string;
        direction: string;
        isMulti: boolean;
      }
    >();

    for (const rec of trafficData) {
      if (!rec.wktgeom || !rec.segmentid) continue;

      const vol = parseInt(rec.vol || "0", 10);
      if (isNaN(vol)) continue;

      // Try parsing as different WKT types
      const point = parseWktPoint(rec.wktgeom);
      if (point) {
        if (!isInStudyArea(point[0], point[1])) continue;
      }

      const existing = segmentMap.get(rec.segmentid);
      if (existing) {
        existing.totalVol += vol;
        existing.count += 1;
      } else {
        // Try to parse geometry
        const line = parseWktLineString(rec.wktgeom);
        const multiLine = !line
          ? parseWktMultiLineString(rec.wktgeom)
          : null;
        const coords = line || multiLine;

        if (!coords) continue;

        // Check if any coordinate is in the study area
        const flat = Array.isArray(coords[0]?.[0])
          ? (coords as [number, number][][]).flat()
          : (coords as [number, number][]);
        const inArea = flat.some(([lng, lat]) => isInStudyArea(lng, lat));
        if (!inArea) continue;

        segmentMap.set(rec.segmentid, {
          coords: coords,
          totalVol: vol,
          count: 1,
          street: rec.street || "Unknown",
          fromst: rec.fromst || "",
          tost: rec.tost || "",
          direction: rec.direction || "",
          isMulti: !!multiLine,
        });
      }
    }

    // Build GeoJSON from aggregated data
    const features: GeoJSON.Feature[] = [];
    segmentMap.forEach((seg, id) => {
      const avgDailyVol = Math.round(seg.totalVol / Math.max(seg.count, 1));
      if (seg.isMulti) {
        features.push({
          type: "Feature",
          properties: {
            id,
            volume: avgDailyVol,
            street: seg.street,
            fromst: seg.fromst,
            tost: seg.tost,
            direction: seg.direction,
          },
          geometry: {
            type: "MultiLineString",
            coordinates: seg.coords as [number, number][][],
          },
        });
      } else {
        features.push({
          type: "Feature",
          properties: {
            id,
            volume: avgDailyVol,
            street: seg.street,
            fromst: seg.fromst,
            tost: seg.tost,
            direction: seg.direction,
          },
          geometry: {
            type: "LineString",
            coordinates: seg.coords as [number, number][],
          },
        });
      }
    });

    const geojson: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features,
    };

    if (m.getSource("traffic-volume")) {
      (m.getSource("traffic-volume") as mapboxgl.GeoJSONSource).setData(
        geojson
      );
    } else {
      m.addSource("traffic-volume", { type: "geojson", data: geojson });

      m.addLayer(
        {
          id: "traffic-lines",
          type: "line",
          source: "traffic-volume",
          paint: {
            "line-color": [
              "interpolate",
              ["linear"],
              ["get", "volume"],
              0,
              "#22c55e",
              5000,
              "#eab308",
              15000,
              "#ef4444",
              30000,
              "#991b1b",
            ],
            "line-width": [
              "interpolate",
              ["linear"],
              ["get", "volume"],
              0,
              2,
              30000,
              8,
            ],
            "line-opacity": 0.85,
          },
        },
        "subway-circles" // insert below subway layer
      );

      m.on("click", "traffic-lines", (e) => {
        if (!e.features?.[0]) return;
        const props = e.features[0].properties;
        const vol = props?.volume || 0;

        let intensity = "Low";
        let color = "#22c55e";
        if (vol > 30000) {
          intensity = "Very High";
          color = "#991b1b";
        } else if (vol > 15000) {
          intensity = "High";
          color = "#ef4444";
        } else if (vol > 5000) {
          intensity = "Moderate";
          color = "#eab308";
        }

        showPopup(
          e.lngLat.toArray() as [number, number],
          `<div>
            <div style="font-weight:600;margin-bottom:4px">
              ${props?.street || "Unknown Street"}
            </div>
            <div style="color:#9ca3af;font-size:12px;margin-bottom:4px">
              ${props?.fromst} to ${props?.tost}
              ${props?.direction ? `(${props.direction})` : ""}
            </div>
            <div style="font-size:14px">
              <span style="color:${color};font-weight:600">${vol.toLocaleString()}</span>
              <span style="color:#9ca3af"> avg daily traffic</span>
            </div>
            <div style="color:${color};font-size:12px;margin-top:2px">
              ${intensity} volume
            </div>
          </div>`
        );
      });

      m.on("mouseenter", "traffic-lines", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "traffic-lines", () => {
        m.getCanvas().style.cursor = "";
      });
    }

    onStatsUpdate((prev) => ({
      ...prev,
      trafficSegments: segmentMap.size,
    }));
  }, [mapLoaded, trafficData]);

  // ----- Pedestrian Counts Layer -----
  useEffect(() => {
    if (!mapLoaded || !map.current || !pedestrianData) return;
    const m = map.current;

    // Process pedestrian data
    const features: GeoJSON.Feature[] = [];
    let totalVolume = 0;

    for (const rec of pedestrianData) {
      let lng: number | undefined;
      let lat: number | undefined;

      if (rec.the_geom?.coordinates) {
        [lng, lat] = rec.the_geom.coordinates;
      } else if (rec.longitude && rec.latitude) {
        lng = parseFloat(rec.longitude);
        lat = parseFloat(rec.latitude);
      }

      if (lng === undefined || lat === undefined) continue;
      if (isNaN(lng) || isNaN(lat)) continue;
      if (!isInStudyArea(lng, lat, 0.005)) continue;

      // Sum all count columns
      let maxCount = 0;
      for (const [key, val] of Object.entries(rec)) {
        if (
          typeof val === "string" &&
          /^\d+$/.test(val) &&
          key !== "latitude" &&
          key !== "longitude"
        ) {
          const n = parseInt(val, 10);
          if (n > maxCount) maxCount = n;
        }
      }

      if (maxCount > 0) totalVolume += maxCount;

      features.push({
        type: "Feature",
        properties: {
          location: rec.loc || "Unknown",
          volume: maxCount,
          borough: rec.borough || "",
        },
        geometry: {
          type: "Point",
          coordinates: [lng, lat],
        },
      });
    }

    const geojson: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features,
    };

    if (m.getSource("pedestrian-counts")) {
      (m.getSource("pedestrian-counts") as mapboxgl.GeoJSONSource).setData(
        geojson
      );
    } else {
      m.addSource("pedestrian-counts", { type: "geojson", data: geojson });

      m.addLayer(
        {
          id: "pedestrian-circles",
          type: "circle",
          source: "pedestrian-counts",
          paint: {
            "circle-radius": [
              "interpolate",
              ["linear"],
              ["get", "volume"],
              0,
              4,
              5000,
              10,
              20000,
              18,
              50000,
              26,
            ],
            "circle-color": "#a78bfa",
            "circle-opacity": 0.7,
            "circle-stroke-width": 1,
            "circle-stroke-color": "#c4b5fd",
          },
        },
        "subway-circles"
      );

      m.on("click", "pedestrian-circles", (e) => {
        if (!e.features?.[0]) return;
        const props = e.features[0].properties;
        const coords = (e.features[0].geometry as GeoJSON.Point).coordinates;

        showPopup(
          coords as [number, number],
          `<div>
            <div style="font-weight:600;color:#a78bfa;margin-bottom:4px">
              ${props?.location || "Pedestrian Count Location"}
            </div>
            <div style="font-size:14px">
              <span style="font-weight:600">${(props?.volume || 0).toLocaleString()}</span>
              <span style="color:#9ca3af"> max recorded pedestrians</span>
            </div>
          </div>`
        );
      });

      m.on("mouseenter", "pedestrian-circles", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "pedestrian-circles", () => {
        m.getCanvas().style.cursor = "";
      });
    }

    onStatsUpdate((prev) => ({
      ...prev,
      pedestrianLocations: features.length,
      totalPedVolume: totalVolume,
    }));
  }, [mapLoaded, pedestrianData]);

  // ----- Crash Data Layer -----
  useEffect(() => {
    if (!mapLoaded || !map.current || !crashData) return;
    const m = map.current;

    const features: GeoJSON.Feature[] = [];

    for (const rec of crashData) {
      const lat = parseFloat(rec.latitude || "");
      const lng = parseFloat(rec.longitude || "");
      if (isNaN(lat) || isNaN(lng)) continue;
      if (!isInStudyArea(lng, lat)) continue;

      const pedInvolved =
        parseInt(rec.number_of_pedestrians_injured || "0", 10) > 0 ||
        parseInt(rec.number_of_pedestrians_killed || "0", 10) > 0;
      const cycInvolved =
        parseInt(rec.number_of_cyclist_injured || "0", 10) > 0 ||
        parseInt(rec.number_of_cyclist_killed || "0", 10) > 0;

      let crashType = "vehicle";
      if (pedInvolved) crashType = "pedestrian";
      else if (cycInvolved) crashType = "cyclist";

      features.push({
        type: "Feature",
        properties: {
          type: crashType,
          date: rec.crash_date?.split("T")[0] || "",
          time: rec.crash_time || "",
          street: rec.on_street_name || "",
          cross: rec.cross_street_name || "",
          injured: parseInt(rec.number_of_persons_injured || "0", 10),
          killed: parseInt(rec.number_of_persons_killed || "0", 10),
          pedInjured: parseInt(rec.number_of_pedestrians_injured || "0", 10),
          pedKilled: parseInt(rec.number_of_pedestrians_killed || "0", 10),
          cycInjured: parseInt(rec.number_of_cyclist_injured || "0", 10),
          cycKilled: parseInt(rec.number_of_cyclist_killed || "0", 10),
          factor: rec.contributing_factor_vehicle_1 || "",
        },
        geometry: {
          type: "Point",
          coordinates: [lng, lat],
        },
      });
    }

    const geojson: GeoJSON.FeatureCollection = {
      type: "FeatureCollection",
      features,
    };

    if (m.getSource("crash-data")) {
      (m.getSource("crash-data") as mapboxgl.GeoJSONSource).setData(geojson);
    } else {
      m.addSource("crash-data", { type: "geojson", data: geojson });

      m.addLayer(
        {
          id: "crash-points",
          type: "circle",
          source: "crash-data",
          paint: {
            "circle-radius": 4,
            "circle-color": [
              "match",
              ["get", "type"],
              "pedestrian",
              "#ef4444",
              "cyclist",
              "#f97316",
              "#6b7280",
            ],
            "circle-opacity": 0.8,
            "circle-stroke-width": 1,
            "circle-stroke-color": "#ffffff",
            "circle-stroke-opacity": 0.4,
          },
        },
        "subway-circles"
      );

      m.on("click", "crash-points", (e) => {
        if (!e.features?.[0]) return;
        const props = e.features[0].properties;
        const coords = (e.features[0].geometry as GeoJSON.Point).coordinates;

        const typeColor =
          props?.type === "pedestrian"
            ? "#ef4444"
            : props?.type === "cyclist"
              ? "#f97316"
              : "#6b7280";
        const typeLabel =
          props?.type === "pedestrian"
            ? "Pedestrian Involved"
            : props?.type === "cyclist"
              ? "Cyclist Involved"
              : "Vehicle Only";

        showPopup(
          coords as [number, number],
          `<div>
            <div style="font-weight:600;color:${typeColor};margin-bottom:4px">
              ${typeLabel}
            </div>
            <div style="color:#9ca3af;font-size:12px;margin-bottom:4px">
              ${props?.date || ""} ${props?.time || ""}<br/>
              ${props?.street || ""}${props?.cross ? ` & ${props.cross}` : ""}
            </div>
            <div style="font-size:12px">
              ${(props?.injured ?? 0) > 0 ? `<span style="color:#eab308">Injured: ${props?.injured}</span>` : ""}
              ${(props?.killed ?? 0) > 0 ? `<span style="color:#ef4444;margin-left:8px">Killed: ${props?.killed}</span>` : ""}
              ${(props?.injured ?? 0) === 0 && (props?.killed ?? 0) === 0 ? '<span style="color:#9ca3af">No injuries reported</span>' : ""}
            </div>
            ${props?.factor && props?.factor !== "Unspecified" ? `<div style="color:#9ca3af;font-size:11px;margin-top:4px">Factor: ${props?.factor}</div>` : ""}
          </div>`
        );
      });

      m.on("mouseenter", "crash-points", () => {
        m.getCanvas().style.cursor = "pointer";
      });
      m.on("mouseleave", "crash-points", () => {
        m.getCanvas().style.cursor = "";
      });
    }

    onStatsUpdate((prev) => ({
      ...prev,
      crashCount: features.length,
    }));
  }, [mapLoaded, crashData]);

  // ----- Layer Visibility -----
  useEffect(() => {
    if (!mapLoaded || !map.current) return;
    const m = map.current;

    const layerMap: Record<string, string[]> = {
      traffic: ["traffic-lines"],
      pedestrian: ["pedestrian-circles"],
      crashes: ["crash-points"],
      transit: ["subway-circles", "subway-labels"],
      ltn: ["ltn-fill", "ltn-boundary-roads", "ltn-modal-filters"],
    };

    for (const [key, layerIds] of Object.entries(layerMap)) {
      const visible = layers[key as keyof LayerVisibility];
      for (const layerId of layerIds) {
        if (m.getLayer(layerId)) {
          m.setLayoutProperty(
            layerId,
            "visibility",
            visible ? "visible" : "none"
          );
        }
      }
    }
  }, [mapLoaded, layers]);

  // ----- Crash Filter -----
  useEffect(() => {
    if (!mapLoaded || !map.current) return;
    const m = map.current;
    if (!m.getLayer("crash-points")) return;

    const typeFilters: string[] = [];
    if (crashFilters.pedestrian) typeFilters.push("pedestrian");
    if (crashFilters.cyclist) typeFilters.push("cyclist");
    if (crashFilters.motorist) typeFilters.push("vehicle");

    if (typeFilters.length === 0 || typeFilters.length === 3) {
      m.setFilter("crash-points", null);
    } else {
      m.setFilter("crash-points", [
        "in",
        ["get", "type"],
        ["literal", typeFilters],
      ]);
    }
  }, [mapLoaded, crashFilters]);

  // Stats update for subway stations
  useEffect(() => {
    onStatsUpdate((prev) => ({
      ...prev,
      subwayStations: subwayStations.length,
    }));
  }, []);

  const showPopup = useCallback(
    (coords: [number, number], html: string) => {
      if (!map.current) return;
      popupRef.current?.remove();
      popupRef.current = new mapboxgl.Popup({ closeOnClick: true })
        .setLngLat(coords)
        .setHTML(html)
        .addTo(map.current);
    },
    []
  );

  return (
    <div ref={mapContainer} className="w-full h-full" />
  );
}
