# NYC Open Data — ideas to enrich the thesis analysis

**Goal:** Add **layers** that strengthen **description**, **equity**, **freight / through-traffic context**, or **institutional** storytelling—not to magically “prove” LTN outcomes without traffic modeling.

**Rule:** Each new layer needs a **sentence in Methods** (source ID, date, join logic) and a **sentence in Discussion** on **what it does not** imply (causality, completeness).

---

## Tier A — High value, usually tract-joinable, moderate effort

| Theme | Dataset / search terms | Why it might help |
|-------|-------------------------|-------------------|
| **Demographics / equity** | U.S. Census ACS (you already pull some); add tract **median income**, **race/ethnicity**, **car availability** (B25044, B19013, B03002) | Lets you discuss **distribution** of pedestrian/crash context alongside **social vulnerability**—parallel to Aldred-style *siting* discourse, not replication. |
| **DOT traffic volumes** | [Automated Traffic Volume Counts](https://data.cityofnewyork.us/d/7ym2-wayt) (and related DOT count products) | **Motor vehicle exposure** proxy where counts exist—sparse spatially, but useful **where points fall in/near the corridor** as **qualifying context** for “motor load.” |
| **Bus stops / SBS** | MTA / NYC DOT GTFS or published stop layers | **Transit dependency** complement to subway; supports narrative on **who relies on surface access**. |
| **Bike infrastructure** | NYC DOT bike routes / lanes (Open Data) | **Mode competition** and street-space politics; optional **buffer** or **length in tract** summary. |
| **Schools / day-care** | DOE school locations, etc. | **Child pedestrian** exposure narrative; join as **density in tract** or distance to corridor. |
| **Hospitals / FDNY** | Hospital points, fire house locations | **Emergency access** paragraph in Discussion—qualitative + **distance** stats, not a full ops model. |

---

## Tier B — Strong for “NYC grid / freight / through-traffic” story, messier joins

| Theme | Dataset / search terms | Notes |
|-------|-------------------------|--------|
| **Truck routes / commercial vehicle context** | NYC DOT truck routes, weight restrictions, loading zone data (where available) | Often **line or rule-based**; summarize **overlap with study polygon** or **presence in tract**. Good for **LTN boundary-road / freight** criticism. |
| **311 street / traffic complaints** | 311 Service Requests (filtered types: street condition, blocked bike lane, noise, etc.) | **Voluntary** reporting bias; still useful as **sentiment / conflict** proxy **in time window** aligned with crash pull. |
| **Curbside / parking** | If you find maintained layers (varies) | Supports **allocation** arguments; check **vintage** and completeness. |
| **Air quality / heat** | DEC or city air sensors, UHF/tract overlays where available | **Environmental justice** angle; join cautiously (scale mismatch). |

---

## Tier C — “More data” that rarely improves *your* core claim

| Approach | Caveat |
|----------|--------|
| **Throwing in dozens of layers** | Multicollinearity, **p-hacking** feel, harder to **explain** in Urban Studies prose. |
| **Fine-grained ML on everything** | **Black box** unless you invest in interpretability; **H100** does not fix **small-n / spatial autocorrelation** issues at tract scale. |
| **Using Open Data as substitute for through-traffic %** | City rarely publishes **continuous through-share** per block; advocacy estimates stay **external** unless you build a **network model**. |

---

## What “better result” can mean (pick one)

1. **Richer Results chapter** — more maps/tables, same **honest limits**.  
2. **Stronger equity section** — ACS + your existing metrics.  
3. **Stronger freight / boundary-road Discussion** — truck routes + crash types (if you add **vehicle type** fields from crashes).  
4. **Stronger “measurement gap” argument** — DOT counts vs NYCWalks vs sparse sensors.

---

## Suggested order if time is limited

1. **ACS tract enrichment** (equity sidebar).  
2. **DOT count points** in/near Houston–Canal (motor exposure where observed).  
3. **Crash field expansion** (e.g. vehicle type, contributing factors) from **same** `h9gi-nx95` pull—often **low marginal cost** if you already fetch full rows.  
4. **Truck route overlay** for one **Discussion** figure.

---

## Hardware note

None of the above **requires** an **H100**. Tabular joins and choropleths are **CPU / laptop** work. GPUs matter only if you later choose a **large** deep learning or graph experiment—and that should be **advisor-scoped**, not “more data = need H100.”

---

*Align additions with `docs/DATA_LOCK.md` when you freeze the thesis run.*
