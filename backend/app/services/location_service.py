"""Dynamic Location Service for GLG Assets AI Automation.

Dynamically queries project locations and names from Supabase/PostgreSQL (ProjectRecord),
caches them with a TTL, and performs intelligent entity extraction from user messages.
"""

import logging
import time
from typing import List

from sqlalchemy import select

logger = logging.getLogger(__name__)

# Canonical baseline fallback locations for Dhaka real estate
DEFAULT_LOCATIONS = [
    "Baridhara Diplomatic Zone",
    "Baridhara",
    "Gulshan 2",
    "Gulshan 1",
    "Gulshan",
    "Banani",
    "Dhanmondi",
    "Uttara Sector 3",
    "Uttara",
    "Bashundhara R/A",
    "Bashundhara",
    "Mohakhali DOHS",
    "Mirpur DOHS",
    "Mirpur",
]

class DynamicLocationService:
    def __init__(self, cache_ttl_seconds: int = 120):
        self._cache_ttl = cache_ttl_seconds
        self._last_refresh = 0.0
        self._cached_locations: List[str] = list(DEFAULT_LOCATIONS)
        self._cached_projects: List[str] = []

    async def _refresh_if_needed(self):
        now = time.time()
        if now - self._last_refresh < self._cache_ttl and self._cached_locations:
            return

        try:
            from app.database import async_session_factory, is_db_reachable
            if is_db_reachable():
                from app.models.models import ProjectRecord

                async with async_session_factory() as session:
                    result = await session.execute(select(ProjectRecord.location, ProjectRecord.name))
                    rows = result.all()
                if rows:
                    locations_set = set(DEFAULT_LOCATIONS)
                    projects_set = set()
                    for loc, name in rows:
                        if loc:
                            # Split commas if multiple locations
                            for part in loc.split(","):
                                cleaned = part.strip()
                                if cleaned:
                                    locations_set.add(cleaned)
                                    # Also add base area (e.g., "Gulshan" from "Gulshan-2, Dhaka")
                                    base = cleaned.split("-")[0].strip()
                                    if base:
                                        locations_set.add(base)
                        if name:
                            projects_set.add(name.strip())

                    # Sort by length descending so longer/more specific locations match first
                    self._cached_locations = sorted(list(locations_set), key=len, reverse=True)
                    self._cached_projects = sorted(list(projects_set), key=len, reverse=True)
                    self._last_refresh = now
        except Exception as e:
            logger.debug(f"Dynamic location cache refresh notice: {e}")
            if not self._cached_locations:
                self._cached_locations = list(DEFAULT_LOCATIONS)

    async def get_known_locations(self) -> List[str]:
        await self._refresh_if_needed()
        return self._cached_locations

    async def resolve_location_from_text(self, text: str) -> str:
        """Extracts the best matching known location from a user inquiry or comment."""
        if not text:
            return ""
        await self._refresh_if_needed()
        text_lower = text.lower()
        for loc in self._cached_locations:
            if loc.lower() in text_lower:
                return loc
        return ""

    async def resolve_project_from_text(self, text: str) -> str:
        """Extracts the best matching project name from a user inquiry or comment."""
        if not text:
            return ""
        await self._refresh_if_needed()
        text_lower = text.lower()
        for proj in self._cached_projects:
            if proj.lower() in text_lower:
                return proj
        return ""


location_service = DynamicLocationService()
