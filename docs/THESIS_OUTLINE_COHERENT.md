# Thesis outline — coherent spine (Houston–Canal / LTN scalability)

**Working title:** *Examining the Scalability of Low-Traffic Neighborhoods in NYC: A Proposal for the Houston-Canal Corridor*  
**Author:** Alexander Huang · Urban Studies · The New School  

**For a chapter-by-chapter TOC with section numbers (1.1, 1.2, …), use `docs/STRUCTURED_THESIS_OUTLINE.md`.** **Narrative:** the **GIS / Chapter V outcomes** are the **centerpiece**; other chapters interpret and limit them—see `docs/ACADEMIC_THESIS_OUTLINE_URBAN_STUDIES.md` (“Narrative spine”). This file stays the **short logic model** (definitions, sub-questions, chapter jobs table).

This document is the **logic model** for the thesis: one central question, what each chapter **decides**, and how **GIS, documents, interviews, and international literature** fit together without overclaiming.

---

## 1. What “scalability” means in *this* thesis

In engineering, “scalable” often means **proven at growing size**. This thesis **does not** simulate traffic filters or measure before–after diversion. Here **scalability** means:

| Dimension | Question the thesis can actually address |
|-----------|-------------------------------------------|
| **Institutional** | Under NYC law, politics, and recent history, is **LTN-style** management even *discussable*—or does the 1997 pedestrianization failure mode block it? |
| **Spatial / urban form** | Does the **Houston–Canal corridor** show tract-scale conditions **consistent with** the problems LTN frameworks target (dense walking context, pedestrian harm pressure, mixed fabric)—using **open data + NYCWalks**, not through-traffic counts? |
| **Political / operational** | What **barriers and enablers** do stakeholders and documents surface for **piloting** filtered streets here? |
| **Precedent & equity** | What do **London and other cases** suggest about **siting, conflict, and equity**—as **external** evidence, not as proof for Manhattan? |

**One-sentence thesis claim (for the Introduction and Conclusion):**  
The thesis argues that **LTN-style street management is institutionally contested but not absurd in NYC**, that **Houston–Canal is a plausible spatial candidate for further design and coalition work** (on the evidence you actually produce), and that **scalability** therefore depends more on **governance, measurement, and politics** than on your maps alone.

---

## 2. Central research question (and sub-questions)

**Central question:**  
What are the **conditions, limits, and plausible pathways** for **low-traffic-neighborhood–style** street management **in NYC**, with **Houston–Canal** as the focal corridor?

**Sub-questions (each maps to evidence types):**

1. **History and policy:** Why did **ambitious pedestrianization** stall in Lower Manhattan, and how do **Local Law 55**, Open Streets, and current rules **shape what is possible**?
2. **Conceptual:** What do **LTNs** assume (filters, boundary roads, access), and how does that **translate** (or not) to a **grid-heavy, freight-heavy** US central business district?
3. **Spatial (quantitative):** At **tract scale**, how does the corridor score on **modeled walking exposure, crash harm proxies, residential mix, and subway context** relative to Manhattan—and what does that **imply for “candidate site”** language?
4. **Qualitative:** What do **interviews and documents** say about **implementation barriers**, **constituencies**, and **framing** (LTN vs. 1997-style “closure”)?
5. **Synthesis:** Given (1)–(4), is **piloting** LTN-style measures **defensible as a next conversation**—and what **data and process** would be needed **next**?

---

## 3. Chapter-by-chapter: what each chapter *does*

