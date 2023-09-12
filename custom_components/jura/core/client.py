import asyncio
import logging
import time
from typing import Callable

from bleak import BleakClient, BLEDevice, BleakError
from bleak_retry_connector import establish_connection

_LOGGER = logging.getLogger(__name__)

ACTIVE_TIME = 120
COMMAND_TIME = 15


class Client:
    def __init__(self, device: BLEDevice, callback: Callable = None):
        self.device = device
        self.callback = callback

        self.client: BleakClient | None = None

        self.ping_task = None
        self.ping_time = 0

        self.send_data = None
        self.send_task = None
        self.send_time = 0

    def ping(self):
        self.ping_time = time.time() + ACTIVE_TIME

        if not self.ping_task:
            self.ping_task = asyncio.create_task(self._ping_loop())

    def send(self, data: bytes):
        self.ping()

        # if send loop active - we change sending data
        self.send_time = time.time() + COMMAND_TIME
        self.send_data = data

        if not self.send_task:
            self.send_task = asyncio.create_task(self._send_loop())

    async def _ping_loop(self):
        while time.time() < self.ping_time:
            try:
                self.client = await establish_connection(
                    BleakClient, self.device, self.device.address
                )
                if self.callback:
                    self.callback(True)

                # heartbeat loop
                while time.time() < self.ping_time:
                    await asyncio.sleep(10)

                    # important dummy read for keep connection
                    await self.client.read_gatt_char(
                        "5a401531-ab2e-2548-c435-08c300000710"
                    )

                await self.client.disconnect()
            except (TimeoutError, BleakError):
                pass
            except Exception as e:
                _LOGGER.warning("ping error", exc_info=e)
            finally:
                self.client = None
                if self.callback:
                    self.callback(False)
                await asyncio.sleep(1)

        self.ping_task = None

    async def _send_loop(self):
        while time.time() < self.send_time:
            if self.client and self.client.is_connected:
                try:
                    await self.client.write_gatt_char(
                        "5a401525-ab2e-2548-c435-08c300000710",
                        self.send_data,
                        response=True,
                    )
                    break  # stop if OK
                except Exception as e:
                    _LOGGER.warning(f"send error", exc_info=e)

            await asyncio.sleep(0.5)

        self.send_task = None
