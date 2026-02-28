from homeassistant.const import EntityCategory

SENSOR_DEFINITIONS = {
"ALERT_SENSORS":
    {   
        "0":
        {
            "name": "insert tray",
            "display_name": "Alarm - Insert Drip Tray",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "1":
        {
            "name": "fill water",
            "display_name": "Alarm - Fill Water Tank",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "2":
        {
            "name": "empty grounds",
            "display_name": "Alarm - Empty Coffee Grounds",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "3":
        {
            "name": "empty tray",
            "display_name": "Alarm - Empty Drip Tray",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "4":
        {
            "name": "insert coffee bin",
            "display_name": "Alarm - Insert Coffee Bin",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "5":
        {
            "name": "outlet missing",
            "display_name": "Alarm - Outlet Missing",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "6":
        {
            "name": "rear cover missing",
            "display_name": "Alarm - Rear Service Cover Missing",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "7":
        {
            "name": "milk alert",
            "display_name": "Alarm - Milk Container Empty",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "8":
        {
            "name": "fill system",
            "display_name": "Alarm - Fill System",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "9":
        {
            "name": "system filling",
            "display_name": "Info - System Is Filling",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "10":
        {
            "name": "no beans",
            "display_name": "Alarm - Fill Beans Container",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "11":
        {
            "name": "welcome",
            "display_name": "Info - Welcome",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "12":
        {
            "name": "heating up",
            "display_name": "Info - Heating Up",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "13":
        {
            "name": "coffee ready",
            "display_name": "Info - Coffee Ready",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "14":
        {
            "name": "no milk (milk sensor)",
            "display_name": "Alarm - Milk Container Empty (milk sensor)",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "15":
        {
            "name": "error milk (milk sensor)",
            "display_name": "Alarm - error milk (milk sensor)",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "16":
        {
            "name": "no signal (milk sensor)",
            "display_name": "Alarm - Milk Cooler Connection Lost",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "17":
        {
            "name": "please wait",
            "display_name": "Info - Machine in operation",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "18":
        {
            "name": "coffee rinsing",
            "display_name": "Info - Coffee Rinsing",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "19":
        {
            "name": "ventilation closed",
            "display_name": "Alarm - Ventilation Slots Are Closed",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "20":
        {
            "name": "close powder cover",
            "display_name": "Alarm - Close Powder Cover",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "21":
        {
            "name": "fill powder",
            "display_name": "Alarm - Add Grounde Coffee",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "22":
        {
            "name": "system emptying",
            "display_name": "Info - System Emptying",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "23":
        {
            "name": "not enough powder",
            "display_name": "Alarm - Not Enough Ground Coffee",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "24":
        {
            "name": "remove water tank",
            "display_name": "Alarm - Remove Water Tank",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "25":
        {
            "name": "press rinse",
            "display_name": "Alarm - Rinse Needed",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "26":
        {
            "name": "goodbye",
            "display_name": "Info - Shutting Down",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "27":
        {
            "name": "periphery alert",
            "display_name": "Alarm - Accessory Alert",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "28":
        {
            "name": "powder product",
            "display_name": "Info - Preparing product with ground coffee",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "29":
        {
            "name": "program-mode status",
            "display_name": "Info - Machine in programming mode",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "30":
        {
            "name": "error status",
            "display_name": "Alarm - error status",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "31":
        {
            "name": "enjoy product",
            "display_name": "Info - Enjoy Product",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "32":
        {
            "name": "filter alert",
            "display_name": "Alarm - Filter Change Needed",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "33":
        {
            "name": "decalc alert",
            "display_name": "Alarm - Descaling Needed",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "34":
        {
            "name": "cleaning alert",
            "display_name": "Alarm - Machine Cleaning Needed",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "35":
        {
            "name": "cappu rinse alert",
            "display_name": "Alarm - Milk System Rinse Needed",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "36":
        {
            "name": "energy safe",
            "display_name": "Info - Energy Save Mode",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "37":
        {
            "name": "active RF filter",
            "display_name": "Info - Filter Installed",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "38":
        {
            "name": "RemoteScreen",
            "display_name": "Info - Remote Screen Active",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "39":
        {
            "name": "LockedKeys",
            "display_name": "Info - Buttons Are Locked",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "40":
        {
            "name": "close tab",
            "display_name": "Alarm - Close Tab",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "41":
        {
            "name": "cappu clean alert",
            "display_name": "Alarm - Milk System Cleaning Needed",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "42":
        {
            "name": "Info - cappu clean alert",
            "display_name": "Alarm - Info - Milk System Cleaning Needed",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "43":
        {
            "name": "Info - coffee clean alert",
            "display_name": "Alarm - Info - Machine Cleaning Needed",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "44":
        {
            "name": "Info - decalc alert",
            "display_name": "Alarm - Info - Descaling Needed",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "45":
        {
            "name": "Info - filter used up alert",
            "display_name": "Alarm - Info - Filter Change Needed",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "46":
        {
            "name": "steam ready",
            "display_name": "Info - Steam Ready",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "47":
        {
            "name": "SwitchOff Delay active",
            "display_name": "Info - Machine is powering off",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "48":
        {
            "name": "close front cover",
            "display_name": "Alarm - Close Front Flap",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "49":
        {
            "name": "left bean alert",
            "display_name": "Alarm - Left Bean Empty",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "50":
        {
            "name": "right bean alert",
            "display_name": "Alarm - Right Bean Container Empty",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "53":
        {
            "name": "empty grounds RTC",
            "display_name": "Alarm - Empty Grounds RTC",
            "device_class": "problem",
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "54":
        {
            "name": "ML/OZ status",
            "display_name": "Info - ML/OZ status",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "55":
        {
            "name": "Open Tap",
            "display_name": "Info - Open Tap",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
        "56":
        {
            "name": "Coffee Eye (cup detected)",
            "display_name": "Info - Coffee Eye (cup detected)",
            "device_class": None,
            "entity_category": EntityCategory.DIAGNOSTIC,
        },
    },

"MAINTENANCE_COUNTERS" :
    {
    # Maintenance alerts (these are normal maintenance operations)
        "Cleaning":
        {
            "name": "Cleaning",
            "display_name": "MNT Cleanings",
            "icon": "mdi:wrench",
            "entity_category": EntityCategory.DIAGNOSTIC,
            "unit": "times",
            "state_class": "total_increasing",
        },
        # Maintenance alerts (these are normal maintenance operations)
        "FilterChange":
        {
            "name": "FilterChange",
            "display_name": "MNT Filter Changes",
            "icon": "mdi:wrench",
            "entity_category": EntityCategory.DIAGNOSTIC,
            "unit": "times",
            "state_class": "total_increasing",
        },
        # Maintenance alerts (these are normal maintenance operations)
        "Decalc":
        {
            "name": "Decalc",
            "display_name": "MNT Descalings",
            "icon": "mdi:wrench",
            "entity_category": EntityCategory.DIAGNOSTIC,
            "unit": "times",
            "state_class": "total_increasing",
        },
        # Maintenance alerts (these are normal maintenance operations)
        "CappuRinse":
        {
            "name": "CappuRinse",
            "display_name": "MNT Milk Rinses",
            "icon": "mdi:wrench",
            "entity_category": EntityCategory.DIAGNOSTIC,
            "unit": "times",
            "state_class": "total_increasing",
        },
        # Maintenance alerts (these are normal maintenance operations)
        "CoffeeRinse":
        {
            "name": "CoffeeRinse",
            "display_name": "MNT Coffee Rinses",
            "icon": "mdi:wrench",
            "entity_category": EntityCategory.DIAGNOSTIC,
            "unit": "times",
            "state_class": "total_increasing",
        },
        # Maintenance alerts (these are normal maintenance operations)
        "CappuClean":
        {
            "name": "CappuClean",
            "display_name": "MNT Milk Cleanings",
            "icon": "mdi:wrench",
            "entity_category": EntityCategory.DIAGNOSTIC,
            "unit": "times",
            "state_class": "total_increasing",
        },
    },

"MAINTENANCE_PERCENTS":
    {
    # Maintenance alerts (these are normal maintenance operations)
        "Cleaning":
        {
            "name": "Cleaning",
            "display_name": "MNT % Cleaning",
            "icon": "mdi:percent",
            "entity_category": EntityCategory.DIAGNOSTIC,
            "unit": "%",
            "state_class": "total",
        },
        # Maintenance alerts (these are normal maintenance operations)
        "FilterChange":
        {
            "name": "FilterChange",
            "display_name": "MNT % Filter Change",
            "icon": "mdi:percent",
            "entity_category": EntityCategory.DIAGNOSTIC,
            "unit": "%",
            "state_class": "total",
        },
        # Maintenance alerts (these are normal maintenance operations)
        "Decalc":
        {
            "name": "Decalc",
            "display_name": "MNT % Decalc",
            "icon": "mdi:percent",
            "entity_category": EntityCategory.DIAGNOSTIC,
            "unit": "%",
            "state_class": "total",
        }
    },

"PRODUCTS":
    {
        "1":
        {
            "name": "Ristretto",
            "display_name": "Ristretto",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "2":
        {
            "name": "Espresso",
            "display_name": "Espresso",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "3":
        {
            "name": "Coffee",
            "display_name": "Coffee",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "4":
        {
            "name": "Cappuccino",
            "display_name": "Cappuccino",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "5":
        {
            "name": "Milkcoffee",
            "display_name": "Milkcoffee",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "6":
        {
            "name": "Espresso Macchiato",
            "display_name": "Espresso Macchiato",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "7":
        {
            "name": "Latte Macchiato",
            "display_name": "Latte Macchiato",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "8":
        {
            "name": "Milk Foam",
            "display_name": "Milk Foam",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
        },
        "10":
        {
            "name": "Milk",
            "display_name": "Milk",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
        },
        "12":
        {
            "name": "Pot",
            "display_name": "Coffee Pot",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "13":
        {
            "name": "Hotwater Portion",
            "display_name": "Hotwater Portion",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "water": True,
        },
        "15":
        {
            "name": "Powderproduct",
            "display_name": "Powderproduct",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "17":
        {
            "name": "2 Ristretti",
            "display_name": "2 Ristretti",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "18":
        {
            "name": "2 Espressi",
            "display_name": "2 Espressi",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "19":
        {
            "name": "2 Coffee",
            "display_name": "2 Coffee",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "20":
        {
            "name": "2 Cappuccini",
            "display_name": "2 Cappuccini",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "21":
        {
            "name": "2 Milkcoffee",
            "display_name": "2 Milkcoffee",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "22":
        {
            "name": "2 Espresso Macchiati",
            "display_name": "2 Espresso Macchiati",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "23":
        {
            "name": "2 Latte Macchiati",
            "display_name": "2 Latte Macchiati",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "24":
        {
            "name": "2 Milk Foam",
            "display_name": "2 Milk Foam",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
        },
        "26":
        {
            "name": "2 Milk",
            "display_name": "2 Milk",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
        },
        "40":
        {
            "name": "Cafe Barista",
            "display_name": "Cafe Barista",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "41":
        {
            "name": "Barista Lungo",
            "display_name": "Barista Lungo",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "43":
        {
            "name": "Cortado",
            "display_name": "Cortado",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "44":
        {
            "name": "RAF Coffee",
            "display_name": "RAF Coffee",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "44":
        {
            "name": "Sweet Latte",
            "display_name": "Sweet Latte",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "45":
        {
            "name": "Hotwater Portion(Green tea)",
            "display_name": "Hotwater Portion (Green tea)",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "water": True,
        },
        "46":
        {
            "name": "Flat White",
            "display_name": "Flat White",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "47":
        {
            "name": "Coffee Special",
            "display_name": "Coffee Special",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "48":
        {
            "name": "Espresso Doppio",
            "display_name": "Espresso Doppio",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "49":
        {
            "name": "2 Espressi",
            "display_name": "2 Espressi",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "50":
        {
            "name": "Americano",
            "display_name": "Americano",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "51":
        {
            "name": "Coffee Big",
            "display_name": "Coffee Big",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "52":
        {
            "name": "Cappuccino Big",
            "display_name": "Cappuccino Big",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "53":
        {
            "name": "Milkcoffee Big",
            "display_name": "Milkcoffee Big",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "54":
        {
            "name": "2 Coffee",
            "display_name": "2 Coffee",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "55":
        {
            "name": "Latte Macchiato Big",
            "display_name": "Latte Macchiato Big",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "56":
        {
            "name": "2 Cafe Barista",
            "display_name": "2 Cafe Barista",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "57":
        {
            "name": "2 Barista Lungo",
            "display_name": "2 Barista Lungo",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "58":
        {
            "name": "Milk Big",
            "display_name": "Milk Big",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
        },
        "59":
        {
            "name": "2 Cortado",
            "display_name": "2 Cortado",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "60":
        {
            "name": "Pot 2 Speed",
            "display_name": "Coffee Pot 2 Speed",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
        "61":
        {
            "name": "Hotwater Portion(black tea)",
            "display_name": "Hotwater Portion (black tea)",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "water": True,
        },
        "62":
        {
            "name": "2 Flat White",
            "display_name": "2 Flat White",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "milk": True,
            "coffee": True,
        },
        "63":
        {
            "name": "2 coffee special",
            "display_name": "2 coffee special",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee-outline",
            "coffee": True,
        },
},

"TOTAL_PRODUCTS":
    {
    # Maintenance alerts (these are normal maintenance operations)
        "Total Products":
        {
            "name": "Total Products",
            "display_name": "Total Products",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee",
        },
        "Total Coffee Only":
        {
            "name": "Total Coffee Only",
            "display_name": "Total Coffee Only",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee",
        },
        "Total Coffee With Milk":
        {
            "name": "Total Coffee With Milk",
            "display_name": "Total Coffee With Milk",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee",
        },
        "Total Coffee Including Milk Coffee" :
        {
            "name": "Total Coffee Including Milk Coffee",
            "display_name": "Total Coffee Including Milk Coffee",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee",
        },
        "Total Milk Only":
        {
            "name": "Total Milk Only",
            "display_name": "Total Milk Only",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee",
        },
        "Total Water Only":
        {
            "name": "Total Water Only",
            "display_name": "Total Water Only",
            "unit": "products",
            "state_class": "total_increasing",
            "icon": "mdi:coffee",
        },
    }
}
