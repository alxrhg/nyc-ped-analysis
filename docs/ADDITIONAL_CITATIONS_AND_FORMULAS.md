# Beyond MIT NYCWalks — references and formula *families* you can cite

**Purpose:** Give your Methods chapter **intellectual company**—classic walkability / accessibility / risk language—**without** replacing your reproducible pipeline. Pull **exact equations** from the original papers (page numbers change by edition).

**Rule:** Cite these to **motivate** weight choices or **compare** your structure to published indices; your **numbers** still come from **NYCWalks + NYPD + PLUTO + MTA** and your locked `DATA_LOCK.md` spec.

---

## 1. Pedestrian exposure and foot traffic (you already anchor on Sevtsuk / NYCWalks)

| Source | Idea to cite |
|--------|----------------|
| **Sevtsuk et al. (*Nature Cities* / City Form Lab)** | Network-based **pedestrian volume estimation**; your \(E_i\) from segment × tract overlay **implements** their published estimates—**primary** ped citation. |
| **Hillier, Hanson — *Space syntax*** | **Integration / choice** on street graphs—**different** paradigm (topology of lines, not ML volumes). Optional sentence: “Alternative tradition models **movement potential** from geometry alone; this thesis uses **empirical** volume surfaces instead.” |

---

## 2. Walkability and built environment (composite indices — conceptual parallel)

| Source | Formula idea (words) | Tie to your thesis |
|--------|----------------------|---------------------|
| **Frank et al.** (e.g. walkability index components) | Combines **net residential density**, **retail floor area ratio**, **intersection density**, **land use mix** (entropy). | Your PLUTO **residential share** + NYCWalks **density** + implicit **urban intensity** are **in the same family** as “walkability composites”—cite as **precedent for multimetric tract scores**, not to copy their exact weights. |
| **Ewing & Cervero** — “Travel and the Built Environment” (*JAPA* / reviews) | **D variables**: **density, diversity, design, destination accessibility, distance to transit**. | One paragraph: your layers map loosely to **D** (e.g. transit = **distance + ridership gravity**; exposure = **design/intensity** via network). |
| **Gehl**, **Whyte** | **Public life** and **pedestrian quality**—qualitative anchor for **why** exposure matters beyond counts. | Discussion / intro, not equations. |

*Search: “Frank walkability index” + first author LD Frank for the canonical formulation.*

---

## 3. Accessibility (gravity-style) — you already use a cousin for subway

| Source | Formula idea |
|--------|----------------|
| **Hansen (1959)** — accessibility | \(A_i = \sum_j O_j \cdot f(c_{ij})\) where \(f\) decays with cost (distance/time). |
| **Your pipeline** | \(\log(1+R)/(d+buffer)\) for **ridership-weighted** transit access is a **gravity-like** score—cite Hansen or a standard **transport geography** text (e.g. **Miller & Shaw**, *Geographic Information Systems for Transportation*) for the **functional form** rationale. |

---

## 4. Risk / harm **per exposure** (epidemiology-style)

| Source | Idea |
|--------|------|
| **Road safety / epidemiology framing** | Rate = **events / exposure** (injuries per person-km, or per unit activity). |
| **Your** \(\mathrm{ksi\_rate}_i = H_i/(E_i+1)\) | Same **logic** as “harm per modeled pedestrian activity”—cite **WHO** road safety documents or a **Vision Zero** evaluation paper for **rate** language (not the +1 smoothing—that’s a small numerical device; say so). |

---

## 5. LTN / traffic restraint (outcome framing, not your GIS proof)

| Source | Use |
|--------|-----|
| **Aldred et al. (2021)** — London LTN equity | **Siting** and **distribution**—already in your lit list. |
| **TfL / UK DfT** reports | **Evaluation norms** (what gets measured post-scheme)—pairs with `LONDON_TO_NYC_TRAFFIC_OPPORTUNITIES_ILLUSTRATION.md`. |

---

## 6. Environmental justice / cumulative burden (optional paragraph)

| Source | Idea |
|--------|------|
| **Maantay**, **Chakraborty** (NYC environmental justice) | **Spatial concentration** of burdens—**parallel** to arguing pedestrian harm **clusters** in dense mixed areas; use **carefully** (pollution ≠ your index). |

---

## 7. What **not** to over-import

- **Space syntax** full integration scores — need **axial maps** and different software; cite as **alternative tradition**, don’t rebuild unless scoped.  
- **Walk Score** — proprietary; cite conceptually if at all.  
- **Any** formula: paste **only** what you actually **use** or **parallel**; don’t decorate with equations you don’t implement.

---

## 8. Suggested “minimum bibliography” expansion (methods + lit)

1. Sevtsuk et al. — NYCWalks (**required**).  
2. Frank et al. or Ewing & Cervero — **walkability / D variables** (**one** of these).  
3. Hansen or Miller & Shaw — **accessibility** (**optional** if you emphasize map 6).  
4. WHO or peer **road injury per exposure** framing — **optional** for KSI rate paragraph.  
5. Aldred et al. — LTN equity (**already**).  

---

## 9. One honest sentence for the thesis

> The tract-level **combined index** is **not** taken from a single prior publication; it is a **transparent weighted combination** of **pedestrian exposure**, **exposure-conditioned harm**, and **residential mix**, **motivated** by **walkability** and **risk-rate** traditions (Frank; Ewing & Cervero; Hansen-style accessibility for transit; injury-rate language following road-safety practice), **calibrated** here only in the sense of **documented weights and sensitivity** (`DATA_LOCK.md`), not **welfare-optimized** weights.

---

*This file is a reading list + framing guide, not a literature review draft.*
