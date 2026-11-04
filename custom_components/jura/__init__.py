import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady

from .core import DOMAIN
from .core.device import Device, EmptyModel, UnsupportedModel, get_machine

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "button", "number", "select", "switch", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    devices = hass.data.setdefault(DOMAIN, {})
    mac = entry.data["mac"]

    @callback
    def update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        _LOGGER.debug(f"{change} {service_info.advertisement}")
        if device := devices.get(entry.entry_id):
            device.update_ble(service_info)

    # https://developers.home-assistant.io/docs/core/bluetooth/api/
    # ACTIVE mode with an address also makes AUTO mode scanners scan actively
    # for this device; the model is only sent in the scan response
    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            update_ble,
            {"address": mac, "manufacturer_id": 171, "connectable": True},
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
    )

    service_info = bluetooth.async_last_service_info(hass, mac, connectable=True)
    if service_info and 171 not in service_info.manufacturer_data:
        # HA 2026.8+: on-demand active sweep instead of waiting for the next one
        if request_active_scan := getattr(bluetooth, "async_request_active_scan", None):
            await request_active_scan(hass)
            service_info = bluetooth.async_last_service_info(
                hass, mac, connectable=True
            )

    if not service_info:
        raise ConfigEntryNotReady(f"Jura {mac} not seen by a connectable scanner yet")
    if 171 not in service_info.manufacturer_data:
        raise ConfigEntryNotReady(
            f"Jura {mac} seen without model data, waiting for an active scan"
        )

    try:
        machine = get_machine(service_info.manufacturer_data[171])
    except EmptyModel:
        _LOGGER.debug(f"Empty model in advertisement: {service_info.advertisement}")
        raise ConfigEntryNotReady(f"Jura {mac} advertised an empty model")
    except UnsupportedModel as e:
        _LOGGER.error("Unsupported model: %s", *e.args)
        return False

    devices[entry.entry_id] = device = Device(
        entry.title,
        machine["model"],
        machine["products"],
        machine["alerts"],
        machine["key"],
        service_info.device,
    )
    device.update_ble(service_info)
    device.client.ble_device_callback = lambda: bluetooth.async_ble_device_from_address(
        hass, mac, connectable=True
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and (device := hass.data[DOMAIN].pop(entry.entry_id, None)):
        await device.client.async_stop()
    return unload_ok
