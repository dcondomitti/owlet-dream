"""DataUpdateCoordinator for Owlet Dream devices."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .api import OwletApi, OwletApiError, OwletAuthError
from .const import (
    DOMAIN,
    VITALS_KEY_SOCK_CONNECTION,
)

_LOGGER = logging.getLogger(__name__)

INTERVAL_ACTIVE = timedelta(seconds=20)
INTERVAL_IDLE = timedelta(seconds=60)
# Night hours: 7 PM to 7 AM (sock likely in use)
NIGHT_START = 19
NIGHT_END = 7


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
            update_interval=INTERVAL_ACTIVE,
        )

    def _sock_is_on(self) -> bool:
        """Return True if the sock is connected based on last known data."""
        if not self.data:
            return False
        sc = self.data.get(VITALS_KEY_SOCK_CONNECTION)
        return sc is not None and int(sc) != 0

    def _is_nighttime(self) -> bool:
        """Return True during night hours (7 PM - 7 AM local time)."""
        now = dt_util.now()
        hour = now.hour
        return hour >= NIGHT_START or hour < NIGHT_END

    def _compute_interval(self) -> timedelta:
        """20s if sock is on or it's nighttime, 60s otherwise."""
        if self._sock_is_on() or self._is_nighttime():
            return INTERVAL_ACTIVE
        return INTERVAL_IDLE

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

        # Adjust poll rate based on sock state and time of day
        self.update_interval = self._compute_interval()

        return vitals
