#!/usr/bin/env python3
"""
Build a small **peer comparison table**: Houston–Canal study tracts vs selected Manhattan NTAs.

Study row = **area-weighted mean** of tracts in ``study_area_tract_rankings.csv`` (same logic
as NTA aggregation). Peer rows = rows from ``manhattan_nta_rankings.csv`` for official
**NTA 2020** codes (DCP / Census neighborhood units).

Default peers:
  MN0203  West Village
  MN0101  Financial District–Battery Park City
  MN0501  Midtown South–Flatiron–Union Square
  MN0502  Midtown–Times Square

Usage (from repo root, after maps + NTA ranking exist)::

  python scripts/export_peer_nta_comparison.py
  python scripts/export_peer_nta_comparison.py --print-md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PEERS: dict[str, str] = {
    "MN0203": "West Village",
    "MN0101": "Financial District–Battery Park City",
    "MN0501": "Midtown South–Flatiron–Union Square",
    "MN0502": "Midtown–Times Square",
}

# Study tract columns → NTA table uses *_awm suffix for the same quantities.
CORE_COMPARE = [
    "combined_idx",
    "combined_idx_base",
    "ped_pctile",
    "crash_pctile",
    "res_pctile",
    "combined_ped_pctile",
    "combined_crash_leg_pctile",
    "crash_density",
    "ped_density",
    "dist_nearest_subway_m",
    "subway_access_pctile",
    "transit_access_ridership_pctile",
]


def _wmean(df: pd.DataFrame, col: str) -> float:
    x = pd.to_numeric(df[col], errors="coerce")
    w = pd.to_numeric(df["area_km2"], errors="coerce").fillna(0.0)
    ok = x.notna() & (w > 0)
    if not ok.any():
        return float("nan")
    return float(np.average(x[ok].to_numpy(dtype=float), weights=w[ok].to_numpy(dtype=float)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--study-csv",
        type=Path,
        default=ROOT / "outputs" / "maps" / "study_area_tract_rankings.csv",
    )
    ap.add_argument(
        "--nta-csv",
        type=Path,
        default=ROOT / "outputs" / "maps" / "manhattan_nta_rankings.csv",
    )
    ap.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "outputs" / "maps" / "peer_nta_comparison.csv",
    )
    ap.add_argument("--print-md", action="store_true", help="Print a markdown table to stdout")
    args = ap.parse_args()

    study = pd.read_csv(args.study_csv)
    nta = pd.read_csv(args.nta_csv)

    if "area_km2" not in study.columns:
        sys.exit("study CSV missing area_km2")
    w = pd.to_numeric(study["area_km2"], errors="coerce").fillna(0.0)
    study_row: dict = {
        "region_type": "study_polygon",
        "nta2020": "",
        "label": "Houston–Canal (tracts intersecting study polygon)",
        "n_tracts": int(len(study)),
        "area_km2": float(w.sum()),
    }
    for c in CORE_COMPARE:
        if c in study.columns:
            study_row[c] = _wmean(study, c)

    rows: list[dict] = [study_row]
    for code, short in DEFAULT_PEERS.items():
        hit = nta[nta["nta2020"].astype(str) == code]
        if hit.empty:
            sys.stderr.write(f"Warning: NTA {code} not in {args.nta_csv}\n")
            continue
        r = hit.iloc[0].to_dict()
        peer: dict = {
            "region_type": "nta2020",
            "nta2020": code,
            "label": f"{short} ({r.get('ntaname', code)})",
            "n_tracts": int(r.get("n_tracts", 0)),
            "area_km2": float(r.get("area_km2", float("nan"))),
        }
        for c in CORE_COMPARE:
            awm = f"{c}_awm"
            if awm in hit.columns:
                peer[c] = float(hit.iloc[0][awm])
            elif c in hit.columns:
                peer[c] = float(hit.iloc[0][c])
            else:
                peer[c] = float("nan")
        # NTA file has borough-wide percentile among NTAs
        if "combined_idx_nta_pctile" in r:
            peer["combined_idx_nta_pctile"] = float(r["combined_idx_nta_pctile"])
        rows.append(peer)

    out = pd.DataFrame(rows)
    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out_csv, index=False)
    print(f"Wrote {args.out_csv}")

    if args.print_md:
        print()
        cols = [c for c in out.columns if c not in ("region_type",)]
        print("| " + " | ".join(cols) + " |")
        print("| " + " | ".join("---" for _ in cols) + " |")
        for _, row in out.iterrows():
            cells = []
            for c in cols:
                v = row[c]
                if isinstance(v, float) and np.isfinite(v):
                    cells.append(f"{v:.2f}" if abs(v) < 1000 else f"{v:.1f}")
                else:
                    cells.append("" if pd.isna(v) else str(v))
            print("| " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
