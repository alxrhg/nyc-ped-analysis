# LTN “effects,” prediction models, and defining a “good result”

**Purpose:** Separate what a **prediction model** can show from what counts as **evidence that an LTN worked**—and give thesis-usable definitions of **good** that match what you can actually measure.

---

## 1. Three different questions (do not merge them)

| Question | Tool family | Your Houston–Canal thesis |
|----------|-------------|---------------------------|
| **A. Where** is pedestrian activity + harm pressure + mixed use **concentrated**? | Descriptive GIS, indices, maps | **Yes — core contribution** |
| **B. Given features \(X\), can we **predict** \(Y\) (e.g. high crash rate class)? | Supervised ML / stats | **Optional** — typology or screening only |
| **C. Did (or would) an **LTN cause** \(\Delta Y\) (safety, flow, equity)? | Causal inference, before–after, DiD, simulation | **Not** from cross-sectional NYC tract map alone |

A model that **predicts** \(Y\) from \(X\) answers **B**, not **C**. It does **not** prove that installing filters **changes** outcomes unless **LTN (or equivalent) is embedded in the data as a treatment** with a **credible comparison group** or **time dimension**.

---

## 2. What “good result” should mean — pick definitions by chapter

Avoid one vague “good.” Use **explicit criteria** tied to **evidence type**:

### 2.1 Spatial / planning screening (what your GIS chapter can claim)

**Good result (defensible):**  
The Houston–Canal study tracts **rank highly** on a **stated combination** of:

- modeled **pedestrian intensity** (or exposure proxy),
- **exposure-conditioned** or **density-based** pedestrian harm metrics,
- **residential / mixed-use** stock (PLUTO),
- optional **transit context**,

**relative to** Manhattan and/or **peer NTAs**, with **sensitivity** to index rules.

**Not required for this to be “good”:** proof of post-intervention safety.

### 2.2 Outcome-based “good” (safety, traffic) — only with causal design

**Good result (strict):**  
A **documented change** in pre-specified outcomes **after** an intervention (or a **credible quasi-experiment** comparing treated vs control over time).

Examples elsewhere: London evaluations, academic DiD on LTN areas.  
**Your corridor:** no installed LTN in the study → you **do not** claim this level of outcome proof for NYC without **external** studies or **future** pilot data.

### 2.3 Equity “good”

**Good result (defensible in thesis):**  
Explicit **who** lives/works near high-stress segments (ACS + maps); alignment or tension with **siting** norms from literature (e.g. Aldred et al. on London)—**not** proof that *your* proposal distributes benefits fairly without implementation detail.

### 2.4 Governance “good”

**Good result:**  
Clear **pathways and barriers** (law, politics, agencies) from **documents and interviews**—**conditional** recommendations, not a single score.

---

## 3. If you still add a “prediction model” — honest roles

### 3.1 Role A — **Risk / stress typology** (recommended if you add ML)

- **\(Y\):** e.g. high vs low **pedestrian KSI density** or **ksi_rate** class (defined on **historical** window).
- **\(X\):** tract features you already have (and optionally ACS, DOT count density in buffer).
- **Claim:** “Model **separates** tract types along harm–exposure–mix axes; study tracts **fall** mainly in [these] clusters.”
- **Non-claim:** “Model proves LTN **effect**.”

Report **simple, interpretable** models first (logistic regression, small RF with **permutation importance** or SHAP). **Spatial cross-validation** if you want to be slightly more serious about overfitting (still not causal).

### 3.2 Role B — **Forecasting future crashes**

- **Very risky** at tract scale: **non-stationarity**, **autocorrelation**, policy endogeneity. Easy to **overfit**. Committee may ask why forecasts matter without intervention timing.
- **Skip** unless advisor explicitly wants it.

### 3.3 Role C — **Simulated LTN effect**

- Requires **network model** (routing, OD or approximate demand), **treatment** on links/zones, **before/after** assignment. **Different thesis**; H100 optional, **data and calibration** are the hard part.

---

## 4. One paragraph you can put in Discussion

> This thesis does **not** estimate a **causal treatment effect** of Low Traffic Neighborhoods on the Houston–Canal corridor because no such scheme is observed here and the analysis is **cross-sectional**. **“Good”** is therefore defined in **layers**: (1) **spatial screening**—whether the corridor exhibits **high** modeled walking, **meaningful** pedestrian harm pressure relative to exposure, and **mixed** urban fabric compared to explicit comparators; (2) **institutional** feasibility and conflict from **historical and qualitative** evidence; (3) **equity and boundary-road** considerations informed by **literature** and optional **demographic** overlays. A **predictive model**, if used, classifies **tract stress typologies** and must not be read as proof that **installing filters** would **produce** a given safety or traffic outcome.

---

## 5. Checklist before you invest in a prediction chapter

- [ ] **\(Y\)** is defined without **leaking** future information.  
- [ ] **Claim** is **typology / association**, not **LTN causal effect**.  
- [ ] **Train/test** or **cross-validation** strategy is stated (ideally **spatial** blocks if you care about generalization).  
- [ ] **Methods** name data lock and **features**; **Discussion** repeats **non-causal** interpretation.  
- [ ] Advisor agrees the **added complexity** is worth it vs **stronger qual** or **ACS equity** layer.

---

*For transparent equations without ML, see `docs/EXPLAINABLE_MODEL_DATA_PROOF_CHAIN.md`. For extra Open Data ideas, `docs/OPEN_DATA_ENRICHMENT_IDEAS.md`.*
