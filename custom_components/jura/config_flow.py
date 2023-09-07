import voluptuous as vol
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow

from .core import DOMAIN


class FlowHandler(ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
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
