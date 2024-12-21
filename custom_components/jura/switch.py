import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .core.entity import JuraEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]

    add_entities([JuraSwitch(device, "connection")])


class JuraSwitch(JuraEntity, SwitchEntity):
    def internal_update(self):
        self._attr_is_on = self.device.connected

        if self.hass:
            self._async_write_ha_state()

    async def async_turn_on(self) -> None:
        self.device.client.ping()
        for _ in range(5):
            if not self.device.connected:
                await asyncio.sleep(1)

    async def async_turn_off(self) -> None:
        self.device.client.ping_cancel()
        for _ in range(5):
            if self.device.connected:
                await asyncio.sleep(1)
