"""Tests for the Bazarr config flow."""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import patch

import aiohttp
import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_URL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
)

from custom_components.bazarr.const import DOMAIN

from .conftest import DATA, URL


async def test_user_flow(hass: HomeAssistant, bazarr: AiohttpClientMocker) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: f" {URL}/ ", CONF_API_KEY: "key"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Bazarr (bazarr.local)"
    assert result["data"] == {**DATA, CONF_VERIFY_SSL: True}


@pytest.mark.parametrize(
    ("mock_kwargs", "error"),
    [
        ({"status": HTTPStatus.UNAUTHORIZED}, "invalid_api_key"),
        ({"exc": aiohttp.ClientConnectionError()}, "cannot_connect"),
        ({"exc": TimeoutError()}, "cannot_connect"),
        ({"json": {"data": {}}}, "not_bazarr"),
        ({"text": "<html>"}, "not_bazarr"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_kwargs: dict,
    error: str,
) -> None:
    aioclient_mock.get(f"{URL}/api/system/status", **mock_kwargs)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], DATA)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}


async def test_user_flow_already_configured(
    hass: HomeAssistant, bazarr: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: f"{URL}/", CONF_API_KEY: "other"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth(
    hass: HomeAssistant, bazarr: AiohttpClientMocker, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    assert result["description_placeholders"]["name"] == config_entry.title
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "new"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[CONF_API_KEY] == "new"
    # Let the reload finish, so its update timer doesn't outlive the test.
    await hass.async_block_till_done()


async def test_reconfigure(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry: MockConfigEntry,
) -> None:
    new_url = "https://subs.example.com"
    aioclient_mock.get(
        f"{new_url}/api/system/status", json={"data": {"bazarr_version": "1.5.3"}}
    )
    aioclient_mock.get(f"{new_url}/api/badges", json={})
    aioclient_mock.get(f"{new_url}/api/system/health", json={"data": []})
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_URL: new_url, CONF_API_KEY: "key2"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    await hass.async_block_till_done()
    assert config_entry.data == {
        CONF_URL: new_url,
        CONF_API_KEY: "key2",
        CONF_VERIFY_SSL: True,
    }


async def test_user_flow_without_ssl_verification(
    hass: HomeAssistant, bazarr: AiohttpClientMocker
) -> None:
    with patch(
        "custom_components.bazarr.config_flow.async_get_clientsession",
        wraps=async_get_clientsession,
    ) as get_session:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**DATA, CONF_VERIFY_SSL: False}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_VERIFY_SSL] is False
    get_session.assert_called_with(hass, verify_ssl=False)
