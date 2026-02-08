"""API routes for pedestrian safety / Vision Zero incident data."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db.core import get_session
from app.models.models import SafetyIncident, SafetyIncidentRead

router = APIRouter(prefix="/api/safety", tags=["safety"])


@router.get("/", response_model=list[SafetyIncidentRead])
def list_incidents(
    borough: str | None = Query(None),
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    limit: int = Query(1000, le=10000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    stmt = select(SafetyIncident)
    if borough:
        stmt = stmt.where(SafetyIncident.borough == borough.upper())
    if start:
        stmt = stmt.where(SafetyIncident.incident_date >= start)
    if end:
        stmt = stmt.where(SafetyIncident.incident_date <= end)
    stmt = stmt.order_by(SafetyIncident.incident_date.desc())
    stmt = stmt.offset(offset).limit(limit)
    return session.exec(stmt).all()


@router.get("/heatmap")
def heatmap_data(
    borough: str | None = Query(None),
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    session: Session = Depends(get_session),
):
    """Return [lat, lng, intensity] triples for heatmap rendering."""
    stmt = select(
        SafetyIncident.latitude,
        SafetyIncident.longitude,
        SafetyIncident.pedestrians_injured + SafetyIncident.pedestrians_killed,
    )
    if borough:
        stmt = stmt.where(SafetyIncident.borough == borough.upper())
    if start:
        stmt = stmt.where(SafetyIncident.incident_date >= start)
    if end:
        stmt = stmt.where(SafetyIncident.incident_date <= end)

    rows = session.exec(stmt).all()
    return [{"lat": r[0], "lng": r[1], "intensity": r[2]} for r in rows]
