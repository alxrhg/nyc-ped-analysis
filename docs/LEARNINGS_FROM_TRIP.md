# Learnings from itskovacs/trip

Source: https://github.com/itskovacs/trip

## Project Overview

**trip** is a self-hosted, privacy-focused travel planning app built with Angular + FastAPI + Leaflet + SQLite, deployed as a single Docker container. It has ~1.1k GitHub stars, 518 commits, and 63 releases. The architectural decisions are directly applicable to our NYC pedestrian analysis project.

---

## Key Architectural Patterns to Adopt

### 1. Map-Centric Interface (Leaflet)

Trip uses a **full-screen Leaflet map** as the primary interface with all UI elements floating above it. This is the right model for pedestrian data visualization.

**What to adopt:**
- Full-screen Leaflet map as the base layer
- `leaflet.markercluster` for dense data points (essential for NYC pedestrian volumes)
- Category-colored markers with embedded icons
- GPX polyline rendering for route/corridor visualization
- Right-click context menus via `leaflet-contextmenu`
- Marker clustering that disables at high zoom levels to show individual points

**Applied to our project:** Pedestrian count stations, crosswalk locations, and safety incidents can all be visualized as clustered markers on the NYC map, with color coding by data type or severity.

### 2. FastAPI + SQLite Backend

Trip runs a lean **FastAPI** backend with **SQLite** as the sole database, using **SQLModel** (SQLAlchemy + Pydantic) for ORM.

**What to adopt:**
- FastAPI for async API endpoints serving pedestrian data
- SQLite for zero-config local storage of processed datasets
- SQLModel for type-safe models combining validation and ORM
- Alembic for database migrations
- Pydantic Settings for environment-driven configuration with sensible defaults

**Applied to our project:** Store processed NYC pedestrian counts, geographic data, and computed metrics in SQLite. Serve them via FastAPI endpoints that the Leaflet frontend consumes.

### 3. Single-Container Docker Deployment

Trip packages everything (frontend build + Python backend + SQLite) into **one Docker container** using a multi-stage build.

**What to adopt:**
- Multi-stage Dockerfile: Node for frontend build, Python slim for runtime
- FastAPI serves both the API and the static frontend files
- Custom 404 handler for SPA client-side routing fallback
- `docker-compose.yml` for one-command deployment
- Volume mount for persistent SQLite data

### 4. Provider Abstraction Pattern

Trip abstracts map data providers (OSM, Google Maps) behind a **base class interface** with `text_search()`, `get_place_details()`, etc.

**What to adopt:**
- Abstract base class for data sources (NYC Open Data, DOT counts, Vision Zero)
- Each provider implements standardized fetch/parse/transform methods
- `asyncio.Semaphore` to throttle concurrent requests to external APIs
- Consistent data model output regardless of source

### 5. Frontend Component Architecture

Trip uses Angular standalone components with OnPush change detection and Signals for state management.

**What to adopt for our simpler frontend:**
- Modular component structure even if using vanilla JS or a lighter framework
- Separation of API service, map service, and UI components
- Loading/skeleton states for data-heavy views
- Centralized error handling with user-friendly notifications

---

## Visualization Techniques to Adopt

### Route/Corridor Visualization
- **Color-coded polylines** with 13 distinct colors and automatic allocation
- **Animated paths** connecting sequential points
- **Midpoint badges** showing distance/duration between nodes
- **Hover effects** with increased weight and opacity

**Applied to our project:** Visualize pedestrian corridors, high-traffic routes, and safety hotspot connections.

### Filtering and Search
- Quick filter buttons for common categories
- Multi-select category grid with select/deselect all
- Text search across entities
- Geographic boundary filtering via geocoding

**Applied to our project:** Filter by borough, time period, pedestrian volume thresholds, incident type, etc.

### Data Layer Management
- Toggle-able data layers (markers, routes, heatmaps)
- Per-category visibility controls
- Cluster/uncluster based on zoom level

---

## Technical Decisions Worth Noting

| Decision | Rationale | Our Adaptation |
|----------|-----------|----------------|
| SQLite only | Zero external deps, simple self-hosting | Same -- our datasets are read-heavy, SQLite is perfect |
| SPA served by FastAPI | No nginx needed, simpler container | Same approach |
| Argon2 for passwords | Strongest modern hashing | Adopt if we add auth |
| JWT with refresh tokens | Stateless auth with rotation | Adopt if we add auth |
| Levenshtein for dedup | Catch near-duplicate entries | Useful for matching location names across datasets |
| Haversine for distance | Automatic transport mode selection | Use for pedestrian catchment area analysis |
| Pydantic Settings | Config with env vars + sensible defaults | Same pattern for API keys, data paths, etc. |
| Event listener cleanup | Delete files when DB records removed | Use for cached/processed data files |

---

## Project Structure Inspiration

```
nyc-ped-analysis/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, middleware, static serving
│   │   ├── config.py            # Pydantic Settings
│   │   ├── db/
│   │   │   └── core.py          # SQLite engine, migrations
│   │   ├── models/
│   │   │   └── models.py        # SQLModel entities
│   │   ├── routers/
│   │   │   ├── stations.py      # Pedestrian count stations
│   │   │   ├── counts.py        # Volume data endpoints
│   │   │   ├── safety.py        # Vision Zero / crash data
│   │   │   └── analytics.py     # Computed metrics
│   │   └── providers/
│   │       ├── base.py          # Abstract data provider
│   │       ├── nyc_opendata.py  # NYC Open Data (Socrata API)
│   │       ├── dot_counts.py    # DOT pedestrian counts
│   │       └── vision_zero.py   # Vision Zero crash data
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── css/
│   ├── js/
│   │   ├── app.js               # Main application
│   │   ├── map.js               # Leaflet map management
│   │   ├── api.js               # Backend API client
│   │   ├── filters.js           # Data filtering logic
│   │   └── charts.js            # Chart visualizations
│   └── assets/
├── data/                         # Sample/seed data
├── docs/
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Summary

The trip project demonstrates that a **map-first, single-container, SQLite-backed** architecture works well for geographic data applications. For nyc-ped-analysis, we adopt:

1. **Leaflet + marker clustering** for dense pedestrian data points
2. **FastAPI + SQLite** for a lean, zero-dependency backend
3. **Provider abstraction** for multiple NYC data sources
4. **Single Docker container** for simple deployment
5. **Color-coded layers** for multi-dimensional pedestrian data visualization
