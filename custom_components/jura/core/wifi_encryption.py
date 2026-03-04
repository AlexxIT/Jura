"""WiFi-specific encryption for Jura machines (TCP 51515 protocol).

The WiFi protocol reuses the same shuffle/S-box from BLE encryption but adds:
- Per-frame random key byte prepended to the payload
- ESC encoding for reserved bytes (0x00, 0x0A, 0x0D, 0x26, 0x1B)
- Frame format: 0x2A + key_byte + encoded_payload + 0x0D 0x0A
"""

import random

from .encryption import shuffle

ESCAPED_CHARS = [0x00, 0x0A, 0x0D, 0x26, 0x1B]


def wifi_encode(key: int, data: bytes) -> bytes:
    """Encode data for WiFi transmission with key byte and ESC escaping."""
    out = bytearray()
    key1 = key >> 4
    key2 = key & 0xF
    kb = key & 0xFF
    if kb in ESCAPED_CHARS:
        out += bytes([0x1B, (kb ^ 0x80) & 0xFF])
    else:
        out.append(kb)
    cnt = 0
    for byte in data:
        src1 = (byte >> 4) & 0xF
        src2 = byte & 0xF
        dst1 = shuffle(src1, cnt, key1, key2)
        cnt += 1
        dst2 = shuffle(src2, cnt, key1, key2)
        cnt += 1
        m = ((dst1 << 4) | dst2) & 0xFF
        if m in ESCAPED_CHARS:
            out += bytes([0x1B, (m ^ 0x80) & 0xFF])
        else:
            out.append(m)
    return bytes(out)


def wifi_decode(buf: bytes) -> str:
    """Decode a received WiFi payload (0x2A prefix already stripped).

    Handles ESC sequences, extracts key from first byte, returns decoded string.
    """
    if len(buf) < 2:
        return ""
    idx = 0
    b = buf[idx]
    if b == 0x1B:
        key = (buf[idx + 1] ^ 0x80) & 0xFF
        idx = 2
    else:
        key = b
        idx = 1
    key1 = key >> 4
    key2 = key & 0xF
    result = bytearray()
    cnt = 0
    while idx < len(buf):
        c = buf[idx]
        if c == 0x0D:
            break
        if c == 0x1B:
            idx += 1
            if idx >= len(buf):
                break
            c = (buf[idx] ^ 0x80) & 0xFF
        dl = shuffle((c >> 4) & 0xF, cnt, key1, key2)
        cnt += 1
        dr = shuffle(c & 0xF, cnt, key1, key2)
        cnt += 1
        result.append((dl << 4) | dr)
        idx += 1
    return result.decode("utf-8", errors="replace")


def wifi_make_frame(cmd: str) -> bytes:
    """Create a complete WiFi frame for sending.

    Format: 0x2A + wifi_encode(random_key, cmd) + 0x0D 0x0A
    Key nibbles 0xE and 0xF are avoided to prevent decode issues.
    """
    while True:
        key = random.randint(0, 255)
        if (key & 0xF) not in (0xE, 0xF):
            break
    return bytes([0x2A]) + wifi_encode(key, cmd.encode()) + bytes([0x0D, 0x0A])


def wifi_parse_frame(raw: bytes) -> str:
    """Parse a received raw frame including its 0x2A prefix."""
    if not raw or raw[0] != 0x2A:
        return ""
    return wifi_decode(raw[1:])
