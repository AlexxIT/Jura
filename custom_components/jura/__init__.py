from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .core import DOMAIN
from .core.device import Device

PLATFORMS = ["button", "number", "select"]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    mac = config_entry.data["mac"]

    device = bluetooth.async_ble_device_from_address(hass, mac)
    if not device:
        raise ConfigEntryNotReady("MAC not found")

    try:
        adv = device.metadata["manufacturer_data"][171]
    except:
        raise ConfigEntryNotReady("BLE not found")

    devices = hass.data.setdefault(DOMAIN, {})
    devices[config_entry.entry_id] = Device(config_entry.title, mac, adv)

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
    return True
