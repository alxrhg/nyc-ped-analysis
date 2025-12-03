"""
Equity Analysis Module for NYC Pedestrian Spatial Analysis

Assesses distributional implications of potential LTN interventions
across demographic groups and neighborhoods.

Author: Alexander Huang
"""

import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import geopandas as gpd

from src import (
    PROCESSED_DATA_DIR,
    ANALYSIS_DIR,
    OUTPUT_DIR,
    DEFAULT_CRS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Analysis output directory
EQUITY_DIR = ANALYSIS_DIR / "equity"


# Key demographic variables for equity analysis
EQUITY_VARIABLES = [
    "median_household_income",
    "pct_nonwhite",
    "pct_no_vehicle",
    "pct_transit_commute",
    "total_population",
]


def load_suitability_results(
    input_path: Optional[Path] = None,
) -> gpd.GeoDataFrame:
    """
    Load suitability analysis results.

    Args:
        input_path: Path to suitability results file.

    Returns:
        GeoDataFrame with suitability scores.
    """
    input_path = input_path or ANALYSIS_DIR / "suitability" / "suitability_results.geojson"

    if not input_path.exists():
        raise FileNotFoundError(f"Suitability results not found at {input_path}")

    return gpd.read_file(input_path)


def load_nycha_data(
    input_path: Optional[Path] = None,
) -> gpd.GeoDataFrame:
    """
    Load NYCHA public housing data.

    Args:
        input_path: Path to NYCHA data file.

    Returns:
        GeoDataFrame with NYCHA development locations.
    """
    input_path = input_path or PROCESSED_DATA_DIR / "nycha.geojson"

    # Try raw data if processed doesn't exist
    if not input_path.exists():
        from src import RAW_DATA_DIR
        input_path = RAW_DATA_DIR / "nycha.geojson"

    if not input_path.exists():
        logger.warning("NYCHA data not found")
        return gpd.GeoDataFrame()

    return gpd.read_file(input_path)


def calculate_demographic_statistics(
    gdf: gpd.GeoDataFrame,
    group_column: str = "suitability_category",
) -> pd.DataFrame:
    """
    Calculate demographic statistics by suitability category.

    Args:
        gdf: GeoDataFrame with suitability and demographic data.
        group_column: Column to group by.

    Returns:
        DataFrame with demographic statistics by group.
    """
    logger.info(f"Calculating demographic statistics by {group_column}...")

    # Identify available demographic columns
    demo_cols = [c for c in EQUITY_VARIABLES if c in gdf.columns]

    if not demo_cols:
        logger.warning("No demographic columns found")
        return pd.DataFrame()

    # Calculate statistics by group
    stats = gdf.groupby(group_column)[demo_cols].agg(["mean", "median", "std", "count"])

    # Flatten column names
    stats.columns = ["_".join(col).strip() for col in stats.columns.values]

    return stats


def compare_intervention_vs_citywide(
    gdf: gpd.GeoDataFrame,
    threshold_category: str = "Very High",
) -> pd.DataFrame:
    """
    Compare demographics of high-suitability areas to citywide averages.

    Args:
        gdf: GeoDataFrame with suitability and demographic data.
        threshold_category: Category to consider as "intervention" area.

    Returns:
        DataFrame comparing intervention areas to citywide.
    """
    logger.info("Comparing intervention areas to citywide averages...")

    demo_cols = [c for c in EQUITY_VARIABLES if c in gdf.columns]

    if not demo_cols:
        return pd.DataFrame()

    # Citywide statistics (population-weighted where applicable)
    citywide = {}
    for col in demo_cols:
        if "pct" in col.lower():
            # Percentage - use mean
            citywide[col] = gdf[col].mean()
        elif col == "median_household_income":
            # Income - use median
            citywide[col] = gdf[col].median()
        else:
            # Count - use sum or mean
            citywide[col] = gdf[col].mean()

    # High suitability statistics
    high_suit = gdf[gdf["suitability_category"] == threshold_category]

    intervention = {}
    for col in demo_cols:
        if "pct" in col.lower():
            intervention[col] = high_suit[col].mean()
        elif col == "median_household_income":
            intervention[col] = high_suit[col].median()
        else:
            intervention[col] = high_suit[col].mean()

    # Create comparison table
    comparison = pd.DataFrame({
        "citywide": citywide,
        "intervention_area": intervention,
    })

    comparison["difference"] = comparison["intervention_area"] - comparison["citywide"]
    comparison["pct_difference"] = (
        comparison["difference"] / comparison["citywide"] * 100
    ).round(1)

    return comparison


def analyze_nycha_proximity(
    suitability_gdf: gpd.GeoDataFrame,
    nycha_gdf: gpd.GeoDataFrame,
    buffer_distances: list = [500, 1000, 2640],  # feet (500ft, 1000ft, 0.5 mile)
) -> pd.DataFrame:
    """
    Analyze proximity of NYCHA developments to high-suitability areas.

    Args:
        suitability_gdf: Suitability analysis results.
        nycha_gdf: NYCHA development locations.
        buffer_distances: Buffer distances to analyze in feet.

    Returns:
        DataFrame with NYCHA proximity analysis.
    """
    logger.info("Analyzing NYCHA proximity to high-suitability areas...")

    if len(nycha_gdf) == 0:
        logger.warning("No NYCHA data available for proximity analysis")
        return pd.DataFrame()

    # Ensure same CRS
    if nycha_gdf.crs != suitability_gdf.crs:
        nycha_gdf = nycha_gdf.to_crs(suitability_gdf.crs)

    # Get high suitability areas
    high_suit = suitability_gdf[
        suitability_gdf["suitability_category"].isin(["High", "Very High"])
    ]

    if len(high_suit) == 0:
        logger.warning("No high suitability areas found")
        return pd.DataFrame()

    # Create union of high suitability areas
    high_suit_union = high_suit.unary_union

    results = []
    for dist in buffer_distances:
        # Buffer high suitability areas
        buffered = high_suit_union.buffer(dist)

        # Count NYCHA developments within buffer
        within = nycha_gdf[nycha_gdf.geometry.intersects(buffered)]

        results.append({
            "buffer_distance_ft": dist,
            "buffer_distance_miles": dist / 5280,
            "nycha_developments_within": len(within),
            "pct_of_total_nycha": len(within) / len(nycha_gdf) * 100 if len(nycha_gdf) > 0 else 0,
        })

    return pd.DataFrame(results)


def calculate_equity_index(
    gdf: gpd.GeoDataFrame,
    income_weight: float = 0.3,
    nonwhite_weight: float = 0.3,
    vehicle_weight: float = 0.2,
    transit_weight: float = 0.2,
) -> pd.Series:
    """
    Calculate a composite equity priority index.

    Higher values indicate areas that should be prioritized for equity reasons
    (lower income, higher % nonwhite, lower vehicle ownership, higher transit use).

    Args:
        gdf: GeoDataFrame with demographic data.
        income_weight: Weight for income factor.
        nonwhite_weight: Weight for race/ethnicity factor.
        vehicle_weight: Weight for vehicle ownership factor.
        transit_weight: Weight for transit use factor.

    Returns:
        Series of equity index scores.
    """
    logger.info("Calculating equity priority index...")

    scores = pd.DataFrame(index=gdf.index)

    # Income: lower is higher priority (invert normalized score)
    if "median_household_income" in gdf.columns:
        income = gdf["median_household_income"].fillna(gdf["median_household_income"].median())
        income_norm = 1 - (income - income.min()) / (income.max() - income.min())
        scores["income"] = income_norm * income_weight
    else:
        scores["income"] = 0

    # % nonwhite: higher is higher priority
    if "pct_nonwhite" in gdf.columns:
        nonwhite = gdf["pct_nonwhite"].fillna(0)
        nonwhite_norm = (nonwhite - nonwhite.min()) / (nonwhite.max() - nonwhite.min())
        scores["nonwhite"] = nonwhite_norm * nonwhite_weight
    else:
        scores["nonwhite"] = 0

    # % no vehicle: higher is higher priority
    if "pct_no_vehicle" in gdf.columns:
        no_vehicle = gdf["pct_no_vehicle"].fillna(0)
        no_vehicle_norm = (no_vehicle - no_vehicle.min()) / (no_vehicle.max() - no_vehicle.min())
        scores["no_vehicle"] = no_vehicle_norm * vehicle_weight
    else:
        scores["no_vehicle"] = 0

    # % transit commute: higher is higher priority
    if "pct_transit_commute" in gdf.columns:
        transit = gdf["pct_transit_commute"].fillna(0)
        transit_norm = (transit - transit.min()) / (transit.max() - transit.min())
        scores["transit"] = transit_norm * transit_weight
    else:
        scores["transit"] = 0

    return scores.sum(axis=1)


def run_equity_analysis(
    suitability_path: Optional[Path] = None,
    nycha_path: Optional[Path] = None,
    output_dir: Optional[Path] = None,
) -> dict:
    """
    Run complete equity analysis.

    Args:
        suitability_path: Path to suitability results.
        nycha_path: Path to NYCHA data.
        output_dir: Directory for outputs.

    Returns:
        Dictionary with analysis results.
    """
    output_dir = output_dir or EQUITY_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 50)
    logger.info("Running Equity Analysis")
    logger.info("=" * 50)

    results = {}

    # Load suitability results
    try:
        suitability = load_suitability_results(suitability_path)
        logger.info(f"Loaded {len(suitability)} areas with suitability scores")
    except FileNotFoundError:
        logger.error("Suitability results not found. Run suitability analysis first.")
        return {}

    # Load NYCHA data
    nycha = load_nycha_data(nycha_path)

    # 1. Demographic statistics by suitability category
    demo_stats = calculate_demographic_statistics(suitability)
    if not demo_stats.empty:
        demo_stats.to_csv(output_dir / "demographic_by_suitability.csv")
        results["demographic_stats"] = demo_stats

    # 2. Compare intervention areas to citywide
    comparison = compare_intervention_vs_citywide(suitability)
    if not comparison.empty:
        comparison.to_csv(output_dir / "intervention_vs_citywide.csv")
        results["intervention_comparison"] = comparison

        # Log key findings
        if "median_household_income" in comparison.index:
            income_diff = comparison.loc["median_household_income", "pct_difference"]
            logger.info(f"Intervention area income vs citywide: {income_diff:+.1f}%")

        if "pct_nonwhite" in comparison.index:
            nonwhite_diff = comparison.loc["pct_nonwhite", "difference"]
            logger.info(f"Intervention area % nonwhite vs citywide: {nonwhite_diff:+.1f} pp")

    # 3. NYCHA proximity analysis
    if len(nycha) > 0:
        nycha_proximity = analyze_nycha_proximity(suitability, nycha)
        if not nycha_proximity.empty:
            nycha_proximity.to_csv(output_dir / "nycha_proximity.csv", index=False)
            results["nycha_proximity"] = nycha_proximity

    # 4. Calculate equity priority index
    suitability["equity_index"] = calculate_equity_index(suitability)

    # 5. Combined suitability + equity score
    if "suitability_score" in suitability.columns:
        # Normalize both scores
        suit_norm = (suitability["suitability_score"] - suitability["suitability_score"].min()) / \
                    (suitability["suitability_score"].max() - suitability["suitability_score"].min())
        equity_norm = (suitability["equity_index"] - suitability["equity_index"].min()) / \
                      (suitability["equity_index"].max() - suitability["equity_index"].min())

        # Combined score (equal weighting)
        suitability["combined_score"] = (suit_norm + equity_norm) / 2

        # Rank by combined score
        suitability["combined_rank"] = suitability["combined_score"].rank(
            ascending=False, method="min"
        ).astype(int)

    # Save updated results with equity metrics
    suitability.to_file(output_dir / "suitability_with_equity.geojson", driver="GeoJSON")

    # Create top 20 by combined score
    if "combined_rank" in suitability.columns:
        equity_cols = ["suitability_score", "equity_index", "combined_score", "combined_rank"]
        demo_cols = [c for c in EQUITY_VARIABLES if c in suitability.columns]

        top_20_equity = suitability.nsmallest(20, "combined_rank")[equity_cols + demo_cols]
        top_20_equity.to_csv(output_dir / "top_20_equity_priority.csv")
        results["top_20_equity"] = top_20_equity

    # Generate summary report
    report = generate_equity_report(results, suitability)
    report_path = output_dir / "equity_analysis_report.md"
    with open(report_path, "w") as f:
        f.write(report)

    logger.info("=" * 50)
    logger.info("Equity analysis complete")
    logger.info(f"Results saved to {output_dir}")
    logger.info("=" * 50)

    return results


