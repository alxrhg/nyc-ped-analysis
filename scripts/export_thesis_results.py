#!/usr/bin/env python3
"""
Results-first bundle for the thesis: figures + tables + a RESULTS.md you write against.

Produces (default):
  outputs/maps/*.png                     — Manhattan choropleths (ped, crash, PLUTO res. share, combined) + study outline
  outputs/maps/study_area_tract_rankings.csv
  outputs/results/crashes_study_polygon.csv
  outputs/results/crash_summary_by_year.csv
  outputs/results/key_metrics.json
  outputs/results/RESULTS.md             — numbers + file index + suggested factual bullets

Usage:
  python scripts/export_thesis_results.py
  python scripts/export_thesis_results.py --since 2018-01-01 --fast   # smaller crash pull + skip full map pagination
  python scripts/export_thesis_results.py --skip-maps                  # only crash exports + RESULTS (maps must exist)

Requires network unless --skip-fetch (then expects prior crash CSV — not implemented; use full run).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nycwalks.crash_data import (  # noqa: E402
    fetch_crashes_in_bbox,
    filter_crashes_to_polygon,
)
from nycwalks.study_area import load_study_area_polygon, study_area_bbox_wgs84  # noqa: E402

RESULTS_DIR = ROOT / "outputs" / "results"
MAPS_DIR = ROOT / "outputs" / "maps"
TRACT_RANK = MAPS_DIR / "study_area_tract_rankings.csv"


def _safe_int(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s, errors="coerce").fillna(0).astype(int)


def run_maps(fast: bool) -> None:
    cmd = [sys.executable, str(ROOT / "scripts" / "make_manhattan_maps.py")]
    if fast:
        cmd.append("--fast")
    subprocess.run(cmd, check=True, cwd=str(ROOT))


def main() -> None:
    ap = argparse.ArgumentParser(description="Export thesis results bundle")
    ap.add_argument("--since", default="2019-01-01")
    ap.add_argument(
        "--fast",
        action="store_true",
        help="Smaller crash pagination + make_manhattan_maps --fast",
    )
    ap.add_argument("--skip-maps", action="store_true")
    args = ap.parse_args()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    poly = load_study_area_polygon()
    bbox = study_area_bbox_wgs84()

    print("Fetching crashes in study-area envelope…")
    env_df = fetch_crashes_in_bbox(args.since, bbox, fast=args.fast)
    print(f"  Envelope rows: {len(env_df):,}")

    gdf_in = filter_crashes_to_polygon(env_df, poly)
    print(f"  Inside CSCL quadrilateral: {len(gdf_in):,}")

    crash_out = RESULTS_DIR / "crashes_study_polygon.csv"
    gdf_in.drop(columns=["geometry"]).to_csv(crash_out, index=False)
    print(f"Wrote {crash_out}")

    ped_inj = _safe_int(gdf_in["number_of_pedestrians_injured"])
    ped_killed = _safe_int(gdf_in["number_of_pedestrians_killed"])
    with_ped_injury = (ped_inj > 0) | (ped_killed > 0)

    gdf_in = gdf_in.copy()
    gdf_in["_crash_year"] = pd.to_datetime(gdf_in["crash_date"], errors="coerce").dt.year
    gdf_in["_ped_harm"] = (ped_inj > 0) | (ped_killed > 0)
    by_year = (
        gdf_in.groupby("_crash_year", dropna=False)
        .agg(
            crashes=("crash_date", "count"),
            pedestrians_injured=(
                "number_of_pedestrians_injured",
                lambda s: int(_safe_int(s).sum()),
            ),
            pedestrians_killed=(
                "number_of_pedestrians_killed",
                lambda s: int(_safe_int(s).sum()),
            ),
            crashes_with_pedestrian_injured_or_killed=("_ped_harm", "sum"),
        )
        .reset_index()
    )
    year_csv = RESULTS_DIR / "crash_summary_by_year.csv"
    by_year.to_csv(year_csv, index=False)
    print(f"Wrote {year_csv}")

    metrics = {
        "study_boundary": "CSCL quadrilateral: 6th Ave (Ave of Americas), Houston (W+E), Bowery, Canal",
        "crash_window_start": args.since,
        "fast_mode": bool(args.fast),
        "crashes_in_envelope_downloaded": len(env_df),
        "crashes_inside_study_polygon": len(gdf_in),
        "pedestrians_injured_total": int(ped_inj.sum()),
        "pedestrians_killed_total": int(ped_killed.sum()),
        "crashes_with_any_pedestrian_injured_or_killed": int(with_ped_injury.sum()),
        "study_bbox_wgs84": {"min_lon": bbox[0], "min_lat": bbox[1], "max_lon": bbox[2], "max_lat": bbox[3]},
    }
    json_path = RESULTS_DIR / "key_metrics.json"
    json_path.write_text(json.dumps(metrics, indent=2))
    print(f"Wrote {json_path}")

    if not args.skip_maps:
        print("Building maps…")
        run_maps(fast=args.fast)
    else:
        print("Skipped map generation (--skip-maps)")

    # RESULTS.md
    rank_blurb = ""
    if TRACT_RANK.is_file():
        rank = pd.read_csv(TRACT_RANK)
        try:
            table = rank.head(12).to_markdown(index=False)
        except ImportError:
            table = rank.head(12).to_string(index=False)
        rank_blurb = (
            "\n## Tracts touching study area (from maps pipeline)\n\n"
            f"Source: `{TRACT_RANK.relative_to(ROOT)}`\n\n"
            + table
            + "\n"
        )

    maps_blurb = ""
    for name in (
        "01_pedestrian_intensity_percentile.png",
        "02_crash_intensity_percentile.png",
        "03_residential_intensity_percentile.png",
        "04_combined_multimetric_index.png",
    ):
        p = MAPS_DIR / name
        if p.is_file():
            maps_blurb += f"- `{p.relative_to(ROOT)}`\n"

    fast_note = ""
    if args.fast:
        fast_note = (
            "\n> **Note:** This export used `--fast` (first ~3k crashes in the envelope only). "
            "For final thesis numbers, run without `--fast`.\n"
        )

    md = f"""# Thesis results export

