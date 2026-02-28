import asyncio
import logging
import time
from typing import Callable

from bleak import BLEDevice, BleakClient, BleakError
from bleak_retry_connector import establish_connection

from . import encryption
from enum import Enum

_LOGGER = logging.getLogger(__name__)

ACTIVE_TIME = 120
COMMAND_TIME = 15


class UUIDs(Enum):
    """BLE characteristic UUIDs."""

    # https://github.com/Jutta-Proto/protocol-bt-cpp?tab=readme-ov-file#bluetooth-characteristics
    # Start product
    START_PRODUCT = "5A401525-AB2E-2548-C435-08C300000710"
    # Heartbeat
    P_MODE = "5A401529-AB2E-2548-C435-08C300000710"
    # Statistics command
    STATS_COMMAND = "5A401533-AB2E-2548-C435-08C300000710"
    # Statistics data
    STATS_DATA = "5A401534-AB2E-2548-C435-08C300000710"
    # Status (alerts)
    MACHINE_STATUS = "5a401524-AB2E-2548-C435-08C300000710"
    # Manufacturer data
    MANUFACTURER_DATA = "5a401531-AB2E-2548-C435-08C300000710"
    # Heartbeat read
    HEARTBEAT_READ = "5A401538-AB2E-2548-C435-08C300000710"

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

    @property
    def connected(self):
        return self.client is not None and self.client.is_connected

    def ping(self):
        self.ping_time = time.time() + ACTIVE_TIME

        if not self.ping_task:
            self.ping_task = self.loop.create_task(self._ping_loop())

    async def ping_cancel(self):
        # stop ping time
        self.ping_time = 0

        # cancel ping sleep timer
        if self.ping_future:
            self.ping_future.cancel()

        self.client = None
        self.callback(False)

    def send(self, data: bytes):
        # if send loop active - we change sending data
        self.send_time = time.time() + COMMAND_TIME
        self.send_data = data

        # refresh ping time
        self.ping()

    async def wait_for_connection(self):
        retries = 0
        while not (self.client and self.connected and retries < 5):
            retries += 1
            try:
                self.client = await establish_connection(BleakClient, self.device, self.device.address)
                self.ping()
                return
            except Exception as exc:
                _LOGGER.debug("Connection error", exc_info=exc)
                await asyncio.sleep(1)
                logging.debug("Not connected, retrying in 5 seconds")
                self._client = None
                await asyncio.sleep(5)
                return
        return None

    async def _ping_loop(self):
        while time.time() < self.ping_time:
            try:
                await self.wait_for_connection()
                if self.callback:
                    self.callback(True)

                # heartbeat loop
                while time.time() < self.ping_time:
                    if self.send_data:
                        if time.time() < self.send_time:
                            await self.write_gatt(characteristic=UUIDs.START_PRODUCT, data=self.send_data)
                        self.send_data = None

                    try:
                        _LOGGER.debug(f"Pinging")
                        async with asyncio.timeout(5):
                            await self.client.read_gatt_char(UUIDs.HEARTBEAT_READ.value)
                            _LOGGER.debug("Heartbeat received")
                    except Exception as e:
                        _LOGGER.debug("heartbeat error, trying to reconnect")
                        self.client = None
                        await self.wait_for_connection()

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
                self.client = None
                if self.callback:
                    self.callback(False)
                await asyncio.sleep(1)

        self.ping_task = None

    async def read_data_until_ready(
            self,  characteristic: UUIDs, check_pos: int, check_value_not: int | None = None, max_attempts: int=30
    ) -> bytes | None:
        """ Read data from a characteristic until byte in position 'check_pos' is not 'check_value_not'."""
        attempts=0

        while attempts < max_attempts:
            try:
                await self.wait_for_connection()
                async with asyncio.timeout(10):
                    data = await self.client.read_gatt_char(characteristic.value)
                decrypted = encryption.encdec(data, self.key)
                _LOGGER.debug(f"Read data from {characteristic.name} ({characteristic.value}):")
                _LOGGER.debug(f"Encrypted: {' '.join(f'{b:02x}' for b in data)}")
                _LOGGER.debug(f"Decrypted: {' '.join(f'{b:02x}' for b in decrypted)}")
                if (check_value_not is None) or (len(decrypted) > check_pos and decrypted[check_pos] != check_value_not):
                    return decrypted
            except Exception:
                _LOGGER.debug(f"Error reading {characteristic.name} ({characteristic.value})", exc_info=True)
                pass
            attempts += 1
            await asyncio.sleep(0.8)
        return None

    async def write_gatt(self, characteristic: UUIDs, data: bytes, max_attempts: int=30):
        attempts=0

        encrypted=encrypt(bytes(data), self.key)
        while attempts < max_attempts:
            try:
                await self.wait_for_connection()
                async with asyncio.timeout(5):
                    await self.client.write_gatt_char(characteristic.value, encrypted, response=True)
                    _LOGGER.debug(f"Wrote {' '.join(f'{b:02x}' for b in data)} to {characteristic.name} ({characteristic.value}) (encypted as {' '.join(f'{b:02x}' for b in encrypted)})")
                return None
            except Exception:
                pass
            attempts += 1
            await asyncio.sleep(0.8)
        return None

    async def read_statistics_data(self, command_bytes: bytes) -> bytes | None:
        """Read statistics data from the device."""
        _LOGGER.debug("Reading Jura statistics from device...")
        # Request statistics
        await self.write_gatt(characteristic=UUIDs.STATS_COMMAND, data=command_bytes)
        # Wait until statistics are ready
        await self.read_data_until_ready(characteristic=UUIDs.STATS_COMMAND, check_pos=0, check_value_not=self.key)
        # Read statistics data
        result = await self.read_data_until_ready(characteristic=UUIDs.STATS_DATA, check_pos=0)
        return result

    async def read_machine_status(self) -> bytes | None:
        """Read machine status from the device."""
        _LOGGER.debug("Reading Jura machine status (alerts)...")

        # Alerts are sometimes wrong, let's read them multiple times to make sure that there are no errors.
        check1 = await self.read_data_until_ready(characteristic=UUIDs.MACHINE_STATUS, check_pos=0)
        await asyncio.sleep(1)

        for _ in range(3):
            result = await self.read_data_until_ready(characteristic=UUIDs.MACHINE_STATUS, check_pos=0)
            await asyncio.sleep(1)
            if result != check1:
                _LOGGER.debug("Machine status (alerts) incorrect, ignoring.")
                return None

        return result

def encrypt(data: bytes | list, key: int) -> bytes:
    data = bytearray(data)
    data[0] = key
    return encryption.encdec(data, key)
