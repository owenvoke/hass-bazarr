"""Tests for Bazarr setup and entities."""

from __future__ import annotations

from http import HTTPStatus

import aiohttp
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.bazarr.const import DOMAIN

from .conftest import URL


async def test_entities(
    hass: HomeAssistant, bazarr: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    movies = hass.states.get("sensor.bazarr_wanted_movies")
    assert movies.state == "3"
    assert movies.attributes["unit_of_measurement"] == "movies"
    assert hass.states.get("sensor.bazarr_wanted_episodes").state == "12"
    assert hass.states.get("binary_sensor.bazarr_health").state == "off"

    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, config_entry.entry_id), config_entry.entry_id
    )
    assert device.sw_version == "1.5.3"


async def test_device_version_follows_bazarr_upgrades(
    hass: HomeAssistant, bazarr: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    bazarr.clear_requests()
    bazarr.get(f"{URL}/api/system/status", json={"data": {"bazarr_version": "1.6.0"}})
    bazarr.get(f"{URL}/api/badges", json={"movies": 3, "episodes": 12})
    bazarr.get(f"{URL}/api/system/health", json={"data": []})
    await config_entry.runtime_data.async_refresh()
    await hass.async_block_till_done()

    device = dr.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, config_entry.entry_id), config_entry.entry_id
    )
    assert device.sw_version == "1.6.0"


async def test_health_issues(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
) -> None:
    aioclient_mock.get(
        f"{URL}/api/system/status", json={"data": {"bazarr_version": "1.5.3"}}
    )
    aioclient_mock.get(f"{URL}/api/badges", json={})
    aioclient_mock.get(
        f"{URL}/api/system/health",
        json={"data": [{"object": "Sonarr", "issue": "Unreachable"}]},
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    health = hass.states.get("binary_sensor.bazarr_health")
    assert health.state == "on"
    assert health.attributes["issues"] == [{"object": "Sonarr", "issue": "Unreachable"}]
    assert hass.states.get("sensor.bazarr_wanted_movies").state == "0"


async def test_setup_retries_on_network_error(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
) -> None:
    aioclient_mock.get(f"{URL}/api/system/status", exc=aiohttp.ClientConnectionError())
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_auth_failure_starts_reauth(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
) -> None:
    aioclient_mock.get(f"{URL}/api/system/status", status=HTTPStatus.UNAUTHORIZED)
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert [f["context"]["source"] for f in flows] == ["reauth"]
