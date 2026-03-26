# Explainable model + data: what you can *show* vs what you cannot *prove*

**Audience:** Thesis Methods / Results — formal enough to satisfy a committee that asks for “a model and the data,” without overclaiming causal proof of LTN effectiveness.

---

## 1. Honest meaning of “prove” here

| You **cannot** prove from this pipeline | You **can** demonstrate with equations + open data |
|----------------------------------------|---------------------------------------------------|
| That an LTN **will** reduce through traffic or improve safety | That chosen tracts **score** in stated ways on **defined** quantities built from **cited** inputs |
| That this corridor is **optimal** citywide | That the corridor is **non-trivially high** on a **transparent** multimetric index relative to **Manhattan** (or vs **peer NTAs**) |
| That the **weights** are “true” social welfare weights | That the **weights are explicit**, **fixed in advance** (or sensitivity-tested), and **interpretable** |

Use thesis language: **demonstrate**, **support**, **consistent with**, **necessary (not sufficient) conditions for screening** — not **proves the solution**.

---

## 2. Core explainable chain (equations + where data enter)

All symbols below refer to **census tract** \(i\) in Manhattan unless noted.

### Step A — Pedestrian exposure (NYCWalks → tract)

**Data:** MIT NYCWalks segment GeoJSON (`predwkdyAM`, …, `predwkndPM`); DCP 2020 tract polygons; overlay in EPSG:2263.

\[
E_{i,c} = \sum_{\ell} \widehat{\mathrm{vol}}_{\ell,c}\cdot \mathrm{Len}^{2263}(\ell \cap T_i),
\qquad
E_i = \frac{1}{|\mathcal{C}_{\mathrm{peak}}|}\sum_{c\in\mathcal{C}_{\mathrm{peak}}} E_{i,c}.
\]

**Export check:** columns `nw_exp_*`, composite driving `ped_metric` / `ped_density` in `study_area_tract_rankings.csv` (and full tract GPKG).

### Step B — Borough percentile of walking intensity

\[
\mathrm{ped\_density}_i = E_i / \mathrm{area}^{\mathrm{km}^2}_i,
\qquad
P_i = 100 \times \text{percentile rank of } \mathrm{ped\_density}_i \text{ among Manhattan tracts}.
\]

**Data:** same as A + tract area from projected geometry.

### Step C — Pedestrian harm and exposure-conditioned rate

**Data:** NYPD Motor Vehicle Collisions (geocoded, Manhattan, date window); join to tract.

\[
H_i = \sum_{\text{crashes in }i} (\text{pedestrians injured} + \text{pedestrians killed}),
\qquad
\mathrm{ksi\_rate}_i = \frac{H_i}{E_i + 1}.
\]

\(K_i\) = percentile rank of \(\mathrm{ksi\_rate}_i\) within the **combined-index scope** (default: all Manhattan tracts).

**Interpretation (explainable):** “Harm per unit of **modeled** pedestrian activity,” not a causal crash model.

### Step D — Residential mix (PLUTO)

**Data:** PLUTO tax lots → tract via `bct2020`.

\[
s_i = 100 \times \frac{\sum_{\ell\in i}\mathrm{UnitsRes}_\ell}{\sum_{\ell\in i}\mathrm{UnitsTotal}_\ell}.
\]

Map 3 uses percentile of \(s_i\); default combined index uses **raw** \(s_i\) in the weighted mean (see §8 of `ACADEMIC_METHODS_AND_OUTPUTS.md`).

### Step E — Combined index (primary explainable scalar)

**Default (`ped_primary`):**

\[
I^{\mathrm{base}}_i = 0.65\,P_i + 0.30\,K_i + 0.05\,s_i.
\]

**Optional visibility rules** (disclose in thesis): study blend \(W\), then rank floor \(K\) → reported **`combined_idx`**. For **cross-area comparison** (e.g. vs peer NTAs), prefer **`combined_idx_base`** \(= I^{\mathrm{base}}_i\) and the **components** \(P_i, K_i, s_i\), because the floor targets only study-intersecting tracts.

