import re

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo, Entity

from . import DOMAIN
from .device import Device


def sanitize(entity_id: str) -> str:
    return re.sub(r"[^0-9a-z_]+", "", entity_id.lower())


class JuraEntity(Entity):
    _attr_should_poll = False

    def __init__(self, device: Device, attr: str):
        self.device = device
        self.attr = attr

        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_NETWORK_MAC, device.mac)},
            identifiers={(DOMAIN, device.mac)},
            manufacturer="Jura",
            model=device.model,
            name=device.name or "Jura",
        )
        self._attr_name = device.name + " " + attr.replace("_", " ").title()
        self._attr_unique_id = device.mac.replace(":", "") + "_" + attr

        self.entity_id = DOMAIN + "." + sanitize(self._attr_unique_id)

        self.internal_update()

        device.register_update(attr, self.internal_update)

    def internal_update(self):
        pass

    async def async_update(self):
        self.device.client.ping()


class JuraWifiEntity(Entity):
    """Base entity for Jura machines connected via WiFi."""

    _attr_should_poll = False

    def __init__(self, device, attr: str):
        self.device = device
        self.attr = attr

        mac_clean = re.sub(r"[^0-9a-zA-Z]", "", device.mac)

        # Only register MAC connection if we have a real colon-separated MAC
        connections = (
            {(CONNECTION_NETWORK_MAC, device.mac)} if ":" in device.mac else set()
        )
        self._attr_device_info = DeviceInfo(
            connections=connections,
            identifiers={(DOMAIN, device.mac)},
            manufacturer="Jura",
            model=device.model,
            name=device.name or "Jura",
        )
        self._attr_name = device.name + " " + attr.replace("_", " ").title()
        self._attr_unique_id = mac_clean + "_wifi_" + attr

        self.entity_id = DOMAIN + "." + sanitize(self._attr_unique_id)

        self.internal_update()

        device.register_wifi_update(self.internal_update)

    def internal_update(self):
        pass
