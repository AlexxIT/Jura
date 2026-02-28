import logging
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import EntityCategory

from . import DOMAIN
from .core.entity import JuraEntity

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]
    device.raw_command_data = JuraRawCommandData(device)
    add_entities([device.raw_command_data])

class JuraRawCommandData(JuraEntity, TextEntity):
    def __init__(self, device):
        super().__init__(device, "raw_command_data")
        self._attr_native_value = ""
        self._attr_mode = "text"
        self._attr_name = "RAW Command data (HEX)"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_set_value(self, value: str) -> None:
        """Handle input from UI."""
        self._attr_native_value = value
        self._async_write_ha_state()
        # Optional: validate/parse hex here
        # parsed = self.get_hex_bytes()

    def get_text(self) -> bytes:
        """Return the input string as raw bytes."""
        return self._attr_native_value
