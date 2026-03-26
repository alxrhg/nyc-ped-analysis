#!/usr/bin/env python3
"""
Rebuild study_area_bowery_houston_6th_canal.geojson from NYC Street Centerline (CSCL).

Boundaries (centerlines): Avenue of the Americas, Houston St (W+E), Bowery, Canal St.

Requires network and optional SOCRATA_APP_TOKEN.

Usage:
  python scripts/build_study_area_polygon.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from nycwalks.study_area_polygon import (  # noqa: E402
    build_bowery_houston_6th_canal_polygon,
    save_study_area_geojson,
)


def main() -> None:
    tok = os.environ.get("SOCRATA_APP_TOKEN")
    poly = build_bowery_houston_6th_canal_polygon(app_token=tok)
    out = ROOT / "data" / "mit" / "study_area_bowery_houston_6th_canal.geojson"
    save_study_area_geojson(
        out,
        poly,
        source_note=(
            "NYC CSCL inkn-q76z; west=AVE OF THE AMERICAS, north=W+E HOUSTON ST, "
            "east=BOWERY, south=CANAL ST"
        ),
    )
    print("Wrote", out)
    print("bounds", poly.bounds)


if __name__ == "__main__":
    main()
