# Academic outline — Bachelor of Arts, Urban Studies thesis

**Student:** Alexander Huang · **Program:** Urban Studies, The New School  
**Working title:** *Examining the Scalability of Low-Traffic Neighborhoods in New York City: A Proposal for the Houston–Canal Corridor*

**Note:** Chapter numbering and titles should be adjusted to match your program’s **thesis handbook** and advisor preference (some committees combine Chapters II and III, or merge Findings into a single chapter).

---

## Narrative spine — GIS outcomes as centerpiece

**Committee-facing story:** The thesis **leads with** reproducible **tract-scale GIS** of the Houston–Canal corridor (and Manhattan context): what **open data + NYCWalks** show about **modeled walking exposure**, **pedestrian harm pressure**, **mixed building stock**, and **transit context**. Every other chapter **supports interpretation** of that centerpiece—not parallel “another study.”

| Chapter role | Relation to GIS centerpiece |
|--------------|-----------------------------|
| **I Introduction** | States the puzzle and **promises** the spatial evidence readers will see in Ch. V; RQ framed as “what do we learn from **mapping** this corridor in dialogue with LTN ideas?” |
| **II Literature & history** | **Lenses** to read the maps (LTN concepts, NYC street politics, equity precedents)—not a substitute for Ch. V. |
| **III Framework** | Defines **how** to describe map outputs without overclaiming (scalability dimensions, screening vs causal proof). |
| **IV Methods** | GIS pipeline is **primary** technical contribution; qual methods **secondary** but necessary for politics. |
| **V Findings — GIS** | **Centerpiece:** figures, tables, peer NTAs, sensitivity—**longest** empirical chapter. |
| **VI Findings — qual** | **Interprets why** the spatial pattern is hard or possible to **act on** in NYC (documents/interviews). |
| **VII Discussion** | **Opens** with what Ch. V **shows**, then folds in Ch. VI + II–III (so the argument **returns** to the maps). |
| **VIII Conclusion** | Recommendations **tied to** the spatial diagnosis (“given what the tract analysis shows…”). |

**Abstract:** Lead with **one sentence** on the **GIS finding** (corridor relative to borough/peers), then methods sketch, then qual/policy implications.

---

## Abstract

*Draft last (150–250 words). **Lead with the spatial centerpiece:** what the tract-level analysis shows about the Houston–Canal study area relative to Manhattan (and peers if used). Then:* mixed methods *briefly*; principal **map/table** takeaways; modest policy implications. State explicitly that the study does not estimate traffic diversion or causal safety impacts from the spatial analysis.

---

## Chapter I — Introduction

**Purpose:** Establish the research problem, case selection, and the boundaries of the argument—**oriented toward the GIS centerpiece** in Chapter V.

1. **Context and problem.** Walking as urban infrastructure; motor dominance and through-traffic on Manhattan’s grid; limits of official pedestrian data—and why **mapping** the corridor matters.
2. **Low-traffic neighborhoods (LTNs).** Definition for this thesis: area-based filtering of through motor traffic while preserving local access; contrast with comprehensive pedestrianization.
3. **Case focus.** The **Houston–Canal** corridor as a geographically explicit study area (CSCL-derived polygon) and why Lower Manhattan warrants analysis.
4. **Research question and sub-questions.** Framed so Ch. V **answers the spatial half** directly; qual and history answer **limits and pathways**.
5. **Contribution.** **Primary:** reproducible, explainable **tract GIS** of pedestrian-related conditions in a defined LTN-relevant corridor. **Supporting:** literature, framework, and qualitative material to **interpret** those outcomes and institutional feasibility.
6. **Scope and limitations.** What the **maps** demonstrate versus what they do not claim (no LTN simulation; no before–after causal inference from GIS alone).
7. **Organization of the thesis.** Roadmap that **foregrounds** Chapter V (“the spatial analysis appears in Chapter V; Chapters II–IV prepare and document it; Chapters VI–VIII interpret and conclude”).

---

## Chapter II — Literature Review and Historical Context

**Purpose:** Supply **interpretive lenses** for the **GIS outcomes** in Chapter V—situate the thesis in scholarship and NYC institutional history so the maps are not read in a vacuum.

