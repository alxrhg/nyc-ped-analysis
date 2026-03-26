# Manhattan pedestrian exposure, crash intensity, and multimetric tract indices: methods, data, and reproducible outputs

**Document type:** Methods summary and output inventory for thesis or supplementary materials.  
**Software:** Repository `nyc-ped-analysis`; primary script `scripts/make_manhattan_maps.py`.  
**Frozen run spec for the thesis (dates, flags, dataset IDs, figure filenames):** see **`docs/DATA_LOCK.md`**. Draft **Results (quant)** prose and **figure captions** aligned to that lock: **`docs/RESULTS_QUANT_PROSE_AND_CAPTIONS.md`**.  
**Suggested citation for NYCWalks:** Sevtsuk, A., Basu, R., Liu, L., Alhassan, A., & Kollar, J. (2026). *Spatial Distribution of Foot-traffic in New York City and Applications for Urban Planning.* **Nature Cities**. [https://doi.org/10.1038/s44284-025-00383-y](https://doi.org/10.1038/s44284-025-00383-y). Project page: [NYCWalks — City Form Lab, MIT](https://cityform.mit.edu/projects/nycwalks).

---

## 1. Purpose and analytic frame

This workflow produces **tract-level** descriptors of (i) **pedestrian exposure** derived from MIT NYCWalks network estimates, (ii) **motor vehicle crash concentration** from NYPD open data, (iii) **residential share of building units** from PLUTO, (iv) an explicit **combined index** merging those dimensions, and (v) **subway proximity and ridership-weighted accessibility** metrics. Optional **neighborhood tabulation area (NTA)** roll-ups and **3D schematic figures** support interpretation at multiple geographic scales and for presentation.

The combined index is intended as a **transparent summary surface** for visualization and narrative—not a causal estimand. Post-hoc **study-area emphasis** (polygon blend and rank floor) is documented as **visibility rules** for policy-relevant geography, not as empirical dominance over all central business district tracts.

---

## 2. Study area (thesis corridor)

The **Houston–Canal** quadrilateral is defined from NYC **street centerlines** (DCP CSCL): **Avenue of the Americas**, **Houston Street** (east and west segments), **Bowery**, and **Canal Street** (Holland Tunnel label excluded). Geometry is stored as `data/mit/study_area_bowery_houston_6th_canal.geojson` and may be rebuilt with `scripts/build_study_area_polygon.py`. Tracts **intersecting** this polygon are flagged in tabular outputs (`study_intersects`).

---

## 3. Spatial units and projections

| Unit | Source | Role |
|------|--------|------|
| **2020 census tract, Manhattan** | NYC DCP / Open Data [63ge-mke6](https://data.cityofnewyork.us/d/63ge-mke6) | Primary analysis polygon; maps 1–6 and tract tables. |
| **NTA 2020 (Manhattan)** | NYC Open Data [9nt8-h7nd](https://data.cityofnewyork.us/d/9nt8-h7nd) | Optional aggregation of tract metrics (`scripts/rank_manhattan_nta.py`). |

**Planar calculations** (tract area, line–polygon intersection, subway distance) use **EPSG:2263** (NAD83 / New York Long Island, US survey feet) unless noted. **Choropleth frames** are plotted in **WGS84** with latitude-corrected aspect (`nycwalks.mapping.frame_lonlat_map_north_up`). Tract areas for density denominators are converted to **km²** as \(\mathrm{area}^{2263} \times (0.3048)^2 / 10^6\).

---

## 4. Data sources

| Layer | Provider / ID | Use |
|-------|----------------|-----|
| Pedestrian network & volumes | MIT NYCWalks GeoJSON (e.g. `NYC_pednetwork_estimates_counts_2018-2019.geojson`) | Segment-level \(\widehat{\mathrm{vol}}\) (ped/h) for peak periods; optional `HME_*` disaggregated components. |
| Motor vehicle collisions | NYC Open Data [h9gi-nx95](https://data.cityofnewyork.us/d/h9gi-nx95) | Geocoded crashes; Manhattan filter; pedestrian injury and fatality fields. |
| Tax-lot units | NYC PLUTO [64uk-42ks](https://data.cityofnewyork.us/d/64uk-42ks) | Residential and total building units by tract. |
| Housing units (reference) | U.S. Census ACS 2022 5-year, table B25001 | Optional `acs_hu_per_km2` in exports. |
| Subway stops | NY Open Data [39hk-dx4f](https://data.ny.gov/Transportation/MTA-Subway-Stations/39hk-dx4f) | Manhattan stops (`borough = M`). |
| Subway ridership | NY Open Data [ak4z-sape](https://data.ny.gov/Transportation/MTA-Subway-Station-Monthly-Ridership-Beginning-February/ak4z-sape) | Monthly entries by `station_complex_id`; joined to stops via `complex_id`. |
| DOT pedestrian counts (fallback) | NYC Open Data [cqsj-cfgu](https://data.cityofnewyork.us/d/cqsj-cfgu) | Used only if NYCWalks GeoJSON is absent (sparse spatial coverage). |

---

## 5. Pedestrian exposure (NYCWalks → tracts)

### 5.1 Segment-to-tract aggregation

Let \(\ell\) index network segments with nonnegative estimate \(\widehat{\mathrm{vol}}_{\ell,c}\) for column \(c\) (e.g. `predwkdyAM`, or `HME_JOB`). Let \(T_i\) denote tract \(i\)’s polygon in EPSG:2263.

**Default (overlay):** for each segment–tract pair, take the intersection geometry \(g_{\ell,i} = \ell \cap T_i\). Under **uniform intensity along the segment**,

\[
E_{i,c} \;=\; \sum_{\ell} \widehat{\mathrm{vol}}_{\ell,c} \cdot \mathrm{Len}^{2263}(g_{\ell,i}).
\]

**Legacy (centroid):** assign the **entire** segment length to the tract containing the segment centroid, with the same multiplicative form using full segment length.

Implementation performs **one** line–polygon overlay and reuses intersection lengths for all columns (see `nycwalks.ped_tract_aggregate`).

### 5.2 Peak periods and composite exposure

Let \(\mathcal{C}_{\mathrm{peak}}\) be the set of MIT peak columns present in the file (typically six: `predwkdyAM/MD/PM`, `predwkndAM/MD/PM`). The **default tract scalar** used in the main maps and in the denominator of the KSI rate is

\[
E_i \;=\; \frac{1}{|\mathcal{C}_{\mathrm{peak}}|} \sum_{c \in \mathcal{C}_{\mathrm{peak}}} E_{i,c}.
\]

Each \(E_{i,c}\) is exported as **`nw_exp_<c>`**. **Trip-purpose** columns `HME_*` are aggregated to **`nw_exp_HME_*`** but are **not** included in \(E_i\) unless the user selects **`--ped-metric-source single --volume-col …`**.

**Pedestrian density** (default map 1 and \(P\) leg): \(\mathrm{ped\_density}_i = E_i / \mathrm{area}^{\mathrm{km}^2}_i\). **Borough percentile** \(P_i\) ranks \(\mathrm{ped\_density}_i\) (or raw \(E_i\) if `--ped-percentile-basis total`) among Manhattan tracts.

A machine-readable summary of columns found on the user’s file is written to **`outputs/maps/nycwalks_aggregation_summary.txt`**.

---

## 6. Crash intensity and pedestrian harm

**Crash count** \(N_i\) joins geocoded incidents to tract polygons. **Crash density** is \(N_i / \mathrm{area}^{\mathrm{km}^2}_i\) (or raw \(N_i\) under `--crash-percentile-basis total`). **Borough percentile** for map 2 follows the same convention as map 1.

Let \(H_i\) be the sum of **pedestrians injured + killed** in tract \(i\) over the user-specified date window. The **KSI rate** used in the default combined map’s crash leg is

\[
\mathrm{ksi\_rate}_i \;=\; \frac{H_i}{E_i + 1},
\]

where \(E_i\) is the NYCWalks composite exposure above. **\(K_i\)** is the percentile rank of \(\mathrm{ksi\_rate}_i\) within the **map-4 scope** (all Manhattan by default, or south-of-latitude subset if configured). This ties harm to **exposure-conditioned** risk; sensitivity runs may use crash density instead (`--combined-crash-metric count`).

**Note:** `--fast` truncates crash pagination; full runs are preferred for stable \(H_i\) and \(N_i\).

---

## 7. Residential building-stock mix (PLUTO)

Let \(\mathrm{UnitsRes}_\ell\) and \(\mathrm{UnitsTotal}_\ell\) denote PLUTO residential and total units on lot \(\ell\). Tract-level share is

\[
s_i \;=\; 100 \times \frac{\sum_{\ell \in i} \mathrm{UnitsRes}_\ell}{\sum_{\ell \in i} \mathrm{UnitsTotal}_\ell},
\]

(undefined if the denominator is zero). Map 3 shows the **borough percentile** of \(s_i\). In the default combined index, the raw \(s_i\) enters with a small weight (see §8).

---

## 8. Combined multimetric index (map 4)

Within the chosen **scope**, let \(P_i\) be the pedestrian percentile (§5), \(K_i\) the crash-leg percentile (KSI rate by default, §6), and \(s_i\) the PLUTO share (§7). **Default weighted mean** (`ped_primary`):

\[
I^{\mathrm{base}}_i \;=\; 0.65\,P_i + 0.30\,K_i + 0.05\,s_i.
\]

**Optional study-area blend** with weight \(W \in [0,1]\):

\[
I'_i \;=\; (1-W)\,I^{\mathrm{base}}_i + W\,G_i,\qquad G_i = \begin{cases} 100 & \text{if tract intersects study polygon} \\ 0 & \text{otherwise.} \end{cases}
\]

**Optional rank floor** (default \(K=3\)): let \(I_{(K)}\) be the \(K\)-th largest value of \(I'\) among all Manhattan tracts. For tracts intersecting the study polygon,

\[
I_i \;=\; \max\bigl(I'_i,\, I_{(K)}\bigr).
\]

Otherwise \(I_i = I'_i\). Setting \(K=0\) disables the floor. **`combined_idx_base`** tabulates \(I^{\mathrm{base}}_i\) before blend and floor; **`combined_idx`** is \(I_i\).

**Interpretation:** The blend and floor are **explicit graphic and narrative devices** for a focal geography; they should be disclosed as such. **`Greys`** is used with **high = dark** for \(I_i\).

Alternative balances (`ped_crash`, `equal`), geometric mean, alternate residential encoding (`percentile`), and alternate scope (`south_of`) are supported for sensitivity analysis.

---

## 9. Subway proximity and ridership-weighted score

**Distance:** Minimum planar distance in EPSG:2263 from tract polygon to nearest Manhattan stop point [39hk-dx4f]. **Access percentile** ranks \((d_{\max} - d_i)\) so higher values imply closer stops (not network walking time).

**Ridership:** Summed reported **entries** \(R_i\) at the nearest stop’s `complex_id` over months with `month \geq` the configured start date [ak4z-sape], Manhattan rows only. **Gravity-style percentile score:**

\[
S_i \;=\; \mathrm{rank\ percentile}\Bigl(\frac{\log(1+R_i)}{d_i + b}\Bigr),
\]

with buffer \(b = 50\,\mathrm{m}\) by default (`--transit-gravity-buffer-m`). **`subway_nearest_ridership_pctile`** ranks \(\log(1+R_i)\) only.

---

## 10. Neighborhood tabulation areas (optional)

`scripts/rank_manhattan_nta.py` assigns each tract to the **single NTA** with **largest** intersection area in EPSG:2263, then computes **area-weighted means** of tract-level metrics within each NTA and **percentiles among Manhattan NTAs**. This is a **coarser reporting scale**; inference at tract scale remains primary unless otherwise justified.

---

## 11. Reproducibility

**Environment:** Python 3.9+; dependencies in `requirements.txt`; `scikit-learn==1.3.1` for compatibility with bundled MIT `.pckl` files if used. Install: `pip install -r requirements.txt` and `pip install -e .`.

**Canonical map run:**

```bash
python scripts/make_manhattan_maps.py
python scripts/make_manhattan_maps.py --fast   # truncated crash pull for iteration
```

**Tract metrics export and NTA table:**

```bash
python scripts/make_manhattan_maps.py --write-tract-metrics outputs/maps/manhattan_tract_metrics.gpkg
python scripts/rank_manhattan_nta.py
```

**Sensitivity (examples):** `--ped-spatial-aggregation centroid`, `--ped-metric-source single --volume-col predwkdyPM`, `--study-floor-at-borough-rank 0`, `--skip-subway-ridership`, `--combined-scope south_of`.

**3D prism figure (schematic):** `scripts/plot_tract_3d_bars.py` (centroid prisms; exaggerated height).

**MIT pickle models:** See `docs/nycwalks_model_pickles.md` for the relationship between published GeoJSON fields and sklearn objects.

---

## 12. Output inventory (default `outputs/maps/`)

| Output | Description |
|--------|-------------|
| `01_pedestrian_intensity_percentile.png` | Borough percentile of pedestrian exposure density (or total). |
| `02_crash_intensity_percentile.png` | Borough percentile of crash density (or count). |
| `03_residential_intensity_percentile.png` | Borough percentile of PLUTO residential unit share. |
| `04_combined_multimetric_index.png` | Combined index \(I_i\) (Greys). |
| `05_subway_access_percentile.png` | Subway distance–based access percentile (if fetched). |
| `06_transit_access_ridership_percentile.png` | Ridership–distance combined percentile (if ridership loads). |
| `01_nycwalks_peak_*.png`, `01_nycwalks_hme_*.png` | Optional (`--ped-extra-maps`). |
| `study_area_tract_rankings.csv` | Study-envelope tracts; full metric columns including `nw_exp_*`, subway fields, `combined_idx` / `combined_idx_base`. |
| `nycwalks_aggregation_summary.txt` | Peak and `HME_*` columns detected; aggregation mode. |
| `manhattan_nta_rankings.csv` | From `rank_manhattan_nta.py`. |
| `3d_*.png` | From `plot_tract_3d_bars.py` if run. |

---

## 13. Limitations

- **Modifiable areal unit problem (MAUP):** Results depend on tract boundaries; corridor signal may be split across polygons. NTA tables are a partial response at coarser scale.  
- **NYCWalks as model output:** \(\widehat{\mathrm{vol}}\) is an estimate for a defined temporal and modeling framework; it is not a direct census of pedestrians. Peak-period **mean** across columns reduces sensitivity to one arbitrary band but remains a modeling choice.  
- **Temporal alignment:** Network vintage and crash window may not coincide; state both in text.  
- **KSI rate:** Uses exposure in the denominator; interpret as **exposure-conditioned** harm, not independent validation of a separate risk model.  
- **Subway metrics:** Euclidean **projected** distance; \(R_i\) is summed **reported entries** over a chosen month range, not unique persons.  
- **Study blend and rank floor:** Normative / presentational; report alongside a **pure** run (`W=0`, `K=0`) when claiming empirical ordering.  

---

## 14. Related documentation

- `docs/thesis_maps.md` — expanded map-by-map notes and thesis talking points.  
- `docs/mit_nycwalks_files.md` — file layout and column naming for MIT downloads.  
- `docs/nycwalks_model_pickles.md` — sklearn pickles vs. GeoJSON columns.  
- `README.md` — setup, symlinks, and quick commands.

---

*End of methods and outputs summary.*
