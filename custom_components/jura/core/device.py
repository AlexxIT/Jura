from pathlib import Path
from typing import TypedDict, Callable
from zipfile import ZipFile

import xmltodict

from .client import Client

SELECTS = [
    "product",  # 1
    # "grinder_ratio",  # 2
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


class Device:
    def __init__(self, name: str, mac: str, adv: bytes):
        number = str(int.from_bytes(adv[4:6], "little"))

        self.name = name
        self.mac = mac

        self.client = Client(mac, adv[0])

        machine = get_machine(number)
        self.model = machine["model"]
        self.products = machine["products"]
        self.options = get_options(self.products)

        self.product = None
        self.values = None
        self.updates: list[Callable] = []

    def selects(self) -> list[str]:
        products = str(self.products).lower()
        return [k for k in SELECTS if k in products]

    def numbers(self) -> list[str]:
        products = str(self.products).lower()
        return [k for k in NUMBERS if k in products]

    def attribute(self, attr: str) -> Attribute:
        if attr == "product":
            return Attribute(
                options=[i["@Name"] for i in self.products],
                default=self.product["@Name"] if self.product else None,
            )

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
        for update in self.updates:
            update()

    def start_product(self):
        if self.product:
            self.client.send(self.command())

    def command(self) -> bytearray:
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


def get_machine(number: str) -> dict:
    path = Path(__file__).parent / "resources.zip"
    with ZipFile(path) as f:
        with f.open("JOE_MACHINES.TXT") as txt:
            for line in txt:
                line = line.decode()
                if not line.startswith(number):
                    continue
                items = line.split(";")
                break

        with f.open("machinefiles/" + items[2] + ".xml") as xml:
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
