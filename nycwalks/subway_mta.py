"""MTA subway stop locations, ridership, and tract-level distance helpers (NY Open Data)."""

from __future__ import annotations

import io
from datetime import datetime

import geopandas as gpd
import numpy as np
import pandas as pd
import requests

from nycwalks.mapping import percentile_rank

# MTA Subway Stations — tabular + point geometry (all NYC boroughs).
# GeoJSON works on data.ny.gov (not on data.cityofnewyork.us for this dataset).
MTA_SUBWAY_STATIONS_GEOJSON = "https://data.ny.gov/resource/39hk-dx4f.geojson"
# Station complex × month ridership (join ``station_complex_id`` ↔ stops ``complex_id``).
MTA_MONTHLY_RIDERSHIP_JSON = "https://data.ny.gov/resource/ak4z-sape.json"


def fetch_mta_subway_stations_gdf(*, borough: str | None = "M") -> gpd.GeoDataFrame:
    """
    Load MTA subway **station stops** as points.

    ``borough`` uses MTA codes: ``M`` = Manhattan, ``Bk``, ``Bx``, ``Q``, ``SI``.
    Pass ``None`` for all boroughs.
    """
    params: dict[str, str] = {"$limit": "5000"}
    if borough is not None:
        params["$where"] = f"borough = '{borough}'"
    r = requests.get(MTA_SUBWAY_STATIONS_GEOJSON, params=params, timeout=120)
    r.raise_for_status()
    gdf = gpd.read_file(io.BytesIO(r.content))
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    return gdf


def _month_ge_iso(since_day: str) -> str:
    """Normalize ``YYYY-MM-DD`` to a SoQL-friendly timestamp for ``month`` columns."""
    d = datetime.strptime(since_day[:10], "%Y-%m-%d")
    return d.strftime("%Y-%m-%dT00:00:00.000")


def fetch_mta_manhattan_ridership_sum_by_complex(
    *,
    since_month_day: str = "2024-01-01",
    page_limit: int = 50_000,
) -> pd.Series:
    """
    Sum **ridership** (entries) across all monthly rows per ``station_complex_id`` for
    **Manhattan** complexes, for ``month >= since_month_day``.

    Returns a Series indexed by **string** ``complex_id`` compatible with stop polygons
    (``39hk-dx4f`` ``complex_id``).
    """
    since_ts = _month_ge_iso(since_month_day)
    where = f"borough = 'Manhattan' AND month >= '{since_ts}'"
    offset = 0
    rows: list[dict] = []
    while True:
        r = requests.get(
            MTA_MONTHLY_RIDERSHIP_JSON,
            params={
                "$where": where,
                "$order": "month ASC",
                "$limit": str(page_limit),
                "$offset": str(offset),
            },
            timeout=180,
        )
        r.raise_for_status()
        batch = r.json()
        if isinstance(batch, dict) and batch.get("error"):
            raise ValueError(batch.get("message", str(batch)))
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_limit:
            break
        offset += page_limit
    if not rows:
        return pd.Series(dtype=float)
    df = pd.DataFrame(rows)
    df["ridership"] = pd.to_numeric(df["ridership"], errors="coerce").fillna(0.0)
    df["_complex_key"] = df["station_complex_id"].astype(str)
    g = df.groupby("_complex_key", as_index=True)["ridership"].sum()
    return g.astype(float)


def enrich_stations_with_ridership_sum(
    stations_wgs84: gpd.GeoDataFrame,
    ridership_by_complex: pd.Series,
    *,
    column_name: str = "ridership_sum_window",
) -> gpd.GeoDataFrame:
    """Map ``complex_id`` on each stop to summed ridership for that station complex."""
    out = stations_wgs84.copy()
    if "complex_id" not in out.columns:
        raise KeyError("stations GeoDataFrame must have column 'complex_id'")
    key = out["complex_id"].astype(str)
    mp = ridership_by_complex.astype(float)
    mp.index = mp.index.astype(str)
    out[column_name] = key.map(mp.to_dict())
    return out


