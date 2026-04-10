"""DataUpdateCoordinator for Owlet Dream devices."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .api import OwletApi, OwletApiError, OwletAuthError
from .const import (
    DOMAIN,
    SLEEP_STATE_DEEP,
    VITALS_KEY_MOVEMENT,
    VITALS_KEY_SLEEP_STATE,
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

        # State tracking for derived sensors
        self.last_movement_time: datetime | None = None
        self.last_deep_sleep_end: datetime | None = None
        self.last_deep_sleep_duration: timedelta | None = None
        self._deep_sleep_start: datetime | None = None
        self._prev_sleep_state: int | None = None
        self._prev_movement: int | None = None

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

    def _track_state(self, vitals: dict[str, Any]) -> None:
        """Update derived state from new vitals."""
        now = dt_util.now()

        # Track movement
        mv = vitals.get(VITALS_KEY_MOVEMENT)
        if mv is not None and int(mv) > 0:
            self.last_movement_time = now
        self._prev_movement = mv

        # Track deep sleep transitions
        ss = vitals.get(VITALS_KEY_SLEEP_STATE)
        if ss is not None:
            ss = int(ss)
            prev = self._prev_sleep_state

            if ss == SLEEP_STATE_DEEP and prev != SLEEP_STATE_DEEP:
                # Entered deep sleep
                self._deep_sleep_start = now
            elif ss != SLEEP_STATE_DEEP and prev == SLEEP_STATE_DEEP:
                # Exited deep sleep
                if self._deep_sleep_start is not None:
                    self.last_deep_sleep_duration = now - self._deep_sleep_start
                self.last_deep_sleep_end = now
                self._deep_sleep_start = None

            # If currently in deep sleep, keep updating the running duration
            # so the "last duration" reflects the current ongoing period too
            if ss == SLEEP_STATE_DEEP and self._deep_sleep_start is not None:
                self.last_deep_sleep_duration = now - self._deep_sleep_start
                self.last_deep_sleep_end = now

            self._prev_sleep_state = ss

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch real-time vitals from Ayla."""
        try:
            vitals = await self.api.get_real_time_vitals(self.dsn)
        except OwletAuthError:
            _LOGGER.warning("Auth expired for %s, re-authenticating", self.dsn)
            try:
                await self.api.authenticate()
                vitals = await self.api.get_real_time_vitals(self.dsn)
            except (OwletAuthError, OwletApiError) as inner:
                raise UpdateFailed(f"Auth recovery failed for {self.dsn}") from inner
        except OwletApiError as err:
            raise UpdateFailed(f"Error fetching vitals for {self.dsn}: {err}") from err
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Connection error for {self.dsn}: {err}") from err

        if vitals is None:
            raise UpdateFailed(f"No vitals data available for {self.dsn}")

        _LOGGER.debug(
            "Vitals update for %s: hr=%s ox=%s ss=%s",
            self.dsn,
            vitals.get("hr"),
            vitals.get("ox"),
            vitals.get("ss"),
        )

        # Update derived state tracking
        self._track_state(vitals)

        # Adjust poll rate based on sock state and time of day
        self.update_interval = self._compute_interval()

        return vitals
