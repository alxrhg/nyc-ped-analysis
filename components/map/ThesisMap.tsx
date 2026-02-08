"use client";

import { useMemo, useEffect } from "react";
import {
  MapContainer,
  TileLayer,
  Polygon,
  Polyline,
  CircleMarker,
  Popup,
  Tooltip,
  Marker,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
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

// Leaflet uses [lat, lng], our data stores [lng, lat]
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

// Diamond SVG icon for modal filters
const diamondIcon = L.divIcon({
  className: "",
  html: `<svg width="16" height="16" viewBox="0 0 16 16" style="filter:drop-shadow(0 1px 2px rgba(0,0,0,0.5))">
    <path d="M8 1 L15 8 L8 15 L1 8 Z" fill="#f59e0b" stroke="#0a0a0a" stroke-width="1"/>
  </svg>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

// Helper: interpolate traffic volume to color
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
  if (type === "pedestrian") return "#ef4444";
  if (type === "cyclist") return "#f97316";
  return "#6b7280";
}

function crashLabel(type: string): string {
  if (type === "pedestrian") return "Pedestrian Involved";
  if (type === "cyclist") return "Cyclist Involved";
  return "Vehicle Only";
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

// ---------- Processed data types ----------

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
  trafficData,
  pedestrianData,
  crashData,
  onStatsUpdate,
}: ThesisMapProps) {
  // ----- Process LTN Boundary -----
  const ltnData = useMemo(() => {
    const boundary: LatLng[] = [];
    const boundaryRoads: { name: string; role: string; positions: LatLng[] }[] =
      [];
    const modalFilters: {
      name: string;
      description: string;
      position: LatLng;
    }[] = [];

    for (const feature of ltnBoundary.features) {
      const props = feature.properties;
      if (
        props?.type === "boundary" &&
        feature.geometry.type === "Polygon"
      ) {
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
          description:
            props.description || "Proposed modal filter location",
          position: toLatLng(coords as [number, number]),
        });
      }
    }

    return { boundary, boundaryRoads, modalFilters };
  }, []);

  // ----- Process Traffic Data -----
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

      const point = parseWktPoint(rec.wktgeom);
      if (point && !isInStudyArea(point[0], point[1])) continue;

      const existing = segmentMap.get(rec.segmentid);
      if (existing) {
        existing.totalVol += vol;
        existing.count += 1;
      } else {
        const line = parseWktLineString(rec.wktgeom);
        const multiLine = !line
          ? parseWktMultiLineString(rec.wktgeom)
          : null;
        const coords = line || multiLine;
        if (!coords) continue;

        const flat = Array.isArray(coords[0]?.[0])
          ? (coords as [number, number][][]).flat()
          : (coords as [number, number][]);
        const inArea = flat.some(([lng, lat]) => isInStudyArea(lng, lat));
        if (!inArea) continue;

        segmentMap.set(rec.segmentid, {
          coords,
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

  // ----- Process Pedestrian Data -----
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

  // Filter crashes by type
  const filteredCrashes = useMemo(() => {
    return crashPoints.filter((c) => {
      if (c.type === "pedestrian" && !crashFilters.pedestrian) return false;
      if (c.type === "cyclist" && !crashFilters.cyclist) return false;
      if (c.type === "vehicle" && !crashFilters.motorist) return false;
      return true;
    });
  }, [crashPoints, crashFilters]);

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
    onStatsUpdate((prev) => ({
      ...prev,
      crashCount: crashPoints.length,
    }));
  }, [crashPoints.length]);

  useEffect(() => {
    onStatsUpdate((prev) => ({
      ...prev,
      subwayStations: subwayStations.length,
    }));
  }, []);

  // Pedestrian circle radius from volume
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
      className="w-full h-full"
      zoomControl={false}
    >
      {/* CartoDB Dark Matter tiles — free, no API key */}
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a>'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />

      <MapResizer />

      {/* ===== Layer 5: Proposed LTN Boundary ===== */}
      {layers.ltn && (
        <>
          {/* Boundary fill */}
          {ltnData.boundary.length > 0 && (
            <Polygon
              positions={ltnData.boundary}
              pathOptions={{
                color: "#3b82f6",
                weight: 0,
                fillColor: "#3b82f6",
                fillOpacity: 0.1,
              }}
            />
          )}

          {/* Boundary roads (dashed) */}
          {ltnData.boundaryRoads.map((road, i) => (
            <Polyline
              key={`br-${i}`}
              positions={road.positions}
              pathOptions={{
                color: "#3b82f6",
                weight: 3,
                dashArray: "12, 8",
                opacity: 0.8,
              }}
            >
              <Popup>
                <div className="popup-content">
                  <div className="font-semibold text-blue-300 mb-1">
                    {road.name}
                  </div>
                  <div className="text-xs text-gray-400">{road.role}</div>
                </div>
              </Popup>
            </Polyline>
          ))}

          {/* Modal filter markers */}
          {ltnData.modalFilters.map((mf, i) => (
            <Marker key={`mf-${i}`} position={mf.position} icon={diamondIcon}>
              <Popup>
                <div className="popup-content">
                  <div className="font-semibold text-blue-300 mb-1">
                    {mf.name}
                  </div>
                  <div className="text-xs text-gray-400 mb-2">
                    {mf.description}
                  </div>
                  <div className="text-xs text-amber-400 border-t border-gray-700 pt-1">
                    PROPOSED — Not existing infrastructure
                  </div>
                </div>
              </Popup>
              <Tooltip direction="top" offset={[0, -10]}>
                {mf.name}
              </Tooltip>
            </Marker>
          ))}
        </>
      )}

      {/* ===== Layer 1: Traffic Volume ===== */}
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
                    <div className="text-xs text-gray-400 mb-1">
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
                      <span className="text-xs text-gray-400">
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
                  <div className="text-xs text-gray-400 mb-1">
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
                    <span className="text-xs text-gray-400">
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

      {/* ===== Layer 2: Pedestrian Counts ===== */}
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
                <div className="font-semibold text-purple-300 mb-1">
                  {p.location}
                </div>
                <div>
                  <span className="font-semibold">
                    {p.volume.toLocaleString()}
                  </span>{" "}
                  <span className="text-xs text-gray-400">
                    max recorded pedestrians
                  </span>
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}

      {/* ===== Layer 3: Crash Data ===== */}
      {layers.crashes &&
        filteredCrashes.map((c, i) => (
          <CircleMarker
            key={`crash-${i}`}
            center={c.position}
            radius={4}
            pathOptions={{
              color: "#ffffff",
              fillColor: crashColor(c.type),
              fillOpacity: 0.8,
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
                <div className="text-xs text-gray-400 mb-1">
                  {c.date} {c.time}
                  <br />
                  {c.street}
                  {c.cross ? ` & ${c.cross}` : ""}
                </div>
                <div className="text-xs">
                  {c.injured > 0 && (
                    <span className="text-yellow-400">
                      Injured: {c.injured}
                    </span>
                  )}
                  {c.killed > 0 && (
                    <span className="text-red-400 ml-2">
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
                  <div className="text-xs text-gray-400 mt-1">
                    Factor: {c.factor}
                  </div>
                )}
              </div>
            </Popup>
          </CircleMarker>
        ))}

      {/* ===== Layer 4: Subway Stations ===== */}
      {layers.transit &&
        subwayStations.map((s, i) => (
          <CircleMarker
            key={`sub-${i}`}
            center={[s.coordinates[1], s.coordinates[0]]}
            radius={7}
            pathOptions={{
              color: "#ffffff",
              fillColor: s.color,
              fillOpacity: 1,
              weight: 2,
            }}
          >
            <Tooltip
              permanent
              direction="top"
              offset={[0, -10]}
              className="subway-tooltip"
            >
              {s.lines.join("/")}
            </Tooltip>
            <Popup>
              <div className="popup-content">
                <div className="font-semibold mb-1">
                  <span
                    className="inline-block w-2.5 h-2.5 rounded-full mr-1.5"
                    style={{ backgroundColor: s.color }}
                  />
                  {s.name} Station
                </div>
                <div className="text-xs text-gray-400">
                  Lines: <strong>{s.lines.join("/")}</strong>
                  <br />
                  at {s.cross_street}
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
    </MapContainer>
  );
}
