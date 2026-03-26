#!/usr/bin/env python3
"""
3D prism / bar map for Manhattan census tracts.

Reads tract polygons + attributes (e.g. from ``make_manhattan_maps.py --write-tract-metrics``)
and saves a PNG of 3D bars: footprint ~ tract size at centroid, height and color from a column.

Usage:
  python scripts/plot_tract_3d_bars.py
  python scripts/plot_tract_3d_bars.py --column transit_access_ridership_pctile
  python scripts/plot_tract_3d_bars.py --input outputs/maps/manhattan_tract_metrics.gpkg \\
      --out outputs/maps/3d_combined_idx.png --column combined_idx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import geopandas as gpd  # noqa: E402

from nycwalks.plot_3d_tract_bars import plot_tract_metric_3d_bars  # noqa: E402
from nycwalks.study_area import load_study_area_polygon  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="3D tract bar / prism map (matplotlib)")
    ap.add_argument(
        "--input",
        type=Path,
        default=ROOT / "outputs" / "maps" / "manhattan_tract_metrics.gpkg",
        help="GeoPackage (or GeoJSON) with tract geometry + numeric column",
    )
    ap.add_argument(
        "--column",
        type=str,
        default="combined_idx",
        help="Numeric field to drive bar height and color",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output PNG (default: outputs/maps/3d_<column>.png)",
    )
    ap.add_argument("--max-height-m", type=float, default=900.0, help="Bar height at max value (meters)")
    ap.add_argument(
        "--footprint-scale",
        type=float,
        default=0.42,
        help="Square side = scale × sqrt(tract area m²), clamped",
    )
    ap.add_argument("--cmap", type=str, default="Greys", help="Matplotlib colormap name")
    ap.add_argument("--elev", type=float, default=28.0, help="3D view elevation")
    ap.add_argument("--azim", type=float, default=-65.0, help="3D view azimuth (degrees)")
    ap.add_argument("--no-study-outline", action="store_true", help="Do not draw study polygon at z=0")
    args = ap.parse_args()

    inp = args.input
    if not inp.is_file():
        raise SystemExit(
            f"Input not found: {inp}\n"
            "Run: python scripts/make_manhattan_maps.py --write-tract-metrics "
            f"{inp}"
        )

    gdf = gpd.read_file(inp)
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)

    out = args.out
    if out is None:
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in args.column)
        out = ROOT / "outputs" / "maps" / f"3d_{safe}.png"

    study = None
    if not args.no_study_outline:
        try:
            study = load_study_area_polygon()
        except FileNotFoundError:
            pass

    plot_tract_metric_3d_bars(
        gdf,
        args.column,
        out,
        study_geom_wgs84=study,
        max_height_m=float(args.max_height_m),
        footprint_scale=float(args.footprint_scale),
        cmap=args.cmap,
        elev=float(args.elev),
        azim=float(args.azim),
    )
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
