"""Choropleth helpers and NYCWalks column detection for thesis maps."""

from __future__ import annotations

from typing import Optional, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle
from shapely.geometry.base import BaseGeometry


def tract_area_km2(tracts_wgs84: gpd.GeoDataFrame) -> pd.Series:
    """Planar area in km² using NY State Plane ft² (EPSG:2263)."""
    t = tracts_wgs84.to_crs(2263)
    ft2 = t.geometry.area
    return pd.Series(ft2 * (0.3048**2) / 1_000_000.0, index=tracts_wgs84.index)


# MIT NYCWalks network file (GeoJSON/SHP) — modeled peak-period volumes (ped/h) + observed count columns.
NYCWALKS_VOLUME_COLUMNS_PREFERRED: tuple[str, ...] = (
    "predwkndAM",
    "predwkndMD",
    "predwkndPM",
    "predwkdyAM",
    "predwkdyMD",
    "predwkdyPM",
)


def resolve_pedestrian_volume_column(
    gdf: gpd.GeoDataFrame,
    override: Optional[str] = None,
) -> Optional[str]:
    """Pick the pedestrian volume column; MIT files use predwkndAM / predwkdyAM, etc."""
    if override:
        if override not in gdf.columns:
            raise ValueError(f"Column {override!r} not in GeoDataFrame")
        return override
    for name in NYCWALKS_VOLUME_COLUMNS_PREFERRED:
        if name in gdf.columns and pd.api.types.is_numeric_dtype(gdf[name]):
            return name
    return infer_pedestrian_volume_column(gdf)


def infer_pedestrian_volume_column(gdf: gpd.GeoDataFrame) -> Optional[str]:
    """Heuristic fallback if MIT column names are absent."""
    skip = {"geometry", "id", "OBJECTID", "id"}
    prefs = ("peak", "vol", "flow", "ped", "tot", "est", "wknd", "wkdy", "pred", "am", "pm")
    candidates: list[str] = []
    for c in gdf.columns:
        if c in skip:
            continue
        if not pd.api.types.is_numeric_dtype(gdf[c]):
            continue
        cl = c.lower()
        if any(p in cl for p in prefs):
            candidates.append(c)
    if candidates:
        return candidates[0]
    for c in gdf.columns:
        if c in skip or c.lower() == "fid":
            continue
        if pd.api.types.is_numeric_dtype(gdf[c]):
            return c
    return None


def add_study_area_outline(
    ax: Axes,
    geom: BaseGeometry,
    *,
    edgecolor: str = "crimson",
    linewidth: float = 2.0,
    linestyle: str = "-",
) -> None:
    """Draw study-area polygon (or any lon/lat geometry) on a WGS84 map axis."""
    gpd.GeoSeries([geom], crs=4326).plot(
        ax=ax,
        facecolor="none",
        edgecolor=edgecolor,
        linewidth=linewidth,
        linestyle=linestyle,
        zorder=20,
    )


def add_wgs84_bbox_outline(
    ax: Axes,
    bbox: Tuple[float, float, float, float],
    *,
    edgecolor: str = "crimson",
    linewidth: float = 2.0,
    linestyle: str = "-",
) -> None:
    """Draw axis-aligned rectangle in lon/lat (legacy; prefer add_study_area_outline)."""
    min_lon, min_lat, max_lon, max_lat = bbox
    rect = Rectangle(
        (min_lon, min_lat),
        max_lon - min_lon,
        max_lat - min_lat,
        fill=False,
        edgecolor=edgecolor,
        linewidth=linewidth,
        linestyle=linestyle,
        zorder=20,
    )
    ax.add_patch(rect)


def frame_lonlat_map_north_up(
    ax: Axes,
    bounds: Tuple[float, float, float, float],
    *,
    margin_frac: float = 0.02,
) -> None:
    """
    Typical NYC-style map: **north up**, Manhattan reads **vertical** (N–S along latitude).

    Uses latitude ``lat0`` at the frame center so one degree of longitude is drawn
    narrower than one degree of latitude (``aspect = 1/cos(lat0)``), matching ground
    distances better than raw ``aspect='equal'`` on lon/lat axes.
    """
    minx, miny, maxx, maxy = bounds
    dx = maxx - minx
    dy = maxy - miny
    if dx <= 0 or dy <= 0:
        return
    px = dx * margin_frac + 1e-5
    py = dy * margin_frac + 1e-5
    ax.set_xlim(minx - px, maxx + px)
    ax.set_ylim(miny - py, maxy + py)
    lat0 = (miny + maxy) / 2.0
    ax.set_aspect(1.0 / np.cos(np.radians(lat0)))


