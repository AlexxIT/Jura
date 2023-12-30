from bleak import BLEDevice, AdvertisementData

from custom_components.jura.core.device import Device
from custom_components.jura.core.encryption import encdec
from custom_components.jura.select import JuraSelect


def make_device(adv: bytes) -> Device:
    ble = BLEDevice("", None, None, 0)
    adv = AdvertisementData(None, {171: adv}, {}, [], None, 0, ())
    device = Device("Jura", ble, adv)
    device.client.ping = lambda *args: None
    return device


def test_device_e8():
    device = make_device(b"*\x05\x08\x03\xfb;")
    assert device.model == "E8 (EB)"

    # Check GUI elements list
    assert device.selects() == ["product", "coffee_strength", "temperature"]
    assert device.numbers() == [
        "water_amount",
        "milk_foam_amount",
        "bypass",
        "milk_break",
    ]

    # Check products list
    attr = device.attribute("product")
    assert attr == {
        "default": None,
        "options": [
            "Espresso",
            "Coffee",
            "Cappuccino",
            "Espresso Macchiato",
            "Latte Macchiato",
            "Milk Foam",
            "Hotwater Portion(normal)",
            "Espresso Doppio",
            "2 Espressi",
            "2 Coffee",
            "Cafe Barista",
            "Barista Lungo",
            "1 Flat White",
            "Cortado",
        ],
    }

    # Select product
    device.select_option("product", "Cafe Barista")

    cmd = device.command()
    assert cmd.hex() == "002800061200000100000900000000000000"

    attr = device.attribute("coffee_strength")
    assert attr == {
        "options": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
        "default": "6",
    }

    device.select_option("coffee_strength", "10")

    attr = device.attribute("water_amount")
    assert attr == {"max": 240, "min": 25, "step": 5, "value": 90}

    device.set_value("water_amount", 50)

    cmd = device.command()
    assert cmd.hex() == "0028000a0a00000100000900000000000000"

    # Select product
    device.select_option("product", "Cappuccino")
    cmd = device.command()
    assert cmd.hex() == "000400080c000e0100000000000000000000"


def test_device_d4():
    device = make_device(b"*\x05\x08\x03u;")
    assert device.model == "D4"

    # Check GUI elements list
    assert device.selects() == ["product", "coffee_strength", "temperature"]
    assert device.numbers() == ["water_amount", "bypass"]

    # Check products list
    attr = device.attribute("product")
    assert attr == {
        "default": None,
        "options": [
            "Espresso",
            "Coffee",
            "2 Espressi",
            "2 Coffee",
            "Ristretto (only JOE)",
            "Cafe Barista (only JOE)",
            "Barista Lungo (only JOE)",
            "Espresso Doppio (only JOE)",
            "2 Ristretti (only JOE)",
        ],
    }


def test_device_giga5():
    # https://github.com/AlexxIT/Jura/issues/10
    device = make_device(b"*\x05\x08\x03=5")
    assert device.model == "GIGA 5"

    assert device.selects() == [
        "product",
        "grinder_ratio",
        "coffee_strength",
        "temperature",
    ]
    assert device.numbers() == ["water_amount", "milk_amount", "milk_foam_amount"]

    # Check products list
    attr = device.attribute("product")
    assert attr == {
        "default": None,
        "options": [
            "Ristretto",
            "Espresso",
            "Coffee",
            "Cappuccino",
            "Milkcoffee",
            "Espresso Macchiato",
            "Latte Macchiato",
            "Milk Foam",
            "Milk Portion",
            "Pot",
            "Hotwater Portion",
            "2 Ristretti",
            "2 Espressi",
            "2 Coffee",
            "2 Cappuccini",
            "2 Milkcoffee",
            "2 Espresso Macchiati",
            "2 Latte Macchiati",
            "2 Milk Foam",
            "2 Portion Milk",
        ],
    }

    # Select product
    device.select_option("product", "Coffee")

    cmd = device.command()
    assert cmd.hex() == "000302031400000100000000000000000000"

    attr = device.attribute("coffee_strength")
    assert attr == {
        "default": "Normal",
        "options": ["XMild", "Mild", "Normal", "Strong", "XStrong"],
    }

    attr = device.attribute("grinder_ratio")
    assert attr == {
        "default": "50_50",
        "options": ["100_0", "75_25", "50_50", "25_75", "0_100"],
    }

    attr = device.attribute("water_amount")
    assert attr == {"max": 240, "min": 25, "step": 5, "value": 100}

    attr = device.attribute("temperature")
    assert attr == {"default": "Normal", "options": ["Low", "Normal", "High"]}


def test_coffee_strength():
    device = make_device(b"*\x05\x08\x03\xfb;")

    select = JuraSelect(device, "coffee_strength")
    assert select.name == "Jura Coffee Strength"
    assert select.available is False
    assert select.current_option is None
    assert select.options == ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]

    device.select_option("product", "Cafe Barista")

    assert select.available is True
    assert select.current_option == "6"
    assert select.options == ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]


def test_encdec():
    # mobile: 2a280006120000010001090000000000062a
    # python: 002800061200000100000900000000000000
    b = bytes.fromhex("77c23dd05e81d3dba32bf898a4a3faab45fd")
    b = encdec(b, 0x2A)
    assert b.hex() == "2a280006120000010001090000000000062a"

    # mobile: 2a0400080c000e010001000000000000062a
    # python: 000400080c000e0100000000000000000000
    b = bytes.fromhex("77ea3dd38981dadba32bfa98a4a3faab45fd")
    b = encdec(b, 0x2A)
    assert b.hex() == "2a0400080c000e010001000000000000062a"


def test_status_key2A():
    b = bytes.fromhex("77E13ED68882D3D7A323FA98A4A3FAAB4756A629")
    b = encdec(b, 0x2A)
    assert b.hex() == "2a00040000040008000000000000000000000007"

    # no bottom tray
    b = bytes.fromhex("77D23DD68882D3D7A323FA98A4A3FAAB4756A625")
    b = encdec(b, 0x2A)
    assert b.hex() == "2a88000000040008000000000000000000000006"

    # no water tray
    b = bytes.fromhex("77113DD68882D3D7A323FA98A4A3FAAB4756A625")
    b = encdec(b, 0x2A)
    assert b.hex() == "2a40000000040008000000000000000000000006"

    # no water tray + remove water from bottom tray
    b = bytes.fromhex("77913DD6888BD3D7A323FA98A4A3FAAB4756A625")
    b = encdec(b, 0x2A)
    assert b.hex() == "2a500000000c0008000000000000000000000006"


def test_status_key00():
    b = bytes.fromhex("14444CC623152D9ABFE772ED1B3F65136B888DDC")
    b = encdec(b, 0)
    assert b.hex() == "0000000000000000000000000000000000000004"

    # coffee trash
    b = bytes.fromhex("14A44CC623153D94BFE772ED1B3F65136B888DD2")
    b = encdec(b, 0)
    assert b.hex() == "0020000000004008000000000000000000000006"

    # zero water
    b = bytes.fromhex("14044CC623153D94BFE772ED1B3F65136B888DDC")
    b = encdec(b, 0)
    assert b.hex() == "0040000000004008000000000000000000000004"

    # cleaning milk and usual cleaning
    b = bytes.fromhex("144448C623753D94BFE772ED1B3F65136B888DDC")
    b = encdec(b, 0)
    assert b.hex() == "0000040000204008000000000000000000000004"

    # usual cleaning
    b = bytes.fromhex("144448C623752D94BFE772ED1B3F65136B888DD2")
    b = encdec(b, 0)
    assert b.hex() == "0000040000200008000000000000000000000006"