Generated for **writing after results**: use this file as the single index of numbers and outputs.
{fast_note}
## Headline counts (crashes strictly **inside** study polygon)

| Metric | Value |
|--------|------:|
| Date filter (≥) | {args.since} |
| Crashes inside quadrilateral | **{len(gdf_in):,}** |
| Pedestrians injured (sum of records) | **{int(ped_inj.sum()):,}** |
| Pedestrians killed (sum of records) | **{int(ped_killed.sum()):,}** |
| Crashes with any ped injured or killed | **{int(with_ped_injury.sum()):,}** |

*Envelope download (before polygon filter): {len(env_df):,} rows.*

## Files in this run

| File | Description |
|------|-------------|
| `{crash_out.relative_to(ROOT)}` | One row per crash inside polygon |
| `{year_csv.relative_to(ROOT)}` | Crashes and ped harm by year |
| `{json_path.relative_to(ROOT)}` | Machine-readable metrics |

## Maps (Manhattan tract percentiles + study outline)

{maps_blurb or '_Run without `--skip-maps` to generate._'}

{rank_blurb}

## Suggested **factual** bullets for the paper (edit, don’t overclaim)

- Between **{args.since}** and the latest crash dates in the export, police reported **{len(gdf_in):,}** motor vehicle crashes with coordinates inside the study quadrilateral (6th Ave – Houston – Bowery – Canal centerlines).
- **{int(with_ped_injury.sum()):,}** of those crashes involved at least one pedestrian injured or killed (per NYPD fields).
- Borough-level tract maps in `outputs/maps` situate walking intensity (NYCWalks), crash concentration, PLUTO **residential share of building units**, and an optional combined index, with the same study outline.

## Next step for the thesis draft

Paste tables into your Methods / Results, cite NYC Open Data (crashes, CSCL, census tracts, ACS) and MIT NYCWalks, then interpret **policy** in a separate Discussion section.
"""
    results_md = RESULTS_DIR / "RESULTS.md"
    results_md.write_text(md)
    print(f"Wrote {results_md}")


if __name__ == "__main__":
    main()
