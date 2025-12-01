"""DataUpdateCoordinator for Bazarr."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

import aiohttp
from aiohttp import ClientResponseError

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL, CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from httpcore import TimeoutException

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class BazarrDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching Bazarr data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=5),
        )
        self.url = entry.data[CONF_URL]
        self.api_token = entry.data[CONF_API_KEY]

    async def ensure_tokens(self):
        """Ensure that the API tokens are valid."""
        session = async_get_clientsession(self.hass)
        headers = {"X-API-KEY": self.api_token}
        status_url = f"{self.url}/api/system/status"

        try:
            async with session.get(
                status_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
        except ClientResponseError as err:
            if err.status == 401:
                raise ConfigEntryAuthFailed(err) from err

        except (asyncio.TimeoutError, TimeoutException) as ex:
            raise ConfigEntryNotReady(
                f"Timed out while connecting to {self.url}"
            ) from ex

    async def _async_update_data(self) -> dict:
        """Fetch data from Bazarr API."""
        session = async_get_clientsession(self.hass)
        headers = {"X-API-KEY": self.api_token}

        try:
            # Fetch badges data
            badges_url = f"{self.url}/api/badges"
            async with session.get(
                badges_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                badges_data = await response.json()

            # Fetch health data
            health_url = f"{self.url}/api/system/health"
            async with session.get(
                health_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                health_data = await response.json()

            # Fetch status data
            status_url = f"{self.url}/api/system/status"
            async with session.get(
                status_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                response.raise_for_status()
                status_data = await response.json()

            return {
                "wanted_movies": badges_data.get("movies", 0),
                "wanted_episodes": badges_data.get("episodes", 0),
                "health_issues": health_data.get("data", []),
                "version": status_data.get("bazarr_version", "Unknown"),
            }
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with Bazarr API: {err}") from err
