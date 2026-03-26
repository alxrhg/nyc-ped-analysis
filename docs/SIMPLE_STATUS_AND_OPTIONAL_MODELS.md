# What you have so far (plain language) + optional “extra” analyses explained simply

---

## Part 1 — What you’ve already got

Think of the thesis GIS piece as: **“A report card for every Manhattan census tract on walking, crashes, building mix, and subway access—and a spotlight on the Houston–Canal box.”**

**Data you combine (all public or published):**

- **Walking-ish activity:** MIT **NYCWalks** gives *estimated* pedestrian volumes along streets; you roll those up to **tracts** (neighborhood-sized blocks used by the Census).
- **Crashes:** NYPD **motor vehicle collisions**, especially harm to **pedestrians**, counted **inside each tract** over a date range you choose.
- **Land use mix:** **PLUTO** — how much of each tract’s building units are **residential** vs other uses.
- **Subway:** how **close** tracts are to stations and (optionally) how **busy** those stations are.

**What you produce:**

- **Maps** (choropleths): darker/lighter = higher/lower vs *the rest of Manhattan* for each theme.
- A **combined score** (your index): mixes walking rank, harm rank, and residential mix in a **transparent** recipe you can explain in words.
- A **study polygon** (Houston–Canal): tracts that touch that box get extra attention; you can compare them to **West Village, FiDi, Midtown** NTAs as “peer neighborhoods.”
- **Sensitivity checks:** e.g. “what if we don’t boost the corridor on the map?” or “what if we count walking slightly differently?” — so readers trust you’re not hiding tricks.

**What this does *not* do (and that’s OK):**

- It does **not** simulate **“after we install an LTN.”**  
- It does **not** prove **traffic will drop X%** or **crashes will fall Y%** from a filter.  
- It **does** show **where**, in open data, the corridor looks like a **busy, mixed, high-stress-for-peds** kind of place compared to Manhattan—so it’s a **reasonable place to talk about** LTN-*style* ideas **together with** history, politics, and London examples.

**Docs you already have** (for writing the thesis): data lock, figure captions draft, outlines, how to *word* LTN claims without overclaiming, optional London “opportunity” table, etc.

---

## Part 2 — Optional “Tier 1 / 2 / 3” extras (explained simply)

These are **add-ons**. None are required. None **prove** an LTN “works.” They can make Chapter V feel **richer** if you want one extra analysis.

---

### Tier 1 — Three kinds of “math on the same tract table”

#### 1) Harm / stress **typology** (clustering — e.g. k-means)

**Plain idea:**  
You have many tracts, each with numbers (walking rank, crash harm, mix, subway…). **Clustering** asks: “If we group tracts into a few **families** (like personality types), who hangs out together?”

**Example intuition:**  
One group might be “**high walking + high harm**,” another “**high walking + low harm**,” another “**low walking + office-heavy**.”

**What you’d say in the thesis:**  
“Our study tracts mostly land in the **high walking / high pressure** family compared to the rest of Manhattan.”

**Why it’s OK:**  
You’re describing **patterns** in today’s data, not saying an LTN **caused** anything.

---

#### 2) **Supervised classification** (logistic regression or small random forest)

**Plain idea:**  
You label each tract **high** or **low** on something simple (e.g. pedestrian harm rate vs exposure). Then you ask: “Can we **guess** that label from the other columns (walking, mix, subway…)?”

**Analogy:**  
Like guessing “spam vs not spam” from words—here it’s “high-stress tract vs not” from urban features.

**What you’d say:**  
“Features **associate** with which tracts look ‘hot’ on harm-in-context; this is **not** predicting the future and **not** the effect of any policy.”

**Spatial cross-validation (simple idea):**  
If you test on tracts **near** the ones you trained on, the model can **cheat** (neighbors are similar). **Blocking** by area (e.g. north vs south Manhattan, or by NTA) is a **fairer** pop quiz—still not causal, just more honest.

---

#### 3) **Regression (OLS) at tract level**

**Plain idea:**  
One line: “Harm rate **goes up or down** with walking exposure when we hold other tract stuff constant” — fit a **straight-line-ish** relationship in data.

**Caveat in one sentence:**  
Tracts **near each other** tend to be similar (**spatial autocorrelation**), so standard “significant stars” can be **too confident**. You **note** that or run a **Moran’s I** check (see Tier 2).

**What you’d say:**  
“**Association** only; tracts aren’t random draws like survey people.”

---

### Tier 2 — **Spatial statistics** (is stuff clumped?)

#### Global **Moran’s I**

**Plain idea:**  
“Are **high** values **next to** other **high** values more than random?” (clustering of hot spots and cold spots.)

**Thesis line:**  
“Crash harm (or the index) is **spatially clustered** in Manhattan—not randomly sprinkled.”

**Still not causal** — just **geography**.

---

#### Local **Gi\*** or **LISA**

**Plain idea:**  
Moran’s I is **whole-city** “clumpiness.” **Local** tests ask tract by tract: “Is **this** tract part of a **hot spot** or **cold spot** patch?”

**Output:**  
Often a **map** with “hot spot / cold spot / not special.”

**Caveats you name:**  
- **Scale:** results change if you use tracts vs blocks.  
- **MAUP** (modifiable areal unit problem): the **shape of zones** affects counts—same reason people argue about gerrymandering, but for statistics.

---

### Tier 3 — **No fancy ML** — still “model-like”

#### **Index sensitivity**

**Plain idea:**  
You change the **recipe** slightly (e.g. weight walking 60% vs 65%, or turn the “boost corridor” rule on/off) and check: “Do the **same** tracts still float to the top?”

**Thesis line:**  
“The **story** doesn’t depend on one arbitrary knob.”

---

#### **Bootstrap** on study-area **average**

**Plain idea:**  
You **resample** tracts (with replacement) many times and see how much the **average** score **wiggles**. You get a **fuzzy band** around “the corridor’s typical level.”

**Thesis line:**  
“Here’s a **range** for the descriptive mean—not magic precision.”

**Still not** predicting LTN outcomes.

---

## Part 3 — What to actually pick (advice)

- **Zero extras** → still a complete GIS centerpiece if writing + maps are strong.  
- **One extra** → **clustering (Tier 1.1)** or **hot-spot map (Tier 2 local)** reads well in Urban Studies.  
- **Two extras** → risk feeling **busy** unless your advisor wants methods depth.

---

*This file restates `docs/OPTIONAL_GIS_EXTENSIONS.md` and earlier tier lists in non-technical language.*
