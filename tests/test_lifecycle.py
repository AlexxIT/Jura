import asyncio

from bleak import BLEDevice

from custom_components.jura.core import client as client_module
from custom_components.jura.core.client import Client


class FakeBleakClient:
    def __init__(self):
        self.disconnected = False

    async def write_gatt_char(self, *args, **kwargs):
        pass

    async def disconnect(self):
        self.disconnected = True


def test_client_async_stop(monkeypatch):
    fake = FakeBleakClient()

    async def establish_connection(*args, **kwargs):
        return fake

    monkeypatch.setattr(client_module, "establish_connection", establish_connection)

    async def main():
        client = Client(BLEDevice("AA:BB:CC:DD:EE:FF", None, None), key=42)
        client.loop = asyncio.get_event_loop()

        client.ping()
        task = client.ping_task
        for _ in range(100):
            if client.client:
                break
            await asyncio.sleep(0.01)
        assert client.client is fake

        await client.async_stop()
        assert task.done()
        assert client.ping_task is None
        assert client.client is None
        assert fake.disconnected

        # no new connections after stop
        client.ping()
        assert client.ping_task is None

    asyncio.run(main())


def test_client_async_stop_idle():
    async def main():
        client = Client(BLEDevice("AA:BB:CC:DD:EE:FF", None, None), key=42)
        await client.async_stop()
        assert client.ping_task is None

    asyncio.run(main())
