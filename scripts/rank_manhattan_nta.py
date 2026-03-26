#!/usr/bin/env python3
"""
Aggregate Manhattan census-tract map metrics to **2020 Neighborhood Tabulation Areas (NTAs)**.

NTAs are NYC DCP / Census “neighborhood-scale” units (official boundaries), not informal labels.
Source: NYC Open Data ``9nt8-h7nd`` (GeoJSON), filtered to ``boroname = Manhattan``.

Each tract is assigned to the **single NTA** with the **largest intersection area** (EPSG:2263),
then metrics are **area-weighted means** of tract values within that NTA. Ranks / percentiles among
**Manhattan NTAs only** are added for the combined index and the three borough tract percentiles.

Requires a tract GeoPackage from::

  python scripts/make_manhattan_maps.py --write-tract-metrics outputs/maps/manhattan_tract_metrics.gpkg

Usage:
  python scripts/rank_manhattan_nta.py
  python scripts/rank_manhattan_nta.py --tract-metrics path/to/tracts.gpkg --out-csv outputs/maps/mn_nta.csv
  python scripts/rank_manhattan_nta.py --out-map outputs/maps/07_combined_index_nta.png
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nycwalks.mapping import (  # noqa: E402
    add_study_area_outline,
    frame_lonlat_map_north_up,
    percentile_rank,
)
from nycwalks.study_area import load_study_area_polygon, study_area_bbox_wgs84  # noqa: E402

NTA_GEOJSON = "https://data.cityofnewyork.us/resource/9nt8-h7nd.geojson"


def _weighted_avg(df: pd.DataFrame, col: str) -> float:
    x = pd.to_numeric(df[col], errors="coerce")
    w = pd.to_numeric(df["area_km2"], errors="coerce").fillna(0.0)
    ok = x.notna() & (w > 0)
    if not ok.any():
        return float("nan")
    return float(np.average(x[ok].to_numpy(dtype=float), weights=w[ok].to_numpy(dtype=float)))


def load_manhattan_nta() -> gpd.GeoDataFrame:
    r = requests.get(
        NTA_GEOJSON,
        params={"$where": "boroname = 'Manhattan'"},
        timeout=180,
    )
    r.raise_for_status()
    gdf = gpd.read_file(io.BytesIO(r.content))
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    return gdf


def assign_tract_to_nta(
    tracts: gpd.GeoDataFrame,
    nta: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    """Return tracts with ``nta2020`` and ``nta2020_name`` from dominant overlap."""
    left = tracts[
        ["geoid", "area_km2", "geometry"]
    ].copy()
    right = nta[["nta2020", "ntaname", "geometry"]].rename(
        columns={"ntaname": "nta2020_name"},
    )
    inter = gpd.overlay(left, right, how="intersection", keep_geom_type=False)
    inter["piece_km2"] = inter.geometry.to_crs(2263).area * (0.3048**2) / 1_000_000.0
    inter = inter.sort_values(["geoid", "piece_km2"], ascending=[True, False])
    pick = inter.drop_duplicates("geoid", keep="first")[["geoid", "nta2020", "nta2020_name"]]
    out = tracts.merge(pick, on="geoid", how="left")
    return out


def plot_nta_map(
    nta_poly: gpd.GeoDataFrame,
    column: str,
    title: str,
    subtitle: str,
    outfile: Path,
    *,
    study_geom=None,
) -> None:
    fig, ax = plt.subplots(figsize=(7.5, 11))
    nta_poly.plot(
        column=column,
        ax=ax,
        legend=True,
        cmap="Greys",
        edgecolor="white",
        linewidth=0.25,
        legend_kwds={
            "label": column,
            "shrink": 0.45,
            "location": "right",
        },
        missing_kwds={"color": "lightgrey", "label": "No data"},
    )
    if study_geom is not None:
        add_study_area_outline(ax, study_geom)
    ax.set_title(title + "\n" + subtitle, fontsize=11)
    ax.axis("off")
    b = tuple(nta_poly.total_bounds)
    if study_geom is not None:
        sb = study_geom.bounds
        b = (min(b[0], sb[0]), min(b[1], sb[1]), max(b[2], sb[2]), max(b[3], sb[3]))
    else:
        bb = study_area_bbox_wgs84()
        b = (min(b[0], bb[0]), min(b[1], bb[1]), max(b[2], bb[2]), max(b[3], bb[3]))
    frame_lonlat_map_north_up(ax, b)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(outfile, dpi=200, bbox_inches="tight")
    plt.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="Rank Manhattan NTAs from tract map metrics")
    ap.add_argument(
        "--tract-metrics",
        type=Path,
        default=ROOT / "outputs" / "maps" / "manhattan_tract_metrics.gpkg",
        help="GeoPackage written by make_manhattan_maps --write-tract-metrics",
    )
    ap.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "outputs" / "maps" / "manhattan_nta_rankings.csv",
    )
    ap.add_argument(
        "--out-map",
        type=Path,
        default=None,
        help="Optional choropleth PNG (NTA combined index percentile, Greys)",
    )
    args = ap.parse_args()

    tpath = args.tract_metrics
    if not tpath.is_file():
        raise SystemExit(
            f"Tract metrics not found: {tpath}\n"
            "Run: python scripts/make_manhattan_maps.py "
            f"--write-tract-metrics {tpath}"
        )

    print("Loading tract metrics…")
    tracts = gpd.read_file(tpath)
    if tracts.crs is None:
        tracts = tracts.set_crs(4326)

    print("Fetching Manhattan NTA boundaries (NYC Open Data 9nt8-h7nd)…")
    nta = load_manhattan_nta()

    print("Assigning tracts to NTAs (largest planar overlap)…")
    joined = assign_tract_to_nta(tracts, nta)
    unassigned = joined["nta2020"].isna().sum()
    if unassigned:
        print(f"  WARNING: {unassigned} tract(s) without NTA overlap (excluded from NTA table).")

    use = joined[joined["nta2020"].notna()].copy()
    metric_cols = [
        "combined_idx",
        "ped_pctile",
        "crash_pctile",
        "res_pctile",
        "combined_ped_pctile",
        "combined_crash_leg_pctile",
    ]
    for _opt in (
        "dist_nearest_subway_m",
        "subway_access_pctile",
        "nearest_subway_ridership_sum",
        "subway_nearest_ridership_pctile",
        "transit_access_ridership_pctile",
    ):
        if _opt in use.columns:
            metric_cols.append(_opt)
    for _nw in sorted(c for c in use.columns if c.startswith("nw_exp_")):
        metric_cols.append(_nw)
    rows: list[dict] = []
    for (nid, nname), g in use.groupby(["nta2020", "nta2020_name"]):
        row: dict = {
            "nta2020": nid,
            "ntaname": nname,
            "n_tracts": int(g["geoid"].nunique()),
            "area_km2": float(pd.to_numeric(g["area_km2"], errors="coerce").fillna(0).sum()),
        }
        for c in metric_cols:
            row[f"{c}_awm"] = _weighted_avg(g, c)
        rows.append(row)

    out = pd.DataFrame(rows)
    out["combined_idx_nta_pctile"] = percentile_rank(out["combined_idx_awm"])
    out["ped_pctile_nta_pctile"] = percentile_rank(out["ped_pctile_awm"])
    out["crash_pctile_nta_pctile"] = percentile_rank(out["crash_pctile_awm"])
    out["res_pctile_nta_pctile"] = percentile_rank(out["res_pctile_awm"])
    if "subway_access_pctile_awm" in out.columns:
        out["subway_access_pctile_nta_pctile"] = percentile_rank(
            out["subway_access_pctile_awm"],
        )
    if "dist_nearest_subway_m_awm" in out.columns:
        d = pd.to_numeric(out["dist_nearest_subway_m_awm"], errors="coerce")
        if d.notna().any():
            out["dist_subway_closer_nta_pctile"] = percentile_rank(d.max() - d)
    if "transit_access_ridership_pctile_awm" in out.columns:
        out["transit_access_ridership_nta_pctile"] = percentile_rank(
            out["transit_access_ridership_pctile_awm"],
        )
    out = out.sort_values("combined_idx_awm", ascending=False, na_position="last")

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out_csv, index=False)
    print(f"Wrote {args.out_csv} ({len(out)} NTAs)")

    if args.out_map is not None:
        try:
            study_poly = load_study_area_polygon()
        except FileNotFoundError:
            study_poly = None
        nta_m = nta.merge(
            out[["nta2020", "combined_idx_nta_pctile"]],
            on="nta2020",
            how="left",
        )
        plot_nta_map(
            nta_m,
            "combined_idx_nta_pctile",
            "Combined index — Manhattan NTA percentile",
            "Tract metrics area-weighted within 2020 NTAs; percentile among Manhattan NTAs (dark = high).",
            args.out_map,
            study_geom=study_poly,
        )
        print(f"Wrote {args.out_map}")


if __name__ == "__main__":
    main()
