"""
LTN Suitability Analysis Module for NYC Pedestrian Spatial Analysis

Weighted overlay analysis identifying high-potential Low Traffic
Neighborhood locations based on multiple criteria.

Author: Alexander Huang
"""

import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.stats import rankdata

from src import (
    PROCESSED_DATA_DIR,
    ANALYSIS_DIR,
    DEFAULT_CRS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Analysis output directory
SUITABILITY_DIR = ANALYSIS_DIR / "suitability"


@dataclass
class SuitabilityCriteria:
    """Configuration for suitability analysis criteria."""

    # Weights must sum to 1.0
    weights: dict = field(default_factory=lambda: {
        "pedestrian_volume": 0.20,
        "transit_access": 0.15,
        "low_vehicle_ownership": 0.15,
        "crash_rate": 0.15,
        "commercial_frontage": 0.10,
        "residential_density": 0.10,
        "street_width": 0.10,
        "cut_through_potential": 0.05,
    })

    # Direction: True = higher is better, False = lower is better
    directions: dict = field(default_factory=lambda: {
        "pedestrian_volume": True,  # Higher volume = better candidate
        "transit_access": False,  # Closer to transit = better (lower distance)
        "low_vehicle_ownership": True,  # Higher % no vehicle = better
        "crash_rate": True,  # Higher crash rate = higher priority
        "commercial_frontage": True,  # More retail = better
        "residential_density": True,  # Higher density = better
        "street_width": False,  # Narrower streets = better for pedestrians
        "cut_through_potential": True,  # Higher cut-through = higher priority
    })

    def validate(self):
        """Validate that weights sum to 1.0."""
        total = sum(self.weights.values())
        if not np.isclose(total, 1.0, atol=0.01):
            raise ValueError(f"Weights must sum to 1.0, got {total}")
        return True


def normalize_values(
    values: np.ndarray,
    higher_is_better: bool = True,
    method: str = "minmax",
) -> np.ndarray:
    """
    Normalize values to 0-1 scale.

    Args:
        values: Array of values to normalize.
        higher_is_better: If True, higher values get higher scores.
        method: Normalization method ('minmax' or 'quantile').

    Returns:
        Normalized values between 0 and 1.
    """
    # Handle missing values
    valid_mask = ~np.isnan(values)
    result = np.zeros_like(values, dtype=float)

    if not valid_mask.any():
        return result

    valid_values = values[valid_mask]

    if method == "quantile":
        # Rank-based normalization
        ranks = rankdata(valid_values, method="average")
        normalized = (ranks - 1) / (len(ranks) - 1) if len(ranks) > 1 else np.ones_like(ranks)
    else:  # minmax
        v_min = valid_values.min()
        v_max = valid_values.max()
        if v_max == v_min:
            normalized = np.ones_like(valid_values) * 0.5
        else:
            normalized = (valid_values - v_min) / (v_max - v_min)

    # Flip if lower is better
    if not higher_is_better:
        normalized = 1 - normalized

    result[valid_mask] = normalized
    return result


def calculate_pedestrian_score(
    gdf: gpd.GeoDataFrame,
    pedestrian_data: gpd.GeoDataFrame,
    buffer_distance: float = 300.0,
) -> pd.Series:
    """
    Calculate pedestrian volume score for each area.

    Args:
        gdf: Analysis units (tracts, streets, or grid cells).
        pedestrian_data: Pedestrian demand data with volume information.
        buffer_distance: Search radius in feet.

    Returns:
        Series of pedestrian volume scores.
    """
    logger.info("Calculating pedestrian volume scores...")

    if len(pedestrian_data) == 0 or "pedestrian_volume" not in pedestrian_data.columns:
        logger.warning("No pedestrian volume data available")
        return pd.Series(0.5, index=gdf.index)

    # Ensure same CRS
    if pedestrian_data.crs != gdf.crs:
        pedestrian_data = pedestrian_data.to_crs(gdf.crs)

    scores = []
    for idx, row in gdf.iterrows():
        # Find nearby pedestrian count points
        nearby = pedestrian_data[
            pedestrian_data.geometry.distance(row.geometry) <= buffer_distance
        ]
        if len(nearby) > 0:
            # Use maximum volume in the area
            scores.append(nearby["pedestrian_volume"].max())
        else:
            scores.append(np.nan)

    return pd.Series(scores, index=gdf.index)


def calculate_transit_score(
    gdf: gpd.GeoDataFrame,
    subway_data: gpd.GeoDataFrame,
    bus_data: Optional[gpd.GeoDataFrame] = None,
) -> pd.Series:
    """
    Calculate transit accessibility score.

    Args:
        gdf: Analysis units.
        subway_data: Subway station locations.
        bus_data: Optional bus stop locations.

    Returns:
        Series of distances to nearest transit.
    """
    logger.info("Calculating transit accessibility scores...")

    if len(subway_data) == 0:
        logger.warning("No subway data available")
        return pd.Series(np.nan, index=gdf.index)

    # Ensure same CRS
    if subway_data.crs != gdf.crs:
        subway_data = subway_data.to_crs(gdf.crs)

    # Calculate distance to nearest subway
    distances = gdf.geometry.apply(
        lambda geom: subway_data.geometry.distance(geom.centroid).min()
    )

    # Optionally include bus stops
    if bus_data is not None and len(bus_data) > 0:
        if bus_data.crs != gdf.crs:
            bus_data = bus_data.to_crs(gdf.crs)

        bus_distances = gdf.geometry.apply(
            lambda geom: bus_data.geometry.distance(geom.centroid).min()
        )
        # Use minimum of subway or bus
        distances = pd.concat([distances, bus_distances], axis=1).min(axis=1)

    return distances


def calculate_crash_score(
    gdf: gpd.GeoDataFrame,
    crash_data: gpd.GeoDataFrame,
    buffer_distance: float = 500.0,
) -> pd.Series:
    """
    Calculate pedestrian crash rate score.

    Args:
        gdf: Analysis units.
        crash_data: Pedestrian crash data.
        buffer_distance: Search radius in feet.

    Returns:
        Series of crash counts/densities.
    """
    logger.info("Calculating crash rate scores...")

    if len(crash_data) == 0:
        logger.warning("No crash data available")
        return pd.Series(0, index=gdf.index)

    # Ensure same CRS
    if crash_data.crs != gdf.crs:
        crash_data = crash_data.to_crs(gdf.crs)

    counts = []
    for idx, row in gdf.iterrows():
        # Count crashes within buffer
        nearby = crash_data[
            crash_data.geometry.distance(row.geometry.centroid) <= buffer_distance
        ]
        counts.append(len(nearby))

    return pd.Series(counts, index=gdf.index)


def calculate_vehicle_ownership_score(
    gdf: gpd.GeoDataFrame,
    census_data: gpd.GeoDataFrame,
) -> pd.Series:
    """
    Calculate low vehicle ownership score from census data.

    Args:
        gdf: Analysis units.
        census_data: Census tract data with vehicle ownership.

    Returns:
        Series of % zero-vehicle households.
    """
    logger.info("Calculating vehicle ownership scores...")

    if len(census_data) == 0 or "pct_no_vehicle" not in census_data.columns:
        logger.warning("No vehicle ownership data available")
        return pd.Series(0.5, index=gdf.index)

    # Ensure same CRS
    if census_data.crs != gdf.crs:
        census_data = census_data.to_crs(gdf.crs)

    # Spatial join to get census values
    joined = gpd.sjoin(gdf, census_data[["geometry", "pct_no_vehicle"]], how="left")

    # Handle duplicates from spatial join
    result = joined.groupby(joined.index)["pct_no_vehicle"].mean()

    return result.reindex(gdf.index)


def run_suitability_analysis(
    analysis_units: Optional[gpd.GeoDataFrame] = None,
    pedestrian_data: Optional[gpd.GeoDataFrame] = None,
    crash_data: Optional[gpd.GeoDataFrame] = None,
    census_data: Optional[gpd.GeoDataFrame] = None,
    subway_data: Optional[gpd.GeoDataFrame] = None,
    bus_data: Optional[gpd.GeoDataFrame] = None,
    criteria: Optional[SuitabilityCriteria] = None,
    output_dir: Optional[Path] = None,
) -> gpd.GeoDataFrame:
    """
    Run complete LTN suitability analysis.

    Args:
        analysis_units: Base geometry for analysis (census tracts if None).
        pedestrian_data: Pedestrian demand data.
        crash_data: Pedestrian crash data.
        census_data: Census demographic data.
        subway_data: Subway station locations.
        bus_data: Bus stop locations.
        criteria: Suitability criteria configuration.
        output_dir: Directory for outputs.

    Returns:
        GeoDataFrame with suitability scores.
    """
    output_dir = output_dir or SUITABILITY_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    criteria = criteria or SuitabilityCriteria()
    criteria.validate()

    logger.info("=" * 50)
    logger.info("Running LTN Suitability Analysis")
    logger.info("=" * 50)

    # Load data if not provided
    if analysis_units is None:
        census_path = PROCESSED_DATA_DIR / "census_data_processed.geojson"
        if census_path.exists():
            analysis_units = gpd.read_file(census_path)
            census_data = analysis_units
        else:
            raise FileNotFoundError("No analysis units provided and census data not found")

    if pedestrian_data is None:
        ped_path = PROCESSED_DATA_DIR / "pedestrian_demand_processed.geojson"
        if ped_path.exists():
            pedestrian_data = gpd.read_file(ped_path)
        else:
            pedestrian_data = gpd.GeoDataFrame()

    if crash_data is None:
        crash_path = PROCESSED_DATA_DIR / "crash_data_processed.geojson"
        if crash_path.exists():
            crash_data = gpd.read_file(crash_path)
        else:
            crash_data = gpd.GeoDataFrame()

    if subway_data is None:
        subway_path = PROCESSED_DATA_DIR / "subway_stations_processed.geojson"
        if subway_path.exists():
            subway_data = gpd.read_file(subway_path)
        else:
            subway_data = gpd.GeoDataFrame()

    # Start with analysis units
    result = analysis_units.copy()

    # Calculate individual scores
    raw_scores = {}

    # Pedestrian volume
    raw_scores["pedestrian_volume"] = calculate_pedestrian_score(
        result, pedestrian_data
    )

    # Transit access
    raw_scores["transit_access"] = calculate_transit_score(
        result, subway_data, bus_data
    )

    # Crash rate
    raw_scores["crash_rate"] = calculate_crash_score(result, crash_data)

    # Vehicle ownership (from census if available)
    if census_data is not None:
        raw_scores["low_vehicle_ownership"] = calculate_vehicle_ownership_score(
            result, census_data
        )
    else:
        raw_scores["low_vehicle_ownership"] = pd.Series(0.5, index=result.index)

    # Normalize and weight scores
    logger.info("Normalizing and weighting scores...")

    weighted_scores = pd.DataFrame(index=result.index)

    for criterion, raw_values in raw_scores.items():
        if criterion in criteria.weights:
            weight = criteria.weights[criterion]
            higher_is_better = criteria.directions.get(criterion, True)

            # Normalize
            normalized = normalize_values(
                raw_values.values,
                higher_is_better=higher_is_better,
                method="quantile",
            )

            # Store raw and normalized
            result[f"{criterion}_raw"] = raw_values
            result[f"{criterion}_norm"] = normalized

            # Weight
            weighted_scores[criterion] = normalized * weight

    # Calculate composite score
    result["suitability_score"] = weighted_scores.sum(axis=1)

    # Rank areas
    result["suitability_rank"] = result["suitability_score"].rank(
        ascending=False, method="min"
    ).astype(int)

    # Categorize
    result["suitability_category"] = pd.qcut(
        result["suitability_score"],
        q=5,
        labels=["Very Low", "Low", "Medium", "High", "Very High"],
    )

    # Save results
    result.to_file(output_dir / "suitability_results.geojson", driver="GeoJSON")

    # Create summary of top candidates
    top_20 = result.nsmallest(20, "suitability_rank")[
        ["suitability_score", "suitability_rank", "suitability_category"]
        + [c for c in result.columns if c.endswith("_raw")]
    ]
    top_20.to_csv(output_dir / "top_20_candidates.csv")

    # Summary statistics
    summary = {
        "total_units": len(result),
        "mean_score": result["suitability_score"].mean(),
        "max_score": result["suitability_score"].max(),
        "high_suitability_count": (result["suitability_category"] == "Very High").sum(),
        "criteria_weights": criteria.weights,
    }

    pd.DataFrame([summary]).to_csv(output_dir / "suitability_summary.csv", index=False)

    logger.info("=" * 50)
    logger.info("Suitability analysis complete")
    logger.info(f"Top score: {summary['max_score']:.3f}")
    logger.info(f"Very High suitability areas: {summary['high_suitability_count']}")
    logger.info(f"Results saved to {output_dir}")
    logger.info("=" * 50)

    return result


if __name__ == "__main__":
    run_suitability_analysis()