def generate_equity_report(results: dict, suitability_gdf: gpd.GeoDataFrame) -> str:
    """Generate a markdown report of equity analysis findings."""

    report = """# Equity Analysis Report

## NYC LTN Suitability Analysis - Equity Assessment

### Overview

This report examines the distributional implications of proposed Low Traffic
Neighborhood interventions, assessing whether high-priority areas align with
or diverge from equity considerations.

"""

    # Add intervention comparison
    if "intervention_comparison" in results:
        report += "### Intervention Areas vs Citywide Averages\n\n"
        comp = results["intervention_comparison"]

        report += "| Metric | Citywide | Intervention Area | Difference |\n"
        report += "|--------|----------|-------------------|------------|\n"

        for metric in comp.index:
            citywide = comp.loc[metric, "citywide"]
            intervention = comp.loc[metric, "intervention_area"]
            diff = comp.loc[metric, "pct_difference"]

            # Format based on metric type
            if "pct" in metric.lower():
                report += f"| {metric} | {citywide:.1f}% | {intervention:.1f}% | {diff:+.1f}% |\n"
            elif "income" in metric.lower():
                report += f"| {metric} | ${citywide:,.0f} | ${intervention:,.0f} | {diff:+.1f}% |\n"
            else:
                report += f"| {metric} | {citywide:.1f} | {intervention:.1f} | {diff:+.1f}% |\n"

        report += "\n"

    # Add NYCHA proximity
    if "nycha_proximity" in results:
        report += "### NYCHA Development Proximity\n\n"
        nycha = results["nycha_proximity"]

        report += "| Buffer Distance | NYCHA Developments | % of Total |\n"
        report += "|-----------------|-------------------|------------|\n"

        for _, row in nycha.iterrows():
            report += f"| {row['buffer_distance_ft']:,.0f} ft ({row['buffer_distance_miles']:.2f} mi) | "
            report += f"{row['nycha_developments_within']} | {row['pct_of_total_nycha']:.1f}% |\n"

        report += "\n"

    # Key findings
    report += """### Key Findings

Based on the equity analysis:

1. **Income Distribution**: Examine whether high-suitability areas have
   higher or lower median incomes compared to citywide averages.

2. **Racial/Ethnic Composition**: Assess whether proposed interventions
   would disproportionately benefit or burden communities of color.

3. **Transit Dependence**: Areas with low vehicle ownership and high transit
   use should be prioritized as they benefit most from pedestrian improvements.

4. **Public Housing Access**: Proximity analysis shows how accessible
   LTN improvements would be to NYCHA residents.

### Recommendations

- Prioritize areas with high combined suitability + equity scores
- Engage communities in high-priority areas during planning process
- Monitor for potential displacement effects
- Ensure improvements reach transit-dependent populations

"""

    return report


if __name__ == "__main__":
    run_equity_analysis()
