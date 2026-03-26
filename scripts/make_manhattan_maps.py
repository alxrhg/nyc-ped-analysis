#!/usr/bin/env python3
"""
Build Manhattan census-tract maps for the thesis:
  1) Pedestrian intensity (percentile) — NYCWalks: default **mean** of six peak Σ(vol×len) per tract
     (line–tract **overlay** in EPSG:2263); all ``HME_*`` flows aggregated separately as ``nw_exp_*``.
     ``--ped-metric-source single``, ``--ped-spatial-aggregation centroid``, ``--ped-extra-maps``.
     ``--ped-percentile-basis total`` = raw Σ not per km². DOT fallback if no GeoJSON.
  2) Crash intensity (percentile) — NYPD crashes **per km²** by default (same area basis as map 1)
  3) Residential “mix” (percentile) — PLUTO: % of tax-lot building units that are residential
  4) Combined multimetric index — merges (1–3) with an explicit equation
  5) Subway access (percentile) — planar distance to nearest MTA Manhattan stop (data.ny.gov 39hk-dx4f);
     ``--skip-subway-distance`` to omit
  6) Transit access × ridership — ``log1p(R)/(d+buffer)`` percentile; R from MTA monthly ridership (ak4z-sape);
     ``--skip-subway-ridership`` for distance-only

Composite index (default ``mean``): **pedestrian percentile** is primary, **crash** secondary,
**residential** raw share ``s`` or percentile ``R`` optional / small by default. Map (3) still
documents PLUTO ``s``; see ``docs/thesis_maps.md`` for methods text.

    Default mean is **pedestrian-led** on map 4: ``I ≈ 0.65 P + 0.30 K + 0.05 s`` with ``K`` =
    percentile of **ped KSI per exposure** (injured+killed ÷ (ped_metric+1)), not raw crash count
    (``--combined-crash-metric``). **Percentiles for map 4** default to **all Manhattan** tracts
    (``--combined-scope borough``). Use ``south_of`` to rank only below a latitude (upper Manhattan
    shows as no data on map 4). Maps 1–3 stay borough-wide.
    ``ped_crash`` = 55/45 P/K only; ``equal`` = thirds; ``ped_emphasis`` = legacy. ``--combined-res percentile`` = ``R``.

Alternative ``--combined-method geometric`` (same P, C; third term s or R as above)::

    I_i = 100 * (P_i/100 * C_i/100 * t_i/100)^(1/3)

Overlays the Houston–Canal study polygon (SoHo / Chinatown corridor).

Usage:
  python scripts/make_manhattan_maps.py
  python scripts/make_manhattan_maps.py --fast
  python scripts/make_manhattan_maps.py --combined-method geometric
  python scripts/make_manhattan_maps.py --combined-res percentile   # legacy: all three percentiles
  python scripts/make_manhattan_maps.py --combined-balance equal      # (P+C+s)/3
  python scripts/make_manhattan_maps.py --combined-balance ped_crash # P+K only
  python scripts/make_manhattan_maps.py --combined-scope south_of  # map 4: rank south of ~59th only
  python scripts/make_manhattan_maps.py --combined-crash-metric count
  python scripts/make_manhattan_maps.py --ped-percentile-basis total   # rank raw Σ(vol×length)
  python scripts/make_manhattan_maps.py --crash-percentile-basis total  # rank raw crash counts
  python scripts/make_manhattan_maps.py --study-area-weight 0.12      # emphasize study polygon on map 4
  python scripts/make_manhattan_maps.py --study-floor-at-borough-rank 0  # no rank floor (default K=3)
  python scripts/make_manhattan_maps.py --skip-subway-distance              # no MTA / maps 5–6
  python scripts/make_manhattan_maps.py --skip-subway-ridership            # map 5 only (no ridership / map 6)
"""

from __future__ import annotations

import argparse
import io
import os
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
    add_wgs84_bbox_outline,
    combined_tract_index,
    frame_lonlat_map_north_up,
    percentile_rank,
    percentile_rank_within,
    resolve_pedestrian_volume_column,
    tract_area_km2,
)
from nycwalks.ped_tract_aggregate import (  # noqa: E402
    aggregate_volume_to_tracts,
    build_nycwalks_tract_exposure_table,
    composite_peak_exposure,
)
from nycwalks.pluto_tracts import (  # noqa: E402
    fetch_manhattan_pluto_unit_aggregates,
    residential_unit_share_percent,
)
from nycwalks.study_area import load_study_area_polygon, study_area_bbox_wgs84  # noqa: E402
from nycwalks.subway_mta import (  # noqa: E402
    enrich_stations_with_ridership_sum,
    fetch_mta_manhattan_ridership_sum_by_complex,
    fetch_mta_subway_stations_gdf,
    subway_access_percentile_from_distance_m,
    subway_nearest_ridership_pctile,
    tract_nearest_subway_table,
    transit_access_ridership_pctile,
)

OUT_DIR = ROOT / "outputs" / "maps"
TRACTS_URL = "https://data.cityofnewyork.us/resource/63ge-mke6.geojson"
CRASHES_URL = "https://data.cityofnewyork.us/resource/h9gi-nx95.json"
DOT_PED_GEOJSON = "https://data.cityofnewyork.us/resource/cqsj-cfgu.geojson"
CENSUS_URL = "https://api.census.gov/data/2022/acs/acs5"

