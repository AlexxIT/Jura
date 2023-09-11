from homeassistant.components import bluetooth
from homeassistant.components.bluetooth.match import ADDRESS, CONNECTABLE
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback

from .core import DOMAIN
from .core.device import Device

PLATFORMS = ["binary_sensor", "button", "number", "select"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    devices = hass.data.setdefault(DOMAIN, {})
    devices[entry.entry_id] = device = Device(
        entry.title, entry.data["mac"], bytes.fromhex(entry.data["adv"])
    )

    @callback
    def _async_update_ble(
        service_info: bluetooth.BluetoothServiceInfoBleak,
        change: bluetooth.BluetoothChange,
    ) -> None:
        device.update_ble(service_info.rssi)

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _async_update_ble,
            {ADDRESS: device.mac, CONNECTABLE: True},
            bluetooth.BluetoothScanningMode.ACTIVE,
        )
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    return True
