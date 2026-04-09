"""Config flow for Owlet Dream integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OwletApi, OwletAuthError, OwletError
from .const import CONF_REGION, DOMAIN, REGION_EU, REGION_US

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_REGION, default=REGION_US): vol.In(
            {REGION_US: "United States", REGION_EU: "Europe"}
        ),
    }
)


class OwletDreamConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Owlet Dream."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step -- email/password login."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]
            region = user_input[CONF_REGION]

            # Prevent duplicate entries for the same email
            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            session = async_get_clientsession(self.hass)
            api = OwletApi(session, email, password, region)

            try:
                await api.authenticate()
            except OwletAuthError:
                errors["base"] = "invalid_auth"
            except (OwletError, aiohttp.ClientError):
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during Owlet auth")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"Owlet ({email})",
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                        CONF_REGION: region,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
