"""Sensor platform for Jura integration."""

import logging
from datetime import timedelta
from typing import Any
from .core.sensor_definitions import SENSOR_DEFINITIONS
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.const import STATE_UNKNOWN, STATE_UNAVAILABLE

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .core import DOMAIN
from .core.entity import JuraEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jura sensor based on a config entry."""
    device = hass.data[DOMAIN][entry.entry_id]

    # Create the total coffees sensor
    entities = []
    entities.append(JuraSensor(device, "Total Products", "TOTAL_PRODUCTS"))
    entities.append(JuraSensor(device, "Total Coffee Only", "TOTAL_PRODUCTS"))
    entities.append(JuraSensor(device, "Total Coffee With Milk", "TOTAL_PRODUCTS"))
    entities.append(JuraSensor(device, "Total Coffee Including Milk Coffee", "TOTAL_PRODUCTS"))
    entities.append(JuraSensor(device, "Total Milk Only", "TOTAL_PRODUCTS"))
    entities.append(JuraSensor(device, "Total Water Only", "TOTAL_PRODUCTS"))

    # Create sensors for each product
    for product in device.products:
        product_id = product["@Code"]
        if product.get("@Active") != "false":
            entities.append(JuraSensor(device, str(int(product_id,16)), "PRODUCTS"))

    for maintenance_counter in device.maintenance_counters:
        entities.append(JuraSensor(device, maintenance_counter, "MAINTENANCE_COUNTERS"))

    for maintenance_percent in device.maintenance_percents:
        entities.append(JuraSensor(device, maintenance_percent, "MAINTENANCE_PERCENTS"))

    # Create alert sensors
    entities.append(JuraAlertSensor(device))

    async_add_entities(entities)

    # Set up automatic refresh
    update_interval = hass.data[DOMAIN].get("update_interval", 120)

    async def refresh_statistics(*_):
        """Refresh statistics regularly."""
        try:
            await device.read_statistics()
            await device.read_alerts()
        except Exception as ex:
            # we log as info as this is expected if the device is off
            _LOGGER.info(f"Error refreshing statistics: {ex}")

    # Schedule regular updates
    entry.async_on_unload(
        async_track_time_interval(
            hass, refresh_statistics, timedelta(seconds=update_interval)
        )
    )

    # Do an initial refresh
    hass.async_create_task(refresh_statistics())

class JuraStatisticsSensor(JuraEntity, SensorEntity, RestoreEntity):
    """Base class for Jura statistics sensors."""
    should_poll = False

    async def async_added_to_hass(self):
        """Restore previous state."""
        await super().async_added_to_hass()

        old_state = await self.async_get_last_state()
        if old_state and old_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            try:
                self._attr_native_value = int(old_state.state)
                _LOGGER.debug(f"Restored state for {self.entity_id}: {old_state.state}")
            except ValueError:
                _LOGGER.warning(f"Cannot restore state for {self.entity_id}: {old_state.state}")
        else:
            _LOGGER.debug(f"No previous state to restore for {self.entity_id}")

        self.async_write_ha_state()

    def __init__(self, device, attr: str):
        """Initialize the sensor."""
        super().__init__(device, attr)

        # Register for updates on statistics
        device.register_statistics_update(self.internal_update)

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self._attr_native_value

    def _get_value(self) -> Any:
        """Get the value for this sensor from statistics."""
        raise NotImplementedError("Subclasses must implement this method")

    def internal_update(self):
        """Override parent method to ensure statistics are refreshed."""
        if self.hass is None:
            return

        new_value = self._get_value()

        if new_value is not None:
            self._attr_native_value = new_value
            self.async_write_ha_state()

class JuraSensor(JuraStatisticsSensor):
    """Sensor for individual statistics."""

    def __init__(self, device, sensor_id: str, read_from: str = None):
        if sensor_id in SENSOR_DEFINITIONS[read_from]:
            sensor = SENSOR_DEFINITIONS[read_from][sensor_id]
            sensor_name=SENSOR_DEFINITIONS[read_from][sensor_id]['name']
            if "icon" in sensor:
                self._attr_icon = sensor["icon"]
            if "entity_category" in sensor:
                self._attr_entity_category = sensor['entity_category']
            if "unit" in sensor:
                self._attr_native_unit_of_measurement = sensor['unit']
            if "state_class" in sensor:
                self._attr_state_class = sensor['state_class']

            """Initialize the sensor."""
            self.sensor_name = sensor_name
            self.read_from = read_from
            attr_name = f"{read_from}_{sensor_name.lower().replace(' ', '_')}"
            super().__init__(device, attr_name)
            self._attr_name = f"{device.name} {sensor['display_name']}"

    def _get_value(self) -> int:
        value = self.device.statistics.get(self.read_from, {}).get(
            self.sensor_name, None
        )
        is_available = value is not None
        self._attr_available = is_available
        state = "Available" if is_available else "Unavailable"    

        if self.hass:
            self.async_write_ha_state()

        _LOGGER.debug(f"Updating sensor {self.sensor_name} from {self.read_from} with value: {value} ({state})")

        if is_available:
            return value

class JuraAlertSensor(JuraEntity, SensorEntity, RestoreEntity):
    """Sensor for machine alerts."""

    should_poll = False
    _attr_icon = "mdi:alert"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["ok", "alert"]

    def __init__(self, device):
        """Initialize the sensor."""
        self._attr_extra_state_attributes = {"active_alerts": []}

        super().__init__(device, "alerts")
        self._attr_name = f"{device.name} Alerts"
        self._attr_native_value = None
        self._attr_icon = "mdi:alert"
        self._attr_device_class = SensorDeviceClass.ENUM
        self._attr_options = ["ok", "alert"]

        # Register for updates on alerts
        device.register_alert_update(self.internal_update)

    async def async_added_to_hass(self):
        """Restore previous state if available."""
        await super().async_added_to_hass()

        old_state = await self.async_get_last_state()
        if old_state and old_state.state not in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            self._attr_native_value = old_state.state
            _LOGGER.debug(f"Restored alert sensor state for {self.entity_id}: {old_state.state}")
        else:
            _LOGGER.debug(f"No previous alert state to restore for {self.entity_id}")

        self.async_write_ha_state()

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self._attr_native_value

    def _get_value(self) -> str:
        """Get the alert status."""
        active_alerts = []
        for bit, name in self.device.active_alerts.items():
            active_alerts.append({"bit": bit, "name": name})
        self._attr_extra_state_attributes["active_alerts"] = active_alerts

        if not active_alerts:
            return "ok"

        # Check if any of the active alerts is PROBLEM type
        for alert in active_alerts:
            matched_sensor = SENSOR_DEFINITIONS["ALERT_SENSORS"][str(bit)]
            if matched_sensor and matched_sensor["device_class"] == "problem":
                return "alert"
        return "ok"

    def internal_update(self):
        """Update the sensor state."""
        new_value = self._get_value()
        if new_value != self._attr_native_value:
            _LOGGER.debug(f"Alert sensor {self.entity_id} state changed to: {new_value}")
            self._attr_native_value = new_value
            if self.hass:
                self.async_write_ha_state()
