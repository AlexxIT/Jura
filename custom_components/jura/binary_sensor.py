from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .core.entity import JuraEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]

    add_entities([JuraSensor(device, "connection")])


class JuraSensor(JuraEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def internal_update(self):
        self._attr_is_on = self.device.connected
        self._attr_extra_state_attributes = self.device.conn_info

        if self.hass:
            self._async_write_ha_state()
