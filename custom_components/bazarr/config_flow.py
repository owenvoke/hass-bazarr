"""Config flow for Bazarr integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Mapping

import aiohttp
import voluptuous as vol
import yarl

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult, SOURCE_REAUTH
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    host = data[CONF_URL]
    api_token = data[CONF_API_KEY]

    session = async_get_clientsession(hass)
    try:
        url = f"{host}/api/system/status"
        headers = {"X-API-KEY": api_token}
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)
        ) as response:
            response.raise_for_status()
            result = await response.json()
            if "data" not in result or "bazarr_version" not in result.get("data", {}):
                raise CannotConnect
    except (aiohttp.ClientError, asyncio.TimeoutError) as err:
        if isinstance(err, aiohttp.ClientResponseError and err.status == 401):
            return {"base": "invalid_api_key"}
        return {"base": "cannot_connect"}

    return {}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bazarr."""

    url: str

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle configuration by re-auth."""
        self.url = entry_data[CONF_URL]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth dialog."""
        errors: dict[str, str] = {}
        if user_input:
            user_input = {**user_input, CONF_URL: self.url}

            errors = await validate_input(self.hass, user_input)

            if not errors:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={CONF_API_KEY: user_input[CONF_API_KEY]},
                    reason="reauth_successful",
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_API_KEY): str}),
            description_placeholders={"api_token_url": f"{self.url}/settings/general"},
            errors=errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._async_abort_entries_match([{CONF_URL: user_input[CONF_URL]}])

            errors = await validate_input(self.hass, user_input)

            if not errors:
                parsed = yarl.URL(user_input[CONF_URL])

                return self.async_create_entry(
                    title=f"Bazarr ({parsed.host})", data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL): str,
                    vol.Required(CONF_API_KEY): str,
                }
            ),
            errors=errors,
        )


class Unauthenticated(HomeAssistantError):
    """Error to indicate invalid auth."""


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""
