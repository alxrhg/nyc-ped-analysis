#!/usr/bin/env python3
"""
Download NYPD crashes inside the study-area bounding envelope (6th Ave – Houston – Bowery – Canal).
Uses axis-aligned bounds of the CSCL-derived polygon for the Socrata query; filter to the
exact quadrilateral in GIS if needed.

Dataset: https://data.cityofnewyork.us/d/h9gi-nx95

Usage:
  python scripts/fetch_crashes_study_area.py
  python scripts/fetch_crashes_study_area.py --since 2019-01-01 --limit 20000

Requires network. For heavy use, set SOCRATA_APP_TOKEN (see https://dev.socrata.com/docs/app_tokens.html).
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nycwalks.study_area import study_area_bbox_wgs84

CRASHES_URL = "https://data.cityofnewyork.us/resource/h9gi-nx95.json"


def _build_where_clause(since: str, bbox: tuple[float, float, float, float]) -> str:
    min_lon, min_lat, max_lon, max_lat = bbox
    # crash_date is date; compare as floating_timestamp for API compatibility
    return (
        f"crash_date >= '{since}T00:00:00.000' "
        f"AND latitude IS NOT NULL AND longitude IS NOT NULL "
        f"AND latitude > {min_lat} AND latitude < {max_lat} "
        f"AND longitude > {min_lon} AND longitude < {max_lon}"
    )


def fetch_crashes(
    since: str,
    bbox: tuple[float, float, float, float],
    limit: int,
    offset: int,
    app_token: str | None,
) -> list[dict]:
    params: dict = {
        "$where": _build_where_clause(since, bbox),
        "$limit": limit,
        "$offset": offset,
        "$order": "crash_date DESC",
    }
    headers = {}
    if app_token:
        headers["X-App-Token"] = app_token
    r = requests.get(CRASHES_URL, params=params, headers=headers, timeout=120)
    r.raise_for_status()
    return r.json()


def main() -> None:
    p = argparse.ArgumentParser(description="Fetch crashes in Houston–Canal bbox")
    p.add_argument("--since", default="2019-01-01", help="YYYY-MM-DD")
    p.add_argument("--limit", type=int, default=5000, help="rows per request (max 50000)")
    p.add_argument("--out", type=Path, default=ROOT / "data/raw/crashes_houston_canal.csv")
    args = p.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)

    token = os.environ.get("SOCRATA_APP_TOKEN")
    rows = fetch_crashes(args.since, study_area_bbox_wgs84(), args.limit, 0, token)
    if not rows:
        print("No rows returned; widen bbox/date or check API.")
        return

    fieldnames = list(rows[0].keys())
    with args.out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
