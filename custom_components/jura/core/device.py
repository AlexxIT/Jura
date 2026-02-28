import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypedDict
from zipfile import ZipFile

import xmltodict
from bleak import AdvertisementData, BLEDevice

from .client import Client
from .sensor_definitions import SENSOR_DEFINITIONS

_LOGGER = logging.getLogger(__name__)

COMMAND_TIME = 15
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
    def __init__(
        self,
        name: str,
        model: str,
        products: list,
        maintenance_counters: list,
        maintenance_percents: list,
        alerts: dict[int, str],
        key: int,
        device: BLEDevice,
    ):
        self.name = name
        self.model = model
        self.products = products
        self.maintenance_counters = maintenance_counters
        self.maintenance_percents = maintenance_percents
        self.alerts = alerts

        self.client = Client(device, self.set_connected, key)

        self.connected = False
        self.conn_info = {"mac": device.address}

        self.options = get_options(self.products)

        self.product = None
        self.values = None
        self.updates_connect: list = []
        self.updates_product: list = []
        self.updates_statistics = []
        self.updates_alerts = []
        self.statistics = {"TOTAL_PRODUCTS": None, "PRODUCTS": {}, "MAINTENANCE_COUNTERS": {}, "MAINTENANCE_PERCENTS": {}}
        self.active_alerts = {}

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
        if attr == "connection":
            return Attribute(is_on=self.connected, extra=self.conn_info)

        if attr == "product":
            return Attribute(
                options=[
                    i["@Name"] for i in self.products if i.get("@Active") != "false"
                ],
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
        for handler in self.updates_product:
            handler()

    def start_product(self):
        if self.product:
            self.client.send(self.get_product_command())

    def get_product_command(self) -> bytes:
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
        # data[0] = self.client.key
        # data[9] = 1
        # data[16] = 6
        # need to be set or the machine will go into a half broken state
        data[17] = self.client.key
        return data

    # Add method to register statistics updates
    def register_statistics_update(self, handler: Callable):
        """Register a callback for statistics updates."""
        self.updates_statistics.append(handler)

    async def read_statistics(self, force_update: bool = False):
        """Read statistics from the machine."""

        _LOGGER.debug("Reading Jura statistics - product counters...")

        # Read statistics data from client
        decrypted_data = await self.client.read_statistics_data(command_bytes=[self.client.key, 0x00, 0x01, 0xFF, 0xFF])
        decrypted_data_2 = await self.client.read_statistics_data(command_bytes=[self.client.key, 0x00, 0x01, 0xFF, 0xFF])
        if decrypted_data is None or (decrypted_data != decrypted_data_2):
            _LOGGER.debug(
                f"Failed to correctly read statistics data (product counters), returning existing statistics {self.statistics}"
            )
            return self.statistics

        # Convert all 3-byte chunks to integers
        product_counts_array = []
        for i in range(0, len(decrypted_data), 3):
            if i + 3 <= len(decrypted_data):
                # Convert 3 bytes to an integer
                count = int.from_bytes(decrypted_data[i : i + 3], "big")
                if count == 0xFFFF:  # means 0 it seems
                    count = 0
                product_counts_array.append(count)

        # get total_count from first 3 bytes if available
        total_count = (
            product_counts_array[0]
            if product_counts_array and product_counts_array[0] is not None
            else None
        )

        _LOGGER.info(
            f"Total coffee count from data: {total_count if total_count is not None else 'undefined'}"
        )

        # get the names associated to the products counts
        total_W=0
        total_C=0
        total_M=0
        total_CM=0
        total_CIM=0

        product_counts = {}
        for i, count in enumerate(product_counts_array):
            if i == 0:  # Skip the total
                continue

            product = next((p for p in self.products if int(p["@Code"], 16) == i), None)
            if product:
                product_counts[product["@Name"]] = count
                _LOGGER.debug(f"Stat entry: Position {i} = {count} -> {product['@Name']}")
                tmp_product=SENSOR_DEFINITIONS["PRODUCTS"][str(i)]
                if tmp_product.get("water"):
                    total_W += count
                if tmp_product.get("coffee") and not tmp_product.get("milk"):
                    total_C += count
                    total_CIM += count
                if tmp_product.get("milk") and not tmp_product.get("coffee"):
                    total_M += count
                if tmp_product.get("coffee") and tmp_product.get("milk"):
                    total_CM += count
                    total_CIM += count
            else:
                if count > 0:
                    _LOGGER.debug(f"No product found for code {i} with count {count}")

        total_products = {"Total Products": total_count, "Total Coffee Only": total_C, "Total Milk Only": total_M, "Total Water Only": total_W, "Total Coffee With Milk": total_CM, "Total Coffee Including Milk Coffee": total_CIM}
        # Log the final counts at info log level
        for product, count in product_counts.items():
            _LOGGER.debug(f"Product: {product}, Count: {count}")

        _LOGGER.debug("Reading Jura statistics - maintenance counters...")
        decrypted_data = await self.client.read_statistics_data(command_bytes=[self.client.key, 0x00, 0x04, 0x01, 0x00])
        decrypted_data_2 = await self.client.read_statistics_data(command_bytes=[self.client.key, 0x00, 0x04, 0x01, 0x00])
        if decrypted_data is None or (decrypted_data != decrypted_data_2):
            _LOGGER.debug(
                f"Failed to read statistics data (maintenance counters), returning existing statistics {self.statistics}"
            )
            return self.statistics

        maintenance_counters_array = [int("".join(["%02x" % d for d in decrypted_data[i:i+2]]), 16) for i in range(0, len(decrypted_data), 2)]
        maintenance_counters = dict(zip(self.maintenance_counters, maintenance_counters_array))
        _LOGGER.debug(f"Maintenance counters: {maintenance_counters}")
        total_mnt = sum(maintenance_counters_array)
        _LOGGER.debug(f"Total maintenance counters: {total_mnt}")
        if (total_mnt > total_count * 5):
            _LOGGER.debug(
                f"Total maintenance counters too high ({total_mnt}, total products {total_count}), something's wrong, returning existing statistics {self.statistics}"
            )
            return self.statistics

        _LOGGER.debug("Reading maintenance percents...")
        decrypted_data = await self.client.read_statistics_data(command_bytes=[self.client.key, 0x00, 0x08, 0x01, 0x00])
        decrypted_data_2 = await self.client.read_statistics_data(command_bytes=[self.client.key, 0x00, 0x08, 0x01, 0x00])
        if decrypted_data is None or (decrypted_data != decrypted_data_2):
            _LOGGER.debug(
                f"Failed to read statistics data (maintenance percents), returning existing statistics {self.statistics}"
            )
            return self.statistics

        maintenance_percents = {}
        for i in range(len(self.maintenance_percents)):
            value = decrypted_data[i]
            if 100 < value < 255:
                _LOGGER.debug(
                    f"Incorrect maintenance percents read, returning existing statistics {self.statistics}"
                )
                return self.statistics
            if value == 255:
                maintenance_percents[self.maintenance_percents[i]] = None
            else:
                maintenance_percents[self.maintenance_percents[i]] = value

        _LOGGER.debug(f"Maintenance percents: {maintenance_percents}")

        # Save the statistics
        self.statistics = {
            "TOTAL_PRODUCTS": total_products,
            "PRODUCTS": product_counts,
            "MAINTENANCE_COUNTERS": maintenance_counters,
            "MAINTENANCE_PERCENTS": maintenance_percents,
        }

        _LOGGER.debug(f"final statistics: {self.statistics}")

        # Notify all statistics listeners
        _LOGGER.debug(f"Notifying {len(self.updates_statistics)} statistics listeners")
        for handler in self.updates_statistics:
            handler()

        _LOGGER.debug(f"Read data OK, sending statistics {self.statistics}")
        return self.statistics

    def register_alert_update(self, handler: Callable):
        """Register a callback for alert updates."""
        self.updates_alerts.append(handler)
        # Trigger an immediate update for the new handler
        if self.active_alerts:
            handler()

    async def read_alerts(self) -> dict:
        """Read alerts from the machine."""

        # Read machine status data from client
        data = await self.client.read_machine_status()
        if data is None:
            _LOGGER.debug("Failed to read machine status data")
            return self.active_alerts

        # Process alert bits
        alerts = {}
        for i in range((len(data) - 1) * 8):
            offset_abs = (i >> 3) + 1
            offset_byte = 7 - (i & 0b111)
            if (data[offset_abs] >> offset_byte) & 0b1:
                alert = self.alerts.get(i)
                if alert is not None:
                    alerts[i] = alert
                    _LOGGER.debug(f"Alert active. Alert bit: {i} - {alert}")
                else:
                    _LOGGER.debug(f"Alert active. Alert bit: {i} - unknown alert")

        # Save the alerts
        self.active_alerts = alerts

        # Notify all alert listeners
        _LOGGER.debug(f"Notifying {len(self.updates_alerts)} alert listeners: {alerts}")
        for handler in self.updates_alerts:
            handler()

        return self.active_alerts


class EmptyModel(Exception):
    pass


class UnsupportedModel(Exception):
    pass


def get_machine(adv: bytes) -> dict | None:
    model_id = int.from_bytes(adv[4:6], "little")
    if model_id == 0:
        raise EmptyModel()

    path = Path(__file__).parent / "resources.zip"
    with ZipFile(path) as f:
        prefix = str(model_id).encode()
        with f.open("JOE_MACHINES.TXT") as txt:
            try:
                line = next(i for i in txt.readlines() if i.startswith(prefix))
            except StopIteration:
                raise UnsupportedModel(model_id)
            items = line.decode().split(";")

        dirname = f"documents/xml/{items[2].upper()}/"
        filename = next(
            i.filename
            for i in f.filelist
            if i.filename.startswith(dirname) and i.filename.endswith(".xml")
        )

        with f.open(filename) as xml:
            raw = xmltodict.parse(xml.read())
            products = raw["JOE"]["PRODUCTS"]["PRODUCT"]

            try:
                alerts = {
                    int(i["@Bit"]): i["@Name"] for i in raw["JOE"]["ALERTS"]["ALERT"]
                }
            except:
                alerts = {}

            try:
                maintenance_counters = [
                    item["@Type"] for bank in raw["JOE"]["STATISTIC"]["MAINTENANCEPAGE"]["BANK"]
                    if bank["@Command"] == "@TG:43"
                    for item in bank["TEXTITEM"]
                ]
            except Exception as e:
                _LOGGER.error(f"Error extracting maintenance counters: {e}")
                maintenance_counters = {}

            try:
                maintenance_percents = [
                    item["@Type"] for bank in raw["JOE"]["STATISTIC"]["MAINTENANCEPAGE"]["BANK"]
                    if bank["@Command"] == "@TG:C0"
                    for item in bank["TEXTITEM"]
                ]
            except Exception as e:
                _LOGGER.error(f"Error extracting maintenance percents: {e}")
                maintenance_percents = {}

            _LOGGER.debug(f"Maintenance counters: {maintenance_counters}")
            _LOGGER.debug(f"Maintenance percents: {maintenance_percents}")

    # First byte is the encryption key
    return {
        "model": items[1],
        "products": products,
        "alerts": alerts,
        "key": adv[0],
        "maintenance_counters": maintenance_counters,
        "maintenance_percents": maintenance_percents,
    }


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
