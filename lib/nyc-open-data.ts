/**
 * NYC Open Data SODA API utilities
 * Fetches live data from NYC Open Data for the Canal St–Houston St corridor.
 */

const SODA_BASE = "https://data.cityofnewyork.us/resource";

// Study area bounding box (Canal St to Houston St corridor)
export const STUDY_AREA = {
  north: 40.728, // Houston St
  south: 40.714, // Canal St
  west: -74.007, // Varick St / 6th Ave
  east: -73.991, // Bowery / Christie St
};

// Widen the bounding box slightly for data queries to capture nearby records
const QUERY_BUFFER = 0.003;
const QUERY_BOUNDS = {
  north: STUDY_AREA.north + QUERY_BUFFER,
  south: STUDY_AREA.south - QUERY_BUFFER,
  west: STUDY_AREA.west - QUERY_BUFFER,
  east: STUDY_AREA.east + QUERY_BUFFER,
};

interface FetchOptions {
  limit?: number;
  offset?: number;
  where?: string;
  select?: string;
  order?: string;
}

async function fetchSODA<T>(
  datasetId: string,
  options: FetchOptions = {}
): Promise<T[]> {
  const { limit = 5000, offset = 0, where, select, order } = options;

  const params = new URLSearchParams({
    $limit: String(limit),
    $offset: String(offset),
  });

  if (where) params.set("$where", where);
  if (select) params.set("$select", select);
  if (order) params.set("$order", order);

  const url = `${SODA_BASE}/${datasetId}.json?${params.toString()}`;
  const res = await fetch(url);

  if (!res.ok) {
    throw new Error(`SODA API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

/**
 * Fetch all pages of a SODA dataset matching the given options.
 */
async function fetchAllPages<T>(
  datasetId: string,
  options: FetchOptions = {}
): Promise<T[]> {
  const pageSize = options.limit ?? 5000;
  let offset = options.offset ?? 0;
  const all: T[] = [];

  // eslint-disable-next-line no-constant-condition
  while (true) {
    const page = await fetchSODA<T>(datasetId, {
      ...options,
      limit: pageSize,
      offset,
    });
    all.push(...page);
    if (page.length < pageSize) break;
    offset += pageSize;
  }

  return all;
}

// ---------------------------------------------------------------------------
// Traffic Volume Counts (7ym2-wayt)
// ---------------------------------------------------------------------------

export interface TrafficVolumeRecord {
  requestid?: string;
  boro?: string;
  yr?: string;
  m?: string;
  d?: string;
  hh?: string;
  mm?: string;
  vol?: string;
  segmentid?: string;
  wktgeom?: string;
  street?: string;
  fromst?: string;
  tost?: string;
  direction?: string;
}

export async function fetchTrafficVolumes(): Promise<TrafficVolumeRecord[]> {
  // Filter to Manhattan and attempt to get records near the study area
  // This dataset uses WKT geometry; we filter by boro and fetch a broad set
  return fetchAllPages<TrafficVolumeRecord>("7ym2-wayt", {
    where: `boro = 'Manhattan'`,
    limit: 10000,
  });
}

// ---------------------------------------------------------------------------
// Bi-Annual Pedestrian Counts (2de2-6x2h)
// ---------------------------------------------------------------------------

export interface PedestrianCountRecord {
  borough?: string;
  loc?: string;
  the_geom?: { type: string; coordinates: [number, number] };
  latitude?: string;
  longitude?: string;
  [key: string]: unknown; // count columns are dynamic by year/period
}

export async function fetchPedestrianCounts(): Promise<
  PedestrianCountRecord[]
> {
  return fetchSODA<PedestrianCountRecord>("2de2-6x2h", {
    where: `borough = 'Manhattan'`,
    limit: 5000,
  });
}

// ---------------------------------------------------------------------------
// Pedestrian Mobility Plan (c4kr-96ik)
// ---------------------------------------------------------------------------

export interface PedMobilityRecord {
  the_geom?: { type: string; coordinates: unknown };
  corridor_classification?: string;
  street_name?: string;
  [key: string]: unknown;
}

export async function fetchPedMobilityPlan(): Promise<PedMobilityRecord[]> {
  return fetchSODA<PedMobilityRecord>("c4kr-96ik", {
    limit: 10000,
  });
}

// ---------------------------------------------------------------------------
// Motor Vehicle Crashes (h9gi-nx95)
// ---------------------------------------------------------------------------

export interface CrashRecord {
  crash_date?: string;
  crash_time?: string;
  borough?: string;
  zip_code?: string;
  latitude?: string;
  longitude?: string;
  on_street_name?: string;
  cross_street_name?: string;
  number_of_persons_injured?: string;
  number_of_persons_killed?: string;
  number_of_pedestrians_injured?: string;
  number_of_pedestrians_killed?: string;
  number_of_cyclist_injured?: string;
  number_of_cyclist_killed?: string;
  number_of_motorist_injured?: string;
  number_of_motorist_killed?: string;
  contributing_factor_vehicle_1?: string;
  vehicle_type_code1?: string;
  collision_id?: string;
}

export async function fetchCrashData(): Promise<CrashRecord[]> {
  const threeYearsAgo = new Date();
  threeYearsAgo.setFullYear(threeYearsAgo.getFullYear() - 3);
  const dateStr = threeYearsAgo.toISOString().split("T")[0];

  return fetchAllPages<CrashRecord>("h9gi-nx95", {
    where: `latitude >= ${QUERY_BOUNDS.south}
      AND latitude <= ${QUERY_BOUNDS.north}
      AND longitude >= ${QUERY_BOUNDS.west}
      AND longitude <= ${QUERY_BOUNDS.east}
      AND crash_date >= '${dateStr}T00:00:00.000'`,
    limit: 5000,
  });
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Check if a point [lng, lat] is within the study area (with optional buffer). */
export function isInStudyArea(
  lng: number,
  lat: number,
  buffer = 0.002
): boolean {
  return (
    lat >= STUDY_AREA.south - buffer &&
    lat <= STUDY_AREA.north + buffer &&
    lng >= STUDY_AREA.west - buffer &&
    lng <= STUDY_AREA.east + buffer
  );
}

/** Parse a WKT POINT string to [lng, lat]. */
export function parseWktPoint(wkt: string): [number, number] | null {
  const match = wkt.match(/POINT\s*\(\s*([-\d.]+)\s+([-\d.]+)\s*\)/i);
  if (!match) return null;
  return [parseFloat(match[1]), parseFloat(match[2])];
}

/** Parse a WKT LINESTRING to an array of [lng, lat] pairs. */
export function parseWktLineString(
  wkt: string
): [number, number][] | null {
  const match = wkt.match(/LINESTRING\s*\(([^)]+)\)/i);
  if (!match) return null;
  return match[1].split(",").map((pair) => {
    const [lng, lat] = pair.trim().split(/\s+/).map(Number);
    return [lng, lat];
  });
}

/** Parse a WKT MULTILINESTRING to arrays of coordinate pairs. */
export function parseWktMultiLineString(
  wkt: string
): [number, number][][] | null {
  const match = wkt.match(/MULTILINESTRING\s*\((.+)\)/i);
  if (!match) return null;
  const lineStrings = match[1].split(/\)\s*,\s*\(/);
  return lineStrings.map((ls) => {
    const clean = ls.replace(/[()]/g, "");
    return clean.split(",").map((pair) => {
      const [lng, lat] = pair.trim().split(/\s+/).map(Number);
      return [lng, lat];
    });
  });
}
