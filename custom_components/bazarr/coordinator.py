"""Data update coordinator for Bazarr."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BazarrAuthError, BazarrClient, BazarrError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

type BazarrConfigEntry = ConfigEntry[BazarrDataUpdateCoordinator]


@dataclass(frozen=True)
class BazarrData:
    """The latest data from Bazarr."""

    wanted_movies: int
    wanted_episodes: int
    health_issues: list[Any]
    version: str


class BazarrDataUpdateCoordinator(DataUpdateCoordinator[BazarrData]):
    """Fetch data from a Bazarr instance."""

    config_entry: BazarrConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: BazarrConfigEntry) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL),
        )
        self.url: str = config_entry.data[CONF_URL].rstrip("/")
        self.client = BazarrClient(
            async_get_clientsession(hass), self.url, config_entry.data[CONF_API_KEY]
        )

    async def _async_update_data(self) -> BazarrData:
        """Fetch the latest data."""
        try:
            version = await self.client.version()
            badges = await self.client.badges()
            health = await self.client.health()
        except BazarrAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from err
        except BazarrError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err

        return BazarrData(
            wanted_movies=badges.get("movies", 0),
            wanted_episodes=badges.get("episodes", 0),
            health_issues=health,
            version=version,
        )