NYCWALKS_PATTERNS = (
    "NYC_pednetwork*.geojson",
    "nycwalks_network.geojson",
    "*nycwalk*.geojson",
    "*NYCWalk*.geojson",
)


def _find_nycwalks_file(raw_dir: Path, mit_dir: Path) -> Path | None:
    for base in (mit_dir, raw_dir):
        for pattern in NYCWALKS_PATTERNS:
            for p in sorted(base.glob(pattern)):
                if p.is_file() and p.suffix.lower() == ".geojson":
                    return p
    return None


def load_manhattan_tracts() -> gpd.GeoDataFrame:
    r = requests.get(
        TRACTS_URL,
        params={"$where": "boroname='Manhattan'"},
        timeout=180,
    )
    r.raise_for_status()
    gdf = gpd.read_file(io.BytesIO(r.content))
    if gdf.crs is None:
        gdf = gdf.set_crs(4326)
    return gdf


def fetch_acs_manhattan_tracts() -> pd.DataFrame:
    params = {
        "get": "NAME,B01003_001E,B25001_001E",
        "for": "tract:*",
        "in": "state:36 county:061",
    }
    r = requests.get(CENSUS_URL, params=params, timeout=120)
    r.raise_for_status()
    rows = r.json()
    cols = rows[0]
    data = rows[1:]
    df = pd.DataFrame(data, columns=cols)
    df["geoid"] = df["state"] + df["county"] + df["tract"]
    for c in ("B01003_001E", "B25001_001E"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
        df.loc[df[c] < 0, c] = np.nan
    return df


def fetch_crashes_manhattan(since: str, fast: bool) -> pd.DataFrame:
    where = (
        f"crash_date >= '{since}T00:00:00.000' AND "
        "latitude IS NOT NULL AND longitude IS NOT NULL AND "
        "borough = 'MANHATTAN'"
    )
    headers = {}
    tok = os.environ.get("SOCRATA_APP_TOKEN")
    if tok:
        headers["X-App-Token"] = tok
    rows: list[dict] = []
    offset = 0
    page = 20000 if not fast else 3000
    while True:
        params = {
            "$where": where,
            "$limit": page,
            "$offset": offset,
            "$order": ":id",
        }
        r = requests.get(CRASHES_URL, params=params, headers=headers, timeout=300)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        if fast or len(batch) < page:
            break
        offset += page
    return pd.DataFrame(rows)


def _aggregate_crashes_fixed(tracts: gpd.GeoDataFrame, crashes: pd.DataFrame) -> pd.Series:
    """Return crash count per tract index aligned with tracts."""
    lon = pd.to_numeric(crashes["longitude"], errors="coerce")
    lat = pd.to_numeric(crashes["latitude"], errors="coerce")
    pts = gpd.GeoDataFrame(
        crashes,
        geometry=gpd.points_from_xy(lon, lat),
        crs="EPSG:4326",
    )
    pts = pts[pts.geometry.notna()]
    joined = pts.sjoin(tracts[["geoid", "geometry"]], predicate="within")
    counts = joined.groupby("geoid").size()
    return tracts["geoid"].map(counts).fillna(0).astype(int)


def _kth_largest_value(s: pd.Series, k: int) -> float | None:
    """k-th largest numeric value in ``s`` (k=1 is max). None if empty or k < 1."""
    v = pd.to_numeric(s, errors="coerce").dropna().to_numpy(dtype=float)
    if v.size == 0 or k < 1:
        return None
    kk = min(int(k), int(v.size))
    return float(np.partition(v, -kk)[-kk])


def _aggregate_ped_ksi_by_tract(tracts: gpd.GeoDataFrame, crashes: pd.DataFrame) -> pd.Series:
    """Sum (pedestrians injured + killed) per tract from geocoded crashes."""
    lon = pd.to_numeric(crashes["longitude"], errors="coerce")
    lat = pd.to_numeric(crashes["latitude"], errors="coerce")
    inj_col = "number_of_pedestrians_injured"
    kill_col = "number_of_pedestrians_killed"
    if inj_col in crashes.columns:
        inj = pd.to_numeric(crashes[inj_col], errors="coerce").fillna(0.0)
    else:
        inj = pd.Series(0.0, index=crashes.index)
    if kill_col in crashes.columns:
        kill = pd.to_numeric(crashes[kill_col], errors="coerce").fillna(0.0)
    else:
        kill = pd.Series(0.0, index=crashes.index)
    ksi = inj.astype(float) + kill.astype(float)
    pts = gpd.GeoDataFrame(
        {"_ksi": ksi},
        geometry=gpd.points_from_xy(lon, lat),
        crs="EPSG:4326",
    )
    pts = pts[pts.geometry.notna()]
    joined = pts.sjoin(tracts[["geoid", "geometry"]], predicate="within")
    summed = joined.groupby("geoid")["_ksi"].sum()
    return tracts["geoid"].map(summed).fillna(0.0).astype(float)


def _dot_numeric_count_columns(df: pd.DataFrame) -> list[str]:
    skip = {
        "objectid",
        "borough",
        "street_nam",
        "from_stree",
        "to_street",
        "loc",
        "iex",
        "geometry",
    }
    out: list[str] = []
    for c in df.columns:
        if c in skip or c.lower() == "the_geom":
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            out.append(c)
            continue
        coerced = pd.to_numeric(df[c], errors="coerce")
        if coerced.notna().sum() > len(df) * 0.3:
            out.append(c)
    return out


def pedestrian_from_dot(tracts: gpd.GeoDataFrame) -> tuple[pd.Series, str]:
    gdf = gpd.read_file(DOT_PED_GEOJSON)
    df = pd.DataFrame(gdf.drop(columns=["geometry"]))
    cols = _dot_numeric_count_columns(df)
    num = pd.concat([pd.to_numeric(df[c], errors="coerce").fillna(0) for c in cols], axis=1)
    num.columns = cols
    df = pd.concat([df.drop(columns=cols, errors="ignore"), num], axis=1)
    df["_ped_sum"] = df[cols].sum(axis=1)
    gdf = gpd.GeoDataFrame(df, geometry=gdf.geometry, crs=4326)
    j = gdf.sjoin(tracts[["geoid", "geometry"]], predicate="within")
    s = j.groupby("geoid")["_ped_sum"].sum()
    return s, "DOT Bi-Annual Pedestrian Counts (sum of all numeric survey columns)"


def plot_map(
    tracts: gpd.GeoDataFrame,
    column: str,
    title: str,
    subtitle: str,
    outfile: Path,
    cmap: str = "YlOrRd",
    legend_label: str | None = None,
    study_geom=None,
) -> None:
    # Portrait figure: Manhattan long axis is N–S; north is up (latitude on y).
    fig, ax = plt.subplots(figsize=(7.5, 11))
    tracts.plot(
        column=column,
        ax=ax,
        legend=True,
        cmap=cmap,
        edgecolor="white",
        linewidth=0.2,
        legend_kwds={
            "label": legend_label or column,
            "shrink": 0.45,
            "location": "right",
        },
        missing_kwds={"color": "lightgrey", "label": "No data"},
    )
    if study_geom is not None:
        add_study_area_outline(ax, study_geom)
    else:
        add_wgs84_bbox_outline(ax, study_area_bbox_wgs84())
    ax.set_title(title + "\n" + subtitle, fontsize=11)
    ax.axis("off")
    b = tuple(tracts.total_bounds)
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="2019-01-01")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument(
        "--ped-percentile-basis",
        choices=("density", "total"),
        default="density",
        help=(
            "Map 1 + combined P leg: rank pedestrian metric **per tract km²** (density, default) "
            "or raw Σ(NYCWalks vol×length) / DOT sum per tract (total)."
        ),
    )
    ap.add_argument(
        "--crash-percentile-basis",
        choices=("density", "total"),
        default="density",
        help=(
            "Map 2 + combined crash-count leg: rank crashes **per tract km²** (density, default) "
            "or raw crash count per tract (total)."
        ),
    )
    ap.add_argument(
        "--volume-col",
        default=None,
        help=(
            "With --ped-metric-source single: NYCWalks column to use. "
            "Ignored for composite (default), which averages all six peak periods."
        ),
    )
    ap.add_argument(
        "--ped-spatial-aggregation",
        choices=("overlay", "centroid"),
        default="overlay",
        help=(
            "NYCWalks line→tract: **overlay** (default) sums vol×length of each line **inside** "
            "each tract (EPSG:2263); **centroid** assigns the full segment to the tract of its centroid."
        ),
    )
    ap.add_argument(
        "--ped-metric-source",
        choices=("composite", "single"),
        default="composite",
        help=(
            "**composite** (default) = mean of tract totals across all available MIT peak columns "
            "(predwkdyAM/MD/PM, predwkndAM/MD/PM). **single** = only --volume-col."
        ),
    )
    ap.add_argument(
        "--skip-hme-purpose",
        action="store_true",
        help="Skip aggregating MIT HME_* disaggregated trip-purpose flow columns to tracts.",
    )
    ap.add_argument(
        "--ped-extra-maps",
        choices=("none", "periods", "purpose", "all"),
        default="none",
        help=(
            "Write extra choropleths: **periods** = one map per peak column; **purpose** = one per HME_*; "
            "**all** = both (many PNGs)."
        ),
    )
    ap.add_argument(
        "--combined-method",
        choices=("mean", "geometric"),
        default="mean",
        help="How to merge ped, crash, and residential term for map 4 (default: mean).",
    )
    ap.add_argument(
        "--combined-res",
        choices=("raw_share", "percentile"),
        default="raw_share",
        help=(
            "Residential term in combined index: raw PLUTO %% residential units (default), "
            "or borough percentile of that share (legacy)."
        ),
    )
    ap.add_argument(
        "--combined-balance",
        choices=("ped_primary", "ped_crash", "equal", "ped_emphasis"),
        default="ped_primary",
        help=(
            "Mean-only weights (ped %%, crash %%, residential term): ped_primary = 65/30/5 "
            "(default; walking is key); ped_crash = 55/45/0 (no residential); equal = thirds; "
            "ped_emphasis = 50/25/25. Ignored for --combined-method geometric."
        ),
    )
    ap.add_argument(
        "--combined-crash-metric",
        choices=("count", "ksi_rate"),
        default="ksi_rate",
        help=(
            "Map 4 crash leg: crash-count **basis** set by --crash-percentile-basis; "
            "or KSI rate (ped injured+killed ÷ ped_metric+1)."
        ),
    )
    ap.add_argument(
        "--combined-scope",
        choices=("borough", "south_of"),
        default="borough",
        help=(
            "Map 4 percentile pool: **borough** (default) = all Manhattan tracts get an index; "
            "**south_of** = rank only among tracts south of --combined-scope-north-lat "
            "(north of line = missing / grey on map 4)."
        ),
    )
    ap.add_argument(
        "--combined-scope-north-lat",
        type=float,
        default=40.765,
        help=(
            "With scope=south_of: include tracts whose centroid latitude is **below** this "
            "(south); ~40.765 ≈ 59th St / south side of Central Park band."
        ),
    )
    ap.add_argument(
        "--study-area-weight",
        type=float,
        default=0.0,
        metavar="W",
        help=(
            "0–1. After the usual combined index, blend toward the study polygon: "
            "I=(1-W)*I_base + W*G with G=100 if the tract intersects the CSCL quadrilateral "
            "else 0 (highlights the thesis corridor vs rest of Manhattan). "
            "Requires data/mit/study_area_*.geojson. Default 0 (off)."
        ),
    )
    ap.add_argument(
        "--study-floor-at-borough-rank",
        type=int,
        default=3,
        metavar="K",
        help=(
            "After optional study-area weight: tracts intersecting the study polygon get "
            "idx = max(idx, K-th largest combined index borough-wide), so the corridor "
            "sits in the top tier (default K=3). Does not lower Midtown/FiDi. 0=off."
        ),
    )
    ap.add_argument(
        "--write-tract-metrics",
        type=str,
        default=None,
        metavar="PATH",
        help=(
            "Write all Manhattan census tracts with map metrics to a GeoPackage "
            "(e.g. outputs/maps/manhattan_tract_metrics.gpkg) for NTA / neighborhood "
            "aggregation (see scripts/rank_manhattan_nta.py)."
        ),
    )
    ap.add_argument(
        "--skip-subway-distance",
        action="store_true",
        help=(
            "Do not fetch MTA subway stops or compute tract distance / subway access percentile "
            "(for offline runs)."
        ),
    )
    ap.add_argument(
        "--skip-subway-ridership",
        action="store_true",
        help=(
            "Fetch subway stop locations only; skip MTA monthly ridership (ak4z-sape) and the "
            "distance×ridership combined percentile."
        ),
    )
    ap.add_argument(
        "--subway-ridership-since",
        type=str,
        default="2024-01-01",
        help=(
            "Include MTA station monthly ridership rows with month >= this date (ISO YYYY-MM-DD). "
            "Summed per station_complex_id for Manhattan (data.ny.gov ak4z-sape)."
        ),
    )
    ap.add_argument(
        "--transit-gravity-buffer-m",
        type=float,
        default=50.0,
        metavar="METERS",
        help=(
            "Buffer added to distance in the combined score log1p(R)/(d+METERS) "
            "(default 50)."
        ),
    )
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    raw = ROOT / "data" / "raw"
    mit = ROOT / "data" / "mit"

    print("Loading Manhattan census tracts…")
    tracts = load_manhattan_tracts()
    tracts["area_km2"] = tract_area_km2(tracts)

    try:
        study_poly = load_study_area_polygon()
    except FileNotFoundError:
        study_poly = None
    if study_poly is not None:
        tracts["study_intersects"] = tracts.geometry.intersects(study_poly)
    else:
        tracts["study_intersects"] = pd.Series(False, index=tracts.index)

    print("Fetching ACS…")
    acs = fetch_acs_manhattan_tracts()
    tracts = tracts.merge(acs[["geoid", "B01003_001E", "B25001_001E"]], on="geoid", how="left")
    tracts["acs_hu_per_km2"] = tracts["B25001_001E"] / tracts["area_km2"]

    print("Fetching PLUTO (tax-lot units → tract residential share)…")
    pluto = fetch_manhattan_pluto_unit_aggregates()
    tracts = tracts.merge(pluto, on="geoid", how="left")
    tracts["pluto_unitsres"] = tracts["pluto_unitsres"].fillna(0)
    tracts["pluto_unitstotal"] = tracts["pluto_unitstotal"].fillna(0)
    tracts["res_unit_share_pct"] = residential_unit_share_percent(
        tracts["pluto_unitsres"],
        tracts["pluto_unitstotal"],
    )
    tracts["res_pctile"] = percentile_rank(tracts["res_unit_share_pct"])

    print("Pedestrian layer…")
    nw = _find_nycwalks_file(raw, mit)
    peak_used: list[str] = []
    hme_used: list[str] = []
    ped_note = ""
    if nw:
        seg = gpd.read_file(nw)
        nw_df, peak_used, hme_used = build_nycwalks_tract_exposure_table(
            seg,
            tracts,
            method=args.ped_spatial_aggregation,
            include_hme=not args.skip_hme_purpose,
        )
        for c in nw_df.columns:
            tracts[c] = nw_df[c].astype(float).to_numpy()

        if args.ped_metric_source == "single":
            col = resolve_pedestrian_volume_column(seg, override=args.volume_col)
            if col is None:
                raise SystemExit(
                    "Could not resolve NYCWalks column for --ped-metric-source single "
                    "(set --volume-col to a numeric pred* or HME_* field present in the GeoJSON)."
                )
            exp_name = f"nw_exp_{col}"
            if exp_name not in tracts.columns:
                tracts[exp_name] = aggregate_volume_to_tracts(
                    seg,
                    tracts,
                    col,
                    method=args.ped_spatial_aggregation,
                )
            tracts["ped_metric"] = tracts[exp_name].astype(float)
            ped_note = (
                f"NYCWalks `{col}` only; Σ(vol×len) per tract via {args.ped_spatial_aggregation}. "
            )
        else:
            tracts["ped_metric"] = composite_peak_exposure(nw_df, peak_used).astype(float)
            ped_note = (
                f"NYCWalks **mean** of {len(peak_used)} peak Σ(vol×len) layers "
                f"({', '.join(peak_used)}); tract aggregation={args.ped_spatial_aggregation}. "
            )
            if hme_used:
                ped_note += (
                    f"Purpose splits (HME_*) stored as separate nw_exp_* columns ({len(hme_used)}). "
                )
        print("  Using", nw.name, "|", ped_note.replace("**", ""))
        if hme_used:
            print("  HME_* columns:", ", ".join(hme_used))
        summ_path_nw = OUT_DIR / "nycwalks_aggregation_summary.txt"
        summ_path_nw.parent.mkdir(parents=True, exist_ok=True)
        summ_path_nw.write_text(
            "MIT NYCWalks → Manhattan census tracts\n"
            f"network_file: {nw.name}\n"
            f"ped_spatial_aggregation: {args.ped_spatial_aggregation}\n"
            f"ped_metric_source: {args.ped_metric_source}\n"
            f"peak_columns_found: {', '.join(peak_used) or '(none)'}\n"
            f"hme_columns_found: {', '.join(hme_used) or '(none)'}\n"
            "\n"
            "overlay: sum over line∩tract fragments of (volume × fragment length) in EPSG:2263.\n"
            "centroid: full segment vol×total length assigned to tract containing segment centroid.\n"
            "composite ped_metric: mean of nw_exp_predwkdy* / predwknd* tract totals present.\n",
            encoding="utf-8",
        )
        print(f"  Wrote {summ_path_nw}")
    else:
        ped, ped_note = pedestrian_from_dot(tracts)
        print("  No NYCWalks GeoJSON in data/mit/ or data/raw — using DOT bi-annual counts.")
        print(" ", ped_note)
        tracts["ped_metric"] = tracts["geoid"].map(ped).fillna(0)
    zero_share = (tracts["ped_metric"] <= 0).mean()
    if zero_share > 0.4 and nw is None:
        print(
            "  WARNING: >40% of tracts have no DOT survey point—pedestrian map is sparse.",
            "Add MIT NYCWalks GeoJSON to data/mit/ (symlink) for a citywide pedestrian layer (see data/README.md).",
            sep="\n  ",
        )
    area_safe = np.maximum(
        pd.to_numeric(tracts["area_km2"], errors="coerce").astype(float),
        1e-9,
    )
    tracts["ped_density"] = tracts["ped_metric"].astype(float) / area_safe
    ped_for_pctile = (
        tracts["ped_density"]
        if args.ped_percentile_basis == "density"
        else tracts["ped_metric"].astype(float)
    )
    tracts["ped_pctile"] = percentile_rank(ped_for_pctile)

    ped_basis_lbl = (
        "Borough percentile of exposure per km² (÷ tract area, EPSG:2263). "
        if args.ped_percentile_basis == "density"
        else "Borough percentile of tract-total exposure (not per km²). "
    )

    if nw and args.ped_extra_maps in ("periods", "all"):
        for c in peak_used:
            col = f"nw_exp_{c}"
            if col not in tracts.columns:
                continue
            extra = (
                tracts[col].astype(float) / area_safe
                if args.ped_percentile_basis == "density"
                else tracts[col].astype(float)
            )
            tracts["_nw_pct_plot"] = percentile_rank(extra)
            safe = "".join(x if x.isalnum() or x in "-_" else "_" for x in c)
            plot_map(
                tracts,
                "_nw_pct_plot",
                f"Pedestrian exposure ({c})",
                (
                    ped_basis_lbl
                    + f"MIT NYCWalks `{c}` only; aggregation={args.ped_spatial_aggregation}. "
                ),
                OUT_DIR / f"01_nycwalks_peak_{safe}.png",
                cmap="YlOrRd",
                legend_label="Percentile",
                study_geom=study_poly,
            )
            tracts.drop(columns=["_nw_pct_plot"], inplace=True)

    if nw and args.ped_extra_maps in ("purpose", "all") and hme_used:
        for c in hme_used:
            col = f"nw_exp_{c}"
            if col not in tracts.columns:
                continue
            extra = (
                tracts[col].astype(float) / area_safe
                if args.ped_percentile_basis == "density"
                else tracts[col].astype(float)
            )
            tracts["_nw_pct_plot"] = percentile_rank(extra)
            safe = "".join(x if x.isalnum() or x in "-_" else "_" for x in c)
            plot_map(
                tracts,
                "_nw_pct_plot",
                f"Pedestrian purpose component ({c})",
                (
                    ped_basis_lbl
                    + f"MIT NYCWalks disaggregated `{c}`; aggregation={args.ped_spatial_aggregation}. "
                ),
                OUT_DIR / f"01_nycwalks_hme_{safe}.png",
                cmap="YlOrRd",
                legend_label="Percentile",
                study_geom=study_poly,
            )
            tracts.drop(columns=["_nw_pct_plot"], inplace=True)

    print("Fetching crashes…")
    cr = fetch_crashes_manhattan(args.since, args.fast)
    tracts["crash_n"] = _aggregate_crashes_fixed(tracts, cr)
    tracts["crash_density"] = tracts["crash_n"].astype(float) / area_safe
    crash_for_pctile = (
        tracts["crash_density"]
        if args.crash_percentile_basis == "density"
        else tracts["crash_n"].astype(float)
    )
    tracts["crash_pctile"] = percentile_rank(crash_for_pctile)
    tracts["ped_ksi"] = _aggregate_ped_ksi_by_tract(tracts, cr)
    tracts["ksi_rate"] = tracts["ped_ksi"] / (tracts["ped_metric"] + 1.0)

    if args.skip_subway_distance:
        tracts["dist_nearest_subway_m"] = np.nan
        tracts["nearest_stop_name"] = np.nan
        tracts["nearest_complex_id"] = np.nan
        tracts["nearest_subway_ridership_sum"] = np.nan
        tracts["subway_access_pctile"] = np.nan
        tracts["subway_nearest_ridership_pctile"] = np.nan
        tracts["transit_access_ridership_pctile"] = np.nan
    else:
        print("Subway station proximity (MTA stops, NY Open Data 39hk-dx4f, borough M)…")
        try:
            _stops = fetch_mta_subway_stations_gdf(borough="M")
            _stops_use = _stops
            if not args.skip_subway_ridership:
                print(
                    "  MTA monthly ridership (data.ny.gov ak4z-sape, Manhattan, "
                    f"month >= {args.subway_ridership_since})…"
                )
                try:
                    _rsum = fetch_mta_manhattan_ridership_sum_by_complex(
                        since_month_day=args.subway_ridership_since,
                    )
                    _stops_use = enrich_stations_with_ridership_sum(_stops, _rsum)
                except (OSError, ValueError, requests.RequestException) as exc:
                    print(f"  WARNING: ridership fetch/join failed ({exc}); distance-only for subway.")
                    _stops_use = _stops.copy()
                    _stops_use["ridership_sum_window"] = np.nan
            else:
                _stops_use = _stops.copy()
                _stops_use["ridership_sum_window"] = np.nan

            _tbl = tract_nearest_subway_table(tracts, _stops_use)
            tracts["dist_nearest_subway_m"] = _tbl["dist_nearest_subway_m"]
            tracts["nearest_stop_name"] = _tbl["nearest_stop_name"]
            tracts["nearest_complex_id"] = _tbl["nearest_complex_id"]
            tracts["nearest_subway_ridership_sum"] = _tbl["nearest_subway_ridership_sum"]
            tracts["subway_access_pctile"] = subway_access_percentile_from_distance_m(
                tracts["dist_nearest_subway_m"],
            )
            tracts["subway_nearest_ridership_pctile"] = subway_nearest_ridership_pctile(
                tracts["nearest_subway_ridership_sum"],
            )
            tracts["transit_access_ridership_pctile"] = transit_access_ridership_pctile(
                tracts["nearest_subway_ridership_sum"],
                tracts["dist_nearest_subway_m"],
                dist_buffer_m=float(args.transit_gravity_buffer_m),
            )
        except (OSError, ValueError, requests.RequestException) as exc:
            print(f"  WARNING: subway distance step failed ({exc}); leaving columns as NaN.")
            tracts["dist_nearest_subway_m"] = np.nan
            tracts["nearest_stop_name"] = np.nan
            tracts["nearest_complex_id"] = np.nan
            tracts["nearest_subway_ridership_sum"] = np.nan
            tracts["subway_access_pctile"] = np.nan
            tracts["subway_nearest_ridership_pctile"] = np.nan
            tracts["transit_access_ridership_pctile"] = np.nan

    if args.combined_scope == "borough":
        scope_mask = pd.Series(True, index=tracts.index)
    else:
        tc = tracts.to_crs(2263)
        cen = gpd.GeoDataFrame(geometry=tc.geometry.centroid, crs=2263).to_crs(4326)
        lat_c = cen.geometry.y
        scope_mask = lat_c < float(args.combined_scope_north_lat)
    tracts["combined_scope_in"] = scope_mask

    tracts["combined_ped_pctile"] = percentile_rank_within(ped_for_pctile, scope_mask)
    if args.combined_crash_metric == "ksi_rate":
        tracts["combined_crash_leg_pctile"] = percentile_rank_within(tracts["ksi_rate"], scope_mask)
    else:
        tracts["combined_crash_leg_pctile"] = percentile_rank_within(crash_for_pctile, scope_mask)

    res_for_combined = (
        tracts["res_unit_share_pct"]
        if args.combined_res == "raw_share"
        else tracts["res_pctile"]
    )
    _bal = args.combined_balance
    if _bal == "equal":
        cw = (1.0 / 3.0, 1.0 / 3.0, 1.0 / 3.0)
    elif _bal == "ped_crash":
        cw = (0.55, 0.45, 0.0)
    elif _bal == "ped_emphasis":
        cw = (0.5, 0.25, 0.25)
    else:
        cw = (0.65, 0.30, 0.05)  # ped_primary

    tracts["combined_idx"] = combined_tract_index(
        tracts["combined_ped_pctile"],
        tracts["combined_crash_leg_pctile"],
        res_for_combined,
        method=args.combined_method,
        weights=cw,
    )
    tracts["combined_idx_base"] = tracts["combined_idx"]

    w_study = float(args.study_area_weight)
    if w_study < 0 or w_study > 1:
        raise SystemExit("--study-area-weight must be between 0 and 1.")
    if w_study > 0:
        if study_poly is None:
            print(
                "WARNING: --study-area-weight > 0 but study polygon not found; "
                "skipping study-area blend (add data/mit/study_area_bowery_houston_6th_canal.geojson).",
            )
        else:
            g = tracts["study_intersects"].astype(float) * 100.0
            ci = tracts["combined_idx"]
            tracts["combined_idx"] = (1.0 - w_study) * ci + w_study * g

    floor_k = int(args.study_floor_at_borough_rank)
    study_floor_thr: float | None = None
    if floor_k > 0 and study_poly is not None:
        study_floor_thr = _kth_largest_value(tracts["combined_idx"], floor_k)
        if study_floor_thr is not None:
            m = tracts["study_intersects"] & tracts["combined_idx"].notna()
            if m.any():
                tracts.loc[m, "combined_idx"] = np.maximum(
                    tracts.loc[m, "combined_idx"].astype(float),
                    study_floor_thr,
                )
    tracts["study_floor_threshold"] = (
        float(study_floor_thr) if study_floor_thr is not None else np.nan
    )

    if args.write_tract_metrics:
        wpath = Path(args.write_tract_metrics).expanduser()
        wpath.parent.mkdir(parents=True, exist_ok=True)
        _nw_cols = sorted(c for c in tracts.columns if c.startswith("nw_exp_"))
        _base_tout = [
            "geoid",
            "ntaname",
            "area_km2",
            "ped_pctile",
            "crash_pctile",
            "res_pctile",
            "combined_ped_pctile",
            "combined_crash_leg_pctile",
            "combined_idx_base",
            "combined_idx",
            "study_intersects",
            "study_floor_threshold",
            "combined_scope_in",
            "ped_metric",
            "ped_density",
            "crash_n",
            "crash_density",
            "ped_ksi",
            "ksi_rate",
            "res_unit_share_pct",
            "acs_hu_per_km2",
            "dist_nearest_subway_m",
            "subway_access_pctile",
            "nearest_stop_name",
            "nearest_complex_id",
            "nearest_subway_ridership_sum",
            "subway_nearest_ridership_pctile",
            "transit_access_ridership_pctile",
        ]
        tract_out = tracts[_base_tout + _nw_cols + ["geometry"]].copy()
        tract_out.to_file(wpath, driver="GPKG")
        print(f"Wrote tract metrics GeoPackage: {wpath}")

    plot_map(
        tracts,
        "ped_pctile",
        "Pedestrian intensity (Manhattan census tracts)",
        ped_basis_lbl + ped_note,
        OUT_DIR / "01_pedestrian_intensity_percentile.png",
        legend_label=(
            "Percentile (ped / km²)" if args.ped_percentile_basis == "density" else "Percentile (ped total)"
        ),
        study_geom=study_poly,
    )
    crash_basis_lbl = (
        "Borough percentile of crash count per km² (÷ tract area, EPSG:2263). "
        if args.crash_percentile_basis == "density"
        else "Borough percentile of raw crash count per tract (not per km²). "
    )
    plot_map(
        tracts,
        "crash_pctile",
        "Motor vehicle crash concentration (Manhattan)",
        crash_basis_lbl + f"NYPD {args.since}+, n={len(cr):,} crashes geocoded in Manhattan.",
        OUT_DIR / "02_crash_intensity_percentile.png",
        cmap="OrRd",
        legend_label=(
            "Percentile (crashes / km²)"
            if args.crash_percentile_basis == "density"
            else "Percentile (crash count)"
        ),
        study_geom=study_poly,
    )
    plot_map(
        tracts,
        "res_pctile",
        "Residential share of PLUTO building units (Manhattan)",
        "Borough percentile of 100×ΣUnitsRes/ΣUnitsTotal per tract (NYC PLUTO 64uk-42ks)",
        OUT_DIR / "03_residential_intensity_percentile.png",
        cmap="Greens",
        legend_label="Percentile (% residential of total units)",
        study_geom=study_poly,
    )
    crash_leg_lbl = (
        "K = KSI÷(ped+1) pct."
        if args.combined_crash_metric == "ksi_rate"
        else (
            "C = crashes per km² pct."
            if args.crash_percentile_basis == "density"
            else "C = crash count pct."
        )
    )
    p_scope = "P = ped per km² pct." if args.ped_percentile_basis == "density" else "P = ped total pct."
    scope_lbl = (
        f"{p_scope} Among tracts south of {args.combined_scope_north_lat:.3f}°N (centroid)."
        if args.combined_scope == "south_of"
        else f"{p_scope} Among all Manhattan tracts."
    )
    if args.combined_method == "mean":
        if _bal == "ped_primary":
            bal = f"0.65P+0.30×({crash_leg_lbl})+0.05s"
        elif _bal == "ped_crash":
            bal = f"0.55P+0.45×({crash_leg_lbl})"
        elif _bal == "equal":
            bal = f"(P+({crash_leg_lbl})+s)/3"
        else:
            bal = f"½P+¼×({crash_leg_lbl})+¼s (legacy)"
        res_note = ""
        if _bal != "ped_crash":
            res_note = (
                " + raw PLUTO %% res." if args.combined_res == "raw_share" else " + res. share pct."
            )
        combo_sub = f"Weighted mean {bal}{res_note}. {scope_lbl}"
        if w_study > 0 and study_poly is not None:
            combo_sub += f" Then I=(1-{w_study:.2f})·I+{w_study:.2f}·G (G=100 in study polygon)."
    else:
        if _bal == "ped_crash":
            combo_sub = f"Geometric: 100·√(P/100·K/100) with {crash_leg_lbl}. {scope_lbl}"
        elif args.combined_res == "raw_share":
            combo_sub = f"Geometric mean (P × {crash_leg_lbl} × s). {scope_lbl}"
        else:
            combo_sub = f"Geometric mean (P × {crash_leg_lbl} × R). {scope_lbl}"
        if w_study > 0 and study_poly is not None:
            combo_sub += f" Then I=(1-{w_study:.2f})·I+{w_study:.2f}·G (G=100 in study polygon)."
    if (
        floor_k > 0
        and study_poly is not None
        and study_floor_thr is not None
    ):
        combo_sub += (
            f" Study tracts: idx=max(idx, borough {floor_k}-largest≈{study_floor_thr:.1f})."
        )
    plot_map(
        tracts,
        "combined_idx",
        "Combined multimetric index (Manhattan)",
        combo_sub,
        OUT_DIR / "04_combined_multimetric_index.png",
        cmap="Greys",
        legend_label="Index (dark = high, light = low)",
        study_geom=study_poly,
    )

    if pd.to_numeric(tracts["dist_nearest_subway_m"], errors="coerce").notna().any():
        plot_map(
            tracts,
            "subway_access_pctile",
            "Subway station access (Manhattan census tracts)",
            (
                "Borough percentile: higher = closer to nearest MTA subway stop. "
                "Distance = planar EPSG:2263 tract polygon → stop point (m); "
                "stops from data.ny.gov MTA Subway Stations (39hk-dx4f, borough M)."
            ),
            OUT_DIR / "05_subway_access_percentile.png",
            cmap="Greys",
            legend_label="Percentile (dark = closer stop)",
            study_geom=study_poly,
        )

    if pd.to_numeric(tracts["transit_access_ridership_pctile"], errors="coerce").notna().any():
        plot_map(
            tracts,
            "transit_access_ridership_pctile",
            "Transit access × ridership (Manhattan census tracts)",
            (
                f"Borough percentile of log1p(R)/(d+{args.transit_gravity_buffer_m:.0f}m): "
                "R = summed MTA entries at nearest station complex (ak4z-sape, Manhattan, "
                f"month ≥ {args.subway_ridership_since}); d = planar distance to nearest stop (m); "
                "stops 39hk-dx4f. Dark = high combined access to busy subway."
            ),
            OUT_DIR / "06_transit_access_ridership_percentile.png",
            cmap="Greys",
            legend_label="Percentile (dark = high)",
            study_geom=study_poly,
        )

    if study_poly is not None:
        sa = tracts[tracts.intersects(study_poly)].copy()
    else:
        from shapely.geometry import box as _box

        sa = tracts[tracts.intersects(_box(*study_area_bbox_wgs84()))].copy()
    summ_base = [
        "geoid",
        "ntaname",
        "ped_pctile",
        "crash_pctile",
        "res_pctile",
        "combined_ped_pctile",
        "combined_crash_leg_pctile",
        "combined_idx_base",
        "combined_idx",
        "study_intersects",
        "study_floor_threshold",
        "combined_scope_in",
        "ped_metric",
        "ped_density",
        "area_km2",
        "crash_n",
        "crash_density",
        "ped_ksi",
        "ksi_rate",
        "res_unit_share_pct",
        "acs_hu_per_km2",
        "dist_nearest_subway_m",
        "subway_access_pctile",
        "nearest_stop_name",
        "nearest_complex_id",
        "nearest_subway_ridership_sum",
        "subway_nearest_ridership_pctile",
        "transit_access_ridership_pctile",
    ]
    summ_nw = [c for c in sorted(tracts.columns) if c.startswith("nw_exp_")]
    summ = sa[summ_base + summ_nw].sort_values("combined_idx", ascending=False, na_position="last")
    summ_path = OUT_DIR / "study_area_tract_rankings.csv"
    summ.to_csv(summ_path, index=False)
    print(f"Wrote maps to {OUT_DIR}")
    print(f"Study-area tract table: {summ_path}")


if __name__ == "__main__":
    main()
