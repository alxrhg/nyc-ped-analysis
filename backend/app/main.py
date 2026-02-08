"""FastAPI application entry point.

Pattern from trip: FastAPI serves both the API and static frontend files,
with a custom 404 handler for SPA client-side routing fallback.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db.core import init_db
from app.routers import counts, safety, stations


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API routers ---
app.include_router(stations.router)
app.include_router(counts.router)
app.include_router(safety.router)


# --- Static file serving & SPA fallback (pattern from trip) ---
_static_dir = Path(__file__).resolve().parent.parent / settings.STATIC_DIR

if _static_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=_static_dir / "assets"), name="assets")

    @app.get("/{path:path}")
    async def _spa_fallback(request: Request, path: str):
        file = _static_dir / path
        if file.is_file():
            return FileResponse(file)
        index = _static_dir / "index.html"
        if index.is_file():
            return FileResponse(index)
        return JSONResponse({"detail": "Not found"}, status_code=404)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}
