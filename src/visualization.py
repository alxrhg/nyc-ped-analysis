"""
Visualization Module for NYC Pedestrian Spatial Analysis

Creates static and interactive maps for thesis deliverables.

Author: Alexander Huang
"""

import logging
from pathlib import Path
from typing import Optional, List, Tuple

import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import folium
from folium.plugins import HeatMap, MarkerCluster

from src import (
    PROCESSED_DATA_DIR,
    ANALYSIS_DIR,
    OUTPUT_DIR,
    MAPS_DIR,
    FIGURES_DIR,
    DEFAULT_CRS,
    GEOGRAPHIC_CRS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Colorblind-friendly palettes
SEQUENTIAL_CMAP = "YlOrRd"  # Yellow-Orange-Red
DIVERGING_CMAP = "RdYlBu_r"  # Red-Yellow-Blue (reversed)
CATEGORICAL_COLORS = [
    "#1b9e77",  # Teal
    "#d95f02",  # Orange
    "#7570b3",  # Purple
    "#e7298a",  # Pink
    "#66a61e",  # Green
]

# Suitability category colors
SUITABILITY_COLORS = {
    "Very Low": "#2c7bb6",
    "Low": "#abd9e9",
    "Medium": "#ffffbf",
    "High": "#fdae61",
    "Very High": "#d7191c",
}


def setup_map_style():
    """Configure matplotlib for publication-quality maps."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "figure.titlesize": 14,
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


def add_basemap(ax, source: str = "CartoDB positron"):
    """
    Add a contextual basemap to matplotlib axes.

    Args:
        ax: Matplotlib axes.
        source: Basemap source (uses contextily).
    """
    try:
        import contextily as ctx
        ctx.add_basemap(ax, source=ctx.providers.CartoDB.Positron, crs=GEOGRAPHIC_CRS)
    except Exception as e:
        logger.warning(f"Could not add basemap: {e}")


def create_study_area_map(
    study_areas: gpd.GeoDataFrame,
    context_data: Optional[gpd.GeoDataFrame] = None,
    output_path: Optional[Path] = None,
    title: str = "Study Areas",
) -> plt.Figure:
    """
    Create a context map showing study areas.

    Args:
        study_areas: GeoDataFrame with study area polygons.
        context_data: Optional background context (e.g., borough boundaries).
        output_path: Path to save figure.
        title: Map title.

    Returns:
        Matplotlib figure.
    """
    setup_map_style()

    fig, ax = plt.subplots(figsize=(10, 12))

    # Reproject for mapping
    study_areas_wgs = study_areas.to_crs(GEOGRAPHIC_CRS)

    # Plot context if available
    if context_data is not None:
        context_wgs = context_data.to_crs(GEOGRAPHIC_CRS)
        context_wgs.boundary.plot(ax=ax, color="gray", linewidth=0.5, alpha=0.5)

    # Plot study areas
    study_areas_wgs.plot(
        ax=ax,
        color=CATEGORICAL_COLORS[0],
        edgecolor="black",
        linewidth=2,
        alpha=0.3,
    )

    # Add labels
    for idx, row in study_areas_wgs.iterrows():
        centroid = row.geometry.centroid
        name = row.get("name", f"Area {idx}")
        ax.annotate(
            name,
            xy=(centroid.x, centroid.y),
            fontsize=9,
            ha="center",
            fontweight="bold",
        )

    # Add basemap
    add_basemap(ax)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # Add north arrow and scale bar
    add_map_elements(ax)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path)
        logger.info(f"Saved study area map to {output_path}")

    return fig


def create_crash_heatmap(
    crash_data: gpd.GeoDataFrame,
    study_area: Optional[gpd.GeoDataFrame] = None,
    output_path: Optional[Path] = None,
    title: str = "Pedestrian Crash Hotspots",
) -> plt.Figure:
    """
    Create a heatmap of pedestrian crashes.

    Args:
        crash_data: GeoDataFrame with crash points.
        study_area: Optional study area boundary.
        output_path: Path to save figure.
        title: Map title.

    Returns:
        Matplotlib figure.
    """
    setup_map_style()

    fig, ax = plt.subplots(figsize=(10, 12))

    # Reproject for mapping
    crashes_wgs = crash_data.to_crs(GEOGRAPHIC_CRS)

    # Plot study area boundary if available
    if study_area is not None:
        study_wgs = study_area.to_crs(GEOGRAPHIC_CRS)
        study_wgs.boundary.plot(ax=ax, color="black", linewidth=2)

    # Create hexbin heatmap
    x = crashes_wgs.geometry.x
    y = crashes_wgs.geometry.y

    hb = ax.hexbin(
        x, y,
        gridsize=50,
        cmap=SEQUENTIAL_CMAP,
        mincnt=1,
        alpha=0.7,
    )

    # Add colorbar
    cbar = plt.colorbar(hb, ax=ax, shrink=0.6, label="Crash Count")

    # Add basemap
    add_basemap(ax)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    add_map_elements(ax)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path)
        logger.info(f"Saved crash heatmap to {output_path}")

    return fig


def create_suitability_map(
    suitability_data: gpd.GeoDataFrame,
    score_column: str = "suitability_score",
    category_column: str = "suitability_category",
    output_path: Optional[Path] = None,
    title: str = "LTN Suitability Analysis",
) -> plt.Figure:
    """
    Create a choropleth map of suitability scores.

    Args:
        suitability_data: GeoDataFrame with suitability results.
        score_column: Column with continuous scores.
        category_column: Column with categorical labels.
        output_path: Path to save figure.
        title: Map title.

    Returns:
        Matplotlib figure.
    """
    setup_map_style()

    fig, axes = plt.subplots(1, 2, figsize=(16, 10))

    # Reproject for mapping
    data_wgs = suitability_data.to_crs(GEOGRAPHIC_CRS)

    # Left: Continuous score
    ax1 = axes[0]
    data_wgs.plot(
        column=score_column,
        cmap=SEQUENTIAL_CMAP,
        legend=True,
        legend_kwds={"shrink": 0.6, "label": "Suitability Score"},
        ax=ax1,
        edgecolor="white",
        linewidth=0.3,
    )
    add_basemap(ax1)
    ax1.set_title("Continuous Score", fontsize=12, fontweight="bold")

    # Right: Categorical
    ax2 = axes[1]

    # Create categorical plot with custom colors
    if category_column in data_wgs.columns:
        for cat, color in SUITABILITY_COLORS.items():
            subset = data_wgs[data_wgs[category_column] == cat]
            if len(subset) > 0:
                subset.plot(ax=ax2, color=color, edgecolor="white", linewidth=0.3)

        # Add legend
        legend_elements = [
            Patch(facecolor=color, label=cat)
            for cat, color in SUITABILITY_COLORS.items()
        ]
        ax2.legend(handles=legend_elements, loc="lower right", title="Suitability")

    add_basemap(ax2)
    ax2.set_title("Categorical", fontsize=12, fontweight="bold")

    fig.suptitle(title, fontsize=14, fontweight="bold", y=1.02)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path)
        logger.info(f"Saved suitability map to {output_path}")

    return fig


def create_interactive_map(
    layers: dict,
    center: Tuple[float, float] = (40.7128, -74.0060),
    zoom: int = 13,
    output_path: Optional[Path] = None,
) -> folium.Map:
    """
    Create an interactive Folium map with multiple layers.

    Args:
        layers: Dictionary of {name: GeoDataFrame} for each layer.
        center: Map center (lat, lon).
        zoom: Initial zoom level.
        output_path: Path to save HTML file.

    Returns:
        Folium map object.
    """
    logger.info("Creating interactive map...")

    # Create base map
    m = folium.Map(
        location=center,
        zoom_start=zoom,
        tiles="cartodbpositron",
    )

    # Add layers
    for name, gdf in layers.items():
        if len(gdf) == 0:
            continue

        # Reproject to WGS84
        gdf_wgs = gdf.to_crs(GEOGRAPHIC_CRS)

        # Create feature group
        fg = folium.FeatureGroup(name=name)

        # Add features based on geometry type
        geom_type = gdf_wgs.geometry.iloc[0].geom_type

        if geom_type == "Point":
            # Add points as markers or heatmap
            if len(gdf_wgs) > 1000:
                # Use heatmap for many points
                heat_data = [
                    [row.geometry.y, row.geometry.x]
                    for _, row in gdf_wgs.iterrows()
                ]
                HeatMap(heat_data, radius=15, blur=10).add_to(fg)
            else:
                # Use marker cluster
                marker_cluster = MarkerCluster().add_to(fg)
                for _, row in gdf_wgs.iterrows():
                    folium.CircleMarker(
                        location=[row.geometry.y, row.geometry.x],
                        radius=5,
                        color=CATEGORICAL_COLORS[0],
                        fill=True,
                    ).add_to(marker_cluster)

        elif geom_type in ["Polygon", "MultiPolygon"]:
            # Add polygons with choropleth if score column exists
            if "suitability_score" in gdf_wgs.columns:
                # Choropleth style
                def style_function(feature):
                    score = feature["properties"].get("suitability_score", 0)
                    # Normalize score to color
                    normalized = min(1, max(0, score))
                    color = plt.cm.YlOrRd(normalized)
                    hex_color = mcolors.to_hex(color)
                    return {
                        "fillColor": hex_color,
                        "color": "black",
                        "weight": 1,
                        "fillOpacity": 0.6,
                    }

                folium.GeoJson(
                    gdf_wgs,
                    style_function=style_function,
                    tooltip=folium.GeoJsonTooltip(
                        fields=["suitability_score", "suitability_category"]
                        if "suitability_category" in gdf_wgs.columns
                        else ["suitability_score"],
                    ),
                ).add_to(fg)
            else:
                folium.GeoJson(
                    gdf_wgs,
                    style_function=lambda x: {
                        "fillColor": CATEGORICAL_COLORS[0],
                        "color": "black",
                        "weight": 1,
                        "fillOpacity": 0.5,
                    },
                ).add_to(fg)

        else:  # LineString
            folium.GeoJson(
                gdf_wgs,
                style_function=lambda x: {
                    "color": CATEGORICAL_COLORS[1],
                    "weight": 2,
                },
            ).add_to(fg)

        fg.add_to(m)

    # Add layer control
    folium.LayerControl().add_to(m)

    # Save map
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        m.save(str(output_path))
        logger.info(f"Saved interactive map to {output_path}")

    return m


def add_map_elements(ax, scale_bar: bool = True, north_arrow: bool = True):
    """Add scale bar and north arrow to map."""
    # This is a simplified implementation
    # For production, consider using matplotlib-scalebar

    if north_arrow:
        # Add simple north arrow text
        ax.annotate(
            "N",
            xy=(0.95, 0.95),
            xycoords="axes fraction",
            fontsize=14,
            fontweight="bold",
            ha="center",
            va="center",
        )
        ax.annotate(
            "",
            xy=(0.95, 0.98),
            xytext=(0.95, 0.92),
            xycoords="axes fraction",
            arrowprops=dict(arrowstyle="->", color="black"),
        )


def create_temporal_chart(
    temporal_data: dict,
    output_path: Optional[Path] = None,
) -> plt.Figure:
    """
    Create temporal analysis charts.

    Args:
        temporal_data: Dictionary with temporal analysis results.
        output_path: Path to save figure.

    Returns:
        Matplotlib figure.
    """
    setup_map_style()

    n_charts = len(temporal_data)
    fig, axes = plt.subplots(1, n_charts, figsize=(5 * n_charts, 4))

    if n_charts == 1:
        axes = [axes]

    for ax, (key, data) in zip(axes, temporal_data.items()):
        if isinstance(data, pd.DataFrame):
            if "n_crashes" in data.columns:
                data["n_crashes"].plot(kind="bar", ax=ax, color=CATEGORICAL_COLORS[0])
            else:
                data.iloc[:, 0].plot(kind="bar", ax=ax, color=CATEGORICAL_COLORS[0])

        ax.set_title(key.replace("_", " ").title())
        ax.set_xlabel("")
        ax.tick_params(axis="x", rotation=45)

    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path)
        logger.info(f"Saved temporal chart to {output_path}")

    return fig


def generate_all_maps(output_dir: Optional[Path] = None) -> dict:
    """
    Generate all thesis maps from analysis outputs.

    Args:
        output_dir: Directory for map outputs.

    Returns:
        Dictionary of generated map paths.
    """
    output_dir = output_dir or MAPS_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 50)
    logger.info("Generating all maps")
    logger.info("=" * 50)

    maps = {}

    # Load data
    suitability_path = ANALYSIS_DIR / "suitability" / "suitability_results.geojson"
    crash_path = PROCESSED_DATA_DIR / "crash_data_processed.geojson"

    # Suitability map
    if suitability_path.exists():
        suitability = gpd.read_file(suitability_path)
        output_path = output_dir / "suitability_map.png"
        create_suitability_map(suitability, output_path=output_path)
        maps["suitability"] = output_path

        # Interactive version
        interactive_path = output_dir / "suitability_interactive.html"
        create_interactive_map(
            {"Suitability": suitability},
            output_path=interactive_path,
        )
        maps["suitability_interactive"] = interactive_path

    # Crash heatmap
    if crash_path.exists():
        crashes = gpd.read_file(crash_path)
        output_path = output_dir / "crash_heatmap.png"
        create_crash_heatmap(crashes, output_path=output_path)
        maps["crashes"] = output_path

    logger.info("=" * 50)
    logger.info(f"Generated {len(maps)} maps")
    logger.info("=" * 50)

    return maps


if __name__ == "__main__":
    generate_all_maps()
