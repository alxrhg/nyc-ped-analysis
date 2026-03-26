"""
Aggregate MIT NYCWalks **segment** volumes to census tracts.

* **Overlay (default):** one line–polygon intersection in EPSG:2263; each fragment contributes
  ``volume × fragment_length`` (uniform intensity along the segment). All peak / HME columns
  share the **same** geometry split (one overlay pass).
* **Centroid (legacy):** each segment’s **full** ``vol×total_length`` is assigned to the tract
  containing the segment centroid.
"""

from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.ops import unary_union

# MIT NYCWalks GeoJSON: six peak-period pedestrian volume estimates (ped/h).
NYCWALKS_PEAK_VOLUME_COLUMNS: tuple[str, ...] = (
    "predwkdyAM",
    "predwkdyMD",
    "predwkdyPM",
    "predwkndAM",
    "predwkndMD",
    "predwkndPM",
)


def discover_hme_purpose_columns(gdf: gpd.GeoDataFrame) -> list[str]:
    """Return sorted ``HME_*`` columns that can be coerced to numeric (trip-purpose components)."""
    out: list[str] = []
    for c in gdf.columns:
        if not c.startswith("HME_"):
            continue
        if pd.api.types.is_numeric_dtype(gdf[c]):
            out.append(c)
            continue
        coerced = pd.to_numeric(gdf[c], errors="coerce")
        if coerced.notna().sum() > max(30, int(len(gdf) * 0.05)):
            out.append(c)
    return sorted(out)


def _series_for_tracts(tracts_wgs84: gpd.GeoDataFrame, geoid_to_val: pd.Series) -> pd.Series:
    s = tracts_wgs84["geoid"].map(geoid_to_val)
    s = pd.to_numeric(s, errors="coerce").fillna(0.0).astype(float)
    s.index = tracts_wgs84.index
    return s


def aggregate_volume_to_tracts(
    seg: gpd.GeoDataFrame,
    tracts_wgs84: gpd.GeoDataFrame,
    volume_col: str,
    *,
    method: str = "overlay",
) -> pd.Series:
    """Per tract, sum ``volume × length`` for one column (uses the same core as the multi-column path)."""
    if volume_col not in seg.columns:
        raise KeyError(volume_col)
    df, _, _ = _build_table_core(seg, tracts_wgs84, [volume_col], method=method)
    return df[f"nw_exp_{volume_col}"]


