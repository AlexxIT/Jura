"""Sensor platform for Jura integration."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .core import DOMAIN
from .core.entity import JuraEntity, JuraWifiEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Jura sensor based on a config entry."""
    device = hass.data[DOMAIN][entry.entry_id]

    if entry.data.get("connection_type") == "wifi":
        entities: list = [
            JuraWifiMachineStateSensor(device),
            JuraWifiFirmwareSensor(device),
            JuraWifiTemperatureSensor(device),
        ]
        async_add_entities(entities)
        return

    # BLE path (unchanged)
    entities = [JuraTotalCoffeeSensor(device)]

    for product in device.products:
        product_name = product["@Name"]
        if product.get("@Active") != "false":
            entities.append(JuraProductCountSensor(device, product_name))

    entities.append(JuraAlertSensor(device))

    async_add_entities(entities)

    update_interval = hass.data[DOMAIN].get("update_interval", 60)

    async def refresh_statistics(*_):
        """Refresh statistics regularly."""
        try:
            await device.read_statistics()
            await device.read_alerts()
        except Exception as ex:
            # we log as info as this is expected if the device is off
            _LOGGER.info(f"Error refreshing statistics: {ex}")

    entry.async_on_unload(
        async_track_time_interval(
            hass, refresh_statistics, timedelta(seconds=update_interval)
        )
    )

    hass.async_create_task(refresh_statistics())


# ---------------------------------------------------------------------------
# BLE sensor classes (unchanged)
# ---------------------------------------------------------------------------


class JuraStatisticsSensor(JuraEntity, SensorEntity):
    """Base class for Jura statistics sensors."""

    def __init__(self, device, attr: str):
        """Initialize the sensor."""
        super().__init__(device, attr)

        # Register for updates on statistics
        device.register_statistics_update(self.internal_update)

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        return self._get_value()

    def _get_value(self) -> Any:
        """Get the value for this sensor from statistics."""
        raise NotImplementedError("Subclasses must implement this method")

    def internal_update(self):
        """Override parent method to ensure statistics are refreshed."""
        _LOGGER.debug(f"Updating sensor {self._attr_name}")
        if self.hass is not None:
            self.async_write_ha_state()


class JuraTotalCoffeeSensor(JuraStatisticsSensor):
    """Sensor for total coffee count."""

    _attr_icon = "mdi:coffee"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "products"

    def __init__(self, device):
        """Initialize the sensor."""
        super().__init__(device, "total_product")
        self._attr_name = f"{device.name} Total Products"

    def _get_value(self) -> int:
        """Get the total coffee count."""
        value = self.device.statistics.get("total_products", 0)
        _LOGGER.debug(f"Total coffee value: {value}")
        return value


class JuraProductCountSensor(JuraStatisticsSensor):
    """Sensor for individual product count."""

    _attr_icon = "mdi:coffee-outline"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_native_unit_of_measurement = "products"

    def __init__(self, device, product_name: str):
        """Initialize the sensor."""
        self.product_name = product_name
        attr_name = f"product_{product_name.lower().replace(' ', '_')}"
        super().__init__(device, attr_name)
        self._attr_name = f"{device.name} {product_name} Count"

    def _get_value(self) -> int:
        """Get the count for this specific product."""
        value = self.device.statistics.get("product_counts", {}).get(
            self.product_name, None
        )
        _LOGGER.debug(f"Product {self.product_name} count: {value}")
        return value


class JuraAlertSensor(JuraEntity, SensorEntity):
    """Sensor for machine alerts."""

    _attr_icon = "mdi:alert"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["ok", "alert"]

    def __init__(self, device):
        """Initialize the sensor."""
        super().__init__(device, "alerts")
        self._attr_name = f"{device.name} Alerts"
        self._attr_extra_state_attributes = {"active_alerts": []}

        # Register for updates on alerts
        device.register_alert_update(self.internal_update)

    @property
    def native_value(self) -> str:
        """Return the state of the sensor."""
        return self._get_value()

    def _get_value(self) -> str:
        """Get the alert status."""
        active_alerts = []
        # Filter out specific alert bits that we don't want to show
        filtered_bits = {12, 13, 36, 37, 148, 149, 150, 151}
        for bit, name in self.device.active_alerts.items():
            if bit not in filtered_bits:
                active_alerts.append({"bit": bit, "name": name})
        self._attr_extra_state_attributes["active_alerts"] = active_alerts
        return "alert" if active_alerts else "ok"

    def internal_update(self):
        """Override parent method to ensure alerts are refreshed."""
        _LOGGER.debug(f"Updating alert sensor {self._attr_name}")
        if self.hass is not None:
            self.async_write_ha_state()


# ---------------------------------------------------------------------------
# WiFi sensor classes
# ---------------------------------------------------------------------------


class JuraWifiMachineStateSensor(JuraWifiEntity, SensorEntity):
    """Sensor reporting the raw @TM:08 machine state word as hex string."""

    _attr_icon = "mdi:state-machine"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device):
        super().__init__(device, "machine_state")
        self._attr_name = f"{device.name} Machine State"

    @property
    def native_value(self) -> str | None:
        sw = self.device.state_word
        return hex(sw) if self.device.connected else None

    def internal_update(self):
        if self.hass:
            self.async_write_ha_state()


class JuraWifiFirmwareSensor(JuraWifiEntity, SensorEntity):
    """Sensor reporting the WiFi firmware version string."""

    _attr_icon = "mdi:chip"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device):
        super().__init__(device, "firmware_version")
        self._attr_name = f"{device.name} Firmware Version"

    @property
    def native_value(self) -> str | None:
        fw = self.device.firmware_version
        return fw if fw else None

    def internal_update(self):
        if self.hass:
            self.async_write_ha_state()


class JuraWifiTemperatureSensor(JuraWifiEntity, SensorEntity):
    """Sensor reporting raw temperature from @TM:0A."""

    _attr_icon = "mdi:thermometer"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device):
        super().__init__(device, "temperature")
        self._attr_name = f"{device.name} Temperature"

    @property
    def native_value(self) -> int | None:
        return self.device.temperature

    def internal_update(self):
        if self.hass:
            self.async_write_ha_state()
