"""NYC Open Data provider (Socrata API).

Fetches pedestrian count and crash data from NYC's public Socrata endpoints.
"""

from typing import Any

import httpx

from app.config import settings
from app.providers.base import BaseDataProvider

# Socrata dataset endpoints
_PEDESTRIAN_COUNTS_DATASET = "https://data.cityofnewyork.us/resource/496j-kwkp.json"
_MOTOR_VEHICLE_CRASHES = "https://data.cityofnewyork.us/resource/h9gi-nx95.json"


class NYCOpenDataProvider(BaseDataProvider):
    @property
    def name(self) -> str:
        return "NYC Open Data"

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if settings.NYC_OPENDATA_APP_TOKEN:
            headers["X-App-Token"] = settings.NYC_OPENDATA_APP_TOKEN
        return headers

    async def fetch_stations(self, **params: Any) -> list[dict]:
        """Fetch pedestrian count station locations."""
        query_params = {
            "$limit": params.get("limit", 1000),
            "$offset": params.get("offset", 0),
        }
        if borough := params.get("borough"):
            query_params["$where"] = f"upper(borough) = upper('{borough}')"

        async with httpx.AsyncClient() as client:
            resp = await self.throttled_request(
                client.get(
                    _PEDESTRIAN_COUNTS_DATASET,
                    params=query_params,
                    headers=self._headers(),
                    timeout=30,
                )
            )
            resp.raise_for_status()
            return resp.json()

    async def fetch_counts(self, station_id: str, **params: Any) -> list[dict]:
        """Fetch volume data for a specific station."""
        query_params = {
            "$limit": params.get("limit", 5000),
            "$where": f"station_id = '{station_id}'",
            "$order": "countdate DESC",
        }

        async with httpx.AsyncClient() as client:
            resp = await self.throttled_request(
                client.get(
                    _PEDESTRIAN_COUNTS_DATASET,
                    params=query_params,
                    headers=self._headers(),
                    timeout=30,
                )
            )
            resp.raise_for_status()
            return resp.json()

    async def fetch_incidents(self, **params: Any) -> list[dict]:
        """Fetch pedestrian-involved crash data from Vision Zero."""
        where_clauses = ["number_of_pedestrians_injured > 0 OR number_of_pedestrians_killed > 0"]

        if borough := params.get("borough"):
            where_clauses.append(f"upper(borough) = upper('{borough}')")
        if start_date := params.get("start_date"):
            where_clauses.append(f"crash_date >= '{start_date}'")
        if end_date := params.get("end_date"):
            where_clauses.append(f"crash_date <= '{end_date}'")

        query_params = {
            "$limit": params.get("limit", 5000),
            "$offset": params.get("offset", 0),
            "$where": " AND ".join(where_clauses),
            "$order": "crash_date DESC",
        }

        async with httpx.AsyncClient() as client:
            resp = await self.throttled_request(
                client.get(
                    _MOTOR_VEHICLE_CRASHES,
                    params=query_params,
                    headers=self._headers(),
                    timeout=30,
                )
            )
            resp.raise_for_status()
            return resp.json()