**Data products:** `combined_idx_base`, `combined_idx`, `study_floor_threshold`, component percentiles in CSV exports.

---

## 3. Symbol → data source → thesis artifact (audit trail)

| Symbol / output | Primary data | Open-data ID or file | Artifact column(s) |
|-----------------|-------------|----------------------|----------------------|
| \(E_i\), \(P_i\) | NYCWalks + tracts | MIT GeoJSON; NYC 63ge-mke6 | `ped_metric`, `ped_density`, `ped_pctile`, `nw_exp_*` |
| \(H_i\), \(\mathrm{ksi\_rate}_i\), \(K_i\) | NYPD crashes | h9gi-nx95 | `ped_ksi`, `ksi_rate`, `combined_crash_leg_pctile` |
| \(s_i\) | PLUTO | 64uk-42ks | `res_unit_share_pct`, `res_pctile` |
| \(I^{\mathrm{base}}_i\) | Derived | — | `combined_idx_base` |
| \(I_i\) (post rules) | Derived | — | `combined_idx` |

Lock dates and CLI in **`docs/DATA_LOCK.md`**.

---

## 4. Example *demonstrable* propositions (fill from your locked CSV)

These are the kind of statements **equations + data** actually support. Replace brackets after you run the final pipeline.

**P1 (comparative intensity).**  
*The area-weighted mean of \(P_i\) among Houston–Canal study tracts equals [·] and exceeds the area-weighted mean of \(P_i\) in [peer NTA name] by [·] index points on the borough percentile scale.*  
→ Compute from `study_area_tract_rankings.csv` and `peer_nta_comparison.csv` / `manhattan_nta_rankings.csv`.

**P2 (exposure-conditioned harm).**  
*Study tract GEOID [·] lies at the [·]th borough percentile of \(\mathrm{ksi\_rate}\) while lying at the [·]th percentile of \(P_i\).*  
→ Shows **decoupling** or **stacking** of exposure and harm—explainable in prose.

**P3 (internal spread vs display rule).**  
*While `combined_idx` ties at [·] under the rank floor, `combined_idx_base` spans [·]–[·] across study tracts.*  
→ Proves you understand the **mechanism** in data, not hand-waving.

**P4 (sensitivity).**  
*With rank floor disabled, study-tract `combined_idx` spans [·]–[·]; centroid vs overlay aggregation shifts the mean index by [·].*  
→ Shows **robustness** of *ranking* under stated alternatives.

None of these assert **LTN success**; they assert **measurable structure** your thesis then **argues** is relevant to LTN *problem definition*.

---

## 5. One-paragraph bridge to “feasibility” (for Discussion)

> The quantities \(P_i\), \(K_i\), and \(s_i\) operationalize a **transparent screening model**: tracts with high modeled walking, non-trivial exposure-conditioned pedestrian harm, and mixed residential-commercial fabric score higher on \(I^{\mathrm{base}}_i\). This does **not** identify a unique engineering solution; it identifies **where**, within Manhattan, the **stated public-health and urban-form rationales** for area-based traffic restraint are most concentrated in **observable** data. **Institutional feasibility**—whether filters can be sited, enforced, and accepted—requires the **qualitative** and **historical** evidence in Chapters II and VI; the present model supplies a **reproducible spatial warrant** for focusing detailed design and coalition work on the Houston–Canal polygon **relative to explicit comparators**.

---

## 6. Where this lives in the academic outline

- **Chapter IV:** Steps A–E as **analytic approach** (subset of full methods).  
- **Chapter V:** **P1–P4** style results as **empirical claims** tied to CSV rows.  
- **Chapter VII:** Paragraph §5 above as **interpretive guardrail**.

---

*This document is not a substitute for traffic simulation literature; it is the **explainable core** your thesis actually implements.*
