"""Config flow for the Jura integration.

Supports two connection types:
- BLE: existing Bluetooth flow (select MAC from discovered devices)
- WiFi: UDP auto-discovery + manual IP entry, then auth hash entry
"""

import asyncio
import logging

import voluptuous as vol
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlow

from .core import DOMAIN
from .core.discovery import discover_machines

_LOGGER = logging.getLogger(__name__)

CONNECTION_TYPE_BLE = "ble"
CONNECTION_TYPE_WIFI = "wifi"
_MANUAL_IP = "manual"


class FlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a Jura config flow."""

    VERSION = 1

    def __init__(self):
        self._wifi_host: str = ""
        self._discovered: list[dict] = []

    async def async_step_user(self, user_input=None):
        """Step 1: choose BLE or WiFi."""
        if user_input is not None:
            conn_type = user_input.get("connection_type", CONNECTION_TYPE_BLE)
            if conn_type == CONNECTION_TYPE_WIFI:
                return await self.async_step_wifi_discover()
            return await self.async_step_ble()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "connection_type", default=CONNECTION_TYPE_BLE
                    ): vol.In([CONNECTION_TYPE_BLE, CONNECTION_TYPE_WIFI])
                }
            ),
        )

    # ------------------------------------------------------------------
    # BLE path (unchanged from original)
    # ------------------------------------------------------------------

    async def async_step_ble(self, user_input=None):
        """BLE: pick from discovered Bluetooth devices."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["mac"],
                data={"connection_type": CONNECTION_TYPE_BLE, "mac": user_input["mac"]},
            )

        devices = bluetooth.async_get_scanner(self.hass).discovered_devices
        macs = [v.address for v in devices if v.name == "TT214H BlueFrog"]

        return self.async_show_form(
            step_id="ble",
            data_schema=vol.Schema({vol.Required("mac"): vol.In(macs)}),
        )

    # ------------------------------------------------------------------
    # WiFi path
    # ------------------------------------------------------------------

    async def async_step_wifi_discover(self, user_input=None):
        """WiFi step 1: run UDP discovery and let the user pick a machine."""
        if user_input is not None:
            host = user_input.get("host", _MANUAL_IP)
            if host == _MANUAL_IP:
                return await self.async_step_wifi_manual()
            self._wifi_host = host
            return await self.async_step_wifi_auth()

        try:
            self._discovered = await asyncio.wait_for(
                discover_machines(timeout=5.0), timeout=6.0
            )
            _LOGGER.debug("WiFi discovery found %d machine(s)", len(self._discovered))
        except Exception as e:
            _LOGGER.warning("WiFi discovery failed: %s", e)
            self._discovered = []

        host_options: dict[str, str] = {
            m["ip"]: f"{m.get('name', m['ip'])} ({m['ip']})"
            for m in self._discovered
        }
        host_options[_MANUAL_IP] = "Enter IP address manually"

        return self.async_show_form(
            step_id="wifi_discover",
            data_schema=vol.Schema({vol.Required("host"): vol.In(host_options)}),
        )

    async def async_step_wifi_manual(self, user_input=None):
        """WiFi step 1b: manually enter machine IP address."""
        if user_input is not None:
            self._wifi_host = user_input["host"]
            return await self.async_step_wifi_auth()

        return self.async_show_form(
            step_id="wifi_manual",
            data_schema=vol.Schema({vol.Required("host"): str}),
        )

    async def async_step_wifi_auth(self, user_input=None):
        """WiFi step 2: enter auth credentials (auth hash from J.O.E. app pairing)."""
        if user_input is not None:
            return self.async_create_entry(
                title=f"Jura WiFi ({self._wifi_host})",
                data={
                    "connection_type": CONNECTION_TYPE_WIFI,
                    "host": self._wifi_host,
                    "port": user_input.get("port", 51515),
                    "pin": user_input.get("pin", ""),
                    "auth_hash": user_input.get("auth_hash", ""),
                    "device_name": user_input.get("device_name", "HomeAssistant"),
                },
            )

        return self.async_show_form(
            step_id="wifi_auth",
            data_schema=vol.Schema(
                {
                    vol.Required("auth_hash"): str,
                    vol.Optional("pin", default=""): str,
                    vol.Optional("device_name", default="HomeAssistant"): str,
                    vol.Optional("port", default=51515): int,
                }
            ),
        )
