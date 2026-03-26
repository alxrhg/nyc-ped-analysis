# Can you build a network model for the thesis? (scope and honesty)

**Direct answer:** **Yes**, you can build **something** on a street graph. A **policy-credible** “how traffic would redistribute under an LTN” model for Lower Manhattan is **much harder**—it needs **demand** (who drives where) and **calibration**, not only lines on a map.

---

## What “network model” can mean (pick one level)

| Level | What you build | Data you need | Credible for thesis if… |
|-------|------------------|---------------|-------------------------|
| **A. Topology only** | Graph from OSM (or CSCL); mark candidate filter locations as **removed / reduced-capacity** edges. | OSM extract for study bbox; your judgment on **which** links are “interior” vs arterial. | You show **which streets are structurally alternate routes**—**illustrative**, not volumes. |
| **B. Path / load sketch** | All-or-nothing or incremental **shortest-path** (or few routes) reassignment: trips **shift** to remaining links when edges close. | Same graph + a **synthetic OD** (e.g. centroid-to-centroid, uniform, or gravity from tract populations) **or** a **single** OD pair story (e.g. Holland-bound flow). | You label outputs **“illustrative sensitivity”**; you **do not** claim match to observed counts. |
| **C. Traffic assignment (equilibrium)** | User equilibrium / incremental assignment on a directed graph with **link cost** functions (BPR-style). | **Network** + **OD matrix** (often the killer—NYC does not hand you a free micro-OD for private cars for your polygon) + **calibration** to something (link counts). | Rare for BA without engineering advisor + time; risk of **garbage numbers** if OD is made up. |
| **D. Full microsim** (SUMO, etc.) | Vehicles, signals, queues. | Network, OD, signal timing, often **months** of setup. | **Thesis-scale** only with **narrow** scenario and **qualitative** use of outputs. |

For **Urban Studies**, **A** or a **very small B** is often enough to say: “**structurally**, cutting these links **forces** use of these corridors; **magnitude** requires data we do not have.”

---

## Why it’s hard without “enough data”

- **Network geometry** is the **easy** part (OSM, DCP linework).  
- **Believable volumes** need **observed or estimated demand** on origin–destination pairs (or link flows you **calibrate** to). Sparse DOT counts **help a bit** but don’t replace an OD matrix.  
- **LTN effect** is **not** only “shortest path”—drivers adapt, times of day differ, trucks differ from cars, **boundary** streets absorb spillover. Simple models **often overstate** diversion on one parallel street unless tuned.

So: **you can build the graph and a toy assignment**; **proving** “traffic would change by X%” needs **Level C/D + calibration**, which is a **different thesis** unless scoped as **exploratory**.

---

## A defensible BA-thesis path (if you want *some* network content)

1. **Extract** OSM (or CSCL) **driving** subgraph for Houston–Canal + buffer (e.g. 500 m–1 km).  
2. **Tag** candidate “filter” edges (hypothetical—clearly labeled **not implemented**).  
3. **Run** one transparent algorithm: e.g. remove edges → recompute **shortest paths** for a **stated** set of OD pairs or tract centroids → report **relative** change in **path length** or **which links gain path count** (link loading as **count of routes**, not vehicles).  
4. **Write** in Methods/Results: **no calibration to observed volumes**; **illustrative** of **network sensitivity** only; **London** or literature for **order-of-magnitude** outcome **ranges** stays separate (`LONDON_TO_NYC_TRAFFIC_OPPORTUNITIES_ILLUSTRATION.md`).

**Deliverable:** 1–2 figures + half a page—not a Chapter replacing your GIS centerpiece unless your advisor wants that pivot.

---

## When *not* to build it

- If it **eats** time from **locking GIS**, **qual**, and **writing**.  
- If the committee expects **engineering-grade** validation and you **cannot** calibrate.

---

## One-sentence for the thesis

> This thesis does **not** include a **calibrated** traffic assignment model; **[optional:] a small OSM-based graph exercise illustrates how **hypothetical** modal filters **alter** shortest-path structure **without** quantifying equilibrium volumes.**

---

*Software pointers (you choose one stack): OSMnx / NetworkX / igraph in Python; QGIS; SUMO if you go micro (heavy). Not prescriptive—match your skills and advisor.*
