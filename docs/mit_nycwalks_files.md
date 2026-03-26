# MIT NYCWalks files (your downloads)

This project expects the City Form Lab release under familiar names. Your copies match the standard MIT layout.

## Network (GeoJSON / Shapefile)

**File:** `NYC_pednetwork_estimates_counts_2018-2019.geojson` (and same basename `.shp` + sidecars)

- **CRS:** EPSG:6538 (NYC-area projected coordinates, US survey feet in practice for lengths).
- **Modeled peak volumes (pedestrians / hour, estimates):**  
  `predwkdyAM`, `predwkdyMD`, `predwkdyPM`, `predwkndAM`, `predwkndMD`, `predwkndPM`
- **Disaggregated raw flow components (same units where applicable):**  
  e.g. `HME_SCH`, `HME_JOB`, `HME_PRK`, `HME_AMN`, …
- **Observed count fields (where a count location exists):**  
  `Wkdy_*_CT`, `Wknd_*_CT`, `CountLoc`, etc.
- **Length:** `Shape_Leng` (and sometimes `Shape_Le_1`) — used with volume as a simple **exposure** weight when aggregating to census tracts.

**Maps / tract pipeline (this repo):** `make_manhattan_maps.py` aggregates **all six** peak columns above to tracts (default **`--ped-metric-source composite`** = **mean** of tract-level Σ(vol×length) across available peaks). Each peak and each numeric **`HME_*`** purpose column is also stored as **`nw_exp_<column>`** on the tract table. Override the **main** pedestrian scalar with **`--ped-metric-source single --volume-col predwkdyPM`** (or any `pred*` / `HME_*` field).

**Spatial aggregation (default `overlay`):** segments are intersected with census tracts in **EPSG:2263**; each fragment contributes **volume × fragment length** (uniform rate along the line). Legacy centroid assignment: **`--ped-spatial-aggregation centroid`**. Summary file: `outputs/maps/nycwalks_aggregation_summary.txt`.

**Optional extra choropleths** (one PNG per column): `--ped-extra-maps periods` | `purpose` | `all`.

**Pickle models (`.pckl`):** see [`docs/nycwalks_model_pickles.md`](nycwalks_model_pickles.md) for how RF pickles relate to the published GeoJSON columns.

## Calibrated models (`.pckl`)

From the **Model files** folder (names from MIT):

| File | Typical meaning |
|------|-----------------|
| `RF_wkdy_n20_am_models.pckl` | Weekday AM |
| `RF_wkdy_n20_ln_models.pckl` | Weekday lunch / midday |
| `RF_wkdy_n20_pm_models.pckl` | Weekday PM |
| `RF_wknd_n20_am_models.pckl` | Weekend AM (also in repo root) |
| `RF_wknd_n20_ln_models.pckl` | Weekend lunch / midday (MIT uses `ln` in filename) |
| `RF_wknd_n20_pm_models.pckl` | Weekend PM |

Use **scikit-learn 1.3.1** to load pickles (see `requirements.txt`).

## Preprint

`Preprint.pdf` — cite the published *Nature Cities* article in the thesis; keep the preprint only as a convenience PDF.

## Symlinks in this repo

`data/raw/` and `data/mit/` may contain **symlinks** to your `Downloads/` copies so the repo stays small. If you move files, refresh the links (see `data/README.md`).
