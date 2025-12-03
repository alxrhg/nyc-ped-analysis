"""
Crash Cluster Analysis Module for NYC Pedestrian Spatial Analysis

Identifies concentrations of pedestrian injuries/fatalities using
kernel density estimation and hotspot analysis.

Author: Alexander Huang
"""

import logging
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy import stats
from scipy.ndimage import gaussian_filter
from sklearn.cluster import DBSCAN

from src import (
    PROCESSED_DATA_DIR,
    ANALYSIS_DIR,
    OUTPUT_DIR,
    DEFAULT_CRS,
    GEOGRAPHIC_CRS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Analysis output directory
CRASH_ANALYSIS_DIR = ANALYSIS_DIR / "crashes"


def load_crash_data(
    input_path: Optional[Path] = None,
) -> gpd.GeoDataFrame:
    """
    Load processed crash data.

    Args:
        input_path: Path to crash data file.

    Returns:
        GeoDataFrame with crash data.
    """
    input_path = input_path or PROCESSED_DATA_DIR / "crash_data_processed.geojson"
    return gpd.read_file(input_path)


def compute_kde_density(
    gdf: gpd.GeoDataFrame,
    bandwidth: float = 200.0,
    cell_size: float = 50.0,
    weight_column: Optional[str] = None,
) -> Tuple[np.ndarray, dict]:
    """
    Compute kernel density estimation for point data.

    Args:
        gdf: GeoDataFrame with point geometries.
        bandwidth: KDE bandwidth in feet.
        cell_size: Output raster cell size in feet.
        weight_column: Optional column to use for weighting.

    Returns:
        Tuple of (density array, metadata dict with bounds and transform).
    """
    logger.info(f"Computing KDE with bandwidth={bandwidth}ft, cell_size={cell_size}ft...")

    # Extract coordinates
    coords = np.array([[geom.x, geom.y] for geom in gdf.geometry])

    # Get weights if specified
    if weight_column and weight_column in gdf.columns:
        weights = gdf[weight_column].values
    else:
        weights = None

    # Define grid extent
    x_min, y_min, x_max, y_max = gdf.total_bounds
    buffer = bandwidth * 2

    x_min -= buffer
    y_min -= buffer
    x_max += buffer
    y_max += buffer

    # Create grid
    x_grid = np.arange(x_min, x_max, cell_size)
    y_grid = np.arange(y_min, y_max, cell_size)
    xx, yy = np.meshgrid(x_grid, y_grid)

    # Compute KDE
    try:
        kernel = stats.gaussian_kde(coords.T, bw_method=bandwidth / coords.std())
        positions = np.vstack([xx.ravel(), yy.ravel()])
        density = kernel(positions).reshape(xx.shape)
    except np.linalg.LinAlgError:
        logger.warning("KDE computation failed, using histogram fallback")
        density, _, _ = np.histogram2d(
            coords[:, 0], coords[:, 1],
            bins=[len(x_grid), len(y_grid)],
            range=[[x_min, x_max], [y_min, y_max]],
        )
        density = gaussian_filter(density.T, sigma=bandwidth / cell_size)

    # Normalize to crashes per unit area
    density = density / density.sum() * len(gdf)

    metadata = {
        "x_min": x_min,
        "y_min": y_min,
        "x_max": x_max,
        "y_max": y_max,
        "cell_size": cell_size,
        "bandwidth": bandwidth,
        "n_crashes": len(gdf),
        "crs": str(gdf.crs),
    }

    logger.info(f"KDE computed: shape={density.shape}, max={density.max():.2f}")

    return density, metadata


def identify_hotspots_dbscan(
    gdf: gpd.GeoDataFrame,
    eps: float = 300.0,
    min_samples: int = 5,
) -> gpd.GeoDataFrame:
    """
    Identify crash clusters using DBSCAN.

    Args:
        gdf: GeoDataFrame with crash points.
        eps: Maximum distance between points in a cluster (feet).
        min_samples: Minimum points to form a cluster.

    Returns:
        GeoDataFrame with cluster labels and cluster summary.
    """
    logger.info(f"Identifying clusters with DBSCAN (eps={eps}ft, min_samples={min_samples})...")

    # Extract coordinates
    coords = np.array([[geom.x, geom.y] for geom in gdf.geometry])

    # Run DBSCAN
    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(coords)

    # Add cluster labels to GeoDataFrame
    result = gdf.copy()
    result["cluster_id"] = clustering.labels_

    # Count clusters (excluding noise points with label -1)
    n_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
    n_noise = (clustering.labels_ == -1).sum()

    logger.info(f"Found {n_clusters} clusters, {n_noise} noise points")

    return result


def compute_cluster_statistics(
    gdf: gpd.GeoDataFrame,
    cluster_column: str = "cluster_id",
) -> pd.DataFrame:
    """
    Compute summary statistics for each cluster.

    Args:
        gdf: GeoDataFrame with cluster labels.
        cluster_column: Name of cluster ID column.

    Returns:
        DataFrame with cluster statistics.
    """
    # Filter out noise points
    clustered = gdf[gdf[cluster_column] >= 0].copy()

    if len(clustered) == 0:
        return pd.DataFrame()

    stats_list = []

    for cluster_id in clustered[cluster_column].unique():
        cluster_points = clustered[clustered[cluster_column] == cluster_id]

        # Calculate centroid
        centroid = cluster_points.unary_union.centroid

        # Calculate statistics
        stats_dict = {
            "cluster_id": cluster_id,
            "n_crashes": len(cluster_points),
            "total_injured": cluster_points.get(
                "number_of_pedestrians_injured", pd.Series([0])
            ).sum(),
            "total_killed": cluster_points.get(
                "number_of_pedestrians_killed", pd.Series([0])
            ).sum(),
            "centroid_x": centroid.x,
            "centroid_y": centroid.y,
            "mean_severity": cluster_points.get(
                "severity_score", pd.Series([1])
            ).mean(),
        }

        # Date range
        if "crash_date" in cluster_points.columns:
            stats_dict["date_range_start"] = cluster_points["crash_date"].min()
            stats_dict["date_range_end"] = cluster_points["crash_date"].max()

        stats_list.append(stats_dict)

    stats_df = pd.DataFrame(stats_list)
    stats_df = stats_df.sort_values("n_crashes", ascending=False)

    return stats_df


def analyze_temporal_patterns(
    gdf: gpd.GeoDataFrame,
) -> dict:
    """
    Analyze temporal patterns in crash data.

    Args:
        gdf: GeoDataFrame with crash data.

    Returns:
        Dictionary with temporal analysis results.
    """
    logger.info("Analyzing temporal patterns...")

    results = {}

    # By year
    if "year" in gdf.columns:
        yearly = gdf.groupby("year").agg({
            "geometry": "count",
            "number_of_pedestrians_injured": "sum",
            "number_of_pedestrians_killed": "sum",
        }).rename(columns={"geometry": "n_crashes"})
        results["by_year"] = yearly

    # By time of day
    if "time_of_day" in gdf.columns:
        by_time = gdf.groupby("time_of_day").agg({
            "geometry": "count",
            "number_of_pedestrians_injured": "sum",
            "number_of_pedestrians_killed": "sum",
        }).rename(columns={"geometry": "n_crashes"})
        results["by_time_of_day"] = by_time

    # By day of week
    if "day_of_week" in gdf.columns:
        by_day = gdf.groupby("day_of_week").agg({
            "geometry": "count",
        }).rename(columns={"geometry": "n_crashes"})
        by_day.index = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        results["by_day_of_week"] = by_day

    # By month
    if "month" in gdf.columns:
        by_month = gdf.groupby("month").agg({
            "geometry": "count",
        }).rename(columns={"geometry": "n_crashes"})
        results["by_month"] = by_month

    return results


def create_cluster_polygons(
    gdf: gpd.GeoDataFrame,
    cluster_column: str = "cluster_id",
    buffer_distance: float = 100.0,
) -> gpd.GeoDataFrame:
    """
    Create convex hull polygons around crash clusters.

    Args:
        gdf: GeoDataFrame with cluster labels.
        cluster_column: Name of cluster ID column.
        buffer_distance: Buffer around convex hull (feet).

    Returns:
        GeoDataFrame with cluster polygons.
    """
    clustered = gdf[gdf[cluster_column] >= 0].copy()

    if len(clustered) == 0:
        return gpd.GeoDataFrame()

    polygons = []

    for cluster_id in clustered[cluster_column].unique():
        cluster_points = clustered[clustered[cluster_column] == cluster_id]

        if len(cluster_points) >= 3:
            hull = cluster_points.unary_union.convex_hull
            buffered = hull.buffer(buffer_distance)
        else:
            buffered = cluster_points.unary_union.buffer(buffer_distance)

        polygons.append({
            "cluster_id": cluster_id,
            "n_crashes": len(cluster_points),
            "geometry": buffered,
        })

    return gpd.GeoDataFrame(polygons, crs=gdf.crs)


def run_crash_analysis(
    input_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    bandwidth: float = 200.0,
    cell_size: float = 50.0,
    dbscan_eps: float = 300.0,
    dbscan_min_samples: int = 5,
) -> dict:
    """
    Run complete crash cluster analysis.

    Args:
        input_path: Path to processed crash data.
        output_dir: Directory for analysis outputs.
        bandwidth: KDE bandwidth in feet.
        cell_size: KDE cell size in feet.
        dbscan_eps: DBSCAN epsilon parameter.
        dbscan_min_samples: DBSCAN minimum samples.

    Returns:
        Dictionary with analysis results.
    """
    output_dir = output_dir or CRASH_ANALYSIS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 50)
    logger.info("Running Crash Cluster Analysis")
    logger.info("=" * 50)

    # Load data
    crashes = load_crash_data(input_path)
    logger.info(f"Loaded {len(crashes)} crash records")

    results = {"n_crashes": len(crashes)}

    # Compute KDE
    density, kde_metadata = compute_kde_density(
        crashes,
        bandwidth=bandwidth,
        cell_size=cell_size,
        weight_column="severity_score",
    )
    results["kde_metadata"] = kde_metadata

    # Save KDE as numpy array (can be converted to raster later)
    np.save(output_dir / "crash_density.npy", density)
    pd.DataFrame([kde_metadata]).to_csv(
        output_dir / "kde_metadata.csv", index=False
    )

    # DBSCAN clustering
    crashes_clustered = identify_hotspots_dbscan(
        crashes,
        eps=dbscan_eps,
        min_samples=dbscan_min_samples,
    )
    crashes_clustered.to_file(
        output_dir / "crashes_clustered.geojson",
        driver="GeoJSON",
    )

    # Cluster statistics
    cluster_stats = compute_cluster_statistics(crashes_clustered)
    if len(cluster_stats) > 0:
        cluster_stats.to_csv(output_dir / "cluster_statistics.csv", index=False)
        results["n_clusters"] = len(cluster_stats)
        results["top_clusters"] = cluster_stats.head(10).to_dict("records")

    # Cluster polygons
    cluster_polys = create_cluster_polygons(crashes_clustered)
    if len(cluster_polys) > 0:
        cluster_polys.to_file(
            output_dir / "cluster_polygons.geojson",
            driver="GeoJSON",
        )

    # Temporal analysis
    temporal = analyze_temporal_patterns(crashes)
    results["temporal"] = {}

    for key, df in temporal.items():
        df.to_csv(output_dir / f"temporal_{key}.csv")
        results["temporal"][key] = df.to_dict()

    logger.info("=" * 50)
    logger.info("Crash analysis complete")
    logger.info(f"Results saved to {output_dir}")
    logger.info("=" * 50)

    return results


if __name__ == "__main__":
    run_crash_analysis()
