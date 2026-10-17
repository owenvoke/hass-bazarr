"""A minimal client for the Bazarr API."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

REQUEST_TIMEOUT = 10


class BazarrError(Exception):
    """Base exception for Bazarr API errors."""


class BazarrConnectionError(BazarrError):
    """Raised when the Bazarr instance cannot be reached."""


class BazarrAuthError(BazarrError):
    """Raised when the API key is invalid."""


class BazarrClient:
    """Client for a Bazarr instance's API."""

    def __init__(self, session: aiohttp.ClientSession, url: str, api_key: str) -> None:
        """Initialise the client."""
        self._session = session
        self._base_url = url.rstrip("/")
        self._api_key = api_key

    async def _get(self, path: str) -> dict[str, Any]:
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.get(
                    f"{self._base_url}/api{path}",
                    headers={"X-API-KEY": self._api_key},
                )
        except (aiohttp.ClientError, TimeoutError) as err:
            raise BazarrConnectionError(str(err) or type(err).__name__) from err

        async with response:
            if response.status in (401, 403):
                raise BazarrAuthError(f"Unauthorized ({response.status})")
            if response.status >= 400:
                raise BazarrError(f"Unexpected response ({response.status})")
            try:
                data = await response.json()
            except (aiohttp.ContentTypeError, ValueError) as err:
                raise BazarrError("Invalid response from Bazarr") from err

        if not isinstance(data, dict):
            raise BazarrError("Invalid response from Bazarr")
        return data

    async def version(self) -> str:
        """Return the Bazarr version, checking this is a Bazarr instance."""
        status = (await self._get("/system/status")).get("data") or {}
        if "bazarr_version" not in status:
            raise BazarrError("Not a Bazarr instance")
        return status["bazarr_version"]

    async def badges(self) -> dict[str, Any]:
        """Return the counts shown in Bazarr's navigation badges."""
        return await self._get("/badges")

    async def health(self) -> list[Any]:
        """Return the current health issues."""
        return (await self._get("/system/health")).get("data") or []
