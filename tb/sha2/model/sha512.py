import struct


def right_rotate(x, n):
    """Rotation to the right function"""
    return (x >> n) | (x << (64 - n))


class sha512:
    """Class implementing the SHA-512 algorithm"""

    k = [
        0x428A2F98D728AE22,
        0x7137449123EF65CD,
        0xB5C0FBCFEC4D3B2F,
        0xE9B5DBA58189DBBC,
        0x3956C25BF348B538,
        0x59F111F1B605D019,
        0x923F82A4AF194F9B,
        0xAB1C5ED5DA6D8118,
        0xD807AA98A3030242,
        0x12835B0145706FBE,
        0x243185BE4EE4B28C,
        0x550C7DC3D5FFB4E2,
        0x72BE5D74F27B896F,
        0x80DEB1FE3B1696B1,
        0x9BDC06A725C71235,
        0xC19BF174CF692694,
        0xE49B69C19EF14AD2,
        0xEFBE4786384F25E3,
        0x0FC19DC68B8CD5B5,
        0x240CA1CC77AC9C65,
        0x2DE92C6F592B0275,
        0x4A7484AA6EA6E483,
        0x5CB0A9DCBD41FBD4,
        0x76F988DA831153B5,
        0x983E5152EE66DFAB,
        0xA831C66D2DB43210,
        0xB00327C898FB213F,
        0xBF597FC7BEEF0EE4,
        0xC6E00BF33DA88FC2,
        0xD5A79147930AA725,
        0x06CA6351E003826F,
        0x142929670A0E6E70,
        0x27B70A8546D22FFC,
        0x2E1B21385C26C926,
        0x4D2C6DFC5AC42AED,
        0x53380D139D95B3DF,
        0x650A73548BAF63DE,
        0x766A0ABB3C77B2A8,
        0x81C2C92E47EDAEE6,
        0x92722C851482353B,
        0xA2BFE8A14CF10364,
        0xA81A664BBC423001,
        0xC24B8B70D0F89791,
        0xC76C51A30654BE30,
        0xD192E819D6EF5218,
        0xD69906245565A910,
        0xF40E35855771202A,
        0x106AA07032BBD1B8,
        0x19A4C116B8D2D0C8,
        0x1E376C085141AB53,
        0x2748774CDF8EEB99,
        0x34B0BCB5E19B48A8,
        0x391C0CB3C5C95A63,
        0x4ED8AA4AE3418ACB,
        0x5B9CCA4F7763E373,
        0x682E6FF3D6B2B8A3,
        0x748F82EE5DEFB2FC,
        0x78A5636F43172F60,
        0x84C87814A1F0AB72,
        0x8CC702081A6439EC,
        0x90BEFFFA23631E28,
        0xA4506CEBDE82BDE9,
        0xBEF9A3F7B2C67915,
        0xC67178F2E372532B,
        0xCA273ECEEA26619C,
        0xD186B8C721C0C207,
        0xEADA7DD6CDE0EB1E,
        0xF57D4F7FEE6ED178,
        0x06F067AA72176FBA,
        0x0A637DC5A2C898A6,
        0x113F9804BEF90DAE,
        0x1B710B35131C471B,
        0x28DB77F523047D84,
        0x32CAAB7B40C72493,
        0x3C9EBE0A15C9BEBC,
        0x431D67C49C100D4C,
        0x4CC5D4BECB3E42B6,
        0x597F299CFC657E2A,
        0x5FCB6FAB3AD6FAEC,
        0x6C44198C4A475817,
    ]

    def __init__(self, digest_width=512, debug=False, encoding="ascii"):
        sha512_h = [
            0x6A09E667F3BCC908,
            0xBB67AE8584CAA73B,
            0x3C6EF372FE94F82B,
            0xA54FF53A5F1D36F1,
            0x510E527FADE682D1,
            0x9B05688C2B3E6C1F,
            0x1F83D9ABFB41BD6B,
            0x5BE0CD19137E2179,
        ]

        sha384_h = [
            0xCBBB9D5DC1059ED8,
            0x629A292A367CD507,
            0x9159015A3070DD17,
            0x152FECD8F70E5939,
            0x67332667FFC00B31,
            0x8EB44A8768581511,
            0xDB0C2E0D64F98FA7,
            0x47B5481DBEFA4FA4,
        ]

        sha256_h = [
            0x22312194FC2BF72C,
            0x9F555FA3C84C64C2,
            0x2393B86B6F53B151,
            0x963877195940EABD,
            0x96283EE2A88EFFE3,
            0xBE5E1E2553863992,
            0x2B0199FC2C85B8AA,
            0x0EB72DDC81C52CA2,
        ]

        sha224_h = [
            0x8C3D37C819544DA2,
            0x73E1996689DCD4D6,
            0x1DFAB7AE32FF9C82,
            0x679DD514582F9FCF,
            0x0F6D2B697BD44DA8,
            0x77E36F7304C48942,
            0x3F9D85A86A1D36C8,
            0x1112E6AD91D692A1,
        ]

        init_hash = {
            512: sha512_h,
            384: sha384_h,
            256: sha256_h,
            224: sha224_h,
        }

        assert digest_width in [
            224,
            256,
            384,
            512,
        ], f"Unsupported digest width for sha256: {digest_width}"

        self._h = init_hash[digest_width]
        self._digest_width = digest_width
        self._encoding = encoding
        self._debug = debug
        self._dbg_hash_values = []
        self.round_computations = []
        self.blocks = []

    def process(self, message):
        _pre_message = self._pre_processing(message)
        l = len(_pre_message)
        N = l // 128

        if self._debug:
            print(f"(N = {N}) -> {l}")

        for m in range(0, l, 128):
            block = _pre_message[m : m + 128]
            self.blocks.append(block)
            self._process_block(block)
            self._dbg_hash_values.append(self.digest())

        return self.digest()

    def _pre_processing(self, message):
        _bin_message = bytearray(message, encoding=self._encoding)
        ml = len(_bin_message) * 8

        if self._debug:
            print(f"\nMessage length: {ml} bits ", end="")

        _bin_message.append(0x80)
        while (len(_bin_message) + 16) % 128 != 0:
            _bin_message.append(0x00)

        # Add ml as two 64 bit words
        _bin_message += struct.pack(">QQ", (ml & (0xFFFF_FFFF < 32)), ml & 0xFFFF_FFFF)

        return _bin_message

    def _process_block(self, block):
        assert len(block) == 128
        w = [0] * 80

        for i in range(16):
            w[i] = struct.unpack(">Q", block[i * 8 : i * 8 + 8])[0]

        for i in range(16, 80):
            s0 = (
                right_rotate(w[i - 15], 1)
                ^ right_rotate(w[i - 15], 8)
                ^ (w[i - 15] >> 7)
            )
            s1 = (
                right_rotate(w[i - 2], 19)
                ^ right_rotate(w[i - 2], 61)
                ^ (w[i - 2] >> 6)
            )
            w[i] = (w[i - 16] + s0 + w[i - 7] + s1) & 0xFFFFFFFFFFFFFFFF

        a, b, c, d, e, f, g, h = self._h

        self.round_computations.append(
            " ".join(format(x, "016x") for x in [a, b, c, d, e, f, g, h])
        )

        for i in range(80):
            s1 = right_rotate(e, 14) ^ right_rotate(e, 18) ^ right_rotate(e, 41)
            ch = (e & f) ^ (~e & g)
            temp1 = (h + s1 + ch + self.k[i] + w[i]) & 0xFFFFFFFFFFFFFFFF
            s0 = right_rotate(a, 28) ^ right_rotate(a, 34) ^ right_rotate(a, 39)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (s0 + maj) & 0xFFFFFFFFFFFFFFFF

            h = g
            g = f
            f = e
            e = (d + temp1) & 0xFFFFFFFFFFFFFFFF
            d = c
            c = b
            b = a
            a = (temp1 + temp2) & 0xFFFFFFFFFFFFFFFF

            self.round_computations.append(
                " ".join(format(x, "016x") for x in [a, b, c, d, e, f, g, h])
            )

        self._h[0] = (self._h[0] + a) & 0xFFFFFFFFFFFFFFFF
        self._h[1] = (self._h[1] + b) & 0xFFFFFFFFFFFFFFFF
        self._h[2] = (self._h[2] + c) & 0xFFFFFFFFFFFFFFFF
        self._h[3] = (self._h[3] + d) & 0xFFFFFFFFFFFFFFFF
        self._h[4] = (self._h[4] + e) & 0xFFFFFFFFFFFFFFFF
        self._h[5] = (self._h[5] + f) & 0xFFFFFFFFFFFFFFFF
        self._h[6] = (self._h[6] + g) & 0xFFFFFFFFFFFFFFFF
        self._h[7] = (self._h[7] + h) & 0xFFFFFFFFFFFFFFFF

    def digest(self):
        digest = "".join(format(x, "016x") for x in self._h)
        end_idx = int((self._digest_width / 4))
        return digest[0:end_idx]

    def _dbg_digest(self):
        N = len(self._dbg_hash_values)

        if N > 1:
            for i in range(N - 1):
                print(f"Intermediate hash value (H({i})): {self._dbg_hash_values[i]}")

        print(f"Final hash value: {self._dbg_hash_values[-1]}")
