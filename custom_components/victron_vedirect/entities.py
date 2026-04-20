"""Entity descriptor tables for Victron VE.Direct devices.

Each descriptor defines:
- key        — the VE.Direct field key (e.g. "V", "I", "SOC")
- scale      — multiplier for integer raw values
- round_to   — rounding precision after scale
- translation_key — maps to translations/<lang>.json entity.sensor.<translation_key>.name
- unit, device_class, state_class, entity_category, icon — standard HA attributes
"""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.helpers.entity import EntityCategory


@dataclass(frozen=True, slots=True)
class VEField:
    """One VE.Direct field rendered as a sensor."""

    key: str
    translation_key: str
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    entity_category: EntityCategory | None = None
    icon: str | None = None
    scale: float = 1.0
    round_to: int | None = None
    enabled_default: bool = True


# --- Fields common to every VE.Direct device -----------------------------
_COMMON_FIELDS: tuple[VEField, ...] = (
    VEField(
        key="PID",
        translation_key="product_id",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
        enabled_default=False,
    ),
    VEField(
        key="FW",
        translation_key="firmware",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
        enabled_default=False,
    ),
    VEField(
        key="SER#",
        translation_key="serial",
        icon="mdi:barcode",
        entity_category=EntityCategory.DIAGNOSTIC,
        enabled_default=False,
    ),
)


# --- MPPT Solar Charger --------------------------------------------------
MPPT_FIELDS: tuple[VEField, ...] = (
    *_COMMON_FIELDS,
    VEField(
        key="V",
        translation_key="battery_voltage",
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_to=2,
    ),
    VEField(
        key="I",
        translation_key="battery_current",
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_to=3,
    ),
    VEField(
        key="VPV",
        translation_key="pv_voltage",
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_to=2,
    ),
    VEField(
        key="PPV",
        translation_key="pv_power",
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    VEField(
        key="IL",
        translation_key="load_current",
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_to=3,
        enabled_default=False,
    ),
    VEField(
        key="CS",
        translation_key="charge_state",
        icon="mdi:power-settings",
    ),
    VEField(
        key="MPPT",
        translation_key="mppt_mode",
        icon="mdi:solar-power",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VEField(
        key="OR",
        translation_key="off_reason",
        icon="mdi:information",
        entity_category=EntityCategory.DIAGNOSTIC,
        enabled_default=False,
    ),
    VEField(
        key="ERR",
        translation_key="error_code",
        icon="mdi:alert",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VEField(
        key="H19",
        translation_key="yield_total",
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.01,
        round_to=2,
    ),
    VEField(
        key="H20",
        translation_key="yield_today",
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.01,
        round_to=2,
    ),
    VEField(
        key="H21",
        translation_key="yield_yesterday",
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        scale=0.01,
        round_to=2,
        enabled_default=False,
    ),
    VEField(
        key="H22",
        translation_key="yield_30d",
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        scale=0.01,
        round_to=2,
        enabled_default=False,
    ),
    VEField(
        key="H23",
        translation_key="max_pv_today",
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        scale=0.001,
        round_to=2,
        enabled_default=False,
    ),
)


# --- BMV / SmartShunt ----------------------------------------------------
BMV_FIELDS: tuple[VEField, ...] = (
    *_COMMON_FIELDS,
    VEField(
        key="V",
        translation_key="battery_voltage",
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_to=2,
    ),
    VEField(
        key="I",
        translation_key="battery_current",
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_to=3,
    ),
    VEField(
        key="P",
        translation_key="power",
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    VEField(
        key="CE",
        translation_key="consumed_ah",
        unit="Ah",
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.001,
        round_to=2,
        icon="mdi:battery-minus",
    ),
    VEField(
        key="SOC",
        translation_key="state_of_charge",
        unit=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        scale=0.1,
        round_to=1,
    ),
    VEField(
        key="TTG",
        translation_key="time_to_go",
        unit=UnitOfTime.MINUTES,
        icon="mdi:timer-outline",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    VEField(
        key="AR",
        translation_key="alarm_reason",
        icon="mdi:alert-circle",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    VEField(
        key="H1",
        translation_key="deepest_discharge",
        unit="Ah",
        scale=0.001,
        round_to=2,
        enabled_default=False,
    ),
    VEField(
        key="H2",
        translation_key="last_discharge",
        unit="Ah",
        scale=0.001,
        round_to=2,
        enabled_default=False,
    ),
    VEField(
        key="H3",
        translation_key="avg_discharge",
        unit="Ah",
        scale=0.001,
        round_to=2,
        enabled_default=False,
    ),
    VEField(
        key="H6",
        translation_key="max_voltage",
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        scale=0.001,
        round_to=2,
        enabled_default=False,
    ),
    VEField(
        key="H7",
        translation_key="min_voltage",
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        scale=0.001,
        round_to=2,
        enabled_default=False,
    ),
    VEField(
        key="H17",
        translation_key="energy_discharged",
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.01,
        round_to=2,
    ),
    VEField(
        key="H18",
        translation_key="energy_charged",
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        scale=0.01,
        round_to=2,
    ),
)


# --- Binary sensor fields (alarm flags) ----------------------------------
@dataclass(frozen=True, slots=True)
class VEBinaryField:
    """One VE.Direct field rendered as a binary sensor."""

    key: str
    translation_key: str
    on_value: str = "ON"
    icon: str | None = None
    entity_category: EntityCategory | None = None


BMV_BINARY_FIELDS: tuple[VEBinaryField, ...] = (
    VEBinaryField(
        key="Alarm",
        translation_key="alarm",
        icon="mdi:alert",
    ),
    VEBinaryField(
        key="Relay",
        translation_key="relay",
        icon="mdi:electric-switch",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


def fields_for_kind(kind: str) -> tuple[VEField, ...]:
    """Return the sensor field set for the given device kind."""
    if kind == "mppt":
        return MPPT_FIELDS
    if kind == "bmv":
        return BMV_FIELDS
    return ()


def binary_fields_for_kind(kind: str) -> tuple[VEBinaryField, ...]:
    """Return the binary-sensor field set for the given device kind."""
    if kind == "bmv":
        return BMV_BINARY_FIELDS
    return ()
