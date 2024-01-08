# Copyright 2023 - cryptopen contributors
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import pytest
from sha256_model import sha256


@pytest.mark.parametrize("digest_width", [224, 256])
def test_one_block_message(digest_width) -> None:
    """One-block message from FIPS sha256 examples"""

    message: str = "abc"

    hash_core = sha256(digest_width=digest_width, debug=True, encoding="ascii")

    hash_core.process(message)

    expected_digest = {
        256: "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        224: "23097d223405d8228642a477bda255b32aadbce4bda0b3f7e36c9da7",
    }

    assert hash_core.digest() == expected_digest[digest_width]


@pytest.mark.parametrize("digest_width", [224, 256])
def test_multi_block_message(digest_width) -> None:
    """Multi-block message from FIPS sha256 examples"""

    message: str = "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"

    hash_core = sha256(digest_width=digest_width, debug=True, encoding="ascii")

    hash_core.process(message)

    expected_digest = {
        256: "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1",
        224: "75388b16512776cc5dba5da1fd890150b0c6455cb4f58b1952522525",
    }

    assert hash_core.digest() == expected_digest[digest_width]
