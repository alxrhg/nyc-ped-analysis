# Structured thesis outline — Houston–Canal / LTN scalability

**Alexander Huang** · Urban Studies · The New School  
**Working title:** *Examining the Scalability of Low-Traffic Neighborhoods in NYC: A Proposal for the Houston-Canal Corridor*

**Companion docs:** **BA Urban Studies (formal chapters)** → `docs/ACADEMIC_THESIS_OUTLINE_URBAN_STUDIES.md` (**GIS as centerpiece** spelled out there). **One-page skim** → `docs/QUICK_OUTLINE_UPDATED.md`. Logic and definitions → `docs/THESIS_OUTLINE_COHERENT.md`. Data lock + quant prose → `docs/DATA_LOCK.md`, `docs/RESULTS_QUANT_PROSE_AND_CAPTIONS.md`.

**Narrative:** **Chapter 5 (quant / GIS)** is the **longest, primary empirical chapter**; Chapters 2–4 **prepare** it; Chapter 6 **interprets** implementation; 7–8 **return** to the maps before closing.

---

## Executive spine (memorize this)

| Layer | Your claim (quality bar) |
|--------|---------------------------|
| **Argument** | LTN-style management is **politically and legally contested** in NYC but **not incoherent**; **Houston–Canal** is a **plausible spatial focus** for further **design and coalition** work—on **your** evidence, not on simulated traffic. |
| **Evidence types** | (1) History & policy (2) Concepts & NYC fit (3) Tract GIS (4) Interviews & documents (5) International desk lit. |
| **Non-claims** | You do **not** prove diversion, through-traffic reduction, or before–after safety from the pipeline. |

---

## Part I — Problem, context, and lens

### Chapter 1 — Introduction

| Section | Content |
|---------|---------|
| **1.1** | Walking as infrastructure; NYC’s **car-through / grid** tension; why **LTN** (filtering / coexistence) rather than **1997-style** full pedestrianization. |
| **1.2** | **Houston–Canal** as focal geography: what bound, why it matters, what “study area” means in the thesis. |
| **1.3** | **Research question** (conditions, limits, pathways for LTN-*style* options in NYC) + **sub-questions** (see coherent spine doc). |
| **1.4** | **Scope and limits** — what each evidence type can answer; pointer to Methods for technical limits. |
| **1.5** | **Roadmap** — chapter summary in one page. |

**Reader takeaway:** They know the puzzle, the case corridor, and what you will *not* pretend to prove.

---

### Chapter 2 — Histories, policy, and precedents

| Section | Content |
|---------|---------|
| **2.1** | Manhattan **grid**, **through-traffic**, freight / CBD pressure — enough urban form to ground politics. |
| **2.2** | **1997 Lower Manhattan pedestrianization** arc: ambition, backlash, **why full closure failed** as a political model. |
| **2.3** | **Contemporary hooks:** Local Law 55, Open Streets, congestion / street-space politics (tight, cited). |
| **2.4** | **International desk — London:** LTN rollout + **TfL / safety discourse** + **equity / siting** (e.g. Aldred et al. 2021). |
| **2.5** | **One deep secondary comparator** (e.g. Barcelona **or** Tokyo/Ginza material); others **one paragraph** max. |
| **2.6** | **Bridge:** why LTN language re-enters *after* 1997 — **smaller bite**, **different coalition math**. |

**Reader takeaway:** NYC’s institutional memory **blocks** one model of pedestrian priority but **leaves room** to discuss another.

---

### Chapter 3 — Analytical framework

| Section | Content |
|---------|---------|
| **3.1** | **LTN mechanism:** interior filter, boundary roads, local access, services / emergency **as design problem**. |
| **3.2** | **NYC translation:** grid, DOT practice, enforcement, **CB / council** politics — **fit and misfit**. |
| **3.3** | **Conceptual diagram** (optional): inputs → governance vs. spatial conditions → “pathways / barriers.” |
| **3.4** | **Evidence map:** which sub-question is answered by **GIS**, **documents**, **interviews**, **international** lit. |

**Reader takeaway:** Clear **operational definition** of LTN for *this* thesis and a **preview of the mixed-methods design**.

---

## Part II — How you studied it

### Chapter 4 — Methods

| Section | Content |
|---------|---------|
| **4.1** | **Mixed-methods design** — sequential or parallel logic; how chapters 5–6 combine. |
| **4.2** | **Qualitative:** interview sampling / substitutes, document corpus, coding approach, ethics / anonymity. |
| **4.3** | **Quantitative:** units (2020 tract), sources (NYCWalks, NYPD, PLUTO, MTA), CRS, study polygon (CSCL), **combined index** + **rank floor** + **sensitivity**; **`DATA_LOCK.md`**. |
| **4.4** | **Integration rule:** when a claim is **GIS-backed**, **interview-backed**, or **literature-backed**. |
| **4.5** | **AI / tools disclosure** (short; align with LU3 appendix paragraph). |

