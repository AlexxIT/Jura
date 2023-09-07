from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import DOMAIN, start_product
from .core.entity import JuraEntity


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> None:
    device = hass.data[DOMAIN][config_entry.entry_id]

    add_entities([JuraButton(device, "make")])


class JuraButton(JuraEntity, ButtonEntity):
    def internal_update(self):
        self._attr_available = self.device.product is not None

        if self.hass:
            self._async_write_ha_state()

    async def async_press(self) -> None:
        await start_product(self.device)