def tract_nearest_subway_table(
    tracts_wgs84: gpd.GeoDataFrame,
    stations_wgs84: gpd.GeoDataFrame,
    *,
    geoid_col: str = "geoid",
    ridership_col: str = "ridership_sum_window",
) -> pd.DataFrame:
    """
    For each tract polygon: nearest MTA stop (EPSG:2263 ``sjoin_nearest``), distance in **m**,
    stop name, ``complex_id``, and optional summed ridership at that complex.
    """
    if geoid_col not in tracts_wgs84.columns:
        raise KeyError(f"Missing column {geoid_col!r} on tracts")
    for need in ("stop_name", "complex_id"):
        if need not in stations_wgs84.columns:
            raise KeyError(f"stations GeoDataFrame must have column {need!r}")
    t = tracts_wgs84[[geoid_col, "geometry"]].to_crs(2263)
    scols = ["geometry", "stop_name", "complex_id"]
    if ridership_col in stations_wgs84.columns:
        scols.append(ridership_col)
    s = stations_wgs84[scols].to_crs(2263)
    j = t.sjoin_nearest(s, how="left", distance_col="_d_ft")
    j = j.sort_values("_d_ft").drop_duplicates(subset=[geoid_col], keep="first")
    dist_m = j["_d_ft"].astype(float) * 0.3048
    gid = tracts_wgs84[geoid_col]
    d_dist = dict(zip(j[geoid_col], dist_m))
    d_name = dict(zip(j[geoid_col], j["stop_name"]))
    d_cpx = dict(zip(j[geoid_col], j["complex_id"].astype(str)))
    out = pd.DataFrame(
        {
            "dist_nearest_subway_m": gid.map(d_dist).astype(float),
            "nearest_stop_name": gid.map(d_name),
            "nearest_complex_id": gid.map(d_cpx),
        },
        index=tracts_wgs84.index,
    )
    if ridership_col in j.columns:
        d_r = dict(zip(j[geoid_col], pd.to_numeric(j[ridership_col], errors="coerce")))
        out["nearest_subway_ridership_sum"] = gid.map(d_r).astype(float)
    else:
        out["nearest_subway_ridership_sum"] = np.nan
    return out


def tract_nearest_subway_distance_m(
    tracts_wgs84: gpd.GeoDataFrame,
    stations_wgs84: gpd.GeoDataFrame,
    *,
    geoid_col: str = "geoid",
) -> pd.Series:
    """
    For each tract polygon, **planar** distance in **meters** (EPSG:2263) to the nearest
    station point, then convert using **US survey feet × 0.3048** (NYC State Plane).

    Distance is the standard GEOS minimum distance (0 if a stop lies inside the tract).
    Returns a float Series aligned to ``tracts_wgs84.index`` (NaN if join fails).
    """
    return tract_nearest_subway_table(
        tracts_wgs84,
        stations_wgs84,
        geoid_col=geoid_col,
    )["dist_nearest_subway_m"]


def subway_access_percentile_from_distance_m(dist_m: pd.Series) -> pd.Series:
    """
    Borough-style 0–100 percentile where **higher = closer** to a station (better access).

    Uses ``max(d) - d`` so the rank satisfies ``percentile_rank``'s non-negative convention.
    """
    d = pd.to_numeric(dist_m, errors="coerce")
    if not d.notna().any():
        return pd.Series(np.nan, index=dist_m.index)
    hi = float(d.max())
    score = hi - d
    return percentile_rank(score)


def subway_nearest_ridership_pctile(ridership_sum: pd.Series) -> pd.Series:
    """
    Borough percentile of **log1p(total ridership)** at the **nearest** station complex
    (higher = busier hub next door).
    """
    r = pd.to_numeric(ridership_sum, errors="coerce")
    if not r.notna().any():
        return pd.Series(np.nan, index=ridership_sum.index)
    return percentile_rank(np.log1p(r.clip(lower=0)))


def transit_access_ridership_pctile(
    ridership_sum: pd.Series,
    dist_m: pd.Series,
    *,
    dist_buffer_m: float = 50.0,
) -> pd.Series:
    """
    Borough percentile of a simple **gravity-style** score:

    ``log1p(R) / (d + buffer)``

    where ``R`` is summed ridership at the nearest complex and ``d`` is planar distance (m).
    Higher = closer to a **high-volume** complex (not just geometric proximity).
    """
    r = pd.to_numeric(ridership_sum, errors="coerce")
    d = pd.to_numeric(dist_m, errors="coerce")
    ok = r.notna() & d.notna() & (r >= 0) & (d >= 0)
    if not ok.any():
        return pd.Series(np.nan, index=ridership_sum.index)
    raw_s = pd.Series(np.nan, index=ridership_sum.index, dtype=float)
    raw_s.loc[ok] = np.log1p(r.loc[ok].astype(float).clip(lower=0)) / (
        d.loc[ok].astype(float) + float(dist_buffer_m)
    )
    return percentile_rank(raw_s)
