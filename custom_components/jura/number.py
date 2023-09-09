from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .core.entity import JuraEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> None:
    device = hass.data[DOMAIN][config_entry.entry_id]

    add_entities([JuraNumber(device, select) for select in device.numbers()])


class JuraNumber(JuraEntity, NumberEntity):
    def internal_update(self):
        attribute = self.device.attribute(self.attr)

        self._attr_available = "value" in attribute
        self._attr_native_min_value = attribute.get("min")
        self._attr_native_max_value = attribute.get("max")
        self._attr_native_step = attribute.get("step")
        self._attr_native_value = attribute.get("value")

        if self.hass:
            self._async_write_ha_state()

    async def async_set_native_value(self, value: float) -> None:
        self.device.set_value(self.attr, int(value))
        self._attr_native_value = int(value)
        self._async_write_ha_state()
