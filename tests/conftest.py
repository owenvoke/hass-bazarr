"""Fixtures for Bazarr tests."""

from __future__ import annotations

import pytest
from homeassistant.const import CONF_API_KEY, CONF_URL
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.bazarr.const import DOMAIN

URL = "http://bazarr.local:6767"
DATA = {CONF_URL: URL, CONF_API_KEY: "key"}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations in every test."""
    yield


@pytest.fixture
def bazarr(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """Mock a healthy Bazarr instance."""
    aioclient_mock.get(
        f"{URL}/api/system/status", json={"data": {"bazarr_version": "1.5.3"}}
    )
    aioclient_mock.get(f"{URL}/api/badges", json={"movies": 3, "episodes": 12})
    aioclient_mock.get(f"{URL}/api/system/health", json={"data": []})
    return aioclient_mock


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """A configured Bazarr entry."""
    return MockConfigEntry(domain=DOMAIN, title="Bazarr (bazarr.local)", data=DATA)
