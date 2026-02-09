"use client";

import { useMemo, useEffect, useRef, useState, useCallback } from "react";
import {
  MapContainer,
  TileLayer,
  Polygon,
  Polyline,
  CircleMarker,
  Popup,
  Marker,
  Tooltip,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "leaflet.heat";
import { STUDY_AREA, PED_COUNT_COL_PATTERN } from "@/lib/nyc-open-data";
import type {
  TrafficVolumeRecord,
  PedestrianCountRecord,
  CrashRecord,
} from "@/lib/nyc-open-data";
import {
  isInStudyArea,
  statePlaneToWGS84,
  parseWktPoint,
  parseWktLineString,
  parseWktMultiLineString,
} from "@/lib/nyc-open-data";
import ltnBoundary from "@/data/ltn-boundary";
import subwayStations from "@/data/subway-stations.json";
import subwayLines from "@/data/subway-lines";

// Leaflet uses [lat, lng], GeoJSON/data stores [lng, lat]
type LatLng = [number, number];

function toLatLng(lngLat: [number, number]): LatLng {
  return [lngLat[1], lngLat[0]];
}

const CENTER: LatLng = [
  (STUDY_AREA.south + STUDY_AREA.north) / 2,
  (STUDY_AREA.west + STUDY_AREA.east) / 2,
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

export interface MapStats {
  crashCount: number;
  crashPedestrian: number;
  crashCyclist: number;
  crashVehicle: number;
  topHotspots: { name: string; count: number }[];
  pedestrianLocations: number;
  totalPedVolume: number;
  trafficSegments: number;
  subwayStations: number;
}

interface ThesisMapProps {
  layers: LayerVisibility;
  crashFilters: CrashFilters;
  darkMode: boolean;
  trafficData: TrafficVolumeRecord[] | undefined;
  pedestrianData: PedestrianCountRecord[] | undefined;
  crashData: CrashRecord[] | undefined;
  onStatsUpdate: (updater: MapStats | ((prev: MapStats) => MapStats)) => void;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function volumeToColor(vol: number): string {
  if (vol > 30000) return "#991b1b";
  if (vol > 15000) return "#ef4444";
  if (vol > 5000) return "#eab308";
  return "#22c55e";
}

function volumeToWeight(vol: number): number {
  if (vol > 30000) return 6;
  if (vol > 15000) return 5;
  if (vol > 5000) return 3;
  return 2;
}

function volumeToLabel(vol: number): string {
  if (vol > 30000) return "Very High";
  if (vol > 15000) return "High";
  if (vol > 5000) return "Moderate";
  return "Low";
}

function crashColor(type: string): string {
  if (type === "pedestrian") return "#e85d75";
  if (type === "cyclist") return "#f0a030";
  return "#aaaaaa";
}

function crashLabel(type: string): string {
  if (type === "pedestrian") return "Pedestrian Involved";
  if (type === "cyclist") return "Cyclist Involved";
  return "Vehicle Only";
}

// ---------------------------------------------------------------------------
// Subway bullet icon factory
// ---------------------------------------------------------------------------

function createSubwayBulletIcon(
  lines: Array<{ name: string; color: string }>,
  darkMode: boolean,
  dimmed: boolean
): L.DivIcon {
  const borderColor = darkMode ? "#ffffff" : "#333333";
  const shadowOpacity = darkMode ? 0.5 : 0.2;
  const opacity = dimmed ? 0.55 : 1;
  const bullets = lines
    .map((line) => {
      const textColor = line.color === "#FCCC0A" ? "#333333" : "#ffffff";
      return `<span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;border:2px solid ${borderColor};background:${line.color};color:${textColor};font-weight:700;font-size:11px;font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;margin-right:1px;line-height:1;">${line.name}</span>`;
    })
    .join("");
  return L.divIcon({
    html: `<div style="display:flex;align-items:center;opacity:${opacity};filter:drop-shadow(0 1px 2px rgba(0,0,0,${shadowOpacity}));">${bullets}</div>`,
    className: "subway-icon-container",
    iconSize: [lines.length * 23, 24],
    iconAnchor: [(lines.length * 23) / 2, 12],
  });
}

// Diamond SVG icon for modal filters
function createDiamondIcon(darkMode: boolean): L.DivIcon {
  const stroke = darkMode ? "#0a0a0a" : "#8a6d20";
  return L.divIcon({
    className: "",
    html: `<svg width="16" height="16" viewBox="0 0 16 16" style="filter:drop-shadow(0 1px 2px rgba(0,0,0,${darkMode ? 0.5 : 0.25}))">
      <path d="M8 1 L15 8 L8 15 L1 8 Z" fill="#f59e0b" stroke="${stroke}" stroke-width="1.5"/>
    </svg>`,
    iconSize: [16, 16],
    iconAnchor: [8, 8],
  });
}

// Component to invalidate map size when container changes
function MapResizer() {
  const map = useMap();
  useEffect(() => {
    const timeout = setTimeout(() => map.invalidateSize(), 100);
    return () => clearTimeout(timeout);
  }, [map]);
  return null;
}

// ---------------------------------------------------------------------------
// Zoom tracker — tells parent the current zoom level
// ---------------------------------------------------------------------------
function ZoomTracker({
  onZoomChange,
}: {
  onZoomChange: (zoom: number) => void;
}) {
  const map = useMap();
  useEffect(() => {
    const handler = () => onZoomChange(map.getZoom());
    map.on("zoomend", handler);
    handler();
    return () => {
      map.off("zoomend", handler);
    };
  }, [map, onZoomChange]);
  return null;
}

// ---------------------------------------------------------------------------
// Crash heatmap layer (imperative Leaflet plugin, no react-leaflet wrapper)
// ---------------------------------------------------------------------------
function CrashHeatmapLayer({
  crashes,
  filters,
  visible,
}: {
  crashes: CrashPoint[];
  filters: CrashFilters;
  visible: boolean;
}) {
  const map = useMap();
  const layersRef = useRef<{
    ped?: L.HeatLayer;
    cyc?: L.HeatLayer;
    veh?: L.HeatLayer;
  }>({});

  useEffect(() => {
    // Clean up previous layers
    Object.values(layersRef.current).forEach((l) => l?.remove());
    layersRef.current = {};

    if (!visible) return;

    const pedPts: [number, number, number][] = [];
    const cycPts: [number, number, number][] = [];
    const vehPts: [number, number, number][] = [];

    for (const c of crashes) {
      if (c.type === "pedestrian")
        pedPts.push([c.position[0], c.position[1], 1]);
      else if (c.type === "cyclist")
        cycPts.push([c.position[0], c.position[1], 1]);
      else vehPts.push([c.position[0], c.position[1], 1]);
    }

    const heatOpts = { radius: 12, blur: 8, maxZoom: 17, minOpacity: 0 };

    // Vehicle heatmap (render first, behind others)
    if (filters.motorist && vehPts.length > 0) {
      layersRef.current.veh = L.heatLayer(vehPts, {
        ...heatOpts,
        max: 1.0,
        gradient: {
          0.4: "rgba(189,189,189,0.35)",
          0.6: "rgba(150,150,150,0.5)",
          0.8: "rgba(99,99,99,0.6)",
          1.0: "rgba(37,37,37,0.7)",
        },
      }).addTo(map);
    }

    // Cyclist heatmap
    if (filters.cyclist && cycPts.length > 0) {
      layersRef.current.cyc = L.heatLayer(cycPts, {
        ...heatOpts,
        max: 1.0,
        gradient: {
          0.4: "rgba(253,174,107,0.35)",
          0.6: "rgba(253,141,60,0.5)",
          0.8: "rgba(230,85,13,0.65)",
          1.0: "rgba(166,54,3,0.8)",
        },
      }).addTo(map);
    }

    // Pedestrian heatmap (on top — most important for the thesis)
    if (filters.pedestrian && pedPts.length > 0) {
      layersRef.current.ped = L.heatLayer(pedPts, {
        ...heatOpts,
        max: 1.0,
        gradient: {
          0.4: "rgba(251,106,74,0.35)",
          0.6: "rgba(222,45,38,0.5)",
          0.8: "rgba(165,15,21,0.65)",
          1.0: "rgba(103,0,13,0.8)",
        },
      }).addTo(map);
    }

    return () => {
      Object.values(layersRef.current).forEach((l) => l?.remove());
      layersRef.current = {};
    };
  }, [crashes, filters, visible, map]);

  return null;
}

// ---------------------------------------------------------------------------
// Processed data types
// ---------------------------------------------------------------------------

interface TrafficSegment {
  id: string;
  positions: LatLng[] | LatLng[][];
  isMulti: boolean;
  volume: number;
  street: string;
  fromst: string;
  tost: string;
  direction: string;
}

interface PedPoint {
  position: LatLng;
  location: string;
  volume: number;
}

interface CrashPoint {
  position: LatLng;
  type: string;
  date: string;
  time: string;
  street: string;
  cross: string;
  injured: number;
  killed: number;
  factor: string;
}

// ==========================================
// Main Component
// ==========================================

export default function ThesisMap({
  layers,
  crashFilters,
  darkMode,
  trafficData,
  pedestrianData,
  crashData,
  onStatsUpdate,
}: ThesisMapProps) {
  const [zoom, setZoom] = useState(15);
  const handleZoomChange = useCallback((z: number) => setZoom(z), []);
  const showHeatmap = zoom < 16;

  // ----- Process LTN Boundary -----
  const ltnData = useMemo(() => {
    const boundary: LatLng[] = [];
    const boundaryRoads: {
      name: string;
      label: string;
      role: string;
      positions: LatLng[];
    }[] = [];
    const modalFilters: {
      name: string;
      description: string;
      position: LatLng;
    }[] = [];

    for (const feature of ltnBoundary.features) {
      const props = feature.properties;
      if (props?.type === "boundary" && feature.geometry.type === "Polygon") {
        const coords = (feature.geometry as GeoJSON.Polygon).coordinates[0];
        for (const c of coords) {
          boundary.push(toLatLng(c as [number, number]));
        }
      } else if (
        props?.type === "boundary_road" &&
        feature.geometry.type === "LineString"
      ) {
        const coords = (feature.geometry as GeoJSON.LineString).coordinates;
        boundaryRoads.push({
          name: props.name || "Boundary Road",
          label: props.label || "",
          role: props.role || "Through traffic corridor",
          positions: coords.map((c) => toLatLng(c as [number, number])),
        });
      } else if (
        props?.type === "modal_filter" &&
        feature.geometry.type === "Point"
      ) {
        const coords = (feature.geometry as GeoJSON.Point).coordinates;
        modalFilters.push({
          name: props.name || "Modal Filter",
          description: props.description || "Proposed modal filter location",
          position: toLatLng(coords as [number, number]),
        });
      }
    }

    return { boundary, boundaryRoads, modalFilters };
  }, []);

  // ----- Process Traffic Data (with proj4 State Plane → WGS84 conversion) -----
  const trafficSegments = useMemo<TrafficSegment[]>(() => {
    if (!trafficData) return [];

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

      const existing = segmentMap.get(rec.segmentid);
      if (existing) {
        existing.totalVol += vol;
        existing.count += 1;
        continue;
      }

      const rawPoint = parseWktPoint(rec.wktgeom);
      const rawLine = !rawPoint ? parseWktLineString(rec.wktgeom) : null;
      const rawMultiLine =
        !rawPoint && !rawLine
          ? parseWktMultiLineString(rec.wktgeom)
          : null;

      let wgs84Coords: [number, number][] | [number, number][][] | null =
        null;
      let isMulti = false;

      if (rawPoint) {
        continue; // Single points can't be rendered as line segments
      } else if (rawLine) {
        const converted = rawLine.map(([x, y]) => statePlaneToWGS84(x, y));
        const inArea = converted.some(([lng, lat]) =>
          isInStudyArea(lng, lat)
        );
        if (!inArea) continue;
        wgs84Coords = converted;
      } else if (rawMultiLine) {
        const converted = rawMultiLine.map((line) =>
          line.map(([x, y]) => statePlaneToWGS84(x, y))
        );
        const inArea = converted
          .flat()
          .some(([lng, lat]) => isInStudyArea(lng, lat));
        if (!inArea) continue;
        wgs84Coords = converted;
        isMulti = true;
      }

      if (!wgs84Coords) continue;

      segmentMap.set(rec.segmentid, {
        coords: wgs84Coords,
        totalVol: vol,
        count: 1,
        street: rec.street || "Unknown",
        fromst: rec.fromst || "",
        tost: rec.tost || "",
        direction: rec.direction || "",
        isMulti,
      });
    }

    const segments: TrafficSegment[] = [];
    segmentMap.forEach((seg, id) => {
      const avgVol = Math.round(seg.totalVol / Math.max(seg.count, 1));
      if (seg.isMulti) {
        segments.push({
          id,
          positions: (seg.coords as [number, number][][]).map((line) =>
            line.map(toLatLng)
          ),
          isMulti: true,
          volume: avgVol,
          street: seg.street,
          fromst: seg.fromst,
          tost: seg.tost,
          direction: seg.direction,
        });
      } else {
        segments.push({
          id,
          positions: (seg.coords as [number, number][]).map(toLatLng),
          isMulti: false,
          volume: avgVol,
          street: seg.street,
          fromst: seg.fromst,
          tost: seg.tost,
          direction: seg.direction,
        });
      }
    });

    return segments;
  }, [trafficData]);

  // ----- Process Pedestrian Data (only match may_XX/sep_XX columns) -----
  const pedPoints = useMemo<PedPoint[]>(() => {
    if (!pedestrianData) return [];

    const points: PedPoint[] = [];

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

      let maxCount = 0;
      for (const [key, val] of Object.entries(rec)) {
        if (typeof val === "string" && PED_COUNT_COL_PATTERN.test(key)) {
          const n = parseInt(val, 10);
          if (!isNaN(n) && n > maxCount) maxCount = n;
        }
      }

      points.push({
        position: [lat, lng],
        location: rec.loc || "Unknown",
        volume: maxCount,
      });
    }

    return points;
  }, [pedestrianData]);

  // ----- Process Crash Data -----
  const crashPoints = useMemo<CrashPoint[]>(() => {
    if (!crashData) return [];

    const points: CrashPoint[] = [];

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

      let type = "vehicle";
      if (pedInvolved) type = "pedestrian";
      else if (cycInvolved) type = "cyclist";

      points.push({
        position: [lat, lng],
        type,
        date: rec.crash_date?.split("T")[0] || "",
        time: rec.crash_time || "",
        street: rec.on_street_name || "",
        cross: rec.cross_street_name || "",
        injured: parseInt(rec.number_of_persons_injured || "0", 10),
        killed: parseInt(rec.number_of_persons_killed || "0", 10),
        factor: rec.contributing_factor_vehicle_1 || "",
      });
    }

    return points;
  }, [crashData]);

  // Filter crashes by type (used for individual dots at high zoom)
  const filteredCrashes = useMemo(() => {
    return crashPoints.filter((c) => {
      if (c.type === "pedestrian" && !crashFilters.pedestrian) return false;
      if (c.type === "cyclist" && !crashFilters.cyclist) return false;
      if (c.type === "vehicle" && !crashFilters.motorist) return false;
      return true;
    });
  }, [crashPoints, crashFilters]);

  // ----- Top hotspot intersections -----
  const topHotspots = useMemo(() => {
    const groups = new Map<string, { name: string; count: number }>();
    for (const c of crashPoints) {
      const rlat = Math.round(c.position[0] / 0.0003) * 0.0003;
      const rlng = Math.round(c.position[1] / 0.0003) * 0.0003;
      const key = `${rlat.toFixed(4)},${rlng.toFixed(4)}`;

      const existing = groups.get(key);
      if (existing) {
        existing.count++;
      } else {
        const name =
          c.street && c.cross
            ? `${c.street} & ${c.cross}`
            : c.street || "Unknown";
        groups.set(key, { name, count: 1 });
      }
    }

    return Array.from(groups.values())
      .sort((a, b) => b.count - a.count)
      .slice(0, 3);
  }, [crashPoints]);

  // ----- Theme-dependent icons (memoized) -----
  const diamondIcon = useMemo(() => createDiamondIcon(darkMode), [darkMode]);
  const stationIcons = useMemo(
    () =>
      subwayStations.map((s) =>
        createSubwayBulletIcon(s.lines, darkMode, s.outsideBoundary)
      ),
    [darkMode]
  );

  // ----- Theme-dependent colors -----
  const boundaryStrokeColor = darkMode ? "#ffffff" : "#1a1a1a";

  // ----- Stats Updates -----
  useEffect(() => {
    onStatsUpdate((prev) => ({
      ...prev,
      trafficSegments: trafficSegments.length,
    }));
  }, [trafficSegments.length]);

  useEffect(() => {
    const totalVol = pedPoints.reduce((sum, p) => sum + p.volume, 0);
    onStatsUpdate((prev) => ({
      ...prev,
      pedestrianLocations: pedPoints.length,
      totalPedVolume: totalVol,
    }));
  }, [pedPoints.length]);

  useEffect(() => {
    const pedCount = crashPoints.filter((c) => c.type === "pedestrian").length;
    const cycCount = crashPoints.filter((c) => c.type === "cyclist").length;
    const vehCount = crashPoints.filter((c) => c.type === "vehicle").length;
    onStatsUpdate((prev) => ({
      ...prev,
      crashCount: crashPoints.length,
      crashPedestrian: pedCount,
      crashCyclist: cycCount,
      crashVehicle: vehCount,
      topHotspots,
    }));
  }, [crashPoints.length, topHotspots]);

  useEffect(() => {
    onStatsUpdate((prev) => ({
      ...prev,
      subwayStations: subwayStations.length,
    }));
  }, []);

  const pedRadius = (vol: number) => {
    if (vol >= 50000) return 20;
    if (vol >= 20000) return 14;
    if (vol >= 5000) return 9;
    if (vol > 0) return 5;
    return 3;
  };

  return (
    <MapContainer
      center={CENTER}
      zoom={15}
      minZoom={13}
      maxZoom={19}
      className={`w-full h-full ${darkMode ? "dark-map" : "light-map"}`}
      zoomControl={false}
    >
      {/* === 1. Basemap === */}
      <TileLayer
        key={darkMode ? "dark" : "light"}
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>'
        url={
          darkMode
            ? "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            : "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        }
      />

      <MapResizer />
      <ZoomTracker onZoomChange={handleZoomChange} />

      {/* === 2. Subway Route Lines (below data layers) === */}
      {layers.transit &&
        subwayLines.map((route) => (
          <Polyline
            key={`route-${route.id}`}
            positions={route.path}
            pathOptions={{
              color: route.color,
              weight: route.weight,
              opacity: route.opacity,
            }}
          />
        ))}

      {/* === 3. LTN boundary fill (subtle blue tint) === */}
      {layers.ltn && ltnData.boundary.length > 0 && (
        <Polygon
          positions={ltnData.boundary}
          pathOptions={{
            color: "transparent",
            weight: 0,
            fillColor: "#4a90d9",
            fillOpacity: 0.05,
          }}
        />
      )}

      {/* === 4. Traffic Volume Segments === */}
      {layers.traffic &&
        trafficSegments.map((seg) =>
          seg.isMulti ? (
            (seg.positions as LatLng[][]).map((line, li) => (
              <Polyline
                key={`t-${seg.id}-${li}`}
                positions={line}
                pathOptions={{
                  color: volumeToColor(seg.volume),
                  weight: volumeToWeight(seg.volume),
                  opacity: 0.85,
                }}
              >
                <Popup>
                  <div className="popup-content">
                    <div className="font-semibold mb-1">{seg.street}</div>
                    <div className="text-xs text-gray-500 mb-1">
                      {seg.fromst} to {seg.tost}
                      {seg.direction ? ` (${seg.direction})` : ""}
                    </div>
                    <div>
                      <span
                        className="font-semibold"
                        style={{ color: volumeToColor(seg.volume) }}
                      >
                        {seg.volume.toLocaleString()}
                      </span>{" "}
                      <span className="text-xs text-gray-500">
                        avg daily traffic
                      </span>
                    </div>
                    <div
                      className="text-xs mt-0.5"
                      style={{ color: volumeToColor(seg.volume) }}
                    >
                      {volumeToLabel(seg.volume)} volume
                    </div>
                  </div>
                </Popup>
              </Polyline>
            ))
          ) : (
            <Polyline
              key={`t-${seg.id}`}
              positions={seg.positions as LatLng[]}
              pathOptions={{
                color: volumeToColor(seg.volume),
                weight: volumeToWeight(seg.volume),
                opacity: 0.85,
              }}
            >
              <Popup>
                <div className="popup-content">
                  <div className="font-semibold mb-1">{seg.street}</div>
                  <div className="text-xs text-gray-500 mb-1">
                    {seg.fromst} to {seg.tost}
                    {seg.direction ? ` (${seg.direction})` : ""}
                  </div>
                  <div>
                    <span
                      className="font-semibold"
                      style={{ color: volumeToColor(seg.volume) }}
                    >
                      {seg.volume.toLocaleString()}
                    </span>{" "}
                    <span className="text-xs text-gray-500">
                      avg daily traffic
                    </span>
                  </div>
                  <div
                    className="text-xs mt-0.5"
                    style={{ color: volumeToColor(seg.volume) }}
                  >
                    {volumeToLabel(seg.volume)} volume
                  </div>
                </div>
              </Popup>
            </Polyline>
          )
        )}

      {/* === 5. Crash Heatmap (zoom < 16) === */}
      {layers.crashes && (
        <CrashHeatmapLayer
          crashes={crashPoints}
          filters={crashFilters}
          visible={showHeatmap}
        />
      )}

      {/* === 5b. Crash Individual Dots (zoom >= 16) === */}
      {layers.crashes &&
        !showHeatmap &&
        filteredCrashes.map((c, i) => (
          <CircleMarker
            key={`crash-${i}`}
            center={c.position}
            radius={5}
            pathOptions={{
              color: darkMode ? "#ffffff" : "#333333",
              fillColor: crashColor(c.type),
              fillOpacity: 0.7,
              weight: 1,
              opacity: 0.4,
            }}
          >
            <Popup>
              <div className="popup-content">
                <div
                  className="font-semibold mb-1"
                  style={{ color: crashColor(c.type) }}
                >
                  {crashLabel(c.type)}
                </div>
                <div className="text-xs text-gray-500 mb-1">
                  {c.date} {c.time}
                  <br />
                  {c.street}
                  {c.cross ? ` & ${c.cross}` : ""}
                </div>
                <div className="text-xs">
                  {c.injured > 0 && (
                    <span style={{ color: "#d97706" }}>
                      Injured: {c.injured}
                    </span>
                  )}
                  {c.killed > 0 && (
                    <span style={{ color: "#dc2626", marginLeft: 8 }}>
                      Killed: {c.killed}
                    </span>
                  )}
                  {c.injured === 0 && c.killed === 0 && (
                    <span className="text-gray-400">
                      No injuries reported
                    </span>
                  )}
                </div>
                {c.factor && c.factor !== "Unspecified" && (
                  <div className="text-xs text-gray-500 mt-1">
                    Factor: {c.factor}
                  </div>
                )}
              </div>
            </Popup>
          </CircleMarker>
        ))}

      {/* === 6. Pedestrian Counts === */}
      {layers.pedestrian &&
        pedPoints.map((p, i) => (
          <CircleMarker
            key={`ped-${i}`}
            center={p.position}
            radius={pedRadius(p.volume)}
            pathOptions={{
              color: "#c4b5fd",
              fillColor: "#a78bfa",
              fillOpacity: 0.7,
              weight: 1,
            }}
          >
            <Popup>
              <div className="popup-content">
                <div
                  className="font-semibold mb-1"
                  style={{ color: "#7c3aed" }}
                >
                  {p.location}
                </div>
                <div>
                  <span className="font-semibold">
                    {p.volume.toLocaleString()}
                  </span>{" "}
                  <span className="text-xs text-gray-500">
                    max recorded pedestrians
                  </span>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}

      {/* === 7. LTN Boundary Roads (dashed) with street labels === */}
      {layers.ltn &&
        ltnData.boundaryRoads.map((road, i) => (
          <Polyline
            key={`br-${i}`}
            positions={road.positions}
            pathOptions={{
              color: boundaryStrokeColor,
              weight: 3,
              dashArray: "10, 6",
              opacity: 0.8,
            }}
          >
            <Tooltip
              permanent
              direction="center"
              className="boundary-label"
            >
              {road.label}
            </Tooltip>
            <Popup>
              <div className="popup-content">
                <div className="font-semibold mb-1">{road.name}</div>
                <div className="text-xs text-gray-500">{road.role}</div>
              </div>
            </Popup>
          </Polyline>
        ))}

      {/* === 8. Modal Filter Diamonds === */}
      {layers.ltn &&
        ltnData.modalFilters.map((mf, i) => (
          <Marker key={`mf-${i}`} position={mf.position} icon={diamondIcon}>
            <Popup>
              <div className="popup-content">
                <div className="font-semibold mb-1">{mf.name}</div>
                <div className="text-xs text-gray-500 mb-2">
                  {mf.description}
                </div>
                <div
                  className="text-xs border-t pt-1"
                  style={{
                    color: "#b45309",
                    borderColor: darkMode ? "#374151" : "#e5e7eb",
                  }}
                >
                  PROPOSED — Not existing infrastructure
                </div>
              </div>
            </Popup>
          </Marker>
        ))}

      {/* === 9. Subway Station Bullet Icons (always on top) === */}
      {layers.transit &&
        subwayStations.map((s, i) => (
          <Marker
            key={`sub-${i}`}
            position={[s.lat, s.lng]}
            icon={stationIcons[i]}
            zIndexOffset={1000}
            opacity={s.outsideBoundary ? 0.7 : 1}
          >
            <Popup>
              <div className="popup-content">
                <div className="font-semibold text-base mb-1">{s.name}</div>
                <div className="flex items-center gap-0.5 mb-1">
                  {s.lines.map((line, li) => (
                    <span
                      key={li}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        width: 20,
                        height: 20,
                        borderRadius: "50%",
                        border: "2px solid #333",
                        background: line.color,
                        color:
                          line.color === "#FCCC0A" ? "#333333" : "#ffffff",
                        fontWeight: 700,
                        fontSize: 11,
                        fontFamily:
                          "'Helvetica Neue', Helvetica, Arial, sans-serif",
                        lineHeight: 1,
                        marginRight: 1,
                      }}
                    >
                      {line.name}
                    </span>
                  ))}
                </div>
                <div className="text-xs text-gray-500">{s.lineName}</div>
                <div className="text-xs text-gray-500">{s.crossStreet}</div>
                {s.outsideBoundary && (
                  <div className="text-xs text-gray-400 mt-1 italic">
                    Outside proposed LTN boundary
                  </div>
                )}
              </div>
            </Popup>
          </Marker>
        ))}
    </MapContainer>
  );
}
