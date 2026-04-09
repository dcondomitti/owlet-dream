"""Sensor entities for Owlet Dream devices."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import homeassistant.util.dt as dt_util

from .const import (
    DOMAIN,
    SLEEP_STATE_NAMES,
    VITALS_KEY_BATTERY,
    VITALS_KEY_BATTERY_TIME,
    VITALS_KEY_SOCK_CONNECTION,
    VITALS_KEY_HEART_RATE,
    VITALS_KEY_MOVEMENT,
    VITALS_KEY_MOVEMENT_BUCKET,
    VITALS_KEY_OXYGEN,
    VITALS_KEY_OXYGEN_10MIN_AVG,
    VITALS_KEY_PERFUSION_INDEX,
    VITALS_KEY_RSSI,
    VITALS_KEY_SKIN_TEMP,
    VITALS_KEY_SLEEP_STATE,
)
from .coordinator import OwletDeviceCoordinator


@dataclass(frozen=True, kw_only=True)
class OwletSensorEntityDescription(SensorEntityDescription):
    """Describe an Owlet sensor entity."""

    vitals_key: str
    value_fn: Callable[[Any], Any] = lambda x: x
    requires_sock_on: bool = False


def _zero_as_none(raw: Any) -> int | None:
    """Treat 0 as unavailable (sock not reading)."""
    if raw is None or int(raw) == 0:
        return None
    return int(raw)


def _oxygen_10min(raw: Any) -> int | None:
    """Filter O2 10-min average: 0 and 255 are sentinel values."""
    if raw is None or int(raw) in (0, 255):
        return None
    return int(raw)


def _skin_temp_c(raw: Any) -> float | None:
    """Convert raw skin temperature (tenths of degree C) to degrees C."""
    if raw is None or int(raw) == 0:
        return None
    return round(int(raw) / 10.0, 1)


def _sleep_state_name(raw: Any) -> str | None:
    """Convert numeric sleep state to name."""
    if raw is None:
        return None
    return SLEEP_STATE_NAMES.get(int(raw), f"Unknown ({raw})")


SENSOR_DESCRIPTIONS: tuple[OwletSensorEntityDescription, ...] = (
    OwletSensorEntityDescription(
        key="heart_rate",
        translation_key="heart_rate",
        vitals_key=VITALS_KEY_HEART_RATE,
        native_unit_of_measurement="bpm",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:heart-pulse",
        value_fn=_zero_as_none,
        requires_sock_on=True,
    ),
    OwletSensorEntityDescription(
        key="oxygen_level",
        translation_key="oxygen_level",
        vitals_key=VITALS_KEY_OXYGEN,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:percent-circle",
        value_fn=_zero_as_none,
        requires_sock_on=True,
    ),
    OwletSensorEntityDescription(
        key="oxygen_10min_avg",
        translation_key="oxygen_10min_avg",
        vitals_key=VITALS_KEY_OXYGEN_10MIN_AVG,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:percent-circle-outline",
        value_fn=_oxygen_10min,
        requires_sock_on=True,
    ),
    OwletSensorEntityDescription(
        key="skin_temperature",
        translation_key="skin_temperature",
        vitals_key=VITALS_KEY_SKIN_TEMP,
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=_skin_temp_c,
        requires_sock_on=True,
    ),
    OwletSensorEntityDescription(
        key="movement",
        translation_key="movement",
        vitals_key=VITALS_KEY_MOVEMENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:run",
        requires_sock_on=True,
    ),
    OwletSensorEntityDescription(
        key="movement_bucket",
        translation_key="movement_bucket",
        vitals_key=VITALS_KEY_MOVEMENT_BUCKET,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:run-fast",
        entity_registry_enabled_default=False,
    ),
    OwletSensorEntityDescription(
        key="battery_level",
        translation_key="battery_level",
        vitals_key=VITALS_KEY_BATTERY,
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    OwletSensorEntityDescription(
        key="battery_time_remaining",
        translation_key="battery_time_remaining",
        vitals_key=VITALS_KEY_BATTERY_TIME,
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-clock",
        entity_registry_enabled_default=False,
    ),
    OwletSensorEntityDescription(
        key="sleep_state",
        translation_key="sleep_state",
        vitals_key=VITALS_KEY_SLEEP_STATE,
        icon="mdi:sleep",
        value_fn=_sleep_state_name,
        requires_sock_on=True,
    ),
    OwletSensorEntityDescription(
        key="signal_strength",
        translation_key="signal_strength",
        vitals_key=VITALS_KEY_RSSI,
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    OwletSensorEntityDescription(
        key="perfusion_index",
        translation_key="perfusion_index",
        vitals_key=VITALS_KEY_PERFUSION_INDEX,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-percent",
        entity_registry_enabled_default=False,
        requires_sock_on=True,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Owlet Dream sensor entities."""
    coordinators: list[OwletDeviceCoordinator] = hass.data[DOMAIN][entry.entry_id][
        "coordinators"
    ]

    entities: list[OwletSensorEntity | OwletDerivedSensorEntity] = []
    for coordinator in coordinators:
        for description in SENSOR_DESCRIPTIONS:
            entities.append(OwletSensorEntity(coordinator, description))
        for description in DERIVED_SENSOR_DESCRIPTIONS:
            entities.append(OwletDerivedSensorEntity(coordinator, description))

    async_add_entities(entities)


