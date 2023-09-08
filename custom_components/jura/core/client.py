import asyncio
import time

from bleak import BleakClient

from .encryption import encdec

ACTIVE_TIME = 2 * 60
COMMAND_TIME = 15


class Client:
    def __init__(self, mac: str, key: int):
        self.client = BleakClient(mac)
        self.key = key

        self.ping_task = None
        self.ping_time = 0

        self.send_coro = None
        self.send_task = None
        self.send_time = 0

    def ping(self):
        self.ping_time = time.time() + ACTIVE_TIME

        if not self.ping_task:
            self.ping_task = asyncio.create_task(self._ping_loop())

    def send(self, data: bytearray):
        self.ping()

        data[0] = self.key
        data = encdec(data, self.key)

        # if send loop active - we change sending data
        self.send_time = time.time() + COMMAND_TIME
        self.send_coro = self.client.write_gatt_char(
            "5a401525-ab2e-2548-c435-08c300000710", data, response=True
        )

        if not self.send_task:
            self.send_task = asyncio.create_task(self._send_loop())

    async def _ping_loop(self):
        data = bytes([self.key, 0x7F, 0x80])
        data = encdec(data, self.key)

        # reconnection loop
        while time.time() < self.ping_time:
            try:
                await self.client.connect()

                # heartbeat loop
                while time.time() < self.ping_time:
                    await asyncio.sleep(10)
                    await self.client.write_gatt_char(
                        "5a401529-ab2e-2548-c435-08c300000710",
                        data,
                        response=True,
                    )

                await self.client.disconnect()
            except:
                await asyncio.sleep(1)

        self.ping_task = None

    async def _send_loop(self):
        while time.time() < self.send_time:
            if self.client.is_connected:
                try:
                    await self.send_coro
                    break  # stop if OK
                except:
                    pass  # continue if not

            await asyncio.sleep(1)

        self.send_task = None
