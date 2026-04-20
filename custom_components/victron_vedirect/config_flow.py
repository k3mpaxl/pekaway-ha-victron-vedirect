"""Config flow for the Victron VE.Direct integration."""

from __future__ import annotations

import logging
import time
from typing import Any

import serial
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_BAUDRATE,
    CONF_DEVICE_KIND,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_BAUDRATE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    KIND_AUTO,
    KIND_BMV,
    KIND_MPPT,
)
from .coordinator import VictronConfigEntry, detect_kind
from .vedirect import VEDirectParser

_LOGGER = logging.getLogger(__name__)

KIND_OPTIONS = [
    SelectOptionDict(value=KIND_AUTO, label="Automatisch erkennen"),
    SelectOptionDict(value=KIND_MPPT, label="MPPT Solarladeregler"),
    SelectOptionDict(value=KIND_BMV, label="SmartShunt / BMV Batteriemonitor"),
]

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PORT): cv.string,
        vol.Required(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): cv.positive_int,
        vol.Required(CONF_DEVICE_KIND, default=KIND_AUTO): SelectSelector(
            SelectSelectorConfig(options=KIND_OPTIONS, mode=SelectSelectorMode.DROPDOWN)
        ),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            cv.positive_int, vol.Range(min=1, max=60)
        ),
    }
)


def _probe_serial(port: str, baudrate: int, timeout: float = 4.0) -> dict[str, str]:
    """Open the port and try to parse one complete VE.Direct frame.

    Raises SerialException / OSError on connection errors, or returns an
    empty dict if no frame arrived within ``timeout`` seconds.
    """
    parser = VEDirectParser()
    ser = serial.Serial(port, baudrate, timeout=1)
    try:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            chunk = ser.read(256)
            if not chunk:
                continue
            parser.feed(chunk)
            frame = parser.pop_frame()
            if frame is not None:
                return frame
    finally:
        try:
            ser.close()
        except Exception:  # noqa: BLE001
            pass
    return {}


class VictronConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for VE.Direct devices."""

    VERSION = 1

    async def _validate(
        self, user_input: dict[str, Any]
    ) -> tuple[dict[str, Any] | None, dict[str, str]]:
        """Probe the serial port. Returns (resolved_data, errors)."""
        errors: dict[str, str] = {}
        port = user_input[CONF_PORT]
        baudrate = user_input[CONF_BAUDRATE]
        kind = user_input[CONF_DEVICE_KIND]

        try:
            frame = await self.hass.async_add_executor_job(
                _probe_serial, port, baudrate
            )
        except (serial.SerialException, OSError) as err:
            _LOGGER.warning("VE.Direct probe failed on %s: %s", port, err)
            errors["base"] = "cannot_connect"
            return None, errors
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Unexpected error probing VE.Direct")
            errors["base"] = "unknown"
            return None, errors

        if not frame:
            errors["base"] = "no_frame"
            return None, errors

        detected = detect_kind(frame.get("PID"))
        if kind == KIND_AUTO:
            if detected is None:
                errors["base"] = "unknown_device"
                return None, errors
            kind = detected
        elif detected is not None and detected != kind:
            _LOGGER.warning(
                "User selected kind %s but PID %s looks like %s",
                kind,
                frame.get("PID"),
                detected,
            )

        resolved = dict(user_input)
        resolved[CONF_DEVICE_KIND] = kind
        resolved["_serial"] = frame.get("SER#")
        return resolved, errors

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            resolved, errors = await self._validate(user_input)
            if resolved is not None:
                serial_no = resolved.pop("_serial", None)
                unique = serial_no or resolved[CONF_PORT]
                await self.async_set_unique_id(unique)
                self._abort_if_unique_id_configured()

                title = f"Victron {resolved[CONF_DEVICE_KIND].upper()}"
                if serial_no:
                    title = f"{title} ({serial_no})"
                return self.async_create_entry(title=title, data=resolved)

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Allow changing port / baudrate / device kind for an existing entry."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            resolved, errors = await self._validate(user_input)
            if resolved is not None:
                serial_no = resolved.pop("_serial", None)
                unique = serial_no or resolved[CONF_PORT]
                await self.async_set_unique_id(unique)
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(entry, data=resolved)

        suggested = {**entry.data}
        suggested.pop("_serial", None)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_SCHEMA, suggested
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: VictronConfigEntry,
    ) -> VictronOptionsFlow:
        """Return the options flow handler."""
        return VictronOptionsFlow()


class VictronOptionsFlow(OptionsFlow):
    """Options flow for VE.Direct devices (scan interval)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {
            CONF_SCAN_INTERVAL: self.config_entry.options.get(
                CONF_SCAN_INTERVAL,
                self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ),
        }

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(OPTIONS_SCHEMA, current),
        )
