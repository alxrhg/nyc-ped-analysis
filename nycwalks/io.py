"""I/O for MIT NYCWalks calibrated models and network GeoJSON."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Union

import geopandas as gpd

StrPath = Union[str, Path]


def load_calibrated_model(path: StrPath) -> Any:
    """
    Load a calibrated NYCWalks model from a `.pckl` produced by the City Form Lab.

    Requires the same scikit-learn version used when the file was written (see `requirements.txt`).
    The checked-in `RF_wknd_n20_am_models.pckl` is a `RandomForestRegressor` (10 features, 100 trees).
    """
    path = Path(path)
    with path.open("rb") as f:
        return pickle.load(f)


def load_pedestrian_network(geojson_path: StrPath) -> gpd.GeoDataFrame:
    """Load the NYCWalks pedestrian network GeoJSON from disk."""
    return gpd.read_file(Path(geojson_path))
