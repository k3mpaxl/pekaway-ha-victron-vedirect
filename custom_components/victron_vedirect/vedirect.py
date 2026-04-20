"""Minimal VE.Direct protocol parser.

The parser is stateful — feed it bytes with ``feed`` and read completed
frames from ``pop_frame``. No asyncio, no serial, no HA imports here —
so it is trivial to unit-test.

VE.Direct text frames end with a ``Checksum`` key whose value byte
makes the sum of all bytes (including key, tab, newline separators,
and the checksum value) equal to 0 modulo 256. This implementation
does not currently validate the checksum — it just treats ``Checksum``
as the end-of-frame marker. That matches the behaviour of the legacy
implementations we're consolidating.
"""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Iterable

_LOGGER = logging.getLogger(__name__)

_TERMINATOR_KEY = "Checksum"


class VEDirectParser:
    """Incremental parser for VE.Direct text frames."""

    def __init__(self) -> None:
        """Initialize a new parser."""
        self._buffer = bytearray()
        self._current: dict[str, str] = {}
        self._frames: deque[dict[str, str]] = deque(maxlen=8)

    def feed(self, chunk: bytes | bytearray) -> None:
        """Feed raw bytes into the parser."""
        if not chunk:
            return
        self._buffer.extend(chunk)
        while True:
            idx = self._buffer.find(b"\n")
            if idx < 0:
                break
            raw_line = bytes(self._buffer[:idx])
            del self._buffer[: idx + 1]
            line = raw_line.decode("utf-8", errors="ignore").strip("\r\n \t")
            if not line:
                continue
            try:
                key, _, value = line.partition("\t")
            except ValueError:
                continue
            if not key:
                continue
            if key == _TERMINATOR_KEY:
                if self._current:
                    self._frames.append(dict(self._current))
                    self._current.clear()
                continue
            self._current[key] = value

    def pop_frame(self) -> dict[str, str] | None:
        """Return the most recent complete frame, or None."""
        if not self._frames:
            return None
        # Keep only the latest frame — older ones are stale.
        latest = self._frames[-1]
        self._frames.clear()
        return latest

    def frames(self) -> Iterable[dict[str, str]]:
        """Drain and return all pending frames (rarely needed)."""
        while self._frames:
            yield self._frames.popleft()
