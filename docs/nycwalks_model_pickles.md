# MIT NYCWalks `.pckl` models — what they are and how they could be used

The City Form Lab ships **calibrated scikit-learn regressors** (e.g. `RandomForestRegressor`) as `.pckl` files alongside the **published segment GeoJSON**. The published network already contains **column-wise predictions** (`predwkdyAM`, …, `HME_*`, etc.). The pickles are for **re-running the model** when inputs change, not for reading the released map layers.

## What is inside a pickle?

Example (from this repo’s `RF_wknd_n20_am_models.pckl`, loaded with **scikit-learn 1.3.x**):

- A fitted **`RandomForestRegressor`** (or similar) trained on segment-level features used in the *Nature Cities* NYCWalks paper.
- The checked-in file corresponds to **one** time band (e.g. weekend morning); other downloads (`RF_wkdy_n20_pm_models.pckl`, …) are other bands.

Load in Python:

```python
from pathlib import Path
from nycwalks.io import load_calibrated_model

m = load_calibrated_model(Path("RF_wknd_n20_am_models.pckl"))
# hasattr(m, "predict") → True for sklearn estimators
```

## How prediction is *supposed* to work

1. **Build a feature matrix `X`** with the **same columns, order, units, and preprocessing** the MIT team used when training (street network measures, land use, transit access, etc.—see the paper’s data appendix).
2. Call **`m.predict(X)`** to get **pedestrian volume (or flow)** for each segment (or each analysis unit) under **current** inputs.
3. Optionally **compare** to observed counts where `Wkdy_*_CT` / `Wknd_*_CT` exist in the GeoJSON.

The hard part is step **1**: the GeoJSON gives you **outputs** and some inputs, but a full replication usually needs the **same auxiliary GIS layers** and feature engineering pipeline MIT used. Without that, `predict` is not meaningful on arbitrary ad‑hoc `X`.

## Practical roles in *your* thesis workflow

| Use case | Feasibility |
|----------|-------------|
| **Maps and tract indices** using published `pred*` / `HME_*` | **High** — what `make_manhattan_maps.py` does after aggregating segments to tracts. |
| **Sensitivity across time bands** | **High** — use all six `predwk*` columns (composite mean in the pipeline, or `--ped-extra-maps`). |
| **Purpose splits** | **High** — aggregate `HME_*` columns to tracts; interpret as MIT’s disaggregated flow components. |
| **New predictions** with the pickle after you change the network | **Medium / project-sized** — needs MIT-aligned features; cite the paper if you only partially approximate. |
| **Validating** model vs counts | **Medium** — subset segments with count fields; compare to `pred*` at those locations. |

## Citation

Use the **Nature Cities** article (DOI on the [NYCWalks project page](https://cityform.mit.edu/projects/nycwalks)) for methods; describe pickles explicitly if you load them (sklearn version, which band file, and whether features are full MIT spec or simplified).
