"""Constants for the Victron VE.Direct integration."""

from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "victron_vedirect"
PLATFORMS: Final = [Platform.SENSOR, Platform.BINARY_SENSOR]
MANUFACTURER: Final = "Victron Energy"

# -- Config keys ----------------------------------------------------------
CONF_PORT: Final = "port"
CONF_BAUDRATE: Final = "baudrate"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_DEVICE_KIND: Final = "device_kind"

DEFAULT_BAUDRATE: Final = 19200
DEFAULT_SCAN_INTERVAL: Final = 5  # seconds

# -- Device kinds ---------------------------------------------------------
KIND_MPPT: Final = "mppt"           # Solar Charge Controller
KIND_BMV: Final = "bmv"             # SmartShunt / BMV battery monitor
KIND_AUTO: Final = "auto"           # autodetect via PID

# Known Victron PID prefixes. Full map at
# https://www.victronenergy.com/upload/documents/VE.Direct-Protocol-3.33.pdf
PID_MPPT_PREFIXES: Final = ("0xA0", "0xA04", "0xA05", "0xA06", "0xA07", "0xA10", "0xA11", "0xA12", "0xA13", "0xA14", "0xA2")
PID_BMV_PREFIXES: Final = ("0x203", "0x204", "0x205", "0xA38", "0xA39", "0xA3A", "0xA3B", "0xA3C", "0xA3D", "0xA3E", "0xA3F")
