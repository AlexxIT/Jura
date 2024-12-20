from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypedDict
from zipfile import ZipFile

import xmltodict
from bleak import AdvertisementData, BLEDevice

from .client import Client

SELECTS = [
    "product",  # 1
    "grinder_ratio",  # 2
    "coffee_strength",  # 3
    "temperature",  # 7
]

NUMBERS = [
    "water_amount",  # 4
    "milk_amount",  # 5
    "milk_foam_amount",  # 6
    "bypass",  # 10
    "milk_break",  # 11
]


class Attribute(TypedDict, total=False):
    options: list[str]
    default: str

    min: int
    max: int
    step: int
    value: int

    is_on: bool
    extra: dict


class Device:
    def __init__(self, name: str, device: BLEDevice, advertisment: AdvertisementData):
        manufacturer = advertisment.manufacturer_data[171]
        number = str(int.from_bytes(manufacturer[4:6], "little"))

        self.name = name

        self.client = Client(device, self.set_connected)

        self.connected = False
        self.conn_info = {"mac": device.address}

        machine = get_machine(number)
        assert machine, manufacturer.hex()
        self.model = machine["model"]
        self.products = machine["products"]
        self.options = get_options(self.products)

        self.product = None
        self.values = None
        self.updates_connect: list = []
        self.updates_product: list = []

        self.update_ble(advertisment)

    @property
    def mac(self) -> str:
        return self.client.device.address

    def register_update(self, attr: str, handler: Callable):
        if attr == "product":
            return
        elif attr == "connection":
            self.updates_connect.append(handler)
        else:
            self.updates_product.append(handler)

    def update_ble(self, advertisment: AdvertisementData):
        self.conn_info["last_seen"] = datetime.now(timezone.utc)
        self.conn_info["rssi"] = advertisment.rssi

        for handler in self.updates_connect:
            handler()

    def set_connected(self, connected: bool):
        self.connected = connected

        for handler in self.updates_connect:
            handler()

    def selects(self) -> list[str]:
        products = str(self.products).lower()
        return [k for k in SELECTS if k in products]

    def numbers(self) -> list[str]:
        products = str(self.products).lower()
        return [k for k in NUMBERS if k in products]

    def attribute(self, attr: str) -> Attribute:
        if attr == "product":
            return Attribute(
                options=[
                    i["@Name"] for i in self.products if i.get("@Active") != "false"
                ],
                default=self.product["@Name"] if self.product else None,
            )

        if attr == "connection":
            return Attribute(is_on=self.connected, extra=self.conn_info)

        attribute = self.product and self.product.get(attr.upper())
        if not attribute:
            return {"options": self.options[attr]} if attr in self.options else {}

        if "@Value" in attribute:
            return Attribute(
                min=int(attribute["@Min"]),
                max=int(attribute["@Max"]),
                step=int(attribute["@Step"]),
                value=int(attribute["@Value"]),
            )

        default = attribute["@Default"]
        return Attribute(
            options=[i["@Name"] for i in attribute["ITEM"]],
            default=next(
                i["@Name"] for i in attribute["ITEM"] if i["@Value"] == default
            ),
        )

    def select_option(self, attr: str, option: str):
        if attr == "product":
            self.select_product(option)
            return

        attribute = self.product and self.product.get(attr.upper())
        if not attribute:
            return None

        value = next(i["@Value"] for i in attribute["ITEM"] if i["@Name"] == option)
        self.set_value(attr, int(value, 16))

    def set_value(self, attr: str, value: int):
        self.client.ping()

        self.values[attr] = value

    def select_product(self, product: str):
        self.client.ping()

        self.product = next(i for i in self.products if i["@Name"] == product)
        self.values = {}

        # dispatch to all listeners
        for handler in self.updates_product:
            handler()

    def start_product(self):
        if self.product:
            self.client.send(self.command())

    def command(self) -> bytes:
        data = bytearray(18)

        # set product
        data[1] = int(self.product["@Code"], 16)

        for attr in SELECTS + NUMBERS:
            attribute = self.product and self.product.get(attr.upper())
            if not attribute:
                continue

            if attr in self.values:
                # set user's value
                value = self.values[attr]
            elif "@Value" in attribute:
                # set default int value
                value = int(attribute["@Value"])
            else:
                # set default list value
                value = int(attribute["@Default"], 16)

            if step := int(attribute.get("@Step", 0)):
                value = int(value / step)

            pos = int(attribute["@Argument"][1:])
            data[pos] = value

        # additional data (some unknown)
        # data[0] = self.key
        # data[9] = 1
        # data[16] = 6
        # data[17] = self.key

        return data


def get_machine(number: str) -> dict | None:
    path = Path(__file__).parent / "resources.zip"
    with ZipFile(path) as f:
        number = number.encode()
        with f.open("JOE_MACHINES.TXT") as txt:
            try:
                line = next(i for i in txt.readlines() if i.startswith(number))
            except StopIteration:
                return None
            items = line.decode().split(";")

        dirname = f"documents/xml/{items[2]}/"
        filename = next(
            i.filename
            for i in f.filelist
            if i.filename.startswith(dirname) and i.filename.endswith(".xml")
        )

        with f.open(filename) as xml:
            raw = xmltodict.parse(xml.read())
            products = raw["JOE"]["PRODUCTS"]["PRODUCT"]

    return {"model": items[1], "products": products}


def get_options(products: list[dict]) -> dict[str, list]:
    return {
        attr: list(
            {
                option["@Name"]: None
                for product in products
                for option in product.get(attr.upper(), {}).get("ITEM", [])
            }.keys()  # unique keys with save order
        )
        for attr in SELECTS
    }
