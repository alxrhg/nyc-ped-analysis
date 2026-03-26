"""Fetch NYPD Motor Vehicle Collisions from NYC Open Data (Socrata)."""

from __future__ import annotations

import os
from typing import Tuple

import geopandas as gpd
import pandas as pd
import requests

CRASHES_URL = "https://data.cityofnewyork.us/resource/h9gi-nx95.json"


def fetch_crashes_in_bbox(
    since: str,
    bbox: Tuple[float, float, float, float],
    *,
    fast: bool = False,
    app_token: str | None = None,
) -> pd.DataFrame:
    """
    Paginate crashes with coordinates inside WGS84 bbox (min_lon, min_lat, max_lon, max_lat).
    """
    if app_token is None:
        app_token = os.environ.get("SOCRATA_APP_TOKEN")
    min_lon, min_lat, max_lon, max_lat = bbox
    where = (
        f"crash_date >= '{since}T00:00:00.000' AND "
        "latitude IS NOT NULL AND longitude IS NOT NULL AND "
        f"latitude > {min_lat} AND latitude < {max_lat} AND "
        f"longitude > {min_lon} AND longitude < {max_lon}"
    )
    headers = {}
    if app_token:
        headers["X-App-Token"] = app_token
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


def crashes_df_to_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
    lon = pd.to_numeric(df["longitude"], errors="coerce")
    lat = pd.to_numeric(df["latitude"], errors="coerce")
    return gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(lon, lat),
        crs="EPSG:4326",
    ).dropna(subset=["geometry"])


def filter_crashes_to_polygon(df: pd.DataFrame, polygon) -> gpd.GeoDataFrame:
    """Keep only rows whose coordinates fall inside the study polygon."""
    gdf = crashes_df_to_gdf(df)
    return gdf[gdf.within(polygon)].copy()
