import logging

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

_LOGGER = logging.getLogger(__name__)

# Define alert sensors with their expected alert names and configurations
ALERT_SENSORS = [
    # Maintenance alerts (these are normal maintenance operations)
    {
        "name_pattern": "insert tray",
        "type": "insert_tray",
        "display_name": "Insert Tray",
        "icon": "mdi:tray",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "fill water",
        "type": "fill_water",
        "display_name": "Fill Water",
        "icon": "mdi:water",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "empty grounds",
        "type": "empty_grounds",
        "display_name": "Empty Grounds",
        "icon": "mdi:delete",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "empty tray",
        "type": "empty_tray",
        "display_name": "Empty Tray",
        "icon": "mdi:tray-alert",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    # Service alerts (require cleaning or filter replacement)
    {
        "name_pattern": "cleaning alert",
        "type": "cleaning_alert",
        "display_name": "Cleaning Needed",
        "icon": "mdi:washing-machine",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "filter alert",
        "type": "filter_alert",
        "display_name": "Filter Change Needed",
        "icon": "mdi:air-filter",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "cappu rinse alert",
        "type": "cappu_rinse_alert",
        "display_name": "Milk System Rinse Needed",
        "icon": "mdi:cup-water",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "cappu clean alert",
        "type": "cappu_clean_alert",
        "display_name": "Milk System Cleaning Needed",
        "icon": "mdi:cup-water",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
    {
        "name_pattern": "no beans",
        "type": "no_beans",
        "display_name": "No Beans",
        "icon": "mdi:coffee-off",
        "device_class": BinarySensorDeviceClass.PROBLEM,
        "entity_category": EntityCategory.DIAGNOSTIC,
    },
]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, add_entities: AddEntitiesCallback
):
    device = hass.data[DOMAIN][config_entry.entry_id]

    # Create connection sensor
    entities: list = [JuraSensor(device, "connection")]

    # Create alert binary sensors
    for alert_info in ALERT_SENSORS:
        entities.append(JuraAlertBinarySensor(device, alert_info))

    add_entities(entities)


class JuraSensor(JuraEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def internal_update(self):
        self._attr_is_on = self.device.connected
        self._attr_extra_state_attributes = self.device.conn_info

        if self.hass:
            self._async_write_ha_state()


class JuraAlertBinarySensor(JuraEntity, BinarySensorEntity):
    """Binary sensor for Jura alerts."""

    def __init__(self, device, alert_info: dict):
        """Initialize the sensor."""
        # Store name pattern before calling super().__init__
        self._name_pattern = alert_info["name_pattern"].lower()

        super().__init__(device, f"alert_{alert_info['type']}")

        self._attr_name = f"{device.name} {alert_info['display_name']}"
        self._attr_icon = alert_info["icon"]
        self._attr_device_class = alert_info["device_class"]
        self._attr_entity_category = alert_info["entity_category"]

        # Register for updates on alerts
        device.register_alert_update(self.internal_update)

    def internal_update(self):
        """Update the sensor state."""
        # Check if any active alert's name contains our pattern
        self._attr_is_on = any(
            self._name_pattern in alert_name.lower()
            for _, alert_name in self.device.active_alerts.items()
        )

        if self.hass:
            self._async_write_ha_state()
