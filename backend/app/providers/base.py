"""Abstract base class for data providers.

Pattern adopted from trip's provider abstraction: each data source implements
a standard interface so new sources can be added without changing consumers.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any

# Throttle concurrent requests to external APIs (from trip)
_semaphore = asyncio.Semaphore(4)


class BaseDataProvider(ABC):
    """Interface that all NYC data providers must implement."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    async def fetch_stations(self, **params: Any) -> list[dict]:
        """Fetch count station metadata."""
        ...

    @abstractmethod
    async def fetch_counts(self, station_id: str, **params: Any) -> list[dict]:
        """Fetch pedestrian volume data for a station."""
        ...

    @abstractmethod
    async def fetch_incidents(self, **params: Any) -> list[dict]:
        """Fetch safety/crash incident data."""
        ...

    async def throttled_request(self, coro):
        """Run a coroutine with concurrency throttling."""
        async with _semaphore:
            return await coro
