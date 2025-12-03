"""
Data Processing Module for NYC Pedestrian Spatial Analysis

Cleans, transforms, and standardizes spatial data for analysis.

Author: Alexander Huang
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import box, Point
from shapely.validation import make_valid

from src import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    DEFAULT_CRS,
    GEOGRAPHIC_CRS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Study area bounding boxes (from config)
STUDY_AREAS = {
    "chinatown_soho": {
        "north": 40.7280,
        "south": 40.7130,
        "east": -73.9900,
        "west": -74.0050,
    },
    "financial_district": {
        "north": 40.7130,
        "south": 40.7000,
        "east": -74.0000,
        "west": -74.0200,
    },
    "lower_manhattan": {
        "north": 40.7400,
        "south": 40.6950,
        "east": -73.9700,
        "west": -74.0250,
    },
}


def create_study_area_polygon(area_name: str) -> gpd.GeoDataFrame:
    """
    Create a GeoDataFrame polygon for a study area.

    Args:
        area_name: Name of the study area from STUDY_AREAS.

    Returns:
        GeoDataFrame with the study area polygon.
    """
    if area_name not in STUDY_AREAS:
        raise ValueError(f"Unknown study area: {area_name}")

    bounds = STUDY_AREAS[area_name]
    polygon = box(bounds["west"], bounds["south"], bounds["east"], bounds["north"])

    gdf = gpd.GeoDataFrame(
        {"name": [area_name]},
        geometry=[polygon],
        crs=GEOGRAPHIC_CRS,
    )

    return gdf


def validate_and_fix_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Validate and fix invalid geometries.

    Args:
        gdf: Input GeoDataFrame.

    Returns:
        GeoDataFrame with valid geometries.
    """
    logger.info("Validating geometries...")

    # Check for invalid geometries
    invalid_mask = ~gdf.geometry.is_valid
    invalid_count = invalid_mask.sum()

    if invalid_count > 0:
        logger.warning(f"Found {invalid_count} invalid geometries, attempting to fix...")
        gdf.loc[invalid_mask, "geometry"] = gdf.loc[invalid_mask, "geometry"].apply(
            make_valid
        )

    # Remove empty geometries
    empty_mask = gdf.geometry.is_empty
    empty_count = empty_mask.sum()

    if empty_count > 0:
        logger.warning(f"Removing {empty_count} empty geometries")
        gdf = gdf[~empty_mask].copy()

    return gdf


