"""Sensor platform for Victron VE.Direct devices."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_KIND, DOMAIN, KIND_AUTO, MANUFACTURER
from .coordinator import VEDirectCoordinator, VictronConfigEntry
from .entities import VEField, fields_for_kind

PARALLEL_UPDATES = 0


def _model_for_kind(kind: str | None) -> str:
    if kind == "mppt":
        return "SmartSolar / BlueSolar MPPT"
    if kind == "bmv":
        return "SmartShunt / BMV"
    return "VE.Direct Device"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VictronConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up VE.Direct sensors from a config entry."""
    runtime = entry.runtime_data

    # Resolve the device kind. If the user picked "auto" we rely on what
    # the coordinator detected from the first frame's PID.
    configured = entry.data.get(CONF_DEVICE_KIND, KIND_AUTO)
    kind = configured if configured != KIND_AUTO else runtime.kind
    if kind is None:
        # No data yet and autodetect failed — default to MPPT field set so
        # at least voltage/current/power become visible.
        kind = "mppt"

    fields = fields_for_kind(kind)
    model = _model_for_kind(kind)

    async_add_entities(
        VEDirectSensor(runtime.coordinator, entry, field, model)
        for field in fields
    )


class VEDirectSensor(CoordinatorEntity[VEDirectCoordinator], SensorEntity):
    """A single VE.Direct field exposed as a sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VEDirectCoordinator,
        entry: VictronConfigEntry,
        field: VEField,
        model: str,
    ) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._field = field
        self._attr_unique_id = f"{entry.entry_id}_{field.key}"
        self._attr_entity_registry_enabled_default = field.enabled_default
        self._attr_entity_category = field.entity_category
        self._attr_native_unit_of_measurement = field.unit
        self._attr_device_class = field.device_class
        self._attr_state_class = field.state_class
        self._attr_icon = field.icon
        self.entity_description = SensorEntityDescription(
            key=field.key,
            translation_key=field.translation_key,
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=model,
            serial_number=_safe_serial(coordinator),
        )

    @property
    def available(self) -> bool:
        """Entity is available once we've seen the field at least once."""
        if not super().available:
            return False
        return self._raw_value() is not None

    def _raw_value(self) -> str | None:
        data = self.coordinator.data or {}
        return data.get(self._field.key)

    @property
    def native_value(self) -> float | str | None:
        """Return the parsed value for this field."""
        raw = self._raw_value()
        if raw is None:
            return None
        # Numeric fields: apply scale and rounding.
        if self._field.scale != 1.0 or self._field.round_to is not None:
            try:
                value = int(raw) * self._field.scale
            except (TypeError, ValueError):
                return raw
            if self._field.round_to is not None:
                value = round(value, self._field.round_to)
            return value
        # Numeric-but-unscaled fields: try to coerce to int for state stats.
        try:
            return int(raw)
        except (TypeError, ValueError):
            return raw


def _safe_serial(coordinator: VEDirectCoordinator) -> str | None:
    """Extract the serial number from the latest frame if available."""
    data = coordinator.data or {}
    return data.get("SER#")
