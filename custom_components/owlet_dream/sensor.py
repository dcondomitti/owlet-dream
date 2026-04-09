"""Sensor entities for Owlet Dream devices."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
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

from .const import (
    DOMAIN,
    SLEEP_STATE_NAMES,
    VITALS_KEY_BATTERY,
    VITALS_KEY_BATTERY_TIME,
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
    ),
    OwletSensorEntityDescription(
        key="oxygen_level",
        translation_key="oxygen_level",
        vitals_key=VITALS_KEY_OXYGEN,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:percent-circle",
        value_fn=_zero_as_none,
    ),
    OwletSensorEntityDescription(
        key="oxygen_10min_avg",
        translation_key="oxygen_10min_avg",
        vitals_key=VITALS_KEY_OXYGEN_10MIN_AVG,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:percent-circle-outline",
        value_fn=_oxygen_10min,
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
    ),
    OwletSensorEntityDescription(
        key="movement",
        translation_key="movement",
        vitals_key=VITALS_KEY_MOVEMENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:run",
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

    entities: list[OwletSensorEntity] = []
    for coordinator in coordinators:
        for description in SENSOR_DESCRIPTIONS:
            entities.append(OwletSensorEntity(coordinator, description))

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

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        data = self.coordinator.data
        if data is None:
            return None
        raw = data.get(self.entity_description.vitals_key)
        if raw is None:
            return None
        return self.entity_description.value_fn(raw)


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
