# Evidence plan: LTNs and the Houston–Canal corridor

This note connects your thesis claims to **data you can actually analyze** in this repository, and flags what is **not** directly available from a single public table (so you don’t overclaim in the Methods).

Your thesis mixes **policy history** (documents, interviews) with **spatial analysis** (GIS). The data layer below supports the spatial part: *where* people walk, *where* harm concentrates, and *where* vehicle volumes are measured—so you can argue for **filtering** (LTN-style) on specific interior links while keeping **arterials** for through traffic.

---

## 1. Core arguments → empirical support

| Thesis idea | Strongest quantitative support | Main sources | Caveat |
|-------------|-------------------------------|--------------|--------|
| The corridor has **high pedestrian demand** relative to other blocks | Segment-level **pedestrian volume estimates**; maps of peak foot traffic | MIT **NYCWalks** network GeoJSON + paper ([NYCWalks project](https://cityform.mit.edu/projects/nycwalks), [Nature Cities](https://doi.org/10.1038/s44284-025-00383-y)) | NYCWalks is a **model**, validated against counts—not a live sensor feed. Say “estimated peak-period volumes.” |
| **Shortcut / cut-through traffic** strains narrow grids | **Vehicle volume** at counted locations; **inferred** cut-through from pattern (arterial vs parallel local) | NYC Open Data **Automated Traffic Volume Counts** ([7ym2-wayt](https://data.cityofnewyork.us/d/7ym2-wayt)); optional DOT dashboards | “% through trips” per street usually needs **license-plate / OD studies** or advocacy methodology (e.g. Open Plans). Use volumes + classification as **proxy evidence**, cite Open Plans separately. |
| **Pedestrian injury risk** is not only a “Midtown” story | **Crash** points + pedestrian injuries/killed; exposure adjustment using NYCWalks volumes (following the paper’s logic) | NYPD **Motor Vehicle Collisions** ([h9gi-nx95](https://data.cityofnewyork.us/d/h9gi-nx95)) | Crashes are **police-reported**; underreporting is a known limitation—state in Methods. |
| **LTN fits NYC legally** better than full pedestrianization | Primarily **legal / planning** argument | NYC **Local Law 55 of 2021** (Open Streets / “limited local access”); your document analysis | Not a GIS regression—keep in qualitative chapter. |
| **International** LTN / superblock outcomes | **Secondary literature + official evaluations** | TfL LTN impacts; Barcelona; Tokyo/Ginza plans (your bibliography) | Use as **comparative policy**, not as NYC coefficients. |

---

## 2. Houston–Canal study area (GIS)

**Working definition:** Manhattan blocks **between Canal Street and Houston Street** (adjust east–west bounds to match your field work).

In code, a coarse bounding box (WGS84) is in `nycwalks/study_area.py` as `HOUSTON_CANAL_BBOX_WGS84`. **Refine** this with a community district, census tracts, or a hand-drawn polygon in QGIS once your corridor boundary is fixed for the thesis.

Recommended GIS workflow:

1. Download NYCWalks **GeoJSON** from the [NYCWalks page](https://cityform.mit.edu/projects/nycwalks).
2. **Clip** segments to your polygon / bbox (`clip_gdf_to_bbox` or dissolve your own `study_area.geojson`).
3. Pull **crashes** into the same bbox (script: `scripts/fetch_crashes_study_area.py`).
4. **Join** crash points to the nearest NYCWalks segment (or aggregate to hex grid) to discuss **injury hot spots** in high foot-traffic zones.
5. Overlay **traffic count** points from `7ym2-wayt` where they fall inside the study area.

---

## 3. What the bundled `.pckl` model is (and isn’t)

File: `RF_wknd_n20_am_models.pckl`

- It is a calibrated **RandomForestRegressor** (see `scripts/verify_mit_assets.py`).
- It expects **10 input features**—the same feature engineering the City Form Lab used for that scenario (**weekend morning** in the filename).

**For the thesis:** using the **GeoJSON volume fields** on each segment is usually enough for policy GIS maps. Use the `.pckl` only if you are replicating or extending their **prediction** setup with identical covariates. Otherwise, cite **segment estimates from the network file** and the paper’s validation statistics.

---

## 4. NYC Open Data endpoints (API)

| Dataset | Socrata ID | Use |
|---------|------------|-----|
| Motor Vehicle Collisions – Crashes | `h9gi-nx95` | Pedestrian injured/killed; map hot spots in corridor |
| Automated Traffic Volume Counts | `7ym2-wayt` | Vehicle volumes at ATR locations (sparse in time/space) |

API base pattern:

`https://data.cityofnewyork.us/resource/<id>.json`

Use `$where` to filter by date and bounding box on `latitude` / `longitude` (crashes). Respect [Socrata app token](https://dev.socrata.com/docs/app_tokens.html) if you hit rate limits.

---

## 5. Qualitative + quantitative integration (how to write Methods)

- **Interviews / documents:** explain *why* full pedestrianization stalled (1997 study, political/regulatory conflict).
- **GIS:** show *where* LTN-style filtering would address **high pedestrian volume + high motor vehicle exposure + crash history** on **interior** streets, while leaving **Canal/Houston-class** corridors for through movement—mirroring your written argument about **hierarchy** on the grid.
- **Explicit limitation:** without a proprietary OD model, frame “cut-through” claims carefully—pair **Open Plans** citations with **local volume + street classification** evidence.

---

## 6. Suggested figures for the final thesis

1. **Map A:** NYCWalks estimated pedestrian volumes (clipped to Houston–Canal).
2. **Map B:** Pedestrian KSI or injury crashes (same extent, multi-year window).
3. **Map C:** DOT traffic count locations + volumes (where available).
4. **Table:** Summary stats (total crashes, ped injuries) before/after a policy date only if you justify a defensible breakpoint (e.g. post-Vision Zero)—avoid arbitrary slicing.
5. **One-page policy memo:** 3–4 bullet recommendations tied to **specific street roles** (arterial vs filter candidates)—supported by Maps A–C.

This structure gives you **empirical backbone** for LTN feasibility without pretending the city releases a ready-made “through traffic percentage” layer for every block.
