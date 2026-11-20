import asyncio
import time

from custom_components.jura.core import client as client_module
from custom_components.jura.core.client import HEARTBEAT, Client, UUIDs, encrypt
from custom_components.jura.core.encryption import encdec

KEY = 0x2A


class FakeBleakClient:
    """Records GATT operations, answers reads with encrypted payloads."""

    def __init__(self, reads: dict[str, bytes] = None):
        self.ops: list[tuple] = []
        self.reads = reads or {}
        self.is_connected = True
        self.busy = False

    async def _io(self):
        # detect concurrent GATT access
        assert not self.busy, "concurrent GATT operation"
        self.busy = True
        await asyncio.sleep(0)
        self.busy = False

    async def write_gatt_char(self, uuid, data, response=False):
        await self._io()
        self.ops.append(("write", uuid, encdec(data, KEY)))

    async def read_gatt_char(self, uuid):
        await self._io()
        self.ops.append(("read", uuid))
        return encdec(self.reads[uuid], KEY)

    async def disconnect(self):
        self.is_connected = False


def run(coro):
    return asyncio.run(coro)


def make_client(fake: FakeBleakClient, monkeypatch) -> Client:
    async def establish_connection(*args, **kwargs):
        return fake

    monkeypatch.setattr(client_module, "establish_connection", establish_connection)
    monkeypatch.setattr(client_module, "TICK", 0.01)

    class Device:
        address = "00:11:22:33:44:55"

    return Client(Device(), key=KEY)


def test_encrypt_sets_key():
    data = encrypt(bytes([0x00, 0x7F, 0x80]), KEY)
    assert encdec(data, KEY) == bytes([KEY, 0x7F, 0x80])


def test_send_replaces_pending_command(monkeypatch):
    async def main():
        client = make_client(FakeBleakClient(), monkeypatch)
        client.ping = lambda: None
        client.send(b"\x00\x01")
        client.send(b"\x00\x02")
        client.send(b"\x00\x03", uuid=UUIDs.P_MODE)
        return [(op.uuid, op.data) for op in client.queue]

    assert run(main()) == [
        (UUIDs.START_PRODUCT, b"\x00\x02"),
        (UUIDs.P_MODE, b"\x00\x03"),
    ]


def test_loop_serializes_operations(monkeypatch):
    status = bytes([KEY]) + bytes.fromhex("00040000040008000000000000000000000007")
    fake = FakeBleakClient(reads={UUIDs.MACHINE_STATUS: status})

    async def main():
        client = make_client(fake, monkeypatch)
        client.send(b"\x00\x28\x00")
        data = await client.read_machine_status()
        await client.write(b"\x00\x47\xff", UUIDs.P_MODE)
        client.ping_cancel()
        await client.ping_task if client.ping_task else None
        return data

    data = run(main())
    assert data == status

    # first heartbeat comes after the queued product command
    assert fake.ops[0] == ("write", UUIDs.START_PRODUCT, bytes([KEY, 0x28, 0x00]))
    assert ("write", UUIDs.P_MODE, bytes([KEY]) + HEARTBEAT[1:]) in fake.ops
    assert ("read", UUIDs.MACHINE_STATUS) in fake.ops
    assert fake.ops[-1] == ("write", UUIDs.P_MODE, bytes([KEY, 0x47, 0xFF]))


def test_expired_command_is_dropped(monkeypatch):
    fake = FakeBleakClient()

    async def main():
        client = make_client(fake, monkeypatch)
        client.ping = lambda: None
        client.send(b"\x00\x28")
        client.queue[0].expires = time.time() - 1
        client.client = fake
        await client._process_queue()

    run(main())
    assert fake.ops == []


def test_write_error_is_raised_to_caller(monkeypatch):
    fake = FakeBleakClient()

    async def failing_write(uuid, data, response=False):
        raise client_module.BleakError("write not permitted")

    fake.write_gatt_char = failing_write

    async def main():
        client = make_client(fake, monkeypatch)
        client.ping = lambda: None
        client.client = fake
        task = asyncio.ensure_future(client.write(b"\x00\x47\x01", UUIDs.P_MODE))
        await asyncio.sleep(0)
        await client._process_queue()
        try:
            await task
        except client_module.BleakError as e:
            return str(e)

    assert run(main()) == "write not permitted"
