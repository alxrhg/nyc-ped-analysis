"""API routes for pedestrian volume data."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db.core import get_session
from app.models.models import PedestrianCount, PedestrianCountRead

router = APIRouter(prefix="/api/counts", tags=["counts"])


@router.get("/", response_model=list[PedestrianCountRead])
def list_counts(
    station_id: int | None = Query(None),
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    limit: int = Query(1000, le=10000),
    offset: int = Query(0, ge=0),
    session: Session = Depends(get_session),
):
    stmt = select(PedestrianCount)
    if station_id is not None:
        stmt = stmt.where(PedestrianCount.station_id == station_id)
    if start:
        stmt = stmt.where(PedestrianCount.timestamp >= start)
    if end:
        stmt = stmt.where(PedestrianCount.timestamp <= end)
    stmt = stmt.order_by(PedestrianCount.timestamp.desc())
    stmt = stmt.offset(offset).limit(limit)
    return session.exec(stmt).all()


@router.get("/summary")
def count_summary(
    station_id: int | None = Query(None),
    session: Session = Depends(get_session),
):
    """Return aggregate stats for pedestrian counts."""
    from sqlalchemy import func

    stmt = select(
        func.count(PedestrianCount.id).label("total_readings"),
        func.sum(PedestrianCount.volume).label("total_volume"),
        func.avg(PedestrianCount.volume).label("avg_volume"),
        func.max(PedestrianCount.volume).label("max_volume"),
        func.min(PedestrianCount.timestamp).label("earliest"),
        func.max(PedestrianCount.timestamp).label("latest"),
    )
    if station_id is not None:
        stmt = stmt.where(PedestrianCount.station_id == station_id)

    row = session.exec(stmt).one()
    return {
        "total_readings": row[0],
        "total_volume": row[1],
        "avg_volume": round(row[2], 1) if row[2] else None,
        "max_volume": row[3],
        "earliest": row[4],
        "latest": row[5],
    }
