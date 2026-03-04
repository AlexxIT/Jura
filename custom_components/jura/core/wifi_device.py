"""WiFi-connected Jura machine device model.

Wraps WifiClient and provides polling + update-callback infrastructure
compatible with the JuraWifiEntity base class.

Machine state word (@TM:08) bit definitions:
    Bit 0 (0x01): standby / idle
    Bit 1 (0x02): ready
    Bit 2 (0x04): machine ready (heating done, brew-ready)
    Bit 3 (0x08): water tank missing / empty
    Bit 4 (0x10): grinder empty (no beans)
    Bit 5 (0x20): drip tray full
    Bit 6 (0x40): grounds container full
"""

import logging
from typing import Callable

from .wifi_client import WifiClient

_LOGGER = logging.getLogger(__name__)

# Bit masks for the @TM:08 state word
BIT_STANDBY = 0x01
BIT_READY = 0x02
BIT_MACHINE_READY = 0x04
BIT_WATER_MISSING = 0x08
BIT_GRINDER_EMPTY = 0x10
BIT_DRIP_TRAY_FULL = 0x20
BIT_GROUNDS_FULL = 0x40


class WifiDevice:
    """Represents a Jura coffee machine reachable over TCP/IP (WiFi Connect)."""

    def __init__(
        self,
        name: str,
        host: str,
        port: int = 51515,
        pin: str = "",
        device_name: str = "HomeAssistant",
        auth_hash: str = "",
        model: str = "Jura WiFi",
        mac: str = "",
    ):
        self.name = name
        self.model = model
        self.connected = False
        self.conn_info: dict = {"host": host}

        # Use MAC if provided; otherwise derive a stable ID from the IP
        self._mac = mac if mac else host.replace(".", "")

        self._client = WifiClient(host, port, pin, device_name, auth_hash)

        self._state_word: int = 0
        self._firmware_version: str = ""
        self._temperature: int | None = None

        self._update_handlers: list[Callable] = []

    # --- Public properties ---------------------------------------------------

    @property
    def mac(self) -> str:
        """Stable device identifier (real MAC or IP-derived string)."""
        return self._mac

    @property
    def state_word(self) -> int:
        """Raw 32-bit machine state word from @TM:08."""
        return self._state_word

    @property
    def firmware_version(self) -> str:
        """WiFi firmware version string from @TG:C0."""
        return self._firmware_version

    @property
    def temperature(self) -> int | None:
        """Raw temperature value from @TM:0A (unit depends on machine)."""
        return self._temperature

    # --- State-word helpers --------------------------------------------------

    def machine_ready(self) -> bool:
        return bool(self._state_word & BIT_MACHINE_READY)

    def water_missing(self) -> bool:
        return bool(self._state_word & BIT_WATER_MISSING)

    def grinder_empty(self) -> bool:
        return bool(self._state_word & BIT_GRINDER_EMPTY)

    def drip_tray_full(self) -> bool:
        return bool(self._state_word & BIT_DRIP_TRAY_FULL)

    def grounds_full(self) -> bool:
        return bool(self._state_word & BIT_GROUNDS_FULL)

    # --- Update handler registration -----------------------------------------

    def register_wifi_update(self, handler: Callable):
        """Register a callback invoked after each poll cycle completes."""
        self._update_handlers.append(handler)

    def _notify_updates(self):
        for handler in self._update_handlers:
            try:
                handler()
            except Exception as e:
                _LOGGER.warning("Update handler raised an exception: %s", e)

    # --- Polling -------------------------------------------------------------

    async def async_update(self):
        """Poll the machine for current state. Called by the HA coordinator."""
        try:
            if not self._client.connected:
                ok = await self._client.connect()
                if not ok:
                    self.connected = False
                    self._notify_updates()
                    return

            self.connected = True
            self._state_word = await self._client.get_machine_state()
            self.conn_info["state_word"] = hex(self._state_word)

            if not self._firmware_version:
                self._firmware_version = await self._client.get_firmware_version()

            temp = await self._client.get_temperature()
            if temp is not None:
                self._temperature = temp

        except Exception as e:
            _LOGGER.warning("WiFi poll error for %s: %s", self.name, e)
            self.connected = False
            await self._client.disconnect()

        self._notify_updates()

    async def disconnect(self):
        """Disconnect from the machine (called on HA unload)."""
        await self._client.disconnect()
        self.connected = False