def reproject_to_state_plane(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Reproject GeoDataFrame to NY State Plane (EPSG:2263).

    Args:
        gdf: Input GeoDataFrame.

    Returns:
        Reprojected GeoDataFrame.
    """
    if gdf.crs is None:
        logger.warning("No CRS defined, assuming WGS84")
        gdf = gdf.set_crs(GEOGRAPHIC_CRS)

    if gdf.crs.to_epsg() != 2263:
        logger.info(f"Reprojecting from {gdf.crs} to {DEFAULT_CRS}")
        gdf = gdf.to_crs(DEFAULT_CRS)

    return gdf


def clip_to_study_area(
    gdf: gpd.GeoDataFrame,
    study_area: str = "lower_manhattan",
) -> gpd.GeoDataFrame:
    """
    Clip a GeoDataFrame to a study area.

    Args:
        gdf: Input GeoDataFrame.
        study_area: Name of the study area.

    Returns:
        Clipped GeoDataFrame.
    """
    logger.info(f"Clipping to {study_area}...")

    study_area_gdf = create_study_area_polygon(study_area)

    # Ensure same CRS
    if gdf.crs != study_area_gdf.crs:
        study_area_gdf = study_area_gdf.to_crs(gdf.crs)

    clipped = gpd.clip(gdf, study_area_gdf)
    logger.info(f"Clipped from {len(gdf)} to {len(clipped)} features")

    return clipped


def process_crash_data(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    study_area: str = "lower_manhattan",
) -> gpd.GeoDataFrame:
    """
    Process raw crash data for analysis.

    Args:
        input_path: Path to raw crash data.
        output_path: Path to save processed data.
        study_area: Study area to clip to.

    Returns:
        Processed GeoDataFrame.
    """
    input_path = input_path or RAW_DATA_DIR / "crash_data.geojson"
    output_path = output_path or PROCESSED_DATA_DIR / "crash_data_processed.geojson"

    logger.info(f"Processing crash data from {input_path}...")

    # Load data
    gdf = gpd.read_file(input_path)
    logger.info(f"Loaded {len(gdf)} crash records")

    # Parse date columns
    if "crash_date" in gdf.columns:
        gdf["crash_date"] = pd.to_datetime(gdf["crash_date"])
        gdf["year"] = gdf["crash_date"].dt.year
        gdf["month"] = gdf["crash_date"].dt.month
        gdf["day_of_week"] = gdf["crash_date"].dt.dayofweek

    # Parse time columns
    if "crash_time" in gdf.columns:
        gdf["hour"] = pd.to_datetime(gdf["crash_time"], format="%H:%M").dt.hour

        # Categorize time of day
        def categorize_time(hour):
            if pd.isna(hour):
                return "unknown"
            elif 7 <= hour < 10:
                return "morning_peak"
            elif 10 <= hour < 16:
                return "midday"
            elif 16 <= hour < 19:
                return "evening_peak"
            else:
                return "night"

        gdf["time_of_day"] = gdf["hour"].apply(categorize_time)

    # Convert injury/fatality columns to numeric
    for col in ["number_of_pedestrians_injured", "number_of_pedestrians_killed"]:
        if col in gdf.columns:
            gdf[col] = pd.to_numeric(gdf[col], errors="coerce").fillna(0).astype(int)

    # Calculate severity score
    gdf["severity_score"] = (
        gdf.get("number_of_pedestrians_injured", 0) * 1
        + gdf.get("number_of_pedestrians_killed", 0) * 5
    )

    # Validate geometries
    gdf = validate_and_fix_geometries(gdf)

    # Clip to study area
    gdf = clip_to_study_area(gdf, study_area)

    # Reproject to State Plane
    gdf = reproject_to_state_plane(gdf)

    # Save processed data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GeoJSON")
    logger.info(f"Saved processed crash data to {output_path}")

    return gdf


def process_census_data(
    tracts_path: Optional[Path] = None,
    acs_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    study_area: str = "lower_manhattan",
) -> gpd.GeoDataFrame:
    """
    Join census tract geometries with ACS data.

    Args:
        tracts_path: Path to census tract geometries.
        acs_path: Path to ACS tabular data.
        output_path: Path to save joined data.
        study_area: Study area to clip to.

    Returns:
        GeoDataFrame with census data.
    """
    tracts_path = tracts_path or RAW_DATA_DIR / "census_tracts.geojson"
    acs_path = acs_path or RAW_DATA_DIR / "census_acs_data.csv"
    output_path = output_path or PROCESSED_DATA_DIR / "census_data_processed.geojson"

    logger.info("Processing census data...")

    # Load tract geometries
    tracts = gpd.read_file(tracts_path)
    logger.info(f"Loaded {len(tracts)} census tracts")

    # Load ACS data
    acs_data = pd.read_csv(acs_path, dtype={"GEOID": str})
    logger.info(f"Loaded ACS data with {len(acs_data)} records")

    # Find the GEOID column in tracts
    geoid_col = None
    for col in ["GEOID", "GEOID20", "GEOID10", "TRACTCE"]:
        if col in tracts.columns:
            geoid_col = col
            break

    if geoid_col is None:
        logger.error("Could not find GEOID column in tract data")
        return gpd.GeoDataFrame()

    # Join ACS data to tracts
    joined = tracts.merge(acs_data, left_on=geoid_col, right_on="GEOID", how="left")
    joined = gpd.GeoDataFrame(joined, geometry="geometry", crs=tracts.crs)

    # Validate geometries
    joined = validate_and_fix_geometries(joined)

    # Clip to study area
    joined = clip_to_study_area(joined, study_area)

    # Reproject to State Plane
    joined = reproject_to_state_plane(joined)

    # Save processed data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joined.to_file(output_path, driver="GeoJSON")
    logger.info(f"Saved processed census data to {output_path}")

    return joined


def process_transit_data(
    subway_path: Optional[Path] = None,
    bus_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    study_area: str = "lower_manhattan",
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Process transit station data.

    Args:
        subway_path: Path to subway station data.
        bus_path: Path to bus stop data.
        output_dir: Directory to save processed data.
        study_area: Study area to clip to.

    Returns:
        Tuple of (subway_gdf, bus_gdf).
    """
    subway_path = subway_path or RAW_DATA_DIR / "subway_stations.geojson"
    bus_path = bus_path or RAW_DATA_DIR / "bus_stops.geojson"
    output_dir = output_dir or PROCESSED_DATA_DIR

    logger.info("Processing transit data...")

    results = []

    for name, path, output_name in [
        ("subway", subway_path, "subway_stations_processed.geojson"),
        ("bus", bus_path, "bus_stops_processed.geojson"),
    ]:
        if path.exists():
            gdf = gpd.read_file(path)
            logger.info(f"Loaded {len(gdf)} {name} stations/stops")

            gdf = validate_and_fix_geometries(gdf)
            gdf = clip_to_study_area(gdf, study_area)
            gdf = reproject_to_state_plane(gdf)

            output_path = output_dir / output_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            gdf.to_file(output_path, driver="GeoJSON")
            logger.info(f"Saved processed {name} data to {output_path}")

            results.append(gdf)
        else:
            logger.warning(f"{name} data not found at {path}")
            results.append(gpd.GeoDataFrame())

    return tuple(results)


def process_pedestrian_demand(
    input_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    study_area: str = "lower_manhattan",
) -> gpd.GeoDataFrame:
    """
    Process pedestrian demand data for analysis.

    Args:
        input_path: Path to raw pedestrian demand data.
        output_path: Path to save processed data.
        study_area: Study area to clip to.

    Returns:
        Processed GeoDataFrame with pedestrian demand.
    """
    input_path = input_path or RAW_DATA_DIR / "pedestrian_demand.geojson"
    output_path = output_path or PROCESSED_DATA_DIR / "pedestrian_demand_processed.geojson"

    logger.info(f"Processing pedestrian demand data from {input_path}...")

    # Check if file exists
    if not input_path.exists():
        # Try CSV fallback
        csv_path = input_path.with_suffix(".csv")
        if csv_path.exists():
            logger.info(f"Loading from CSV: {csv_path}")
            df = pd.read_csv(csv_path)

            # Look for coordinate columns
            lat_cols = [c for c in df.columns if "lat" in c.lower()]
            lon_cols = [c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()]

            if lat_cols and lon_cols:
                df[lat_cols[0]] = pd.to_numeric(df[lat_cols[0]], errors="coerce")
                df[lon_cols[0]] = pd.to_numeric(df[lon_cols[0]], errors="coerce")
                valid = df[lat_cols[0]].notna() & df[lon_cols[0]].notna()
                df = df[valid].copy()

                gdf = gpd.GeoDataFrame(
                    df,
                    geometry=gpd.points_from_xy(df[lon_cols[0]], df[lat_cols[0]]),
                    crs=GEOGRAPHIC_CRS,
                )
            else:
                logger.warning("No coordinate columns found in pedestrian demand CSV")
                return gpd.GeoDataFrame()
        else:
            logger.warning(f"Pedestrian demand data not found at {input_path}")
            return gpd.GeoDataFrame()
    else:
        gdf = gpd.read_file(input_path)

    logger.info(f"Loaded {len(gdf)} pedestrian demand records")

    # Identify volume columns and standardize
    volume_cols = [
        c for c in gdf.columns
        if any(term in c.lower() for term in ["ped", "volume", "count", "demand", "flow", "total"])
        and c.lower() != "geometry"
    ]

    if volume_cols:
        # Use the first identified volume column as primary
        primary_vol_col = volume_cols[0]
        gdf["pedestrian_volume"] = pd.to_numeric(gdf[primary_vol_col], errors="coerce")
        logger.info(f"Using '{primary_vol_col}' as pedestrian volume metric")

    # Validate geometries
    gdf = validate_and_fix_geometries(gdf)

    # Clip to study area
    gdf = clip_to_study_area(gdf, study_area)

    # Reproject to State Plane
    gdf = reproject_to_state_plane(gdf)

    # Calculate volume quintiles for analysis
    if "pedestrian_volume" in gdf.columns:
        gdf["volume_quintile"] = pd.qcut(
            gdf["pedestrian_volume"].rank(method="first"),
            q=5,
            labels=["Very Low", "Low", "Medium", "High", "Very High"],
        )

    # Save processed data
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(output_path, driver="GeoJSON")
    logger.info(f"Saved processed pedestrian demand data to {output_path}")

    return gdf


def calculate_transit_accessibility(
    points_gdf: gpd.GeoDataFrame,
    subway_gdf: gpd.GeoDataFrame,
    bus_gdf: Optional[gpd.GeoDataFrame] = None,
) -> gpd.GeoDataFrame:
    """
    Calculate distance to nearest transit for each point.

    Args:
        points_gdf: GeoDataFrame with points to analyze.
        subway_gdf: GeoDataFrame with subway stations.
        bus_gdf: Optional GeoDataFrame with bus stops.

    Returns:
        GeoDataFrame with transit accessibility metrics.
    """
    logger.info("Calculating transit accessibility...")

    result = points_gdf.copy()

    # Ensure same CRS
    if subway_gdf.crs != points_gdf.crs:
        subway_gdf = subway_gdf.to_crs(points_gdf.crs)

    # Calculate distance to nearest subway
    if len(subway_gdf) > 0:
        result["dist_to_subway"] = result.geometry.apply(
            lambda geom: subway_gdf.geometry.distance(geom).min()
        )
    else:
        result["dist_to_subway"] = np.nan

    # Calculate distance to nearest bus stop
    if bus_gdf is not None and len(bus_gdf) > 0:
        if bus_gdf.crs != points_gdf.crs:
            bus_gdf = bus_gdf.to_crs(points_gdf.crs)

        result["dist_to_bus"] = result.geometry.apply(
            lambda geom: bus_gdf.geometry.distance(geom).min()
        )
    else:
        result["dist_to_bus"] = np.nan

    # Calculate combined transit access (minimum distance)
    result["dist_to_transit"] = result[["dist_to_subway", "dist_to_bus"]].min(axis=1)

    return result


def process_all_data(study_area: str = "lower_manhattan") -> dict:
    """
    Process all raw data files.

    Args:
        study_area: Study area to clip to.

    Returns:
        Dictionary of processed GeoDataFrames.
    """
    logger.info("=" * 50)
    logger.info("Processing all data")
    logger.info("=" * 50)

    results = {}

    # Create output directory
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Process crash data
    try:
        results["crashes"] = process_crash_data(study_area=study_area)
    except FileNotFoundError as e:
        logger.warning(f"Crash data not found: {e}")

    # Process census data
    try:
        results["census"] = process_census_data(study_area=study_area)
    except FileNotFoundError as e:
        logger.warning(f"Census data not found: {e}")

    # Process transit data
    try:
        subway, bus = process_transit_data(study_area=study_area)
        results["subway"] = subway
        results["bus"] = bus
    except FileNotFoundError as e:
        logger.warning(f"Transit data not found: {e}")

    # Create study area polygons
    for area_name in STUDY_AREAS:
        area_gdf = create_study_area_polygon(area_name)
        area_gdf = reproject_to_state_plane(area_gdf)
        output_path = PROCESSED_DATA_DIR / f"study_area_{area_name}.geojson"
        area_gdf.to_file(output_path, driver="GeoJSON")

    results["study_areas"] = list(STUDY_AREAS.keys())

    logger.info("=" * 50)
    logger.info("Data processing complete")
    logger.info("=" * 50)

    return results


if __name__ == "__main__":
    process_all_data()
