"""SQLModel entities for NYC pedestrian analysis data.

Models cover the three primary data domains:
- Count stations and their volume readings
- Safety/crash incidents from Vision Zero
- Geographic boundaries for filtering
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class CountStation(SQLModel, table=True):
    """A pedestrian counting station (e.g., DOT automated counter)."""

    __tablename__ = "count_stations"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    borough: str = Field(index=True)
    latitude: float
    longitude: float
    street_name: Optional[str] = None
    cross_street: Optional[str] = None
    source: str = Field(default="dot", index=True)  # dot, nyc_opendata, etc.
    external_id: Optional[str] = Field(default=None, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PedestrianCount(SQLModel, table=True):
    """A volume reading from a count station."""

    __tablename__ = "pedestrian_counts"

    id: Optional[int] = Field(default=None, primary_key=True)
    station_id: int = Field(foreign_key="count_stations.id", index=True)
    timestamp: datetime = Field(index=True)
    volume: int
    direction: Optional[str] = None  # e.g., NB, SB, EB, WB
    weather: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SafetyIncident(SQLModel, table=True):
    """A pedestrian-involved crash or safety incident (Vision Zero data)."""

    __tablename__ = "safety_incidents"

    id: Optional[int] = Field(default=None, primary_key=True)
    incident_date: datetime = Field(index=True)
    borough: str = Field(index=True)
    latitude: float
    longitude: float
    zip_code: Optional[str] = None
    street_name: Optional[str] = None
    cross_street: Optional[str] = None
    pedestrians_injured: int = Field(default=0)
    pedestrians_killed: int = Field(default=0)
    contributing_factor: Optional[str] = None
    vehicle_type: Optional[str] = None
    external_id: Optional[str] = Field(default=None, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# --- Pydantic read schemas (non-table models for API responses) ---


class CountStationRead(SQLModel):
    id: int
    name: str
    borough: str
    latitude: float
    longitude: float
    street_name: Optional[str]
    cross_street: Optional[str]
    source: str


class PedestrianCountRead(SQLModel):
    id: int
    station_id: int
    timestamp: datetime
    volume: int
    direction: Optional[str]


class SafetyIncidentRead(SQLModel):
    id: int
    incident_date: datetime
    borough: str
    latitude: float
    longitude: float
    pedestrians_injured: int
    pedestrians_killed: int
    contributing_factor: Optional[str]
    vehicle_type: Optional[str]
