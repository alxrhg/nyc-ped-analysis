# Quantitative data lock — thesis GIS / tract outputs

**Purpose:** One place to record the **frozen** inputs and CLI so figures, tables, and prose stay aligned. Update the **locked-as-of** date and **artifact** notes whenever you re-run the pipeline for final submission.

**Repository / script:** `nyc-ped-analysis` · `scripts/make_manhattan_maps.py`  
**Primary tabular artifact (study tracts):** `outputs/maps/study_area_tract_rankings.csv`  
**Optional full-tract GPKG:** set with `--write-tract-metrics outputs/maps/manhattan_tract_metrics.gpkg` on the same run (needed for NTA roll-up and **peer comparison** vs West Village / FiDi / Midtown NTAs).

After a full run, regenerate NTA table and peer CSV:

`python scripts/rank_manhattan_nta.py` · `python scripts/export_peer_nta_comparison.py`

---

## 1. Locked-as-of (fill when you freeze)

| Field | Value |
|--------|--------|
| **Lock date (local)** | *YYYY-MM-DD — set when you declare final quant* |
| **Machine / OS** | *optional* |
| **Python env** | e.g. repo `venv` + `requirements.txt` versions |
| **Git commit** | *`git rev-parse --short HEAD` from `nyc-ped-analysis`* |

---

## 2. Canonical reproduce command (thesis figures + study CSV)

Run **without** `--fast` so NYPD crashes are **fully paginated** (thesis-grade counts).

```bash
cd /path/to/nyc-ped-analysis
source .venv/bin/activate   # or your env
python scripts/make_manhattan_maps.py
```

Defaults below match **argparse** in `make_manhattan_maps.py` as used for the locked narrative. Override any flag here only if you intentionally change the thesis spec—and then update this file and all captions.

---

## 3. Layer specifications (frozen defaults)

| Layer | Source | Lock detail |
|--------|--------|-------------|
| **Census tracts** | NYC Open Data **63ge-mke6** · GeoJSON · `boroname='Manhattan'` | 2020 tract boundaries |
| **Study polygon** | CSCL-derived quad · `data/mit/study_area_bowery_houston_6th_canal.geojson` (or path `load_study_area_polygon()` resolves) | Houston–Canal corridor |
| **NYCWalks** | MIT GeoJSON · e.g. `NYC_pednetwork_estimates_counts_2018-2019.geojson` in `data/mit/` or `data/raw/` | Modeled peaks **2018–2019** in filename; cite *Nature Cities* NYCWalks paper (see `ACADEMIC_METHODS_AND_OUTPUTS.md`) |
| **Pedestrian → tract** | Default **`--ped-spatial-aggregation overlay`** | Line–tract intersection in **EPSG:2263**; composite = **mean** of six `predwkdy*` / `predwknd*` tract totals |
| **Crashes** | NYC Open Data **h9gi-nx95** | **`--since 2019-01-01`** (inclusive) · borough **MANHATTAN** · geocoded points · **no `--fast`** |
| **PLUTO units** | NYC Open Data **64uk-42ks** | `borough='MN'` · fields `bct2020`, `unitsres`, `unitstotal` → tract residential share |
| **PLUTO “vintage”** | Socrata API (live pull) | Record **HTTP fetch date** in the lock table above; PLUTO has no fixed “edition” in the URL |
| **ACS (reference)** | U.S. Census **2022 ACS 5-year** API | Tract B01003, B25001 (population, housing units) — used for optional `acs_hu_per_km2` |
| **Subway stops** | data.ny.gov **39hk-dx4f** | Manhattan (`borough = M`) |
| **Subway ridership sum** | data.ny.gov **ak4z-sape** | **`--subway-ridership-since 2024-01-01`** (default): sum monthly entries ≥ that month per `station_complex_id` |

**Projection for metrics:** **EPSG:2263** (NYS plane, ft) → km² for densities as in methods doc.

---

## 4. Index / map rules (frozen defaults)

| Parameter | Default | Notes |
|-----------|---------|--------|
| Pedestrian percentile basis | `--ped-percentile-basis density` | Σ(vol×length) per km² |
| Crash map / density basis | `--crash-percentile-basis density` | Crashes per km² |
| Combined method | `--combined-method mean` | |
| Combined balance | `--combined-balance ped_primary` | ≈ **0.65 P + 0.30 K + 0.05 s** (P, K, s as in methods doc) |
| Combined crash leg | `--combined-crash-metric ksi_rate` | Ped injured+killed vs exposure + 1; K = percentile of that rate |
| Combined scope | `--combined-scope borough` | All Manhattan tracts in percentile pool for map 4 |
| Study-area blend | `--study-area-weight 0.0` | Default **off** unless you turn on for a specific figure |
| **Study rank floor** | `--study-floor-at-borough-rank 3` | Tracts intersecting study polygon floored to **3rd-highest** borough combined index → **`combined_idx`** can tie while **`combined_idx_base`** stays pre-floor |
| Transit gravity buffer | `--transit-gravity-buffer-m 50` | Map 6 denominator `d + 50 m` |

**Sensitivity runs** (separate CSVs, same thesis):  
- No floor: `--study-floor-at-borough-rank 0`  
- Centroid aggregation: `--ped-spatial-aggregation centroid` (with or without floor)  

After any sensitivity run, re-run **`nycwalks_aggregation_summary.txt`** with the **primary** spec so the summary file matches the main figures.

---

## 5. Figure outputs (filenames to cite in captions)

Written to **`outputs/maps/`** by default:

1. `01_pedestrian_intensity_percentile.png`  
2. `02_crash_intensity_percentile.png`  
3. `03_residential_intensity_percentile.png`  
4. `04_combined_multimetric_index.png`  
5. `05_subway_access_percentile.png`  
6. `06_transit_access_ridership_percentile.png`  

Caption text templates aligned to this lock: **`docs/RESULTS_QUANT_PROSE_AND_CAPTIONS.md`**.

---

## 6. Data-quality check before submission

- [ ] Confirm the run used **`python scripts/make_manhattan_maps.py` without `--fast`**.  
- [ ] Confirm `outputs/maps/nycwalks_aggregation_summary.txt` lists **`ped_spatial_aggregation: overlay`** for the main thesis maps (unless you intentionally lock centroid).  
- [ ] Paste **lock date** and **git commit** into §1.  
- [ ] Copy or symlink final CSVs into any second workspace so `docs/` and `outputs/` do not disagree.

---

*Cross-reference: `docs/ACADEMIC_METHODS_AND_OUTPUTS.md` (full notation), `docs/SOURCES_AND_CITATIONS.md` (dataset IDs and URLs).*
