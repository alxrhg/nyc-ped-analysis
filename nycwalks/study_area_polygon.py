"""
Build the thesis study area polygon from NYC Street Centerline (CSCL) segments:
west = Avenue of the Americas (6th Ave), north = Houston St (W+E),
east = Bowery, south = Canal St.

Data: NYC Open Data inkn-q76z (Street Centerline).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import geopandas as gpd
import pandas as pd
import requests
from shapely.geometry import LineString, MultiLineString, Point, Polygon, box, mapping
from shapely.ops import linemerge, unary_union

CSCL_URL = "https://data.cityofnewyork.us/resource/inkn-q76z.json"

# Loose clip so we only keep segments near the quadrilateral (Manhattan south of Midtown)
CLIP_BBOX_WGS84 = (-74.015, 40.708, -73.985, 40.732)

STREETS = {
    "west": ("AVE OF THE AMERICAS",),
    "north": ("W  HOUSTON ST", "E  HOUSTON ST"),
    "east": ("BOWERY",),
    "south": ("CANAL ST",),
}


def _fetch_street_segments(
    full_street_names: tuple[str, ...],
    app_token: str | None = None,
) -> list[dict]:
    """Paginate CSCL rows for Manhattan (borough 1) and given street names."""
    if len(full_street_names) == 1:
        where = f"boroughcode = '1' AND full_street_name = '{full_street_names[0]}'"
    else:
        inner = ", ".join(f"'{n}'" for n in full_street_names)
        where = f"boroughcode = '1' AND full_street_name in ({inner})"
    headers = {}
    if app_token:
        headers["X-App-Token"] = app_token
    rows: list[dict] = []
    offset = 0
    page = 50000
    while True:
        params = {"$where": where, "$limit": page, "$offset": offset}
        r = requests.get(CSCL_URL, params=params, headers=headers, timeout=300)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page:
            break
        offset += page
    return rows


def _rows_to_gdf(rows: list[dict]) -> gpd.GeoDataFrame:
    if not rows:
        return gpd.GeoDataFrame(geometry=[], crs=4326)
    geoms = []
    for row in rows:
        g = row.get("the_geom")
        if isinstance(g, dict):
            from shapely.geometry import shape

            geoms.append(shape(g))
        else:
            geoms.append(None)
    df = pd.DataFrame(rows)
    df["geometry"] = geoms
    gdf = gpd.GeoDataFrame(df, geometry="geometry", crs=4326)
    return gdf[gdf.geometry.notna()]


def _clip_to_bbox(gdf: gpd.GeoDataFrame, bbox: tuple[float, float, float, float]) -> gpd.GeoDataFrame:
    b = box(*bbox)
    poly = gpd.GeoSeries([b], crs=4326)
    return gdf[gdf.intersects(b)].copy()


def _merged_line(gdf: gpd.GeoDataFrame) -> Any:
    if gdf.empty:
        return None
    u = unary_union(gdf.geometry.tolist())
    merged = linemerge(u)
    return merged


def _point_from_intersection(geom: Any) -> Optional[Point]:
    if geom is None or geom.is_empty:
        return None
    if isinstance(geom, Point):
        return geom
    if hasattr(geom, "geoms"):
        for g in geom.geoms:
            p = _point_from_intersection(g)
            if p is not None:
                return p
    return None


def _intersect_lines(a: Any, b: Any) -> Optional[Point]:
    if a is None or b is None or a.is_empty or b.is_empty:
        return None
    inter = a.intersection(b)
    p = _point_from_intersection(inter)
    if p is not None:
        return p
    # Tiny buffer to catch near-misses between digitized centerlines
    buf = 1e-5  # ~1m in degrees
    inter = a.buffer(buf).intersection(b.buffer(buf))
    return _point_from_intersection(inter)


def build_bowery_houston_6th_canal_polygon(
    *,
    clip_bbox: tuple[float, float, float, float] = CLIP_BBOX_WGS84,
    app_token: str | None = None,
) -> Polygon:
    """
    Return a Polygon whose boundary follows CSCL centerlines for:
    6th Ave (west), Houston (north), Bowery (east), Canal (south).
    """
    west_g = _clip_to_bbox(
        _rows_to_gdf(_fetch_street_segments(STREETS["west"], app_token)),
        clip_bbox,
    )
    north_g = _clip_to_bbox(
        _rows_to_gdf(_fetch_street_segments(STREETS["north"], app_token)),
        clip_bbox,
    )
    east_g = _clip_to_bbox(
        _rows_to_gdf(_fetch_street_segments(STREETS["east"], app_token)),
        clip_bbox,
    )
    south_g = _clip_to_bbox(
        _rows_to_gdf(_fetch_street_segments(STREETS["south"], app_token)),
        clip_bbox,
    )

    # Exclude Holland Tunnel etc. on Canal — keep segments inside clip that are clearly "CANAL ST"
    south_g = south_g[
        ~south_g["full_street_name"].str.contains("HOLLAND", case=False, na=False)
    ]

    L_w = _merged_line(west_g)
    L_n = _merged_line(north_g)
    L_e = _merged_line(east_g)
    L_s = _merged_line(south_g)

    for name, L in (("west", L_w), ("north", L_n), ("east", L_e), ("south", L_s)):
        if L is None or L.is_empty:
            raise RuntimeError(f"No centerline geometry for {name} boundary")

    # Corners: NW = Houston ∩ 6th, NE = Houston ∩ Bowery, SE = Bowery ∩ Canal, SW = Canal ∩ 6th
    nw = _intersect_lines(L_n, L_w)
    ne = _intersect_lines(L_n, L_e)
    se = _intersect_lines(L_s, L_e)
    sw = _intersect_lines(L_s, L_w)

    corners = [nw, ne, se, sw]
    if any(c is None for c in corners):
        missing = [k for k, v in zip(("nw", "ne", "se", "sw"), corners) if v is None]
        raise RuntimeError(f"Could not compute street intersections: missing {missing}")

    # Ring: SW -> SE -> NE -> NW -> SW (CCW exterior)
    ring = Polygon(
        [
            (sw.x, sw.y),
            (se.x, se.y),
            (ne.x, ne.y),
            (nw.x, nw.y),
            (sw.x, sw.y),
        ]
    )
    if not ring.is_valid:
        ring = ring.buffer(0)
    return ring


def save_study_area_geojson(path: Path, polygon: Polygon, *, source_note: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fc = {
        "type": "FeatureCollection",
        "name": "study_area_bowery_houston_6th_canal",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": [
            {
                "type": "Feature",
                "properties": {"description": source_note},
                "geometry": mapping(polygon),
            }
        ],
    }
    path.write_text(json.dumps(fc, indent=2))


