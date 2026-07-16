import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core import DOMAIN
from .core.entity import JuraEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
) -> None:
    device = hass.data[DOMAIN][config_entry.entry_id]

    add_entities(
        [
            JuraMakeButton(device, "make"),
            JuraRefreshStatsButton(device),
            JuraRefreshMaintenanceButton(device),
        ]
    )


class JuraMakeButton(JuraEntity, ButtonEntity):
    def internal_update(self):
        self._attr_available = self.device.product is not None

        if self.hass:
            self._async_write_ha_state()

    async def async_press(self) -> None:
        self.device.start_product()


class JuraRefreshStatsButton(JuraEntity, ButtonEntity):
    """Button to refresh statistics from the Jura machine."""

    def __init__(self, device):
        super().__init__(device, "refresh_stats")
        self._attr_icon = "mdi:refresh"
        self._attr_name = f"{device.name} Refresh Statistics"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_available = True  # Always make the button available

    def internal_update(self):
        if self.hass:
            self._async_write_ha_state()

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Manually refreshing Jura statistics and alerts")
        try:
            await self.device.read_statistics(force_update=True)
            await self.device.read_alerts()
        except Exception as e:
            _LOGGER.error(f"Error refreshing Jura statistics: {e}")


class JuraRefreshMaintenanceButton(JuraEntity, ButtonEntity):
    """Button to refresh maintenance percentages from the Jura machine."""

    def __init__(self, device):
        super().__init__(device, "refresh_maintenance")
        self._attr_icon = "mdi:refresh"
        self._attr_name = f"{device.name} Refresh Maintenance"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_available = True

    def internal_update(self):
        if self.hass:
            self._async_write_ha_state()

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.debug("Manually refreshing Jura maintenance percentages")
        try:
            await self.device.read_maintenance_percents()
        except Exception as e:
            _LOGGER.error(f"Error refreshing Jura maintenance: {e}")
