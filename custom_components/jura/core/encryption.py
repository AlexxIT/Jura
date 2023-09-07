NUMB1 = [14, 4, 3, 2, 1, 13, 8, 11, 6, 15, 12, 7, 10, 5, 0, 9]
NUMB2 = [10, 6, 13, 12, 14, 11, 1, 9, 15, 7, 0, 5, 3, 2, 4, 8]


def mod256(i: int):
    return i % 256


def shuffle(src, cnt, key1, key2):
    i1 = mod256(cnt >> 4)
    i2 = NUMB1[mod256(src + cnt + key1) % 16]
    i3 = NUMB2[mod256(i2 + key2 + i1 - cnt - key1) % 16]
    i4 = NUMB1[mod256(i3 + key1 + cnt - key2 - i1) % 16]
    return mod256(i4 - cnt - key1) % 16


def encdec(src: bytes, key: int):
    dst = b""
    key1 = key >> 4
    key2 = key & 0xF
    cnt = 0
    for b in src:
        src1 = b >> 4
        src2 = b & 0xF
        dst1 = shuffle(src1, cnt, key1, key2)
        cnt += 1
        dst2 = shuffle(src2, cnt, key1, key2)
        cnt += 1
        dst += bytes([(dst1 << 4) | dst2])
    return dst
