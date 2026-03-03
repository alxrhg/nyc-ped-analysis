"""Analysis helpers for NYC pedestrian collision data.

These helpers are designed to work with the NYC Open Data "Motor Vehicle
Collisions - Crashes" export. Only a small column subset is required:

- CRASH DATE
- BOROUGH
- LATITUDE
- LONGITUDE
- ON STREET NAME (optional, for location summaries)
- NUMBER OF PEDESTRIANS INJURED
- NUMBER OF PEDESTRIANS KILLED

The code avoids heavy geo dependencies and focuses on tabular summaries that can
be consumed by mapping tools or downstream notebooks.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

# Column constants to avoid typos when renaming or accessing fields.
COL_CRASH_DATE = "CRASH DATE"
COL_BOROUGH = "BOROUGH"
COL_LAT = "LATITUDE"
COL_LON = "LONGITUDE"
COL_STREET = "ON STREET NAME"
COL_PED_INJURED = "NUMBER OF PEDESTRIANS INJURED"
COL_PED_KILLED = "NUMBER OF PEDESTRIANS KILLED"


@dataclass
class LocationSummary:
    """Aggregated counts for a unique on-street location."""

    street: str
    collisions: int
    pedestrians_injured: int
    pedestrians_killed: int


@dataclass
class BoroughSummary:
    """Aggregated counts for a borough."""

    borough: str
    collisions: int
    pedestrians_injured: int
    pedestrians_killed: int


@dataclass
class MonthlyTrend:
    """Time series of collisions and pedestrian injuries per month."""

    month: str
    collisions: int
    pedestrians_injured: int
    pedestrians_killed: int


def load_collision_data(csv_path: str | Path) -> pd.DataFrame:
    """Load collision data from a CSV file.

    The loader keeps only columns relevant for pedestrian analysis and parses
    crash dates into datetime objects for downstream grouping.
    """

    required_columns = [
        COL_CRASH_DATE,
        COL_BOROUGH,
        COL_LAT,
        COL_LON,
        COL_PED_INJURED,
        COL_PED_KILLED,
    ]
    optional_columns = [COL_STREET]

    df = pd.read_csv(csv_path, parse_dates=[COL_CRASH_DATE], low_memory=False)
    present_columns = df.columns.intersection(required_columns + optional_columns)
    missing = set(required_columns) - set(present_columns)
    if missing:
        missing_list = ", ".join(sorted(missing))
        raise ValueError(
            f"Input file is missing required columns: {missing_list}"
        )
    return df[present_columns]


def clean_collision_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize and filter collision data for analysis."""

    working = df.copy()

    # Standardize coordinate values and drop rows missing usable geometry.
    for coord in (COL_LAT, COL_LON):
        working[coord] = pd.to_numeric(working[coord], errors="coerce")
    working = working.dropna(subset=[COL_LAT, COL_LON])

    # Ensure numeric injury and fatality counts even if the CSV stores strings.
    for column in [COL_PED_INJURED, COL_PED_KILLED]:
        working[column] = pd.to_numeric(working[column], errors="coerce").fillna(0)

    # Replace unknown boroughs with a consistent placeholder for grouping.
    working[COL_BOROUGH] = (
        working[COL_BOROUGH]
        .fillna("UNKNOWN")
        .astype(str)
        .str.strip()
        .replace("", "UNKNOWN")
        .str.upper()
    )

    # Normalize street names if present.
    if COL_STREET in working.columns:
        working[COL_STREET] = (
            working[COL_STREET]
            .fillna("(no street reported)")
            .astype(str)
            .str.strip()
            .replace("", "(no street reported)")
            .str.upper()
        )

    return working


def compute_borough_summary(df: pd.DataFrame) -> list[BoroughSummary]:
    """Aggregate collisions and pedestrian impacts by borough."""

    grouped = df.groupby(COL_BOROUGH).agg(
        collisions=(COL_CRASH_DATE, "count"),
        pedestrians_injured=(COL_PED_INJURED, "sum"),
        pedestrians_killed=(COL_PED_KILLED, "sum"),
    )
    return [
        BoroughSummary(
            borough=borough,
            collisions=int(row.collisions),
            pedestrians_injured=int(row.pedestrians_injured),
            pedestrians_killed=int(row.pedestrians_killed),
        )
        for borough, row in grouped.sort_values("collisions", ascending=False).iterrows()
    ]


def compute_top_locations(df: pd.DataFrame, limit: int = 10) -> list[LocationSummary]:
    """Identify locations with the most pedestrian injuries.

    Results default to the top 10 on-street locations but can be adjusted using
    the ``limit`` parameter.
    """

    if limit <= 0:
        raise ValueError("limit must be positive")

    if COL_STREET not in df.columns:
        return []

    grouped = df.groupby(COL_STREET).agg(
        collisions=(COL_CRASH_DATE, "count"),
        pedestrians_injured=(COL_PED_INJURED, "sum"),
        pedestrians_killed=(COL_PED_KILLED, "sum"),
    )
    top = grouped.sort_values("pedestrians_injured", ascending=False).head(limit)

    return [
        LocationSummary(
            street=street,
            collisions=int(row.collisions),
            pedestrians_injured=int(row.pedestrians_injured),
            pedestrians_killed=int(row.pedestrians_killed),
        )
        for street, row in top.iterrows()
    ]


def compute_monthly_trend(df: pd.DataFrame) -> list[MonthlyTrend]:
    """Generate a monthly time series for collisions and injuries."""

    if COL_CRASH_DATE not in df.columns:
        return []

    working = df.copy()
    working["MONTH"] = working[COL_CRASH_DATE].dt.to_period("M").dt.to_timestamp()
    grouped = working.groupby("MONTH").agg(
        collisions=(COL_CRASH_DATE, "count"),
        pedestrians_injured=(COL_PED_INJURED, "sum"),
        pedestrians_killed=(COL_PED_KILLED, "sum"),
    )

    return [
        MonthlyTrend(
            month=row.name.strftime("%Y-%m"),
            collisions=int(row.collisions),
            pedestrians_injured=int(row.pedestrians_injured),
            pedestrians_killed=int(row.pedestrians_killed),
        )
        for row in grouped.sort_index().itertuples()
    ]


def build_summary(df: pd.DataFrame, top_location_limit: int = 10) -> dict:
    """Build a JSON-serializable summary bundle for reporting."""

    if top_location_limit <= 0:
        raise ValueError("top_location_limit must be positive")

    boroughs = compute_borough_summary(df)
    locations = compute_top_locations(df, limit=top_location_limit)
    trend = compute_monthly_trend(df)

    return {
        "boroughs": [borough.__dict__ for borough in boroughs],
        "top_locations": [location.__dict__ for location in locations],
        "monthly_trend": [entry.__dict__ for entry in trend],
    }
