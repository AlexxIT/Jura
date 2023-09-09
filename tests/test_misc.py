from custom_components.jura.core.device import Device
from custom_components.jura.core.encryption import encdec
from custom_components.jura.select import JuraSelect


def test_device():
    device = Device("Jura", "AA:BB:CC:DD:EE:FF", b"*\x05\x08\x03\xfb;")
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

    # Check we have no command
    assert device.command() is None

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


def test_coffee_strength():
    device = Device("JURA", "AA:BB:CC:DD:EE:FF", b"*\x05\x08\x03\xfb;")

    select = JuraSelect(device, "coffee_strength")
    assert select.name == "JURA Coffee Strength"
    assert select.available is False
    assert select.current_option is None
    assert select.options == []

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