def _build_table_core(
    seg: gpd.GeoDataFrame,
    tracts_wgs84: gpd.GeoDataFrame,
    volume_cols: list[str],
    *,
    method: str,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Internal: aggregate listed columns; returns (df with nw_exp_*, peak_used, hme_used)."""
    peak_used = [c for c in NYCWALKS_PEAK_VOLUME_COLUMNS if c in volume_cols]
    hme_used = [c for c in volume_cols if c.startswith("HME_")]
    if not volume_cols:
        empty = pd.DataFrame(index=tracts_wgs84.index)
        return empty, [], []

    tr = tracts_wgs84[["geoid", "geometry"]].to_crs(2263)
    hu = unary_union(tr.geometry.tolist())
    s = seg.to_crs(2263)
    s = s[s.intersects(hu)].copy()
    if s.empty:
        z = pd.DataFrame(
            {f"nw_exp_{c}": 0.0 for c in volume_cols},
            index=tracts_wgs84.index,
            dtype=float,
        )
        return z, peak_used, hme_used

    if method == "centroid":
        s_reset = s.reset_index(drop=True)
        s_reset["_sid"] = np.arange(len(s_reset), dtype=np.int64)
        if "Shape_Leng" in s_reset.columns:
            len_ft = pd.to_numeric(s_reset["Shape_Leng"], errors="coerce").fillna(0.0)
        else:
            len_ft = s_reset.geometry.length.astype(float)
        cen_gdf = gpd.GeoDataFrame(
            {"_sid": s_reset["_sid"].to_numpy()},
            geometry=s_reset.geometry.centroid,
            crs=s_reset.crs,
        ).to_crs(4326)
        tr_w = tracts_wgs84[["geoid", "geometry"]]
        j = cen_gdf.sjoin(tr_w, predicate="within", how="inner")
        out: dict[str, pd.Series] = {}
        sid_j = j["_sid"].to_numpy(dtype=np.int64)
        for col in volume_cols:
            v = pd.to_numeric(s_reset[col], errors="coerce").fillna(0.0).to_numpy(dtype=float)
            lf = len_ft.to_numpy(dtype=float)
            contrib = v[sid_j] * lf[sid_j]
            tmp = pd.DataFrame({"geoid": j["geoid"].to_numpy(), "c": contrib})
            gsum = tmp.groupby("geoid", as_index=True)["c"].sum()
            out[f"nw_exp_{col}"] = _series_for_tracts(tracts_wgs84, gsum)
        return pd.DataFrame(out, index=tracts_wgs84.index), peak_used, hme_used

    if method != "overlay":
        raise ValueError("method must be 'overlay' or 'centroid'")

    s_reset = s.reset_index(drop=True)
    s_reset["_sid"] = np.arange(len(s_reset), dtype=np.int64)
    left = s_reset[["_sid", "geometry"]]
    inter = gpd.overlay(left, tr, how="intersection", keep_geom_type=False)
    gt = inter.geometry.geom_type
    inter = inter.loc[gt.str.contains("Line", na=False)].copy()
    if inter.empty:
        z = pd.DataFrame(
            {f"nw_exp_{c}": 0.0 for c in volume_cols},
            index=tracts_wgs84.index,
            dtype=float,
        )
        return z, peak_used, hme_used

    inter["_len"] = inter.geometry.length.astype(float)
    sid = inter["_sid"].to_numpy(dtype=np.int64)
    out: dict[str, pd.Series] = {}
    for col in volume_cols:
        vn = pd.to_numeric(s_reset[col], errors="coerce").fillna(0.0).to_numpy(dtype=float)
        vv = vn[sid]
        contrib = vv * inter["_len"].to_numpy(dtype=float)
        tmp = pd.DataFrame({"geoid": inter["geoid"].to_numpy(), "c": contrib})
        gsum = tmp.groupby("geoid", as_index=True)["c"].sum()
        out[f"nw_exp_{col}"] = _series_for_tracts(tracts_wgs84, gsum)
    return pd.DataFrame(out, index=tracts_wgs84.index), peak_used, hme_used


def build_nycwalks_tract_exposure_table(
    seg: gpd.GeoDataFrame,
    tracts_wgs84: gpd.GeoDataFrame,
    *,
    method: str = "overlay",
    include_hme: bool = True,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """
    Build columns ``nw_exp_<col>`` for every available peak column and (optionally) ``HME_*``.

    Returns ``(df, peak_used, hme_used)`` with ``df`` aligned to ``tracts_wgs84.index``.
    """
    peak = [c for c in NYCWALKS_PEAK_VOLUME_COLUMNS if c in seg.columns]
    hme: list[str] = []
    if include_hme:
        hme = [c for c in discover_hme_purpose_columns(seg) if c in seg.columns]
    vol_cols = list(peak)
    if include_hme:
        vol_cols.extend(hme)
    return _build_table_core(seg, tracts_wgs84, vol_cols, method=method)


def composite_peak_exposure(df: pd.DataFrame, peak_cols: list[str]) -> pd.Series:
    """Mean across ``nw_exp_<peak>`` columns (only peaks present in ``df``)."""
    names = [f"nw_exp_{c}" for c in peak_cols if f"nw_exp_{c}" in df.columns]
    if not names:
        return pd.Series(0.0, index=df.index, dtype=float)
    sub = df[names].astype(float)
    return sub.mean(axis=1)
