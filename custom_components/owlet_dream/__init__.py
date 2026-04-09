"""Owlet Dream integration for Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import OwletApi, OwletApiError, OwletAuthError
from .const import CONF_REGION, DOMAIN, REGION_US
from .coordinator import OwletDeviceCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Owlet Dream from a config entry."""
    session = async_get_clientsession(hass)
    api = OwletApi(
        session,
        entry.data[CONF_EMAIL],
        entry.data[CONF_PASSWORD],
        entry.data.get(CONF_REGION, REGION_US),
    )

    try:
        await api.authenticate()
    except OwletAuthError as err:
        raise ConfigEntryAuthFailed("Invalid Owlet credentials") from err
    except OwletApiError as err:
        raise ConfigEntryNotReady(f"Cannot connect to Owlet: {err}") from err

    try:
        devices = await api.discover_devices()
    except OwletApiError as err:
        raise ConfigEntryNotReady(f"Failed to discover devices: {err}") from err

    if not devices:
        _LOGGER.warning("No Owlet devices found on account %s", entry.data[CONF_EMAIL])

    # Create a coordinator per device
    coordinators: list[OwletDeviceCoordinator] = []
    for device_info in devices:
        coordinator = OwletDeviceCoordinator(hass, api, device_info)
        await coordinator.async_config_entry_first_refresh()
        coordinators.append(coordinator)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinators": coordinators,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Owlet Dream config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