def percentile_rank(series: pd.Series) -> pd.Series:
    """0–100 percentile rank (higher = more intense)."""
    s = pd.to_numeric(series, errors="coerce")
    valid = s.notna() & (s >= 0)
    if not valid.any():
        return pd.Series(np.nan, index=series.index)
    ranks = s[valid].rank(pct=True) * 100.0
    out = pd.Series(np.nan, index=series.index)
    out.loc[valid] = ranks
    return out


def percentile_rank_within(series: pd.Series, mask: pd.Series) -> pd.Series:
    """
    0–100 percentile rank using **only** rows where ``mask`` is True; others NaN.

    Used to normalize map inputs within a geographic subset (e.g. south of 59th St)
    without changing borough-wide maps (1–3).
    """
    s = pd.to_numeric(series, errors="coerce")
    m = mask.fillna(False).astype(bool) & s.notna() & (s >= 0)
    out = pd.Series(np.nan, index=series.index, dtype=float)
    if not m.any():
        return out
    ranks = s[m].rank(pct=True) * 100.0
    out.loc[m] = ranks
    return out


def combined_tract_index(
    ped_pctile: pd.Series,
    crash_pctile: pd.Series,
    res_term: pd.Series,
    *,
    method: str = "mean",
    weights: Optional[Tuple[float, float, float]] = None,
) -> pd.Series:
    """
    Single 0–100-ish index from pedestrian and crash **borough percentiles** plus a
    residential term on a 0–100 scale.

    The third series is usually **raw** PLUTO residential share ``s`` (0–100) or its
    borough percentile; it can be dropped by setting residential weight to 0.

    * ``mean``: ``I = w_p P + w_c C + w_r r`` with ``weights`` ``(w_p, w_c, w_r)``
      normalized to sum 1. If ``w_r`` is 0 after normalization, ``r`` is omitted so
      tracts need only valid ``P`` and ``C`` (pedestrian + crash only).
    * ``geometric``: if residential weight is 0, ``I = 100 * sqrt((P/100)(C/100))``;
      else ``I = 100 * (P/100 * C/100 * r/100)^(1/3)``. Weights normalized to read ``w_r``.
    """
    p = pd.to_numeric(ped_pctile, errors="coerce")
    c = pd.to_numeric(crash_pctile, errors="coerce")
    r = pd.to_numeric(res_term, errors="coerce")
    out = pd.Series(np.nan, index=ped_pctile.index)
    wr_geom = 1.0 / 3.0
    if weights is not None:
        wp0, wc0, wr0 = weights
        s0 = float(wp0 + wc0 + wr0)
        if s0 > 0:
            wr_geom = wr0 / s0
    if method == "mean":
        if weights is None:
            wp, wc, wr = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
        else:
            wp, wc, wr = weights
            s = float(wp + wc + wr)
            if s <= 0:
                raise ValueError("combined weights must sum to a positive value")
            wp, wc, wr = wp / s, wc / s, wr / s
        ok_pc = p.notna() & c.notna()
        if wr <= 1e-12:
            ok = ok_pc
            out.loc[ok] = wp * p[ok] + wc * c[ok]
        else:
            ok = ok_pc & r.notna()
            out.loc[ok] = wp * p[ok] + wc * c[ok] + wr * r[ok]
    elif method == "geometric":
        if wr_geom <= 1e-12:
            ok_geo = p.notna() & c.notna()
            out.loc[ok_geo] = 100.0 * np.sqrt((p[ok_geo] / 100.0) * (c[ok_geo] / 100.0))
        else:
            ok_geo = p.notna() & c.notna() & r.notna()
            out.loc[ok_geo] = (
                (p[ok_geo] / 100.0) * (c[ok_geo] / 100.0) * (r[ok_geo] / 100.0)
            ) ** (1.0 / 3.0) * 100.0
    else:
        raise ValueError(f"method must be 'mean' or 'geometric', got {method!r}")
    return out
