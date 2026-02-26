"""
NYC Pedestrian-First Street Design: Spatial Analysis Package

This package contains modules for analyzing pedestrian infrastructure
and identifying potential Low Traffic Neighborhood locations in NYC.

Author: Alexander Huang
Institution: The New School - Urban Studies
"""

from pathlib import Path

# Package version
__version__ = "0.1.0"

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "spatial_analysis" / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

# Analysis directories
ANALYSIS_DIR = PROJECT_ROOT / "spatial_analysis" / "analysis"

# Output directories
OUTPUT_DIR = PROJECT_ROOT / "spatial_analysis" / "outputs"
MAPS_DIR = OUTPUT_DIR / "maps"
FIGURES_DIR = OUTPUT_DIR / "figures"
TABLES_DIR = OUTPUT_DIR / "tables"

# Coordinate reference systems
DEFAULT_CRS = "EPSG:2263"  # NY State Plane (feet)
GEOGRAPHIC_CRS = "EPSG:4326"  # WGS84 for web mapping
