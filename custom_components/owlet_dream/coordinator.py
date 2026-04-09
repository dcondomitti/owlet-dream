"""DataUpdateCoordinator for Owlet Dream devices."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import OwletApi, OwletApiError, OwletAuthError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class OwletDeviceCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls vitals for a single Owlet device (by DSN)."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: OwletApi,
        device_info: dict[str, Any],
    ) -> None:
        self.api = api
        self.dsn: str = device_info["dsn"]
        self.device_info = device_info

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.dsn}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch real-time vitals from Ayla."""
        try:
            vitals = await self.api.get_real_time_vitals(self.dsn)
        except OwletAuthError as err:
            _LOGGER.warning("Auth expired for %s, re-authenticating", self.dsn)
            try:
                await self.api.authenticate()
                vitals = await self.api.get_real_time_vitals(self.dsn)
            except (OwletAuthError, OwletApiError) as inner:
                raise UpdateFailed(f"Auth recovery failed for {self.dsn}") from inner
        except OwletApiError as err:
            raise UpdateFailed(f"Error fetching vitals for {self.dsn}: {err}") from err

        if vitals is None:
            raise UpdateFailed(f"No vitals data available for {self.dsn}")

        return vitals
