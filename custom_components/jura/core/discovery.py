"""UDP discovery for Jura WiFi Connect machines.

Jura machines with the WiFi Connect module broadcast a 117-byte UDP beacon
every ~60 seconds to the subnet broadcast address on port 51515.
"""

import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

DISCOVERY_PORT = 51515
BEACON_SIZE = 117


def parse_beacon(data: bytes) -> dict | None:
    """Parse a 117-byte Jura UDP discovery beacon.

    The beacon contains null-terminated UTF-8/latin-1 strings for device name,
    model, and other fields. A 6-byte MAC address is embedded at a fixed offset.
    """
    if len(data) != BEACON_SIZE:
        return None
    try:
        text = data.decode("latin-1", errors="replace")
        fields = [f.strip() for f in text.split("\x00") if f.strip()]
        result: dict = {"raw": data.hex()}
        if len(fields) >= 1:
            result["name"] = fields[0]
        if len(fields) >= 2:
            result["model"] = fields[1]
        # MAC address is typically embedded at offset 6–12 in the beacon
        mac_bytes = data[6:12]
        result["mac"] = ":".join(f"{b:02X}" for b in mac_bytes)
        return result
    except Exception as e:
        _LOGGER.debug("Error parsing beacon: %s", e)
        return None


class _JuraDiscoveryProtocol(asyncio.DatagramProtocol):
    """asyncio UDP protocol that fires a callback for each valid Jura beacon."""

    def __init__(self, callback):
        self.callback = callback
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        _LOGGER.debug(
            "UDP datagram from %s, length=%d", addr[0], len(data)
        )
        if len(data) == BEACON_SIZE:
            machine = parse_beacon(data)
            if machine:
                machine["ip"] = addr[0]
                self.callback(machine)

    def error_received(self, exc):
        _LOGGER.debug("Discovery socket error: %s", exc)


async def discover_machines(timeout: float = 5.0) -> list[dict]:
    """Listen for Jura WiFi beacons and return discovered machines.

    Opens a UDP socket on port 51515, waits *timeout* seconds, then closes it.
    Returns a list of machine dicts with keys: ip, mac, name, model, raw.
    """
    machines: dict[str, dict] = {}

    def on_machine(machine: dict):
        key = machine.get("mac") or machine.get("ip", "")
        machines[key] = machine

    loop = asyncio.get_event_loop()
    try:
        transport, _ = await loop.create_datagram_endpoint(
            lambda: _JuraDiscoveryProtocol(on_machine),
            local_addr=("0.0.0.0", DISCOVERY_PORT),
            allow_broadcast=True,
        )
    except OSError as e:
        _LOGGER.warning(
            "Cannot bind UDP port %d for discovery: %s", DISCOVERY_PORT, e
        )
        return []

    try:
        await asyncio.sleep(timeout)
    finally:
        transport.close()

    return list(machines.values())
