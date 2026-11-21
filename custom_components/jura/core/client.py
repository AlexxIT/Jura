import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from bleak import BLEDevice, BleakClient, BleakError
from bleak_retry_connector import establish_connection

from . import encryption

_LOGGER = logging.getLogger(__name__)

# keep the connection open this long after the last activity
ACTIVE_TIME = 120
# drop a queued fire-and-forget command if it was not sent within this time
COMMAND_TIME = 15
# the official app sends the heartbeat every 6 seconds (10 is too late)
HEARTBEAT_INTERVAL = 6
# main loop resolution
TICK = 1
# max time to wait for a queued read/write when the caller awaits it
OP_TIMEOUT = 30
# max time to wait for the connection when a read is requested
CONNECT_TIMEOUT = 20

HEARTBEAT = bytes([0x00, 0x7F, 0x80])


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


@dataclass
class Operation:
    """One GATT operation, executed by the connection loop."""

    uuid: str
    data: bytes | None = None  # None means read
    decrypt: bool = False
    # fire-and-forget commands are replaced by a newer one for the same uuid
    replaceable: bool = False
    expires: float = 0
    future: asyncio.Future | None = field(default=None, repr=False)

    @property
    def is_read(self) -> bool:
        return self.data is None


class Client:
    """BLE client.

    A single loop owns the GATT connection. Every read and write goes through
    a queue executed by this loop, so heartbeats, commands and polling never
    run concurrently on the connection.
    """

    def __init__(self, device: BLEDevice, callback: Callable = None, key: int = None):
        self.device = device
        self.callback = callback
        self.client: BleakClient | None = None
        self.loop = asyncio.get_running_loop()
        self.key = key

        self.ping_task: asyncio.Task | None = None
        self.ping_time = 0

        self.queue: deque[Operation] = deque()
        self.wake = asyncio.Event()
        self.connected = asyncio.Event()

    def ping(self):
        """Keep (or open) the connection for ACTIVE_TIME seconds."""
        self.ping_time = time.time() + ACTIVE_TIME

        if not self.ping_task:
            self.ping_task = self.loop.create_task(self._ping_loop())

    def ping_cancel(self):
        """Close the connection as soon as possible."""
        self.ping_time = 0
        self.wake.set()

    def send(self, data: bytes, uuid: str = UUIDs.START_PRODUCT):
        """Queue a fire-and-forget command.

        A newer command for the same characteristic replaces a pending one,
        and a command not sent within COMMAND_TIME seconds is dropped.
        """
        for op in list(self.queue):
            if op.replaceable and op.uuid == uuid:
                self.queue.remove(op)

        self.queue.append(
            Operation(
                uuid=uuid,
                data=bytes(data),
                replaceable=True,
                expires=time.time() + COMMAND_TIME,
            )
        )
        self.ping()
        self.wake.set()

    async def write(self, data: bytes, uuid: str, timeout: float = OP_TIMEOUT):
        """Queue a write and wait for its result. Raises on GATT error."""
        await self._run(Operation(uuid=uuid, data=bytes(data)), timeout)

    async def read(self, uuid: str, decrypt: bool = False, timeout: float = OP_TIMEOUT):
        """Queue a read and wait for its (optionally decrypted) value."""
        return await self._run(Operation(uuid=uuid, decrypt=decrypt), timeout)

    async def wait_connected(self, timeout: float = CONNECT_TIMEOUT) -> bool:
        """Open the connection if needed and wait until it is ready."""
        self.ping()
        try:
            await asyncio.wait_for(self.connected.wait(), timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def _run(self, op: Operation, timeout: float):
        op.future = self.loop.create_future()
        self.queue.append(op)
        self.ping()
        self.wake.set()
        return await asyncio.wait_for(op.future, timeout)

    async def _execute(self, op: Operation):
        if op.is_read:
            data = await self.client.read_gatt_char(op.uuid)
            if op.decrypt and self.key is not None:
                return encryption.encdec(list(data), self.key)
            return data

        await self.client.write_gatt_char(
            op.uuid, data=encrypt(op.data, self.key), response=True
        )
        return None

    async def _process_queue(self):
        while self.queue:
            op = self.queue.popleft()

            if op.future and op.future.done():
                continue  # caller gave up (timeout)

            if op.replaceable and time.time() > op.expires:
                _LOGGER.debug("command expired: %s", op)
                continue

            try:
                result = await self._execute(op)
            except Exception as e:
                if op.future:
                    op.future.set_exception(e)
                else:
                    _LOGGER.warning("command error: %s", op, exc_info=e)
                if not self.client or not self.client.is_connected:
                    raise
                continue

            if op.future:
                op.future.set_result(result)

    async def _heartbeat(self):
        # important dummy write to keep the connection
        # https://github.com/Jutta-Proto/protocol-bt-cpp?tab=readme-ov-file#heartbeat
        try:
            await self.client.write_gatt_char(
                UUIDs.P_MODE, data=encrypt(HEARTBEAT, self.key), response=True
            )
            _LOGGER.debug("heartbeat sent")
        except Exception as e:
            # we log as info as this is expected if the device is off
            _LOGGER.info("heartbeat error", exc_info=e)
            if not self.client.is_connected:
                raise

    async def _wait_tick(self):
        try:
            await asyncio.wait_for(self.wake.wait(), TICK)
        except asyncio.TimeoutError:
            pass
        self.wake.clear()

    async def _ping_loop(self):
        while time.time() < self.ping_time:
            try:
                self.client = await establish_connection(
                    BleakClient, self.device, self.device.address
                )
                self.connected.set()
                if self.callback:
                    self.callback(True)

                last_heartbeat = 0
                while time.time() < self.ping_time:
                    await self._process_queue()

                    if time.time() - last_heartbeat >= HEARTBEAT_INTERVAL:
                        await self._heartbeat()
                        last_heartbeat = time.time()

                    await self._wait_tick()
            except TimeoutError:
                pass
            except BleakError as e:
                _LOGGER.debug("ping error", exc_info=e)
            except Exception as e:
                _LOGGER.warning("ping error", exc_info=e)

            self.connected.clear()

            if self.client:
                try:
                    await self.client.disconnect()
                except Exception as e:
                    _LOGGER.debug("disconnect error", exc_info=e)
                self.client = None

            if self.callback:
                self.callback(False)

            await asyncio.sleep(1)

        self._fail_pending()
        self.ping_task = None

    def _fail_pending(self):
        while self.queue:
            op = self.queue.popleft()
            if op.future and not op.future.done():
                op.future.set_exception(ConnectionError("connection closed"))

    async def read_statistics_data(
        self, timeout: int = 20, retries: int = 30
    ) -> bytes | None:
        """Read statistics data from the device."""
        _LOGGER.debug("Reading Jura statistics...")

        if not await self.wait_connected(timeout):
            _LOGGER.debug("Failed to establish connection")
            return None

        try:
            # Send statistics request command
            # https://github.com/Jutta-Proto/protocol-bt-cpp?tab=readme-ov-file#writing-1
            await self.write(
                bytes([0x2A, 0x00, 0x01, 0xFF, 0xFF]), UUIDs.STATS_COMMAND
            )

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
        except Exception as e:
            _LOGGER.info("Error reading statistics", exc_info=e)
            return None

    async def read_machine_status(self) -> bytes | None:
        """Read machine status from the device."""
        _LOGGER.debug("Reading Jura machine status...")

        if not await self.wait_connected():
            _LOGGER.debug("Failed to establish connection")
            return None

        try:
            data = await self.read(UUIDs.MACHINE_STATUS, decrypt=True)
            _LOGGER.debug(f"Machine status data: {data}")
            return data
        except Exception as e:
            _LOGGER.warning("Error reading machine status", exc_info=e)
            return None


def encrypt(data: bytes | list, key: int) -> bytes:
    data = bytearray(data)
    data[0] = key
    return encryption.encdec(data, key)
