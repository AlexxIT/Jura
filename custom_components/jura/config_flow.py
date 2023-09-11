import voluptuous as vol
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow

from .core import DOMAIN


class FlowHandler(ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            mac = user_input["mac"]
            info = bluetooth.async_last_service_info(self.hass, mac)
            adv: bytes = info.manufacturer_data[info.manufacturer_id]
            user_input["adv"] = adv.hex()
            return self.async_create_entry(title="", data=user_input)

        devices = bluetooth.async_get_scanner(self.hass).discovered_devices
        macs = [v.address for v in devices if v.name == "TT214H BlueFrog"]

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("mac"): vol.In(macs),
                }
            ),
        )
