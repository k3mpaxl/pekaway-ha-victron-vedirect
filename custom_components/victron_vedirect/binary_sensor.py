"""Binary sensors (alarm, relay) for Victron VE.Direct devices."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_KIND, DOMAIN, KIND_AUTO, MANUFACTURER
from .coordinator import VEDirectCoordinator, VictronConfigEntry
from .entities import VEBinaryField, binary_fields_for_kind

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VictronConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VE.Direct binary sensors from a config entry."""
    runtime = entry.runtime_data
    configured = entry.data.get(CONF_DEVICE_KIND, KIND_AUTO)
    kind = configured if configured != KIND_AUTO else runtime.kind
    if kind is None:
        return
    fields = binary_fields_for_kind(kind)
    async_add_entities(
        VEDirectBinarySensor(runtime.coordinator, entry, field) for field in fields
    )


class VEDirectBinarySensor(
    CoordinatorEntity[VEDirectCoordinator], BinarySensorEntity
):
    """A VE.Direct alarm/relay field exposed as a binary sensor."""

    _attr_has_entity_name = True
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(
        self,
        coordinator: VEDirectCoordinator,
        entry: VictronConfigEntry,
        field: VEBinaryField,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._field = field
        self._attr_unique_id = f"{entry.entry_id}_{field.key}"
        self._attr_entity_category = field.entity_category
        self._attr_icon = field.icon
        self.entity_description = BinarySensorEntityDescription(
            key=field.key,
            translation_key=field.translation_key,
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
        )

    @property
    def available(self) -> bool:
        """Available once we've seen the field."""
        if not super().available:
            return False
        return (self.coordinator.data or {}).get(self._field.key) is not None

    @property
    def is_on(self) -> bool | None:
        """Return True if the field equals the configured on-value."""
        raw = (self.coordinator.data or {}).get(self._field.key)
        if raw is None:
            return None
        return raw.strip().upper() == self._field.on_value.upper()
