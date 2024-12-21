import asyncio
import logging
import time
from typing import Callable

from bleak import BLEDevice, BleakClient, BleakError
from bleak_retry_connector import establish_connection

from . import encryption

_LOGGER = logging.getLogger(__name__)

ACTIVE_TIME = 120
COMMAND_TIME = 15


class Client:
    def __init__(self, device: BLEDevice, callback: Callable = None):
        self.device = device
        self.callback = callback

        self.client: BleakClient | None = None
        self.loop = asyncio.get_running_loop()

        self.ping_future: asyncio.Future | None = None
        self.ping_task: asyncio.Task | None = None
        self.ping_time = 0

        self.send_data = None
        self.send_time = 0

    def ping(self):
        self.ping_time = time.time() + ACTIVE_TIME

        if not self.ping_task:
            self.ping_task = self.loop.create_task(self._ping_loop())

    def ping_cancel(self):
        # stop ping time
        self.ping_time = 0

        # cancel ping sleep timer
        if self.ping_future:
            self.ping_future.cancel()

    def send(self, data: bytes):
        # if send loop active - we change sending data
        self.send_time = time.time() + COMMAND_TIME
        self.send_data = data

        # refresh ping time
        self.ping()

        # cancel ping sleep timer
        if self.ping_future:
            self.ping_future.cancel()

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
                    # important dummy read for keep connection
                    data = await self.client.read_gatt_char(
                        "5a401531-ab2e-2548-c435-08c300000710"
                    )
                    key = data[0]

                    if self.send_data:
                        if time.time() < self.send_time:
                            await self.client.write_gatt_char(
                                "5a401525-ab2e-2548-c435-08c300000710",
                                data=encrypt(self.send_data, key),
                                response=True,
                            )
                        self.send_data = None

                    # asyncio.sleep(10) with cancel
                    self.ping_future = self.loop.create_future()
                    self.loop.call_later(10, self.ping_future.cancel)
                    try:
                        await self.ping_future
                    except asyncio.CancelledError:
                        pass

                await self.client.disconnect()
            except TimeoutError:
                pass
            except BleakError as e:
                _LOGGER.debug("ping error", exc_info=e)
            except Exception as e:
                _LOGGER.warning("ping error", exc_info=e)
            finally:
                self.client = None
                if self.callback:
                    self.callback(False)
                await asyncio.sleep(1)

        self.ping_task = None


def encrypt(data: bytes, key: int) -> bytes:
    data = bytearray(data)
    data[0] = key
    return encryption.encdec(data, key)
