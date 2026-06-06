"""Config flow for the SAJ R5 integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    SajR5AuthenticationError,
    SajR5CannotConnectError,
    SajR5Client,
    SajR5InvalidResponseError,
    normalize_host,
)
from .const import (
    CONF_POLLING_TIME,
    DEFAULT_NAME,
    DEFAULT_POLLING_TIME,
    DOMAIN,
    MAX_POLLING_TIME,
    MIN_POLLING_TIME,
)


async def _validate_input(
    hass: HomeAssistant,
    user_input: dict[str, Any],
) -> dict[str, Any]:
    """Validate and normalize user input."""

    data = {
        CONF_HOST: normalize_host(user_input[CONF_HOST]),
        CONF_NAME: user_input[CONF_NAME].strip(),
        CONF_USERNAME: user_input.get(CONF_USERNAME, "").strip(),
        CONF_PASSWORD: user_input.get(CONF_PASSWORD, ""),
        CONF_POLLING_TIME: int(user_input[CONF_POLLING_TIME]),
    }

    client = SajR5Client(
        async_get_clientsession(hass),
        data[CONF_HOST],
        data[CONF_USERNAME],
        data[CONF_PASSWORD],
    )
    await client.async_get_status()
    return data


def _schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Return the config flow data schema."""

    defaults = defaults or {}

    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=defaults.get(CONF_HOST, "")): str,
            vol.Required(CONF_NAME, default=defaults.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Optional(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): str,
            vol.Optional(
                CONF_PASSWORD,
                default=defaults.get(CONF_PASSWORD, ""),
            ): selector.TextSelector(
                selector.TextSelectorConfig(
                    type=selector.TextSelectorType.PASSWORD,
                )
            ),
            vol.Required(
                CONF_POLLING_TIME,
                default=defaults.get(CONF_POLLING_TIME, DEFAULT_POLLING_TIME),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_POLLING_TIME,
                    max=MAX_POLLING_TIME,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="s",
                )
            ),
        }
    )


class SajR5ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SAJ R5."""

    VERSION = 1

    def _host_is_configured(self, host: str, current_entry_id: str | None = None) -> bool:
        """Return true if another entry already uses this host."""

        normalized_host = normalize_host(host)
        return any(
            entry.entry_id != current_entry_id
            and normalize_host(entry.data.get(CONF_HOST, "")) == normalized_host
            for entry in self._async_current_entries()
        )

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Handle the initial config step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                data = await _validate_input(self.hass, user_input)
            except SajR5AuthenticationError:
                errors["base"] = "invalid_auth"
            except SajR5CannotConnectError:
                errors["base"] = "cannot_connect"
            except SajR5InvalidResponseError:
                errors["base"] = "invalid_response"
            else:
                if self._host_is_configured(data[CONF_HOST]):
                    return self.async_abort(reason="already_configured")
                return self.async_create_entry(title=data[CONF_NAME], data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Handle config entry reconfiguration."""

        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                data = await _validate_input(self.hass, user_input)
            except SajR5AuthenticationError:
                errors["base"] = "invalid_auth"
            except SajR5CannotConnectError:
                errors["base"] = "cannot_connect"
            except SajR5InvalidResponseError:
                errors["base"] = "invalid_response"
            else:
                if self._host_is_configured(data[CONF_HOST], entry.entry_id):
                    return self.async_abort(reason="already_configured")
                return self.async_update_reload_and_abort(
                    entry,
                    title=data[CONF_NAME],
                    data_updates=data,
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_schema(entry.data | (user_input or {})),
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ):
        """Handle a reauthentication request."""

        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ):
        """Ask the user for updated credentials."""

        entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            data = entry.data | {
                CONF_USERNAME: user_input.get(CONF_USERNAME, "").strip(),
                CONF_PASSWORD: user_input.get(CONF_PASSWORD, ""),
            }
            try:
                data = await _validate_input(self.hass, data)
            except SajR5AuthenticationError:
                errors["base"] = "invalid_auth"
            except SajR5CannotConnectError:
                errors["base"] = "cannot_connect"
            except SajR5InvalidResponseError:
                errors["base"] = "invalid_response"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=data,
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_USERNAME,
                        default=entry.data.get(CONF_USERNAME, ""),
                    ): str,
                    vol.Optional(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        )
                    ),
                }
            ),
            errors=errors,
        )
