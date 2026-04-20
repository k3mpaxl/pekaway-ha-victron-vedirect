"""The Victron VE.Direct integration."""

from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    CONF_BAUDRATE,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_BAUDRATE,
    DEFAULT_SCAN_INTERVAL,
    PLATFORMS,
)
from .coordinator import VEDirectCoordinator, VictronConfigEntry, VictronData

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: VictronConfigEntry
) -> bool:
    """Set up a VE.Direct device from a config entry."""
    port = entry.data[CONF_PORT]
    baudrate = entry.data.get(CONF_BAUDRATE, DEFAULT_BAUDRATE)
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    coordinator = VEDirectCoordinator(hass, entry, port, baudrate, scan_interval)

    try:
        await coordinator.async_start()
    except Exception as err:  # noqa: BLE001
        raise ConfigEntryNotReady(
            f"Cannot start VE.Direct reader on {port}: {err}"
        ) from err

    entry.runtime_data = VictronData(coordinator=coordinator)

    # Do a first refresh so we have at least one frame.
    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: VictronConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        await entry.runtime_data.coordinator.async_stop()
    return unload_ok


async def async_reload_entry(
    hass: HomeAssistant, entry: VictronConfigEntry
) -> None:
    """Reload after options change."""
    await hass.config_entries.async_reload(entry.entry_id)