1. **Walking, streets, and urban form.** Relevant urban design and planning literature (e.g. street life, grid logic, freight and CBD pressure)—concise, cited.
2. **Pedestrian safety, exposure, and data.** Modeling and open-data debates; role of modeled pedestrian exposure (e.g. NYCWalks) as proxy versus observed counts.
3. **Low-traffic neighborhoods and active travel.** UK/European literature on LTNs, controversy, and evaluation; **equity and siting** (e.g. spatial analyses of London rollout).
4. **New York City street governance.** **1997 Lower Manhattan pedestrianization** proposal and its political fate; evolution toward **incremental** tools (e.g. Local Law 55, Open Streets)—documented, cited.
5. **International comparison (selective).** One or two additional cities (e.g. Barcelona, Tokyo) as **context**, not as proof of transferability to Canal Street.
6. **Synthesis.** Gap: readers need **concepts and history** to interpret **Chapter V’s maps** responsibly—especially LTN rhetoric vs NYC politics and equity debates.

---

## Chapter III — Conceptual and Analytical Framework

**Purpose:** Define **concepts** and **rules of interpretation** for **reading Chapter V**—what the indices can and cannot claim.

1. **Operational definition of LTN mechanisms.** Interior filters, boundary arterials, local access, emergency and service vehicle considerations.
2. **Translation to New York.** Grid geometry, enforcement, agency roles, community board and council politics—**fit and friction** between LTN logic and NYC practice.
3. **Dimensions of “scalability” in this thesis.** Institutional (law, politics), spatial (urban form and indicators), operational (implementation barriers), and precedent/equity (international evidence)—**distinct from** engineering proof of traffic outcomes.
4. **Mixed-methods logic.** **GIS first** in the evidence hierarchy for **spatial claims**; qualitative and historical material **extends** interpretation to governance; **integration** criteria (when claims are map-supported, interview-supported, or literature-supported).

---

## Chapter IV — Research Design and Methodology

**Purpose:** Meet expectations for **transparency** and **reproducibility**; **foreground the GIS pipeline** as the thesis’s primary technical contribution.

1. **Overall design.** Case-embedded study whose **empirical centerpiece** is tract-scale GIS; document analysis and interviews **contextualize** map-based findings.
2. **Quantitative / GIS component (primary).** Spatial units (**2020 census tracts**); data sources (**NYCWalks**, NYPD motor vehicle collisions, PLUTO, MTA subway locations and ridership); coordinate reference system; construction of **borough percentile maps** and **combined index**; **study polygon** definition; **sensitivity analysis** (e.g. rank floor, aggregation choice); **data lock** and versioning of downloads. **Explainable model ↔ data chain**: `docs/EXPLAINABLE_MODEL_DATA_PROOF_CHAIN.md`.
3. **Qualitative component (supporting).** Document corpus (e.g. 1997 study, statutes, agency/community materials); interview strategy, sampling, coding, ethics and confidentiality; limitations of access or generalizability.
4. **Comparative spatial context (recommended).** Official **NTAs** as **reference geographies** (e.g. West Village, Financial District, Midtown) versus the study polygon—**descriptive** comparison only (`docs/COMPARISON_PEERS_WEST_VILLAGE_FIDI_MIDTOWN.md`).
5. **Ethical use of secondary data and tools.** Citation practice; role of computational or AI-assisted drafting (if required by program)—**assistance only**, not a source of empirical claims.
6. **Chapter summary.** Bridge to **Chapter V (centerpiece)**.

---

## Chapter V — Findings: Quantitative Spatial Analysis *(thesis centerpiece)*

**Purpose:** Present the thesis’s **primary empirical contribution**—reproducible **GIS results** for Houston–Canal and Manhattan context. This chapter should be **substantial**: multiple figures, at least one summary table, and plain-language interpretation **on every map**.

