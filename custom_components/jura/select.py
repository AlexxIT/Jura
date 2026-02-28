from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import EntityCategory

from . import DOMAIN
from .core.entity import JuraEntity
from .core.uuids import UUIDs


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]

    add_entities([JuraSelect(device, select) for select in device.selects()])
    device.raw_command_uuid = JuraUUIDs(device)
    add_entities([device.raw_command_uuid])

class JuraSelect(JuraEntity, SelectEntity):
    def internal_update(self):
        attribute = self.device.attribute(self.attr)

        self._attr_current_option = attribute.get("default")
        self._attr_options = attribute.get("options", [])
        self._attr_available = "default" in attribute

        if self.hass:
            self._async_write_ha_state()

    async def async_select_option(self, option: str) -> None:
        self.device.select_option(self.attr, option)
        self._attr_current_option = option
        self._async_write_ha_state()

class JuraUUIDs(JuraEntity, SelectEntity):
    def __init__(self, device):
        super().__init__(device, "raw_command_uuid")
        self._attr_options = [uuid.name for uuid in UUIDs]
        self._attr_name = "RAW Command UUID"
        self._attr_current_option = self._attr_options[0]  # Default selection
        self._attr_entity_category = EntityCategory.DIAGNOSTIC

    async def async_select_option(self, option: str) -> None:
        """Handle when the user selects an option."""
        if option in [uuid.name for uuid in UUIDs]:
            self._attr_current_option = option
            self._async_write_ha_state()
            # Optional: use the UUID value, e.g., self.get_uuid_value()
        else:
            raise ValueError(f"Invalid option: {option}")

    def get_uuid_value(self) -> str:
        """Return the actual UUID value of the selected option."""
        return UUIDs[self._attr_current_option].value