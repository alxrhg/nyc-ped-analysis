"""Thesis study area: quadrilateral bounded by NYC street centerlines (CSCL)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Tuple

import geopandas as gpd
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

_REPO_ROOT = Path(__file__).resolve().parents[1]
STUDY_AREA_GEOJSON = _REPO_ROOT / "data" / "mit" / "study_area_bowery_houston_6th_canal.geojson"

# Fallback envelope if GeoJSON is missing (coarse rectangle)
_FALLBACK_BBOX_WGS84: Tuple[float, float, float, float] = (
    -74.012,
    40.7175,
    -73.992,
    40.7275,
)


@lru_cache(maxsize=1)
def load_study_area_polygon() -> Polygon:
    """
    Polygon bounded by centerlines of:
    Avenue of the Americas (west), Houston St (north), Bowery (east), Canal St (south).

    Built from NYC Street Centerline (Open Data `inkn-q76z`); see `study_area_polygon.py`.
    """
    if not STUDY_AREA_GEOJSON.is_file():
        raise FileNotFoundError(
            f"Missing {STUDY_AREA_GEOJSON}. Run: python scripts/build_study_area_polygon.py"
        )
    gdf = gpd.read_file(STUDY_AREA_GEOJSON)
    geom = unary_union(gdf.geometry)
    if isinstance(geom, Polygon):
        return geom
    polys = [g for g in getattr(geom, "geoms", [geom]) if isinstance(g, Polygon)]
    if not polys:
        raise ValueError("Study area file contains no polygon")
    return max(polys, key=lambda p: p.area)


def study_area_bbox_wgs84() -> Tuple[float, float, float, float]:
    """Axis-aligned envelope (min_lon, min_lat, max_lon, max_lat) for API filters."""
    try:
        b = load_study_area_polygon().bounds
        return (b[0], b[1], b[2], b[3])
    except (FileNotFoundError, ValueError):
        return _FALLBACK_BBOX_WGS84


try:
    HOUSTON_CANAL_BBOX_WGS84: Tuple[float, float, float, float] = tuple(
        load_study_area_polygon().bounds
    )
except (FileNotFoundError, ValueError):
    HOUSTON_CANAL_BBOX_WGS84 = _FALLBACK_BBOX_WGS84


def bbox_polygon_wgs84(
    bbox: Tuple[float, float, float, float] | None = None,
):
    """Return a shapely box; default uses study-area envelope."""
    if bbox is None:
        bbox = study_area_bbox_wgs84()
    min_lon, min_lat, max_lon, max_lat = bbox
    return box(min_lon, min_lat, max_lon, max_lat)


def clip_gdf_to_bbox(
    gdf: gpd.GeoDataFrame,
    bbox: Tuple[float, float, float, float] | None = None,
) -> gpd.GeoDataFrame:
    """Clip a GeoDataFrame to a WGS84 axis-aligned bbox (default: study envelope)."""
    if bbox is None:
        bbox = study_area_bbox_wgs84()
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    b = box(*bbox)
    return gdf[gdf.intersects(b)].copy()


def clip_gdf_to_study_area(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Clip to the quadrilateral study polygon (6th Ave – Houston – Bowery – Canal)."""
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)
    poly = load_study_area_polygon()
    return gdf[gdf.intersects(poly)].copy()
