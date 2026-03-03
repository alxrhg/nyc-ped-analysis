"""Utilities for analyzing NYC pedestrian collisions.

This package provides functions for cleaning collision datasets and generating
summary statistics useful for spatial or temporal analysis.
"""

from .analysis import (
    load_collision_data,
    clean_collision_data,
    compute_borough_summary,
    compute_top_locations,
    compute_monthly_trend,
    build_summary,
)

__all__ = [
    "load_collision_data",
    "clean_collision_data",
    "compute_borough_summary",
    "compute_top_locations",
    "compute_monthly_trend",
    "build_summary",
]
