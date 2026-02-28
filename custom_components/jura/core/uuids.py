from enum import Enum

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