| Ch | Title (working) | Job of the chapter | Primary evidence |
|----|-----------------|--------------------|------------------|
| **1** | Introduction | Name the puzzle (walkability vs. car dominance); define **Houston–Canal**; define **LTN** as **filtering/coexistence**; state **what you prove vs. do not prove** (no simulated LTN outcomes). | None new—sets terms. |
| **2** | Histories, policy, and precedents | **NYC story** (grid, through-traffic politics, **1997** study, what failed); **national/NYC policy hooks** (Local Law 55, Open Streets); **international** as **compressed** context—**London** (TfL safety + **Aldred et al. on equity/siting**), **one** strong secondary (e.g. Barcelona or Ginza). | Secondary sources + key documents. |
| **3** | Analytical framework | **LTN mechanism** (interior filter, boundary traffic, services/emergency); **NYC constraints** (legal, DOT practice, political risk); **bridge to methods**: how **spatial layers** and **qualitative** work **each answer part of the central question**. | Concepts + citations; no new empirics. |
| **4** | Methods | **Qualitative:** interviews, document corpus, coding. **Quantitative:** tract GIS (NYCWalks, NYPD, PLUTO, MTA, study polygon, optional index); **data lock**; **sensitivity** (e.g. rank floor, centroid). **Integration:** how chapters 5–6 feed question 5. | Protocol + reproducibility note. |
| **5** | Results — quantitative | **Maps and tables**; **borough vs. corridor**; **plain findings** with **`combined_idx_base` vs. `combined_idx`** where emphasis rules apply; **interpretation**: “**consistent with** LTN rationale for *this* kind of place,” not causal traffic claims. | CSVs, figures. |
| **6** | Results — qualitative | Themes from interviews/docs: **barriers**, **allies**, **language**; how **LTN** differs politically from **full pedestrianization**. | Transcripts, memos. |
| **7** | Discussion | **Explicit synthesis table**: institutional / spatial / political / equity; **data gaps** (no through-share in your pipeline); **equity, emergency access, boundary roads**; **Aldred-style** equity only as **precedent**, not NYC proof. | All prior chapters. |
| **8** | Conclusion | **Recommendations**; **policy one-pager** content; **research agenda** (what a *future* study with counts or pilots would do). | — |

This order keeps **history and cases before** your **framework** (so the reader knows *why* LTN is being proposed), then **methods**, then **two results chapters**, then **discussion**.

---

## 4. How Chapters 2 and 3 stay distinct (common confusion)

- **Chapter 2 = “what happened and what others did.”** Narrative, policy, and **desk** international comparison.  
- **Chapter 3 = “how I think about LTN in NYC and what I will test.”** Definitions, mechanisms, **fit/misfit** with Manhattan grid + freight, and **explicit scope** for GIS and interviews.

If Chapter 2 grows too long, **shorten** Tokyo/Saigon to a paragraph each; keep **London** for **both** TfL-style outcomes discourse **and** **equity/siting** (Aldred et al.). For a **New York vs. Tokyo** desk reading, use your scan `4_2_NewYork_Tokyo.pdf` as **comparative context** (see `docs/LITERATURE_4_2_NewYork_Tokyo.md` for placement and limits—add full citation from the PDF’s title page).

---

## 5. Red thread checklist (committee-facing)

- [ ] Every chapter opening **one sentence** ties back to the **central question**.  
- [ ] **Quantitative** chapter never claims **through-traffic reduction** or **LTN simulation** from your code.  
- [ ] **Qualitative** chapter explains **why** maps alone cannot answer **political** scalability.  
- [ ] **Discussion** uses the word **“plausible candidate”** or equivalent only where **Ch. 5 + Ch. 6** together support it.  
- [ ] **International** citations support **framing and equity**, not **“this will work on Canal Street.”**

---

## 6. Relation to Learning Unit 3 documents

- **`LU3_INSTRUCTOR_RESPONSE_REVISED.md` §4** should match this spine (abbreviated list is fine).  
- **`LU3_FINDINGS_REFLECTION_OUTLINE.md`** remains the **findings + timeline** supplement; replace any reference to removed `PROPOSAL_VS_PIPELINE_ALIGNMENT.md` with **this file** for outline logic.

---

*Use this file when the outline “doesn’t feel like one argument.” The thesis is one question answered by four kinds of evidence, not four parallel papers.*
