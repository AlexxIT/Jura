"""Async TCP client for Jura WiFi Connect module (port 51515)."""

import asyncio
import logging

from .wifi_encryption import wifi_make_frame, wifi_parse_frame

_LOGGER = logging.getLogger(__name__)


class WifiClient:
    """Async WiFi client for Jura machines via plain TCP on port 51515."""

    def __init__(
        self,
        host: str,
        port: int = 51515,
        pin: str = "",
        device_name: str = "HomeAssistant",
        auth_hash: str = "",
    ):
        self.host = host
        self.port = port
        self.pin = pin
        self.device_name_hex = device_name.encode().hex()
        self.auth_hash = auth_hash
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.connected = False

    async def connect(self) -> bool:
        """Open TCP connection and authenticate with the machine.

        Returns True if auth succeeded (@hp4 response), False otherwise.
        """
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
        except OSError as e:
            _LOGGER.warning("WiFi connect to %s:%s failed: %s", self.host, self.port, e)
            return False

        auth_cmd = f"@HP:{self.pin},{self.device_name_hex},{self.auth_hash}"
        await self._send_frame(auth_cmd)
        response = await self.read_response()
        _LOGGER.debug("Auth response: %r", response)
        self.connected = "@hp4" in response
        if not self.connected:
            _LOGGER.warning(
                "WiFi auth failed for %s, response: %r", self.host, response
            )
        return self.connected

    async def _send_frame(self, cmd: str):
        """Encode and write one framed command."""
        frame = wifi_make_frame(cmd)
        self.writer.write(frame)
        await self.writer.drain()

    async def send_command(self, cmd: str, timeout: float = 3.0) -> str:
        """Send command string and wait for one response frame."""
        await self._send_frame(cmd)
        return await self.read_response(timeout)

    async def read_response(self, timeout: float = 3.0) -> str:
        """Read and decode one response frame from the machine."""
        try:
            data = await asyncio.wait_for(self._read_until_frame(), timeout)
            return wifi_parse_frame(data)
        except asyncio.TimeoutError:
            _LOGGER.debug("Read timeout waiting for response from %s", self.host)
            return ""

    async def _read_until_frame(self) -> bytes:
        """Read raw bytes until the 0x0D 0x0A frame terminator."""
        buf = bytearray()
        while True:
            byte = await self.reader.read(1)
            if not byte:
                break
            buf.extend(byte)
            if len(buf) >= 2 and buf[-2] == 0x0D and buf[-1] == 0x0A:
                break
        return bytes(buf)

    async def get_machine_state(self) -> int:
        """Return the 32-bit machine state word from @TM:08."""
        await self.send_command("@TS:01")
        resp = await self.send_command("@TM:08")
        await self.send_command("@TS:00")
        if resp.startswith("@tm:08,"):
            try:
                return int(resp[7:].strip(), 16)
            except ValueError:
                _LOGGER.debug("Could not parse state word from: %r", resp)
        return 0

    async def get_firmware_version(self) -> str:
        """Return firmware version string from @TG:C0."""
        resp = await self.send_command("@TG:C0")
        if resp.startswith("@tg:"):
            return resp[4:].strip()
        return ""

    async def get_temperature(self) -> int | None:
        """Return raw temperature value from @TM:0A, or None on failure."""
        await self.send_command("@TS:01")
        resp = await self.send_command("@TM:0A")
        await self.send_command("@TS:00")
        resp_lower = resp.lower()
        if resp_lower.startswith("@tm:0a,"):
            try:
                return int(resp_lower[7:].strip(), 16)
            except ValueError:
                _LOGGER.debug("Could not parse temperature from: %r", resp)
        return None

    async def disconnect(self):
        """Close the TCP connection cleanly."""
        self.connected = False
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass
            self.writer = None
            self.reader = None
