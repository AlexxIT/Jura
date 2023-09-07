from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity import Entity

from . import DOMAIN
from .device import Device


class JuraEntity(Entity):
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

        self.entity_id = DOMAIN + "." + self._attr_unique_id

        self.internal_update()

        device.updates.append(self.internal_update)

    def internal_update(self):
        pass
