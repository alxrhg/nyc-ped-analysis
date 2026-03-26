#!/usr/bin/env python3
"""Print a short summary of NYCWalks calibrated models and linked data paths."""

from pathlib import Path

import sklearn

from nycwalks.io import load_calibrated_model

ROOT = Path(__file__).resolve().parents[1]
MIT_MODELS = ROOT / "data" / "mit" / "models"
DEFAULT_MODEL = (
    MIT_MODELS / "RF_wknd_n20_am_models.pckl"
    if (MIT_MODELS / "RF_wknd_n20_am_models.pckl").is_file()
    else ROOT / "RF_wknd_n20_am_models.pckl"
)


def main() -> None:
    print("scikit-learn:", sklearn.__version__)
    print("model file:", DEFAULT_MODEL)
    m = load_calibrated_model(DEFAULT_MODEL)
    print("model:", type(m).__name__)
    for name in ("n_features_in_", "n_estimators"):
        if hasattr(m, name):
            print(f"  {name}: {getattr(m, name)}")
    geo = ROOT / "data" / "mit" / "NYC_pednetwork_estimates_counts_2018-2019.geojson"
    if geo.is_file():
        print("network GeoJSON:", geo.resolve())
    pre = ROOT / "data" / "mit" / "NYCWalks_preprint.pdf"
    if pre.is_file():
        print("preprint:", pre.resolve())


if __name__ == "__main__":
    main()
