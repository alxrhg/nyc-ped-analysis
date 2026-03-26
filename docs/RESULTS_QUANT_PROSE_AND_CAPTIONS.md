# Results (quantitative) — draft prose and figure captions

**Use:** Paste §1 into the thesis **Results** chapter (edit voice as needed). Use §2 for **figure captions**; replace bracketed items with your figure numbers and the **lock date** from `docs/DATA_LOCK.md`.

**Numbers below** match **`outputs/maps/study_area_tract_rankings.csv`** and **`outputs/maps/manhattan_nta_rankings.csv`** as they exist in the analysis repo when this file was written (study rank floor **K = 3**, **`combined_idx` ≈ 86.557** for all study tracts). After a **full** crash pull without `--fast`, **re-check** crash counts and percentiles and adjust sentences if values shift.

---

## 1. Draft results prose (tract + NTA, base vs displayed index)

**Paragraph A — study set and rank floor**

Ten **2020 census tracts** intersect the CSCL-derived **Houston–Canal** study polygon. Under the default **multimetric combined index** (pedestrian-led mean of borough percentiles and PLUTO residential share, with the crash leg as **pedestrian KSI rate** relative to NYCWalks exposure—see Methods), tracts in the polygon receive a **post-processing rank floor** set to the **third-highest** combined index among all Manhattan tracts (`--study-floor-at-borough-rank 3`). As a result, every study tract’s **displayed** index **`combined_idx`** ties at **86.56** (full precision **86.557**), while the **pre-floor** values **`combined_idx_base`** still separate tracts, ranging from **56.49** (GEOID **36061003601**, Lower East Side) to **84.74** (GEOID **36061004500**, SoHo–Little Italy–Hudson Square). Any ranking or map that uses **`combined_idx`** after the floor must be read together with **`combined_idx_base`** so the tie is not mistaken for identical underlying conditions.

**Paragraph B — contrast within the corridor**

Within the study set, **SoHo–Little Italy–Hudson Square** tracts dominate the **upper end** of **`combined_idx_base`**: for example, GEOID **36061004100** reaches **80.47** base index units with the **highest** motor-vehicle **crash density** in the set (**130.72** crashes per km² over the locked NYPD window) alongside **high** modeled pedestrian exposure percentiles, illustrating how **exposure** and **raw crash intensity** do not coincide on every tract. At the other end, GEOIDs **36061003601** and **36061003602** (Lower East Side / East Village) show **lower** base indices (**56.49** and **58.70**) while still inheriting the **floored** displayed index **86.56**, which highlights how the **visibility rule** compresses apparent spread on the summary map. **Greenwich Village** tracts include both a relatively **high** base index (**69.21** at **36061005502**) and a tract (**36061005501**) with **zero** geocoded crashes in the window yet a **mid** base index (**60.29**), underscoring **small-area volatility** in crash counts.

**Paragraph C — transit context (illustrative)**

Nearest **subway** distance (planar, EPSG:2263) is **0 m** for several study tracts whose boundaries contain a station (e.g. **Canal St**, **Prince St**, **2 Av**, **Broadway–Lafayette St** in the export), while **36061005501** reports **48.4 m** to the nearest complex—useful context for how **heavy rail access** sits alongside **surface** pedestrian and crash layers, not as a measure of network walking time.

**Paragraph D — NTA roll-up**

At **NTA 2020** scale, **SoHo–Little Italy–Hudson Square** (**MN0201**), which contains six of the ten study tracts, ranks at the **top** of Manhattan NTAs on the **area-weighted mean** of the same combined index construction (**≈92.6** on the export’s `combined_idx_awm` scale), reinforcing that the corridor sits in a **high–pedestrian-activity, mixed-use** band relative to the borough—even though the thesis does **not** equate that pattern with proof of **LTN traffic outcomes**.

**Paragraph E — sensitivity (index construction, not new data claims)**

When the **rank floor is disabled** (`--study-floor-at-borough-rank 0`), **displayed** study-tract **`combined_idx`** values **spread** from about **54.8** to **76.9** on a comparable run, and **centroid** vs **overlay** NYCWalks aggregation produced **small** mean shifts in that index in sensitivity testing (see Methods / appendix). Interpretation of the **main** maps and tables should still follow the **locked** specification in `docs/DATA_LOCK.md`.

---

## 2. Figure captions (aligned to data lock)

Use the same **lock date** and **crash window** in every caption. Cite NYCWalks with the **Nature Cities** reference from your bibliography.

**Figure [1].** Modeled pedestrian activity intensity by **2020 census tract**, Manhattan. Choropleth shows **borough percentile** of NYCWalks **mean peak** exposure density (Σ volume × segment length per tract km², six peak columns), line–tract **overlay** in **EPSG:2263**. Network: **MIT NYCWalks** `NYC_pednetwork_estimates_counts_2018-2019.geojson`. Outline: Houston–Canal study polygon (CSCL). *Data lock: [date]; sources: NYCWalks; DCP 63ge-mke6.*

**Figure [2].** Motor vehicle **crash concentration** by tract, Manhattan. Choropleth shows **borough percentile** of **crash count per km²** from NYPD **Motor Vehicle Collisions** (Open Data **h9gi-nx95**), Manhattan geocoded incidents, **`crash_date` ≥ 2019-01-01**. Outline: study polygon. *Data lock: [date].*

**Figure [3].** Residential share of **PLUTO** building units by tract, Manhattan. Choropleth shows **borough percentile** of **100 × residential units / total units** aggregated from NYC Open Data **64uk-42ks** (`borough = MN`, `bct2020`). Outline: study polygon. *PLUTO fetched: [date].*

**Figure [4].** **Combined multimetric index** by tract, Manhattan. Index = **weighted mean** of pedestrian percentile (**P**), exposure-conditioned **pedestrian KSI-rate** percentile (**K**), and raw PLUTO residential share (**s**) with default **ped_primary** weights; percentile pool = **all Manhattan tracts**. **Study tracts** may reflect **rank floor** K = 3 (`combined_idx`); see text for **`combined_idx_base`**. Outline: study polygon. *Data lock: [date].*

**Figure [5].** **Subway access** by tract: **borough percentile** of distance to nearest **MTA** Manhattan station (planar m, EPSG:2263). Stops: data.ny.gov **39hk-dx4f**. Outline: study polygon. *Data lock: [date].*

**Figure [6].** **Ridership-weighted transit access** by tract: **borough percentile** of **log(1 + R) / (d + 50 m)**, with **R** = sum of monthly entries from **ak4z-sape** for months **≥ 2024-01-01** per station complex, **d** = planar distance to nearest stop. Outline: study polygon. *Data lock: [date].*

---

## 3. Optional short table note (for a tract appendix table)

> Table X lists the ten study tracts with **`combined_idx_base`**, **`combined_idx`**, NYPD crash counts and densities, NYCWalks composite exposure, PLUTO residential share, and nearest-subway fields exported from `study_area_tract_rankings.csv` under the lock in `docs/DATA_LOCK.md`.

---

*If prose and CSV diverge after you re-run the pipeline, update §1 first, then LU3 / instructor docs.*
