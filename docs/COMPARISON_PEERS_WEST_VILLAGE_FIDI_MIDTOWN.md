# Peer comparison: Houston–Canal vs West Village, FiDi, Midtown

**Purpose:** Situate the **study polygon** relative to three familiar Manhattan **reference neighborhoods** using the **same tract-level metrics** (NYCWalks, NYPD, PLUTO, MTA) and the **official 2020 NTA** geography—so the comparison is **defensible**, not hand-waved.

---

## 1. Why these peers

| Peer | NTA 2020 code | Rationale |
|------|----------------|-----------|
| **West Village** | **MN0203** | Dense residential / village fabric; contrast to **mixed SoHo–corridor** retail-office-residential blend. |
| **Financial District–Battery Park City** | **MN0101** | Another **dense downtown** job hub with heavy walking and different street politics than the **Houston–Canal** band. |
| **Midtown–Times Square** | **MN0502** | Peak **office / entertainment** intensity and transit gravity—useful ceiling for “central business district” patterns. |
| **Midtown South–Flatiron–Union Square** | **MN0501** | **South-of-Park** mixed core; complements MN0502 so “Midtown” is not a single caricature. |

**Colloquial “Midtown”** is ambiguous; the thesis should say explicitly that you use **two NTAs** (MN0501 + MN0502) or report **both** in tables and interpret them **separately**.

**Study area row:** All census tracts **intersecting** the CSCL **Houston–Canal** polygon, summarized as an **area-weighted mean** (same weighting idea as NTA roll-ups).

---

## 2. Data alignment

- **NTA metrics:** From `outputs/maps/manhattan_nta_rankings.csv` (built by `scripts/rank_manhattan_nta.py` from `manhattan_tract_metrics.gpkg`).
- **Study metrics:** From `outputs/maps/study_area_tract_rankings.csv` (same pipeline run as the thesis lock—see `docs/DATA_LOCK.md`).
- **Comparable columns:** e.g. `combined_idx`, `combined_idx_base`, borough tract percentiles for ped / crash / res, crash density, ped density, subway distance and ridership-weighted access—where present in both tables.

**Caveats**

- **`combined_idx`** applies the **rank floor only to tracts that intersect the study polygon**. Peer NTAs (FiDi, West Village, Midtown) are almost entirely **outside** that rule, so **cross-row comparison of raw `combined_idx` is misleading**. For peer contrast, lead with **`combined_idx_base`**, component **percentiles** (`ped_pctile`, `crash_pctile`, `res_pctile`, crash density, subway fields), and treat **`combined_idx`** as a **map-display** construct for the corridor.
- NTAs are **larger** than your polygon; you are comparing **neighborhood-scale averages**, not block corners.
- This is **descriptive contrast**, not a causal “treatment vs control.”

---

## 3. Reproducible export

In the **`nyc-ped-analysis`** code repository:

```bash
python scripts/make_manhattan_maps.py --write-tract-metrics outputs/maps/manhattan_tract_metrics.gpkg
python scripts/rank_manhattan_nta.py
python scripts/export_peer_nta_comparison.py --print-md
```

Outputs **`outputs/maps/peer_nta_comparison.csv`** plus optional markdown table on stdout.

---

## 4. Where it goes in the thesis

- **Results (quantitative),** after borough + corridor narrative: one subsection **“Comparison to reference NTAs”** with **one table** (from CSV) and **2–4 sentences** (e.g. how study **ped / crash / mix / transit** sits vs FiDi vs West Village vs Midtown pair).
- **Discussion:** one paragraph on **limits**—NTA labels ≠ planning politics; **Houston–Canal** spans **multiple** NTAs (SoHo, Greenwich Village, LES, East Village tracts in your export), so the peer table **contextualizes**, not **relabels**, the corridor.

---

## 5. Outline cross-reference

`docs/STRUCTURED_THESIS_OUTLINE.md` — Chapter 5 includes a subsection for this comparison.
