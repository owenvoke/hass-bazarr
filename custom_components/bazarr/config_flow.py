"""Config flow for the Bazarr integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
import yarl
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_API_KEY, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import BazarrAuthError, BazarrClient, BazarrConnectionError, BazarrError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

API_KEY_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))

USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_URL): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)
        ),
        vol.Required(CONF_API_KEY): API_KEY_SELECTOR,
    }
)

REAUTH_SCHEMA = vol.Schema({vol.Required(CONF_API_KEY): API_KEY_SELECTOR})


async def _async_validate(
    hass: HomeAssistant, data: Mapping[str, Any]
) -> dict[str, str]:
    """Check Bazarr can be reached with the given details."""
    client = BazarrClient(
        async_get_clientsession(hass), data[CONF_URL], data[CONF_API_KEY]
    )
    try:
        await client.version()
    except BazarrAuthError:
        return {"base": "invalid_api_key"}
    except BazarrConnectionError:
        return {"base": "cannot_connect"}
    except BazarrError:
        return {"base": "not_bazarr"}
    except Exception:
        _LOGGER.exception("Unexpected error validating Bazarr")
        return {"base": "unknown"}
    return {}


def _normalise(user_input: dict[str, Any]) -> dict[str, Any]:
    return {**user_input, CONF_URL: user_input[CONF_URL].strip().rstrip("/")}


class BazarrConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Bazarr."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the URL and API key."""
        errors: dict[str, str] = {}
        if user_input is not None:
            user_input = _normalise(user_input)
            self._async_abort_entries_match({CONF_URL: user_input[CONF_URL]})

            errors = await _async_validate(self.hass, user_input)
            if not errors:
                host = yarl.URL(user_input[CONF_URL]).host or user_input[CONF_URL]
                return self.async_create_entry(
                    title=f"Bazarr ({host})", data=user_input
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle a rejected API key."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a new API key."""
        errors: dict[str, str] = {}
        entry = self._get_reauth_entry()

        if user_input is not None:
            errors = await _async_validate(self.hass, {**entry.data, **user_input})
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_API_KEY: user_input[CONF_API_KEY]}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=REAUTH_SCHEMA,
            description_placeholders={
                "name": entry.title,
                "api_token_url": f"{entry.data[CONF_URL]}/settings/general",
            },
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the URL or API key."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            user_input = _normalise(user_input)
            if user_input[CONF_URL] != entry.data[CONF_URL]:
                self._async_abort_entries_match({CONF_URL: user_input[CONF_URL]})

            errors = await _async_validate(self.hass, user_input)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data_updates=user_input
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                USER_SCHEMA, user_input or entry.data
            ),
            errors=errors,
        )
