"""Aggregate NYC PLUTO tax-lot units to 2020 census tracts (Manhattan)."""

from __future__ import annotations

import os
from typing import Optional

import numpy as np
import pandas as pd
import requests

# Primary Land Use Tax Lot Output (PLUTO), tabular — includes units + tract link.
PLUTO_URL = "https://data.cityofnewyork.us/resource/64uk-42ks.json"


def _bct2020_to_manhattan_geoid(bct: object) -> Optional[str]:
    """PLUTO ``bct2020`` is 7 chars: borough (1) + 2020 tract (6). Manhattan → GEOID 36061…"""
    if bct is None or (isinstance(bct, float) and pd.isna(bct)):
        return None
    s = str(bct).strip()
    if "." in s:
        s = s.split(".")[0]
    s = s.zfill(7)
    if len(s) != 7 or not s.isdigit():
        return None
    if s[0] != "1":
        return None
    return "36061" + s[1:]


def fetch_manhattan_pluto_unit_aggregates(
    *,
    page_size: int = 20000,
    app_token: Optional[str] = None,
) -> pd.DataFrame:
    """
    Sum ``unitsres`` and ``unitstotal`` by census tract (2020) for Manhattan lots.

    Returns columns: ``geoid``, ``pluto_unitsres``, ``pluto_unitstotal``.
    """
    headers = {}
    tok = app_token or os.environ.get("SOCRATA_APP_TOKEN")
    if tok:
        headers["X-App-Token"] = tok

    rows: list[dict] = []
    offset = 0
    while True:
        params = {
            "$select": "bct2020,unitsres,unitstotal",
            "$where": "borough='MN'",
            "$limit": page_size,
            "$offset": offset,
        }
        r = requests.get(PLUTO_URL, params=params, headers=headers, timeout=300)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    if not rows:
        return pd.DataFrame(columns=["geoid", "pluto_unitsres", "pluto_unitstotal"])

    df = pd.DataFrame(rows)
    df["geoid"] = df["bct2020"].map(_bct2020_to_manhattan_geoid)
    df = df[df["geoid"].notna()]
    ur = pd.to_numeric(df["unitsres"], errors="coerce").fillna(0).clip(lower=0)
    ut = pd.to_numeric(df["unitstotal"], errors="coerce").fillna(0).clip(lower=0)
    df = df.assign(_ur=ur, _ut=ut)
    g = df.groupby("geoid", as_index=False).agg(pluto_unitsres=("_ur", "sum"), pluto_unitstotal=("_ut", "sum"))
    return g


def residential_unit_share_percent(unitsres: pd.Series, unitstotal: pd.Series) -> pd.Series:
    """
    Percent of combined PLUTO units that are residential: 100 × Σres / Σtotal per tract.

    PLUTO ``UnitsTotal`` counts all units in the building; ``UnitsRes`` is the residential
    portion; the remainder is non-residential (office, retail, institutional, etc.), not
    broken out separately. Tracts with no reported units (Σtotal = 0) are NaN.
    """
    ur = pd.to_numeric(unitsres, errors="coerce").fillna(0).clip(lower=0)
    ut = pd.to_numeric(unitstotal, errors="coerce").fillna(0).clip(lower=0)
    out = pd.Series(np.nan, index=ur.index, dtype=float)
    ok = ut > 0
    share = 100.0 * ur[ok] / ut[ok]
    share = share.clip(upper=100.0)
    out.loc[ok] = share
    return out
