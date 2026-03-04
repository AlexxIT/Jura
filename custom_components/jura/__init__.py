import logging
from datetime import timedelta

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .core import DOMAIN
from .core.device import Device, EmptyModel, UnsupportedModel, get_machine
from .core.wifi_device import WifiDevice

_LOGGER = logging.getLogger(__name__)

# Platforms loaded for BLE entries
BLE_PLATFORMS = ["binary_sensor", "button", "number", "select", "switch", "sensor"]
# Platforms loaded for WiFi entries (read-only state sensors only)
WIFI_PLATFORMS = ["binary_sensor", "sensor"]

WIFI_POLL_INTERVAL = 30  # seconds


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    devices = hass.data.setdefault(DOMAIN, {})

    if entry.data.get("connection_type") == "wifi":
        return await _setup_wifi_entry(hass, entry, devices)

    return await _setup_ble_entry(hass, entry, devices)


async def _setup_wifi_entry(
    hass: HomeAssistant, entry: ConfigEntry, devices: dict
) -> bool:
    """Set up a WiFi-connected Jura machine."""
    data = entry.data
    device = WifiDevice(
        name=entry.title,
        host=data["host"],
        port=data.get("port", 51515),
        pin=data.get("pin", ""),
        device_name=data.get("device_name", "HomeAssistant"),
        auth_hash=data.get("auth_hash", ""),
    )
    devices[entry.entry_id] = device

    # Initial poll (best-effort; machine may be off)
    await device.async_update()

    await hass.config_entries.async_forward_entry_setups(entry, WIFI_PLATFORMS)

    async def _poll(_=None):
        await device.async_update()

    entry.async_on_unload(
        async_track_time_interval(
            hass, _poll, timedelta(seconds=WIFI_POLL_INTERVAL)
        )
    )

    async def _unload():
        await device.disconnect()

    entry.async_on_unload(_unload)
    return True


async def _setup_ble_entry(
    hass: HomeAssistant, entry: ConfigEntry, devices: dict
) -> bool:
    """Set up a BLE-connected Jura machine (original behaviour)."""

    @callback
    def update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        _LOGGER.debug(f"{change} {service_info.advertisement}")

        if device := devices.get(entry.entry_id):
            device.update_ble(service_info.advertisement)
            return

        try:
            machine = get_machine(service_info.advertisement.manufacturer_data[171])
        except EmptyModel:
            return
        except UnsupportedModel as e:
            _LOGGER.error("Unsupported model: %s", *e.args)
            return

        devices[entry.entry_id] = device = Device(
            entry.title,
            machine["model"],
            machine["products"],
            machine["alerts"],
            machine["key"],
            service_info.device,
        )
        device.update_ble(service_info.advertisement)

        hass.create_task(
            hass.config_entries.async_forward_entry_setups(entry, BLE_PLATFORMS)
        )

    # https://developers.home-assistant.io/docs/core/bluetooth/api/
    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            update_ble,
            {"address": entry.data["mac"], "manufacturer_id": 171, "connectable": True},
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    if entry.entry_id in hass.data[DOMAIN]:
        platforms = (
            WIFI_PLATFORMS
            if entry.data.get("connection_type") == "wifi"
            else BLE_PLATFORMS
        )
        await hass.config_entries.async_unload_platforms(entry, platforms)
    return True
