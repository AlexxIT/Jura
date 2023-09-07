import logging

from bleak import BleakClient

from .device import Device
from .encryption import encdec

_LOGGER = logging.getLogger(__name__)

DOMAIN = "jura"


async def start_product(device: Device) -> bool:
    command = device.command()
    data = encdec(command, device.key)

    for _ in range(4):
        try:
            async with BleakClient(device.mac) as client:
                _LOGGER.debug(f"start product {command.hex()} => {data.hex()}")
                await client.write_gatt_char(
                    "5a401525-ab2e-2548-c435-08c300000710", data, response=True
                )
                return True
        except:
            pass

    return False
