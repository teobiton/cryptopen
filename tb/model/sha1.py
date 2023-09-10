"""
Secure Hash Algorithm Python model.
"""

import struct
from typing import List


# Secure Hash Algorithm functions
def left_rotate(x: int, n: int) -> int:
    """Rotation to the left function"""
    return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF


def maj(x: int, y: int, z: int) -> int:
    """Majority function"""
    return (x & y) ^ (x & z) ^ (y & z)


def ch(x: int, y: int, z: int) -> int:
    """Choose function"""
    return (x & y) ^ (~x & z)


def parity(x: int, y: int, z: int) -> int:
    """Parity function"""
    return x ^ y ^ z


class sha1:
    """Class implementing the sha-1 algorithm"""

    def __init__(self, debug: bool = False, encoding: str = "ascii") -> None:
        self._h: List[int] = [
            0x67452301,
            0xEFCDAB89,
            0x98BADCFE,
            0x10325476,
            0xC3D2E1F0,
        ]
        self._encoding: str = encoding
        self._debug: bool = debug
        self._dbg_hash_values: List[str] = []

    def process(self, message: str) -> None:
        """Process a message"""

        _pre_message: bytes = self._pre_processing(message)
        _l: int = len(_pre_message)
        _N: int = _l // 64

        if self._debug:
            print(f"(N = {_N})")

        # Process the message in 512-bit blocks
        for m in range(0, _l, 64):
            block: bytes = _pre_message[m : m + 64]
            self._process_block(block)
            self._dbg_hash_values.append(self.digest())

        return self.digest()

    def _pre_processing(self, message: str) -> bytes:
        """Pre-processing: padding the message"""

        _bin_message: bytes = bytearray(message, encoding=self._encoding)
        ml: int = len(_bin_message) * 8  # Message length in bits

        if self._debug:
            print(f"\nMessage length: {ml} bytes ", end="")

        _bin_message.append(0x80)  # Append a single '1' bit

        # Pad the message with zeros to make it a multiple of 512 bits
        while (len(_bin_message) + 8) % 64 != 0:
            _bin_message.append(0x00)

        # Append the original message length in bits as a 64-bit big-endian integer
        _bin_message += struct.pack(">Q", ml)

        return _bin_message

    def _process_block(self, block: bytes) -> None:
        """Process a block of data and return new digested variables"""

        assert len(block) == 64

        # Initialize the w list with the first 16 words
        w = [struct.unpack(b">I", block[i * 4 : i * 4 + 4])[0] for i in range(16)]

        # Extend the list to contain eighty 4-byte words
        for i in range(16, 80):
            w.append(left_rotate(w[i - 3] ^ w[i - 8] ^ w[i - 14] ^ w[i - 16], 1))

        a, b, c, d, e = self._h

        for i in range(80):
            if i < 20:
                f = ch(b, c, d)
                k = 0x5A827999
            elif i < 40:
                f = parity(b, c, d)
                k = 0x6ED9EBA1
            elif i < 60:
                f = maj(b, c, d)
                k = 0x8F1BBCDC
            elif i < 80:
                f = parity(b, c, d)
                k = 0xCA62C1D6

            a, b, c, d, e = (
                (left_rotate(a, 5) + f + e + k + w[i]) & 0xFFFFFFFF,
                a,
                left_rotate(b, 30),
                c,
                d,
            )

        self._h[0] = (self._h[0] + a) & 0xFFFFFFFF
        self._h[1] = (self._h[1] + b) & 0xFFFFFFFF
        self._h[2] = (self._h[2] + c) & 0xFFFFFFFF
        self._h[3] = (self._h[3] + d) & 0xFFFFFFFF
        self._h[4] = (self._h[4] + e) & 0xFFFFFFFF

    def digest(self) -> str:
        """Convert the final hash values to hexadecimal"""
        return "".join(format(x, "08x") for x in self._h)

    def _dbg_digest(self) -> None:
        """Display final and intermediate (if any) hash values"""

        _N: int = len(self._dbg_hash_values)

        if _N > 1:
            for i in range(_N - 1):
                print(f"Intermediate hash value (H({i})): {self._dbg_hash_values[i]}")

        print(f"Final hash value: {self._dbg_hash_values[-1]}")
