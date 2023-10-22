import struct
from typing import List


def right_rotate(x, n):
    """Rotation to the right function"""
    return (x >> n) | (x << (32 - n))


class sha256:
    """Class implementing the SHA-256 algorithm"""

    k = [
        0x428A2F98,
        0x71374491,
        0xB5C0FBCF,
        0xE9B5DBA5,
        0x3956C25B,
        0x59F111F1,
        0x923F82A4,
        0xAB1C5ED5,
        0xD807AA98,
        0x12835B01,
        0x243185BE,
        0x550C7DC3,
        0x72BE5D74,
        0x80DEB1FE,
        0x9BDC06A7,
        0xC19BF174,
        0xE49B69C1,
        0xEFBE4786,
        0x0FC19DC6,
        0x240CA1CC,
        0x2DE92C6F,
        0x4A7484AA,
        0x5CB0A9DC,
        0x76F988DA,
        0x983E5152,
        0xA831C66D,
        0xB00327C8,
        0xBF597FC7,
        0xC6E00BF3,
        0xD5A79147,
        0x06CA6351,
        0x14292967,
        0x27B70A85,
        0x2E1B2138,
        0x4D2C6DFC,
        0x53380D13,
        0x650A7354,
        0x766A0ABB,
        0x81C2C92E,
        0x92722C85,
        0xA2BFE8A1,
        0xA81A664B,
        0xC24B8B70,
        0xC76C51A3,
        0xD192E819,
        0xD6990624,
        0xF40E3585,
        0x106AA070,
        0x19A4C116,
        0x1E376C08,
        0x2748774C,
        0x34B0BCB5,
        0x391C0CB3,
        0x4ED8AA4A,
        0x5B9CCA4F,
        0x682E6FF3,
        0x748F82EE,
        0x78A5636F,
        0x84C87814,
        0x8CC70208,
        0x90BEFFFA,
        0xA4506CEB,
        0xBEF9A3F7,
        0xC67178F2,
    ]

    def __init__(self, debug=False, encoding="ascii"):
        self._h = [
            0x6A09E667,
            0xBB67AE85,
            0x3C6EF372,
            0xA54FF53A,
            0x510E527F,
            0x9B05688C,
            0x1F83D9AB,
            0x5BE0CD19,
        ]
        self._encoding = encoding
        self._debug = debug
        self._dbg_hash_values = []

    def process(self, message):
        _pre_message = self._pre_processing(message)
        l = len(_pre_message)
        N = l // 64

        if self._debug:
            print(f"(N = {N})")

        for m in range(0, l, 64):
            block = _pre_message[m : m + 64]
            self._process_block(block)
            self._dbg_hash_values.append(self.digest())

        return self.digest()

    def _pre_processing(self, message):
        _bin_message = bytearray(message, encoding=self._encoding)
        ml = len(_bin_message) * 8

        if self._debug:
            print(f"\nMessage length: {ml} bits ", end="")

        _bin_message.append(0x80)
        while (len(_bin_message) + 8) % 64 != 0:
            _bin_message.append(0x00)

        _bin_message += struct.pack(">Q", ml)

        return _bin_message

    def _process_block(self, block):
        assert len(block) == 64
        w = [0] * 64

        for i in range(16):
            w[i] = struct.unpack(">I", block[i * 4 : i * 4 + 4])[0]

        for i in range(16, 64):
            s0 = (
                right_rotate(w[i - 15], 7)
                ^ right_rotate(w[i - 15], 18)
                ^ (w[i - 15] >> 3)
            )
            s1 = (
                right_rotate(w[i - 2], 17)
                ^ right_rotate(w[i - 2], 19)
                ^ (w[i - 2] >> 10)
            )
            w[i] = (w[i - 16] + s0 + w[i - 7] + s1) & 0xFFFFFFFF

        a, b, c, d, e, f, g, h = self._h

        for i in range(64):
            s1 = right_rotate(e, 6) ^ right_rotate(e, 11) ^ right_rotate(e, 25)
            ch = (e & f) ^ (~e & g)
            temp1 = (h + s1 + ch + self.k[i] + w[i]) & 0xFFFFFFFF
            s0 = right_rotate(a, 2) ^ right_rotate(a, 13) ^ right_rotate(a, 22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (s0 + maj) & 0xFFFFFFFF

            h = g
            g = f
            f = e
            e = (d + temp1) & 0xFFFFFFFF
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xFFFFFFFF

        self._h[0] = (self._h[0] + a) & 0xFFFFFFFF
        self._h[1] = (self._h[1] + b) & 0xFFFFFFFF
        self._h[2] = (self._h[2] + c) & 0xFFFFFFFF
        self._h[3] = (self._h[3] + d) & 0xFFFFFFFF
        self._h[4] = (self._h[4] + e) & 0xFFFFFFFF
        self._h[5] = (self._h[5] + f) & 0xFFFFFFFF
        self._h[6] = (self._h[6] + g) & 0xFFFFFFFF
        self._h[7] = (self._h[7] + h) & 0xFFFFFFFF

    def digest(self):
        return "".join(format(x, "08x") for x in self._h)

    def _dbg_digest(self):
        N = len(self._dbg_hash_values)

        if N > 1:
            for i in range(N - 1):
                print(f"Intermediate hash value (H({i})): {self._dbg_hash_values[i]}")

        print(f"Final hash value: {self._dbg_hash_values[-1]}")
