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


class UUIDs:
    """BLE characteristic UUIDs."""

    # https://github.com/Jutta-Proto/protocol-bt-cpp?tab=readme-ov-file#bluetooth-characteristics
    # Start product
    START_PRODUCT = "5a401525-ab2e-2548-c435-08c300000710"
    # Heartbeat
    P_MODE = "5a401529-ab2e-2548-c435-08c300000710"
    # Statistics
    STATS_COMMAND = "5a401533-ab2e-2548-c435-08c300000710"
    STATS_DATA = "5A401534-ab2e-2548-c435-08c300000710"
    # Status
    MACHINE_STATUS = "5a401524-ab2e-2548-c435-08c300000710"


class Client:
    def __init__(self, device: BLEDevice, callback: Callable = None, key: int = None):
        self.device = device
        self.callback = callback
        self.client: BleakClient | None = None
        self.loop = asyncio.get_running_loop()

        self.ping_future: asyncio.Future | None = None
        self.ping_task: asyncio.Task | None = None
        self.ping_time = 0
        self.key = key
        self.send_data = None
        self.send_time = 0
        self.send_uuid = None

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

    def send(self, data: bytes, uuid: str = UUIDs.START_PRODUCT):
        # if send loop active - we change sending data
        self.send_time = time.time() + COMMAND_TIME
        self.send_data = data
        self.send_uuid = uuid

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
                    if self.send_data:
                        if time.time() < self.send_time:
                            await self.client.write_gatt_char(
                                self.send_uuid,
                                data=encrypt(self.send_data, self.key),
                                response=True,
                            )
                        self.send_data = None

                    # important dummy write to keep the connection
                    # https://github.com/Jutta-Proto/protocol-bt-cpp?tab=readme-ov-file#heartbeat
                    heartbeat = [0x00, 0x7F, 0x80]
                    try:
                        await self.client.write_gatt_char(
                            UUIDs.P_MODE,
                            data=encrypt(heartbeat, self.key),
                            response=True,
                        )
                        _LOGGER.debug("heartbeat sent")
                    except Exception as e:
                        # we log as info as this is expected if the device is off
                        _LOGGER.info("heartbeat error", exc_info=e)

                    self.ping_future = self.loop.create_future()
                    # 10 is too late, 9 is ok
                    self.loop.call_later(9, self.ping_future.cancel)
                    try:
                        await self.ping_future
                    except asyncio.CancelledError:
                        pass

            except TimeoutError:
                pass
            except BleakError as e:
                _LOGGER.debug("ping error", exc_info=e)
            except Exception as e:
                _LOGGER.warning("ping error", exc_info=e)
            finally:
                # Disconnect here rather than on the happy path only: any exception
                # above would otherwise skip the disconnect, and dropping the
                # reference orphans the BleakClient and its D-Bus connection.
                client, self.client = self.client, None
                if client is not None:
                    try:
                        await client.disconnect()
                    except Exception as e:
                        _LOGGER.debug("disconnect error", exc_info=e)
                if self.callback:
                    self.callback(False)
                await asyncio.sleep(1)

        self.ping_task = None

    async def read(self, uuid: str, decrypt: bool = False):
        """Read data from a characteristic."""
        if not self.client:
            _LOGGER.warning("Cannot read: No active client connection")
            return None

        try:
            data = await self.client.read_gatt_char(uuid)
            if decrypt and self.key:
                return encryption.encdec(list(data), self.key)
            return data
        except BleakError as e:
            _LOGGER.info(f"Error reading from characteristic {uuid}", exc_info=e)
            raise
        except Exception as e:
            _LOGGER.info(f"Error reading from characteristic {uuid}", exc_info=e)
            raise

    async def read_statistics_data(
        self, timeout: int = 20, retries: int = 30
    ) -> bytes | None:
        """Read statistics data from the device."""
        _LOGGER.debug("Reading Jura statistics...")

        # Send statistics request command
        # https://github.com/Jutta-Proto/protocol-bt-cpp?tab=readme-ov-file#writing-1
        command_bytes = [0x2A, 0x00, 0x01, 0xFF, 0xFF]
        self.send(bytes(command_bytes), uuid=UUIDs.STATS_COMMAND)

        # Wait for connection
        if not self.client:
            for _ in range(timeout):
                if not self.client:
                    await asyncio.sleep(1)
                else:
                    break
            if not self.client:
                _LOGGER.debug("Failed to establish connection")
                return None

        # Wait for statistics to be ready
        # https://github.com/Jutta-Proto/protocol-bt-cpp?tab=readme-ov-file#reading
        for _ in range(retries):
            status = await self.read(UUIDs.STATS_COMMAND)
            if status and status[1] != 225:  # 225 means not ready
                break
            await asyncio.sleep(0.8)
        else:
            _LOGGER.error("Device not ready for statistics reading")
            return None

        # Read statistics data
        # https://github.com/Jutta-Proto/protocol-bt-cpp?tab=readme-ov-file#statistics-data
        return await self.read(UUIDs.STATS_DATA, decrypt=True)

    async def read_machine_status(self) -> bytes | None:
        """Read machine status from the device."""
        _LOGGER.debug("Reading Jura machine status...")

        # Wait for connection
        if not self.client:
            self.ping()
            for _ in range(20):
                if not self.client:
                    await asyncio.sleep(1)
                else:
                    break
            if not self.client:
                _LOGGER.debug("Failed to establish connection")
                return None

        try:
            data = await self.read(UUIDs.MACHINE_STATUS, decrypt=True)
            if data:
                _LOGGER.debug(f"Machine status data: {data}")
                return data
        except Exception as e:
            _LOGGER.warning("Error reading machine status", exc_info=e)
            return None

        return None


def encrypt(data: bytes | list, key: int) -> bytes:
    data = bytearray(data)
    data[0] = key
    return encryption.encdec(data, key)
