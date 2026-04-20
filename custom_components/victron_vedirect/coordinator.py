"""DataUpdateCoordinator for Victron VE.Direct devices."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import timedelta

import serial

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    KIND_BMV,
    KIND_MPPT,
    PID_BMV_PREFIXES,
    PID_MPPT_PREFIXES,
)
from .vedirect import VEDirectParser

_LOGGER = logging.getLogger(__name__)


@dataclass
class VictronData:
    """Runtime data for a VE.Direct config entry."""

    coordinator: VEDirectCoordinator
    # Resolved device kind ("mppt" or "bmv") after first parse, if known.
    kind: str | None = None
    # Last successful frame (raw string key → string value).
    last_frame: dict[str, str] = field(default_factory=dict)


type VictronConfigEntry = ConfigEntry[VictronData]


def detect_kind(pid: str | None) -> str | None:
    """Return "mppt" / "bmv" / None for the given PID value."""
    if not pid:
        return None
    pid_norm = pid.strip().upper()
    if not pid_norm.startswith("0X"):
        # Some devices emit plain numbers or with a trailing comma.
        return None
    pid_norm = "0x" + pid_norm[2:]
    for prefix in PID_MPPT_PREFIXES:
        if pid_norm.startswith(prefix):
            return KIND_MPPT
    for prefix in PID_BMV_PREFIXES:
        if pid_norm.startswith(prefix):
            return KIND_BMV
    return None


class VEDirectCoordinator(DataUpdateCoordinator[dict[str, str]]):
    """Run a background reader thread and expose the latest VE.Direct frame."""

    config_entry: VictronConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: VictronConfigEntry,
        port: str,
        baudrate: int,
        scan_interval: int | None = None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}-{entry.entry_id}",
            update_interval=timedelta(seconds=scan_interval or DEFAULT_SCAN_INTERVAL),
        )
        self._port = port
        self._baudrate = baudrate
        self._parser = VEDirectParser()
        self._serial: serial.Serial | None = None
        self._reader_task: asyncio.Task | None = None
        self._stop = asyncio.Event()
        self._latest: dict[str, str] = {}
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_start(self) -> None:
        """Open the serial port and start the reader task."""
        await self._open_serial()
        self._stop.clear()
        self._reader_task = self.hass.loop.create_task(
            self._reader_loop(), name=f"vedirect-reader-{self.config_entry.entry_id}"
        )

    async def async_stop(self) -> None:
        """Stop the reader task and close the serial port."""
        self._stop.set()
        if self._reader_task is not None:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass
            self._reader_task = None
        await self.hass.async_add_executor_job(self._close_serial_sync)

    # ------------------------------------------------------------------
    # Serial helpers — always called from executor thread
    # ------------------------------------------------------------------

    def _open_serial_sync(self) -> serial.Serial:
        return serial.Serial(self._port, self._baudrate, timeout=1)

    def _close_serial_sync(self) -> None:
        if self._serial is None:
            return
        try:
            self._serial.close()
        except Exception as err:  # noqa: BLE001
            _LOGGER.debug("Error closing serial port %s: %s", self._port, err)
        self._serial = None

    def _read_chunk_sync(self) -> bytes:
        """Blocking read. Returns up to 256 bytes or b"" on timeout."""
        assert self._serial is not None
        return self._serial.read(256)

    async def _open_serial(self) -> None:
        try:
            self._serial = await self.hass.async_add_executor_job(self._open_serial_sync)
        except (serial.SerialException, OSError) as err:
            raise UpdateFailed(
                f"Cannot open VE.Direct port {self._port}: {err}"
            ) from err

    # ------------------------------------------------------------------
    # Background reader
    # ------------------------------------------------------------------

    async def _reader_loop(self) -> None:
        """Continuously read the serial port and feed the parser."""
        backoff = 1
        while not self._stop.is_set():
            try:
                if self._serial is None:
                    await self._open_serial()
                    backoff = 1
                chunk = await self.hass.async_add_executor_job(self._read_chunk_sync)
                if chunk:
                    self._parser.feed(chunk)
                    frame = self._parser.pop_frame()
                    if frame is not None:
                        async with self._lock:
                            self._latest = frame
            except (serial.SerialException, OSError) as err:
                _LOGGER.warning(
                    "VE.Direct serial error on %s (retry in %ss): %s",
                    self._port,
                    backoff,
                    err,
                )
                await self.hass.async_add_executor_job(self._close_serial_sync)
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=backoff)
                    return
                except asyncio.TimeoutError:
                    pass
                backoff = min(backoff * 2, 30)
            except asyncio.CancelledError:
                raise
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected VE.Direct reader error")
                await asyncio.sleep(1)

    # ------------------------------------------------------------------
    # Coordinator hook — called every update_interval
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict[str, str]:
        """Return the latest frame, or raise UpdateFailed if none yet."""
        async with self._lock:
            frame = dict(self._latest)
        if not frame:
            # Do not raise on the first few cycles — entity-unavailable
            # is the better signal than a setup failure here.
            return frame
        runtime: VictronData = self.config_entry.runtime_data
        runtime.last_frame = frame
        if runtime.kind is None:
            runtime.kind = detect_kind(frame.get("PID"))
        return frame
