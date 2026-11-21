import logging
from datetime import timedelta

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval

from .core import DOMAIN
from .core.device import Device, EmptyModel, UnsupportedModel, get_machine

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "button", "number", "select", "switch", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    devices = hass.data.setdefault(DOMAIN, {})

    @callback
    def update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        _LOGGER.debug(f"{change} {service_info.advertisement}")

        if device := devices.get(entry.entry_id):
            device.update_ble(service_info.advertisement)
            return

        # a passive scanner (Shelly...) never gets the scan response with the
        # manufacturer data: use the last advertisement of a connectable one
        service_info = (
            bluetooth.async_last_service_info(hass, entry.data["mac"]) or service_info
        )
        if 171 not in service_info.advertisement.manufacturer_data:
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
            hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        )

    # https://developers.home-assistant.io/docs/core/bluetooth/api/
    # HA only dispatches the advertisements of the scanner that "owns" the
    # machine, often a passive one (Shelly...): listen to all scanners
    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            update_ble,
            {"address": entry.data["mac"], "connectable": False},
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
    )

    # HA does not dispatch unchanged advertisements: until the machine is
    # found, also check the connectable advertisements periodically
    @callback
    def discovery(_now) -> None:
        if entry.entry_id not in devices and (
            info := bluetooth.async_last_service_info(hass, entry.data["mac"])
        ):
            update_ble(info, bluetooth.BluetoothChange.ADVERTISEMENT)

    entry.async_on_unload(
        async_track_time_interval(hass, discovery, timedelta(seconds=5))
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    if entry.entry_id in hass.data[DOMAIN]:
        await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    return True
