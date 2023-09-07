from platform import system

if system() == "Windows":
    import socket
    import sys
    from types import ModuleType

    # fix bluetooth for Hass v2022.9+
    sys.modules["fcntl"] = ModuleType("")
    setattr(sys.modules["fcntl"], "ioctl", None)

    # fix bluetooth for Hass v2022.12+
    socket.CMSG_LEN = lambda *args: None
    socket.SCM_RIGHTS = 0
