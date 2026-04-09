"""Binary sensor entities for Owlet Dream devices."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    VITALS_KEY_ALERTS_MASK,
    VITALS_KEY_ALERT_PAUSED,
    VITALS_KEY_BASE_STATION_ON,
    VITALS_KEY_CHARGING,
    VITALS_KEY_SOCK_CONNECTION,
    VITALS_KEY_SOCK_READINGS,
    VITALS_KEY_WELLNESS_ALERT,
)
from .coordinator import OwletDeviceCoordinator


@dataclass(frozen=True, kw_only=True)
class OwletBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describe an Owlet binary sensor entity."""

    vitals_key: str
    is_on_fn: Callable[[Any], bool | None] = lambda x: bool(x)


def _nonzero(val: Any) -> bool | None:
    if val is None:
        return None
    return int(val) != 0


def _sock_connected(val: Any) -> bool | None:
    """Sock connection: 0 = disconnected, nonzero = connected."""
    if val is None:
        return None
    return int(val) != 0


def _is_charging(val: Any) -> bool | None:
    """Charge status: 0 = not charging, nonzero = charging."""
    if val is None:
        return None
    return int(val) != 0


def _base_station_on(val: Any) -> bool | None:
    if val is None:
        return None
    return int(val) != 0


def _has_active_alert(val: Any) -> bool | None:
    """Alert mask: 0 = no alerts, nonzero = at least one alert active."""
    if val is None:
        return None
    return int(val) != 0


BINARY_SENSOR_DESCRIPTIONS: tuple[OwletBinarySensorEntityDescription, ...] = (
    OwletBinarySensorEntityDescription(
        key="sock_connected",
        translation_key="sock_connected",
        vitals_key=VITALS_KEY_SOCK_CONNECTION,
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        is_on_fn=_sock_connected,
    ),
    OwletBinarySensorEntityDescription(
        key="base_station_on",
        translation_key="base_station_on",
        vitals_key=VITALS_KEY_BASE_STATION_ON,
        device_class=BinarySensorDeviceClass.POWER,
        is_on_fn=_base_station_on,
    ),
    OwletBinarySensorEntityDescription(
        key="charging",
        translation_key="charging",
        vitals_key=VITALS_KEY_CHARGING,
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        is_on_fn=_is_charging,
    ),
    OwletBinarySensorEntityDescription(
        key="active_alert",
        translation_key="active_alert",
        vitals_key=VITALS_KEY_ALERTS_MASK,
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_has_active_alert,
    ),
    OwletBinarySensorEntityDescription(
        key="alerts_paused",
        translation_key="alerts_paused",
        vitals_key=VITALS_KEY_ALERT_PAUSED,
        icon="mdi:bell-off",
        is_on_fn=_nonzero,
    ),
    OwletBinarySensorEntityDescription(
        key="sock_reading",
        translation_key="sock_reading",
        vitals_key=VITALS_KEY_SOCK_READINGS,
        icon="mdi:signal-variant",
        is_on_fn=_nonzero,
    ),
    OwletBinarySensorEntityDescription(
        key="wellness_alert",
        translation_key="wellness_alert",
        vitals_key=VITALS_KEY_WELLNESS_ALERT,
        device_class=BinarySensorDeviceClass.PROBLEM,
        is_on_fn=_nonzero,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Owlet Dream binary sensor entities."""
    coordinators: list[OwletDeviceCoordinator] = hass.data[DOMAIN][entry.entry_id][
        "coordinators"
    ]

    entities: list[OwletBinarySensorEntity] = []
    for coordinator in coordinators:
        for description in BINARY_SENSOR_DESCRIPTIONS:
            entities.append(OwletBinarySensorEntity(coordinator, description))

    async_add_entities(entities)


class OwletBinarySensorEntity(
    CoordinatorEntity[OwletDeviceCoordinator], BinarySensorEntity
):
    """Binary sensor entity for an Owlet Dream device."""

    entity_description: OwletBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OwletDeviceCoordinator,
        description: OwletBinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.dsn}_{description.key}"
        self._attr_device_info = _device_info(coordinator)

    @property
    def available(self) -> bool:
        """Return True if the value is present in the latest data."""
        if not super().available:
            return False
        data = self.coordinator.data
        return (
            data is not None
            and self.entity_description.vitals_key in data
        )

    @property
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        data = self.coordinator.data
        if data is None:
            return None
        raw = data.get(self.entity_description.vitals_key)
        return self.entity_description.is_on_fn(raw)


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
