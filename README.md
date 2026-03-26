# nyc-ped-analysis

Research workspace for analyzing **New York City pedestrian** volumes and risk, built around MIT City Form Lab’s **NYCWalks** citywide foot-traffic model and network data.

## Source (MIT)

- **Project page:** [NYCWalks — City Form Lab](https://cityform.mit.edu/projects/nycwalks)
- **Paper:** Sevtsuk, A., Basu, R., Liu, L., Alhassan, A., & Kollar, J. (2026). *Spatial Distribution of Foot-traffic in New York City and Applications for Urban Planning.* **Nature Cities**. [doi:10.1038/s44284-025-00383-y](https://doi.org/10.1038/s44284-025-00383-y)

From the project page you can download:

- **Pedestrian network** (GeoJSON and/or Shapefile): segment-level geometry with peak-period volume estimates, disaggregated flows, and observed counts where available.
- **Calibrated models** (`.pckl`): scikit-learn models for inference.

This repo includes one calibrated model file: `RF_wknd_n20_am_models.pckl` (weekend morning; Random Forest Regressor).

## Setup

**macOS:** The system often has only `python3` / `pip3`, not `python` / `pip`. After `source .venv/bin/activate`, if you still see `zsh: command not found: python`, run scripts with **`python3`** (the venv puts its `python3` first on `PATH`) or the full path **`.venv/bin/python3`**.

Example: `python3 scripts/export_thesis_results.py` or `.venv/bin/python3 scripts/export_thesis_results.py` (no need to activate).

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .              # optional: import nycwalks without PYTHONPATH
```

**Important:** NYCWalks `.pckl` files were produced with **scikit-learn 1.3.x**. This repo pins `scikit-learn==1.3.1` so pickles load without version warnings or broken estimators. If you upgrade sklearn, re-save models or re-download from MIT.

## Download GeoJSON locally

1. Open [NYCWalks](https://cityform.mit.edu/projects/nycwalks) and download the **GeoJSON** (and optional **SHP**) dataset.
2. Symlink into `data/mit/` (see `data/README.md`). Example: `data/mit/NYC_pednetwork_estimates_counts_2018-2019.geojson`.

## Use in Python

From the repository root (after `pip install -e .`, or with `PYTHONPATH=.`):

```python
from pathlib import Path
from nycwalks.io import load_calibrated_model, load_pedestrian_network

model = load_calibrated_model(Path("RF_wknd_n20_am_models.pckl"))
# gdf = load_pedestrian_network("data/mit/NYC_pednetwork_estimates_counts_2018-2019.geojson")
```

Quick check:

```bash
PYTHONPATH=. python scripts/verify_mit_assets.py
```

## Results first (then write the thesis)

One command refreshes **maps**, **polygon-filtered crashes**, **year summaries**, and a prose index:

```bash
pip install -e .
python scripts/export_thesis_results.py              # full crash pagination + maps
python scripts/export_thesis_results.py --fast        # quick iteration
python scripts/export_thesis_results.py --skip-maps  # only crash tables + RESULTS.md
```

Read **`outputs/results/RESULTS.md`** for headline counts and paths to CSV/PNG/JSON.

## Study area boundary

The thesis maps use a **quadrilateral** traced on **official street centerlines** (NYC CSCL): **6th Ave** (Avenue of the Americas), **Houston St**, **Bowery**, and **Canal St**. Geometry: `data/mit/study_area_bowery_houston_6th_canal.geojson`. Rebuild from Open Data: `python scripts/build_study_area_polygon.py`.

## Thesis maps (SoHo / Chinatown justification)

Up to **six** choropleth maps when subway + ridership load (walking, crashes, **PLUTO residential share**, combined index, **subway proximity**, **proximity × subway ridership**), plus a study-area tract table:

```bash
pip install -e .
python scripts/make_manhattan_maps.py
# quick test: python scripts/make_manhattan_maps.py --fast
```

**Neighborhood-scale rankings (official NYC borders):** write tract metrics to GeoPackage, then aggregate to **2020 Neighborhood Tabulation Areas (NTAs)** — DCP/Census “neighborhood” units, not informal polygons:

```bash
python scripts/make_manhattan_maps.py --write-tract-metrics outputs/maps/manhattan_tract_metrics.gpkg
python scripts/rank_manhattan_nta.py
# optional NTA choropleth (use 07+ so it does not collide with 05/06 subway maps):
#   --out-map outputs/maps/07_combined_index_nta.png
```

Outputs: `outputs/maps/*.png`, `study_area_tract_rankings.csv`, and (when you run the lines above) `manhattan_nta_rankings.csv`.  

**Peer NTA table (West Village, FiDi, two Midtown NTAs vs study polygon):** after the lines above,

```bash
python scripts/export_peer_nta_comparison.py --print-md
```

writes `outputs/maps/peer_nta_comparison.csv`. Methodology: [`docs/COMPARISON_PEERS_WEST_VILLAGE_FIDI_MIDTOWN.md`](docs/COMPARISON_PEERS_WEST_VILLAGE_FIDI_MIDTOWN.md).

**Important:** symlink MIT **`NYC_pednetwork_estimates_counts_2018-2019.geojson`** into `data/mit/` so Map 1 uses the full network. Details: [`data/README.md`](data/README.md), [`docs/mit_nycwalks_files.md`](docs/mit_nycwalks_files.md), [`docs/thesis_maps.md`](docs/thesis_maps.md).

**3D prism / bar map (matplotlib):** after exporting tract metrics, extrude any numeric column as a 3D PNG (centroid bars, height + color = value; optional crimson study outline at base):

```bash
python scripts/make_manhattan_maps.py --write-tract-metrics outputs/maps/manhattan_tract_metrics.gpkg
python scripts/plot_tract_3d_bars.py --column combined_idx --out outputs/maps/3d_combined_idx.png
# e.g. --column transit_access_ridership_pctile --max-height-m 1200 --elev 32 --azim -70
```

## Thesis-oriented evidence (LTN, Houston–Canal)

A mapping from **thesis claims → datasets → analyses** (including limitations like “through traffic %”) lives in [`docs/thesis_evidence_plan.md`](docs/thesis_evidence_plan.md).

Quick GIS workflow:

1. Download NYCWalks **GeoJSON** → clip to the study bbox with `nycwalks.study_area.clip_gdf_to_bbox` (or your own polygon).
2. Pull **NYPD crashes** for the same corridor: `python scripts/fetch_crashes_study_area.py` (writes `data/raw/crashes_houston_canal.csv`; requires network).
3. Overlay **DOT traffic counts** from [Automated Traffic Volume Counts](https://data.cityofnewyork.us/d/7ym2-wayt) where points fall in your area.

## Next steps for your research

- Join NYCWalks segments to your study areas (tracts, corridors, intersections) with **spatial joins** in GeoPandas.
- Align **crash / injury** tables (e.g. NYC DOT) using shared street IDs or geometry.
- Use `model.predict(X)` once you build feature matrices matching the paper’s specification (the bundled model expects **10 features**). For most policy mapping, rely on **segment attributes in the NYCWalks GeoJSON** rather than re-running the RF without the paper’s full feature pipeline.
