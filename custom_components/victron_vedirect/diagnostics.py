"""Diagnostics support for the Victron VE.Direct integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from .const import CONF_PORT
from .coordinator import VictronConfigEntry

TO_REDACT = {CONF_PORT, "SER#"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: VictronConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime = entry.runtime_data
    coordinator = runtime.coordinator

    return {
        "entry": async_redact_data(
            {
                "title": entry.title,
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            TO_REDACT,
        ),
        "runtime": async_redact_data(
            {
                "kind": runtime.kind,
                "last_frame": runtime.last_frame,
            },
            TO_REDACT,
        ),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
        },
    }
