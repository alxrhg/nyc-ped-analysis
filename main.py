#!/usr/bin/env python3
"""
NYC Pedestrian-First Street Design: Spatial Analysis

Main entry point for the LTN suitability analysis pipeline.

Usage:
    python main.py --all                    # Run complete pipeline
    python main.py --download               # Download data only
    python main.py --process                # Process data only
    python main.py --analyze                # Run all analyses
    python main.py --visualize              # Generate maps only

Author: Alexander Huang
Institution: The New School - Urban Studies
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src import (
    PROJECT_ROOT,
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    ANALYSIS_DIR,
    OUTPUT_DIR,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(module)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(PROJECT_ROOT / "analysis.log"),
    ],
)
logger = logging.getLogger(__name__)


def setup_directories():
    """Create all required directories."""
    directories = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        ANALYSIS_DIR / "los",
        ANALYSIS_DIR / "crashes",
        ANALYSIS_DIR / "suitability",
        ANALYSIS_DIR / "equity",
        OUTPUT_DIR / "maps",
        OUTPUT_DIR / "figures",
        OUTPUT_DIR / "tables",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Created directory: {directory}")


def run_download(nyc_token: str = None, census_key: str = None):
    """Download all data sources."""
    from src.data_download import download_all_data

    logger.info("=" * 60)
    logger.info("STEP 1: DATA DOWNLOAD")
    logger.info("=" * 60)

    results = download_all_data(
        nyc_app_token=nyc_token,
        census_api_key=census_key,
    )

    return results


def run_processing(study_area: str = "lower_manhattan"):
    """Process all raw data."""
    from src.data_processing import process_all_data

    logger.info("=" * 60)
    logger.info("STEP 2: DATA PROCESSING")
    logger.info("=" * 60)

    results = process_all_data(study_area=study_area)

    return results


def run_crash_analysis():
    """Run crash cluster analysis."""
    from src.crash_analysis import run_crash_analysis as _run_crash_analysis

    logger.info("=" * 60)
    logger.info("STEP 3: CRASH CLUSTER ANALYSIS")
    logger.info("=" * 60)

    results = _run_crash_analysis()

    return results


def run_suitability_analysis():
    """Run LTN suitability analysis."""
    from src.suitability_analysis import run_suitability_analysis as _run_suitability

    logger.info("=" * 60)
    logger.info("STEP 4: SUITABILITY ANALYSIS")
    logger.info("=" * 60)

    results = _run_suitability()

    return results


def run_equity_analysis():
    """Run equity analysis."""
    from src.equity_analysis import run_equity_analysis as _run_equity

    logger.info("=" * 60)
    logger.info("STEP 5: EQUITY ANALYSIS")
    logger.info("=" * 60)

    results = _run_equity()

    return results


def run_visualization():
    """Generate all maps and visualizations."""
    from src.visualization import generate_all_maps

    logger.info("=" * 60)
    logger.info("STEP 6: VISUALIZATION")
    logger.info("=" * 60)

    maps = generate_all_maps()

    return maps


def run_full_pipeline(
    nyc_token: str = None,
    census_key: str = None,
    study_area: str = "lower_manhattan",
    skip_download: bool = False,
):
    """Run the complete analysis pipeline."""
    logger.info("=" * 60)
    logger.info("NYC PEDESTRIAN-FIRST STREET DESIGN")
    logger.info("LTN SUITABILITY ANALYSIS PIPELINE")
    logger.info("=" * 60)

    # Setup
    setup_directories()

    # 1. Download data
    if not skip_download:
        try:
            run_download(nyc_token, census_key)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            logger.info("Continuing with existing data...")

    # 2. Process data
    try:
        run_processing(study_area)
    except Exception as e:
        logger.error(f"Processing failed: {e}")
        raise

    # 3. Crash analysis
    try:
        run_crash_analysis()
    except Exception as e:
        logger.error(f"Crash analysis failed: {e}")
        logger.info("Continuing...")

    # 4. Suitability analysis
    try:
        run_suitability_analysis()
    except Exception as e:
        logger.error(f"Suitability analysis failed: {e}")
        logger.info("Continuing...")

    # 5. Equity analysis
    try:
        run_equity_analysis()
    except Exception as e:
        logger.error(f"Equity analysis failed: {e}")
        logger.info("Continuing...")

    # 6. Visualization
    try:
        run_visualization()
    except Exception as e:
        logger.error(f"Visualization failed: {e}")

    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Outputs saved to: {OUTPUT_DIR}")


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="NYC Pedestrian-First Street Design: Spatial Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py --all                    # Run complete pipeline
    python main.py --download               # Download data only
    python main.py --process                # Process data only
    python main.py --analyze crashes        # Run crash analysis
    python main.py --analyze suitability    # Run suitability analysis
    python main.py --analyze equity         # Run equity analysis
    python main.py --visualize              # Generate maps

Environment variables:
    NYC_OPENDATA_TOKEN      NYC Open Data API token (optional)
    CENSUS_API_KEY          Census API key (optional)
        """,
    )

    # Pipeline stages
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run complete analysis pipeline",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download data from APIs",
    )
    parser.add_argument(
        "--process",
        action="store_true",
        help="Process raw data",
    )
    parser.add_argument(
        "--analyze",
        choices=["all", "crashes", "suitability", "equity"],
        help="Run analysis module(s)",
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate maps and figures",
    )

    # Configuration
    parser.add_argument(
        "--study-area",
        default="lower_manhattan",
        choices=["lower_manhattan", "chinatown_soho", "financial_district"],
        help="Study area for analysis (default: lower_manhattan)",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip data download step",
    )

    # API keys
    parser.add_argument(
        "--nyc-token",
        help="NYC Open Data API token",
    )
    parser.add_argument(
        "--census-key",
        help="Census API key",
    )

    args = parser.parse_args()

    # Get API keys from args or environment
    import os
    nyc_token = args.nyc_token or os.environ.get("NYC_OPENDATA_TOKEN")
    census_key = args.census_key or os.environ.get("CENSUS_API_KEY")

    # Setup directories
    setup_directories()

    # Execute based on arguments
    if args.all:
        run_full_pipeline(
            nyc_token=nyc_token,
            census_key=census_key,
            study_area=args.study_area,
            skip_download=args.skip_download,
        )
    elif args.download:
        run_download(nyc_token, census_key)
    elif args.process:
        run_processing(args.study_area)
    elif args.analyze:
        if args.analyze == "all":
            run_crash_analysis()
            run_suitability_analysis()
            run_equity_analysis()
        elif args.analyze == "crashes":
            run_crash_analysis()
        elif args.analyze == "suitability":
            run_suitability_analysis()
        elif args.analyze == "equity":
            run_equity_analysis()
    elif args.visualize:
        run_visualization()
    else:
        parser.print_help()
        print("\nNo action specified. Use --all to run complete pipeline.")


if __name__ == "__main__":
    main()