**Reader takeaway:** Reproducible, **bounded** methods; no bait-and-switch on what was measured.

---

## Part III — Findings

### Chapter 5 — Results: quantitative (spatial analysis)

| Section | Content |
|---------|---------|
| **5.1** | **Borough context** — what maps 1–3 show (exposure, crashes, residential mix) in plain language. |
| **5.2** | **Corridor focus** — tracts intersecting Houston–Canal; **borough vs. study** comparison. |
| **5.2b** | **Reference NTAs** — **West Village (MN0203)**, **Financial District–Battery Park City (MN0101)**, **Midtown–Times Square (MN0502)**, **Midtown South–Flatiron–Union Square (MN0501)**: same metrics, **area-weighted** NTA means vs **area-weighted** study-tract mean (`peer_nta_comparison.csv`; methodology `docs/COMPARISON_PEERS_WEST_VILLAGE_FIDI_MIDTOWN.md`). Interpret as **descriptive peers**, not controls. |
| **5.3** | **Combined index** — always pair **`combined_idx_base`** and **`combined_idx`** when rank floor applies; **no-floor** sensitivity in text or footnote. |
| **5.4** | **Transit layers** — subway distance and ridership-weighted access as **context**, not LTN outcomes. |
| **5.5** | **NTA-readable summary** (optional subsection) — neighborhood names for non-GIS readers. |
| **5.6** | **Interpretation guardrails** — “**consistent with** LTN *problems* (walking + harm + mix)” ≠ proof of filters. |

**Draft text / captions:** `docs/RESULTS_QUANT_PROSE_AND_CAPTIONS.md`.

**Reader takeaway:** The corridor is **spatially legible** as a **high-activity, mixed, transit-rich** band with **heterogeneity inside the polygon**.

---

### Chapter 6 — Results: qualitative (documents and interviews)

| Section | Content |
|---------|---------|
| **6.1** | **Document findings** — 1997 study, Local Law 55, CB / agency materials: **themes** tied to mechanisms from Ch. 3. |
| **6.2** | **Interview findings** — barriers, allies, **language** (LTN vs. “closing streets”). |
| **6.3** | **Crosswalk to map** — where qual **confirms**, **complicates**, or **fails to see** what GIS suggests (no forced fit). |
| **6.4** | **Limits** — access, positionality, what was not heard. |

**Reader takeaway:** **Why** implementation is hard **independent of** whether the choropleth looks “bad.”

---

## Part IV — Synthesis and close

### Chapter 7 — Discussion

| Section | Content |
|---------|---------|
| **7.1** | **Synthesis table or matrix:** institutional / spatial / political / equity dimensions × **evidence** × **verdict** (conditional language). |
| **7.2** | **Data gaps** — no through-share in pipeline; modeled walking; planar subway; **what a pilot would need**. |
| **7.3** | **Equity and distribution** — London precedent vs. NYC; **no overclaim**. |
| **7.4** | **Boundary roads, freight, emergency** — honest treatment of **LTN criticisms**. |
| **7.5** | **Answer to central question** — pathways and limits in **one** disciplined page. |

**Reader takeaway:** Scalability = **governance + politics + measurement**, not a single map score.

---

### Chapter 8 — Conclusion

| Section | Content |
|---------|---------|
| **8.1** | **Claims restated** — what changed from Ch. 1 to here. |
| **8.2** | **Recommendations** — staged, actor-specific (who does what). |
| **8.3** | **Policy one-pager** — contents summarized or included as appendix. |
| **8.4** | **Future research** — counts, pilots, network models, equity variables. |

**Reader takeaway:** Clear **stop point** and **honest next steps**.

---

## Appendices (suggested)

| Appendix | Content |
|----------|---------|
| **A** | Figure set at print resolution + **captions** (mirror `RESULTS_QUANT_PROSE_AND_CAPTIONS` §2). |
| **B** | **Data lock** + reproducibility (repo path, command, key CSV names). |
| **C** | Interview guide / codebook excerpt (if allowed). |
| **D** | Extended methods (equations, extra sensitivity tables). |

---

## Writing order (optional)

1. Ch. 4 Methods + Ch. 5 Results (quant) — **stable** once data lock is final.  
2. Ch. 2–3 — **narrative spine**.  
3. Ch. 6 — **when transcripts exist**.  
4. Ch. 1 roadmap + Ch. 7–8 — **last**, so they match what you actually wrote.

---

## One-page checkpoint before submission

- [ ] Central question answered in **Ch. 7** in the reader’s own words.  
- [ ] No chapter implies **traffic engineering proof** from GIS.  
- [ ] Ch. 5 + Ch. 6 **both** support any **“plausible candidate”** language.  
- [ ] **DATA_LOCK** dates filled; figures match lock.  
- [ ] International lit **frames**, does not **prove** NYC outcomes.

---

*This outline is the default **table of contents** scaffold; trim subsections per advisor and page limits.*