class OwletSensorEntity(CoordinatorEntity[OwletDeviceCoordinator], SensorEntity):
    """Sensor entity for an Owlet Dream device vital."""

    entity_description: OwletSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OwletDeviceCoordinator,
        description: OwletSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.dsn}_{description.key}"
        self._attr_device_info = _device_info(coordinator)

    @property
    def available(self) -> bool:
        """Return True if the sensor value is present in the latest data."""
        if not super().available:
            return False
        data = self.coordinator.data
        return (
            data is not None
            and self.entity_description.vitals_key in data
        )

    def _sock_is_on(self) -> bool:
        """Return True if sock is connected."""
        data = self.coordinator.data
        if data is None:
            return False
        sc = data.get(VITALS_KEY_SOCK_CONNECTION)
        return sc is not None and int(sc) != 0

    @property
    def native_value(self) -> Any:
        """Return the sensor value, or None if sock is off for vitals sensors."""
        data = self.coordinator.data
        if data is None:
            return None
        if self.entity_description.requires_sock_on and not self._sock_is_on():
            return None
        raw = data.get(self.entity_description.vitals_key)
        if raw is None:
            return None
        return self.entity_description.value_fn(raw)


# ── Derived sensors (computed from coordinator state tracking) ────────


@dataclass(frozen=True, kw_only=True)
class OwletDerivedSensorEntityDescription(SensorEntityDescription):
    """Describe a derived Owlet sensor entity."""

    value_fn: Callable[[OwletDeviceCoordinator], Any]
    available_fn: Callable[[OwletDeviceCoordinator], bool] = lambda c: c.data is not None


def _minutes_since(dt: datetime | None) -> float | None:
    """Return minutes elapsed since a timestamp, or None."""
    if dt is None:
        return None
    delta = dt_util.now() - dt
    return round(delta.total_seconds() / 60.0, 1)


def _td_minutes(td: timedelta | None) -> float | None:
    """Return a timedelta as minutes, or None."""
    if td is None:
        return None
    return round(td.total_seconds() / 60.0, 1)


DERIVED_SENSOR_DESCRIPTIONS: tuple[OwletDerivedSensorEntityDescription, ...] = (
    OwletDerivedSensorEntityDescription(
        key="time_since_last_wiggle",
        translation_key="time_since_last_wiggle",
        icon="mdi:baby-face-outline",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _minutes_since(c.last_movement_time),
        available_fn=lambda c: c.last_movement_time is not None,
    ),
    OwletDerivedSensorEntityDescription(
        key="time_since_last_deep_sleep",
        translation_key="time_since_last_deep_sleep",
        icon="mdi:sleep",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _minutes_since(c.last_deep_sleep_end),
        available_fn=lambda c: c.last_deep_sleep_end is not None,
    ),
    OwletDerivedSensorEntityDescription(
        key="last_deep_sleep_duration",
        translation_key="last_deep_sleep_duration",
        icon="mdi:timer-sand",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        suggested_display_precision=0,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda c: _td_minutes(c.last_deep_sleep_duration),
        available_fn=lambda c: c.last_deep_sleep_duration is not None,
    ),
)


class OwletDerivedSensorEntity(
    CoordinatorEntity[OwletDeviceCoordinator], SensorEntity
):
    """Sensor entity derived from coordinator state tracking."""

    entity_description: OwletDerivedSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OwletDeviceCoordinator,
        description: OwletDerivedSensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.dsn}_{description.key}"
        self._attr_device_info = _device_info(coordinator)

    @property
    def available(self) -> bool:
        if not super().available:
            return False
        return self.entity_description.available_fn(self.coordinator)

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator)


def _device_info(coordinator: OwletDeviceCoordinator) -> dict[str, Any]:
    """Build Home Assistant device info dict."""
    info = coordinator.device_info
    dev: dict[str, Any] = {
        "identifiers": {(DOMAIN, info["dsn"])},
        "name": info.get("display_name", info["dsn"]),
        "manufacturer": "Owlet",
    }
    if info.get("model"):
        dev["model"] = info["model"]
    if info.get("sw_version"):
        dev["sw_version"] = info["sw_version"]
    return dev
