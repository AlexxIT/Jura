from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .core.entity import JuraEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]

    add_entities([JuraSelect(device, select) for select in device.selects()])


class JuraSelect(JuraEntity, SelectEntity):
    def internal_update(self):
        attribute = self.device.attribute(self.attr)

        self._attr_current_option = attribute.get("default")
        self._attr_options = attribute.get("options", [])
        self._attr_available = bool(attribute)

        if self.hass:
            self._async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        self.device.select_option(self.attr, option)
        self._attr_current_option = option
        self._async_write_ha_state()