1. **Manhattan-wide patterns.** Pedestrian exposure, crash intensity, residential mix, and transit-related layers—interpreted as **borough-relative** context.
2. **Houston–Canal study area.** Tracts intersecting the polygon; **heterogeneity** within the corridor; **combined index** with explicit treatment of **base** versus **displayed** index where **rank-floor** rules apply.
3. **Reference neighborhood comparison.** Area-weighted metrics for selected **NTAs** (e.g. West Village, Financial District–Battery Park City, Midtown NTAs) compared to the study area; emphasis on **comparable** quantities (e.g. base index and component percentiles), with **caveats** on index construction.
4. **Synthesis of quantitative findings.** Plain-language summary: conditions **consistent with** the *problems* LTN frameworks often target—**without** claiming simulated LTN impacts or through-traffic shares from this analysis.

---

## Chapter VI — Findings: Qualitative Analysis

**Purpose:** Answer: **given what Chapter V shows spatially**, what do **documents and interviews** say about **acting on** that evidence in NYC?

1. **Document analysis findings.** Themes tied to legal and planning history (e.g. barriers to wholesale pedestrianization; incremental tools)—**linked** to map themes (e.g. freight, tunnel traffic, local vision plans such as SoHo Broadway Initiative 2021).
2. **Interview findings (if completed).** Stakeholder perspectives on pedestrian priority, opposition frames, and feasibility; **LTN** versus **closure** narratives.
3. **Integration with Chapter V.** Explicit **crosswalk**: which map patterns are **expected** given politics, which are **surprising**, and what **cannot** be read from maps alone; limits (e.g. who was not interviewed).

---

## Chapter VII — Discussion

**Purpose:** **Anchor** the argument in **Chapter V**, then widen to framework, qual, and literature.

**Defining “good” and limits of prediction:** If you add a supervised **prediction** model, it can support **tract typology / risk grouping** only—not **causal proof** of LTN impacts without treatment timing and a comparison strategy. See `docs/LTN_OUTCOMES_PREDICTION_VS_CAUSATION.md` for separating **screening**, **outcome evaluation**, **equity**, and **governance** definitions of success.

1. **What the GIS centerpiece establishes.** Restate the **main spatial findings** (corridor vs borough vs peers; base vs displayed index; sensitivity)—**before** folding in other evidence.
2. **Synthesis across evidence types.** Institutional, spatial, political, and equity dimensions revisited.
3. **Implications for LTN-style proposals in NYC.** Defensible **pathways** (pilots, coalitions, data needs) versus **hard limits** (diversion modeling, political conflict).
4. **Equity, emergency access, and boundary-road concerns.** Engage criticisms seriously; use international literature **appropriately** (precedent, not proof).
5. **Limits of the study.** Data gaps; generalizability beyond the corridor; suggestions for **future research** (observation, pilots, network models).

---

## Chapter VIII — Conclusion

**Purpose:** Close the argument and state **modest**, well-grounded recommendations.

1. **Restatement of argument** in light of findings—**lead with the spatial diagnosis** from Chapter V, then governance implications—not a copy-paste of Chapter I.
2. **Recommendations.** For planners, advocates, or policymakers—**staged** and **feasible** within stated limits; **explicitly tied** to GIS findings where relevant.
3. **Policy communication (if required).** One-page summary or memo (per program expectations).
4. **Final reflection.** What the thesis adds to **Urban Studies** understandings of **street-space politics** and **pedestrian infrastructure** in dense U.S. cities.

---

## References

*Full bibliography in Chicago or APA per New School / program guidelines.*

---

## Appendices

*As approved by advisor; examples below.*

- **Appendix A:** Figure plates (maps) with captions aligned to **data lock**.
- **Appendix B:** Reproducibility note (repository location, key commands, CSV outputs).
- **Appendix C:** Interview guide or codebook excerpt (if permissible).
- **Appendix D:** Supplementary tables (tract or NTA statistics, sensitivity runs).

---

## Relation to internal working outlines

| Document | Use |
|----------|-----|
| `QUICK_OUTLINE_UPDATED.md` | Day-to-day skim |
| `STRUCTURED_THESIS_OUTLINE.md` | Section-level drafting (1.1, 5.2b, …) |
| `THESIS_OUTLINE_COHERENT.md` | Definitions of “scalability” and sub-questions |
| **This file** | **Advisor / committee** and **handbook** alignment |

---

*Revise chapter titles to match your department’s preferred nomenclature (e.g. “Analysis” instead of “Findings,” or a single “Results” chapter combining V and VI if page limits require).*
