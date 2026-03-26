#!/usr/bin/env python3
"""
Tier 2 (local): Getis-Ord Gi* on a tract-level variable — hot-spot / cold-spot map.

Reads tract metrics from the GeoPackage written by::

  python scripts/make_manhattan_maps.py --write-tract-metrics outputs/maps/manhattan_tract_metrics.gpkg

Default: **K-nearest neighbors** (k=4) on tract centroids in EPSG:2263 — avoids island tracts
(e.g. water pockets) that break pure Queen adjacency. Optional ``--weights queen`` for shared-boundary
contiguity. Gi* summarizes where highs or lows cluster locally vs the borough — descriptive, not causal.

Outputs (default prefix outputs/maps/tier2_gi_star_):
  - *_{column}_zscores.png   choropleth of Gi* z-scores (diverging)
  - *_{column}_class.png     hot / cold / not significant (α=0.05, permutation p)
  - *_summary.txt             global Moran's I + Gi* counts
  - *_tracts.csv              per-tract z, p_sim, class

Optional: --column ksi_rate for harm-in-context hot spots instead of combined_idx.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nycwalks.mapping import add_study_area_outline, add_wgs84_bbox_outline, frame_lonlat_map_north_up
from nycwalks.study_area import load_study_area_polygon, study_area_bbox_wgs84


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--gpkg",
        type=Path,
        default=ROOT / "outputs" / "maps" / "manhattan_tract_metrics.gpkg",
        help="GeoPackage from make_manhattan_maps.py --write-tract-metrics",
    )
    ap.add_argument(
        "--column",
        default="combined_idx",
        help="Tract variable for Gi* (default: combined_idx). E.g. ksi_rate, ped_pctile.",
    )
    ap.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Two-sided significance level for hot/cold classification (permutation p).",
    )
    ap.add_argument(
        "--permutations",
        type=int,
        default=999,
        help="Random permutations for pseudo p-values.",
    )
    ap.add_argument(
        "--out-prefix",
        type=Path,
        default=ROOT / "outputs" / "maps" / "tier2_gi_star",
        help="Output path prefix (no extension).",
    )
    ap.add_argument(
        "--weights",
        choices=("knn", "queen"),
        default="knn",
        help="Spatial weights: knn (k=--k on centroids, default) or queen (shared edges).",
    )
    ap.add_argument(
        "--k",
        type=int,
        default=4,
        help="KNN neighbor count (default 4). Ignored for queen.",
    )
    args = ap.parse_args()

    try:
        from esda.getisord import G_Local
        from esda.moran import Moran
        from libpysal.weights import KNN, Queen
    except ImportError as e:
        raise SystemExit(
            "Install spatial stack: pip install libpysal esda\n"
            f"Import error: {e}"
        ) from e

    gpkg = args.gpkg.expanduser()
    if not gpkg.is_file():
        raise SystemExit(
            f"Missing {gpkg}. Run first:\n"
            "  python scripts/make_manhattan_maps.py --write-tract-metrics "
            f"{gpkg}"
        )

    gdf = gpd.read_file(gpkg)
    col = args.column
    if col not in gdf.columns:
        raise SystemExit(f"Column {col!r} not in GeoPackage. Available: {list(gdf.columns)}")

    gdf = gdf[gdf[col].notna()].copy()
    y = pd.to_numeric(gdf[col], errors="coerce").astype(float).values
    mask = np.isfinite(y)
    gdf = gdf.loc[mask].copy()
    y = y[mask]
    if len(y) < 5:
        raise SystemExit("Too few tracts with valid values for spatial stats.")

    gdf_proj = gdf.to_crs(2263)
    if args.weights == "knn":
        k = max(2, min(args.k, len(gdf_proj) - 1))
        w = KNN.from_dataframe(gdf_proj, k=k, use_index=True)
        w_desc = f"KNN k={k} (centroids, EPSG:2263)"
    else:
        w = Queen.from_dataframe(gdf_proj, use_index=True)
        w_desc = "Queen (shared edges, EPSG:2263)"
    w.transform = "R"

    moran = Moran(y, w, permutations=args.permutations)
    gi = G_Local(y, w, transform="R", permutations=args.permutations, star=True)

    # esda ≥2.5 exposes standardized scores as Zs (not z_scores)
    z = np.asarray(gi.Zs, dtype=float)
    p_sim = np.asarray(gi.p_sim, dtype=float)
    valid = np.isfinite(z) & np.isfinite(p_sim)
    hot = valid & (z > 0) & (p_sim < args.alpha)
    cold = valid & (z < 0) & (p_sim < args.alpha)
    ns = ~(hot | cold)

    gdf = gdf.copy()
    gdf["gi_z"] = z
    gdf["gi_p_sim"] = p_sim
    gdf["gi_class"] = np.where(hot, "hot_spot", np.where(cold, "cold_spot", "not_significant"))

    prefix = args.out_prefix.expanduser()
    prefix.parent.mkdir(parents=True, exist_ok=True)

    try:
        study_poly = load_study_area_polygon()
    except FileNotFoundError:
        study_poly = None

    summ_lines = [
        f"Weights: {w_desc}",
        f"Variable: {col}",
        f"Tracts (valid n): {len(y)}",
        f"Neighbors: min={w.min_neighbors} max={w.max_neighbors} mean={w.mean_neighbors:.2f}",
        "",
        f"Global Moran's I: {moran.I:.4f}  E(I): {moran.EI:.4f}  p_sim: {moran.p_sim:.4f}",
        f"Getis-Ord Gi* (local): hot spots (z>0, p<{args.alpha}): {int(hot.sum())}",
        f"                         cold spots (z<0, p<{args.alpha}): {int(cold.sum())}",
        f"                         not significant: {int(ns.sum())}",
        "",
        "Descriptive pattern summary only — not causal inference.",
    ]
    summ_path = Path(str(prefix) + f"_{col}_summary.txt")
    summ_path.write_text("\n".join(summ_lines) + "\n", encoding="utf-8")

    csv_path = Path(str(prefix) + f"_{col}_tracts.csv")
    out_tbl = gdf.drop(columns=["geometry"], errors="ignore")
    out_tbl.to_csv(csv_path, index=False)

    zmax = float(np.nanmax(np.abs(z[np.isfinite(z)]))) if np.isfinite(z).any() else 3.0
    zlim = max(3.0, zmax)

    # Map 1: z-scores (diverging)
    fig, ax = plt.subplots(figsize=(7.5, 11))
    gdf.plot(
        column="gi_z",
        ax=ax,
        legend=True,
        cmap="RdBu_r",
        vmin=-zlim,
        vmax=zlim,
        edgecolor="white",
        linewidth=0.2,
        legend_kwds={"label": "Gi* z-score", "shrink": 0.45, "location": "right"},
    )
    if study_poly is not None:
        add_study_area_outline(ax, study_poly)
    else:
        add_wgs84_bbox_outline(ax, study_area_bbox_wgs84())
    ax.set_title(
        f"Local Getis-Ord Gi* (z-scores)\n{col} — Manhattan census tracts",
        fontsize=11,
    )
    ax.axis("off")
    b = tuple(gdf.total_bounds)
    if study_poly is not None:
        sb = study_poly.bounds
        b = (min(b[0], sb[0]), min(b[1], sb[1]), max(b[2], sb[2]), max(b[3], sb[3]))
    frame_lonlat_map_north_up(ax, b)
    plt.tight_layout()
    z_path = Path(str(prefix) + f"_{col}_zscores.png")
    plt.savefig(z_path, dpi=200, bbox_inches="tight")
    plt.close()

    # Map 2: discrete classes (explicit colors — hot / cold / not significant)
    colors = {
        "hot_spot": "#b2182b",
        "cold_spot": "#2166ac",
        "not_significant": "#e0e0e0",
    }
    gdf = gdf.copy()
    gdf["_gi_color"] = gdf["gi_class"].map(colors)
    fig, ax = plt.subplots(figsize=(7.5, 11))
    gdf.plot(
        ax=ax,
        color=gdf["_gi_color"],
        edgecolor="white",
        linewidth=0.2,
    )
    leg = [
        Patch(facecolor=colors["hot_spot"], edgecolor="white", label="Hot spot (high cluster)"),
        Patch(facecolor=colors["not_significant"], edgecolor="white", label="Not significant"),
        Patch(facecolor=colors["cold_spot"], edgecolor="white", label="Cold spot (low cluster)"),
    ]
    ax.legend(handles=leg, title=f"Gi* perm. p < {args.alpha}", loc="lower left", framealpha=0.9)
    if study_poly is not None:
        add_study_area_outline(ax, study_poly)
    else:
        add_wgs84_bbox_outline(ax, study_area_bbox_wgs84())
    ax.set_title(
        f"Hot spots & cold spots ({col})\n"
        f"{w_desc} · permutation p · α={args.alpha}",
        fontsize=11,
    )
    ax.axis("off")
    frame_lonlat_map_north_up(ax, b)
    plt.tight_layout()
    cls_path = Path(str(prefix) + f"_{col}_class.png")
    plt.savefig(cls_path, dpi=200, bbox_inches="tight")
    plt.close()

    print("Wrote:")
    print(f"  {summ_path}")
    print(f"  {csv_path}")
    print(f"  {z_path}")
    print(f"  {cls_path}")


if __name__ == "__main__":
    main()
