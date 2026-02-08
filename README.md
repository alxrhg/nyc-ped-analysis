# nyc-ped-analysis

Map-centric pedestrian data analysis tool for New York City. Visualizes pedestrian count stations, volume data, and safety incidents on an interactive Leaflet map.

Architecture inspired by [itskovacs/trip](https://github.com/itskovacs/trip) -- a single-container FastAPI + Leaflet + SQLite stack with zero external dependencies.

## Architecture

```
backend/           FastAPI + SQLModel + SQLite
  app/
    main.py        App entry, serves API + static frontend
    config.py      Pydantic Settings (env-driven)
    db/            SQLite engine, session management
    models/        Count stations, volumes, safety incidents
    routers/       REST endpoints for each data domain
    providers/     Abstract data source interface (NYC Open Data, etc.)
frontend/          Vanilla JS + Leaflet
  js/
    map.js         Leaflet map with marker clustering + heatmaps
    api.js         Centralized API client
    filters.js     Borough / date range filtering
    app.js         Main controller
```

## Key patterns from trip

- **Full-screen Leaflet map** as the base layer with floating UI panels
- **Marker clustering** via `leaflet.markercluster` for dense data points
- **Provider abstraction** -- pluggable data sources behind a base class interface
- **FastAPI serves everything** -- API routes + static frontend, no nginx needed
- **SQLite only** -- zero-config database, perfect for read-heavy analysis
- **Single Docker container** -- multi-stage build, one-command deployment
- **Event-driven updates** -- filter changes trigger data reload across layers

## Quick start

```bash
docker compose up -d
# App runs at http://localhost:8000
```

### Local development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend is served from the static directory automatically
```

## Data sources

| Source | Endpoint | Data |
|--------|----------|------|
| NYC Open Data (Socrata) | Pedestrian counts | Station locations + volume readings |
| NYC Open Data (Socrata) | Motor vehicle crashes | Vision Zero pedestrian incidents |

## API

- `GET /api/stations/` -- List count stations (filter by borough, source)
- `GET /api/counts/` -- List volume readings (filter by station, date range)
- `GET /api/counts/summary` -- Aggregate stats
- `GET /api/safety/` -- List safety incidents (filter by borough, date range)
- `GET /api/safety/heatmap` -- Lat/lng/intensity data for heatmap rendering
- `GET /api/health` -- Health check
