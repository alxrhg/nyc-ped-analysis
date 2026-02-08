"""API routes for pedestrian count stations."""

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db.core import get_session
from app.models.models import CountStation, CountStationRead

router = APIRouter(prefix="/api/stations", tags=["stations"])


@router.get("/", response_model=list[CountStationRead])
def list_stations(
    borough: str | None = Query(None),
    source: str | None = Query(None),
    limit: int = Query(100, le=5000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    stmt = select(CountStation)
    if borough:
        stmt = stmt.where(CountStation.borough == borough.upper())
    if source:
        stmt = stmt.where(CountStation.source == source)
    stmt = stmt.offset(offset).limit(limit)
    return session.exec(stmt).all()


@router.get("/{station_id}", response_model=CountStationRead)
def get_station(station_id: int, session: Session = Depends(get_session)):
    station = session.get(CountStation, station_id)
    if not station:
        from fastapi import HTTPException
        raise HTTPException(404, "Station not found")
    return station
