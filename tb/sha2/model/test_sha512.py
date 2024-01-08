# Copyright 2023 - cryptopen contributors
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import pytest
from sha512_model import sha512


@pytest.mark.parametrize("digest_width", [224, 256, 384, 512])
def test_one_block_message(digest_width) -> None:
    """One-block message from FIPS sha512 examples"""

    message: str = "abc"

    hash_core = sha512(digest_width=digest_width, debug=True, encoding="ascii")

    hash_core.process(message)

    expected_digest = {
        512: "ddaf35a193617abacc417349ae20413112e6fa4e89a97ea20a9eeee64b55d39a2192992a274fc1a836ba3c23a3feebbd454d4423643ce80e2a9ac94fa54ca49f",
        384: "cb00753f45a35e8bb5a03d699ac65007272c32ab0eded1631a8b605a43ff5bed8086072ba1e7cc2358baeca134c825a7",
        256: "53048e2681941ef99b2e29b76b4c7dabe4c2d0c634fc6d46e0e2f13107e7af23",
        224: "4634270f707b6a54daae7530460842e20e37ed265ceee9a43e8924aa",
    }

    assert hash_core.digest() == expected_digest[digest_width]


@pytest.mark.parametrize("digest_width", [224, 256, 384, 512])
def test_multi_block_message(digest_width) -> None:
    """Multi-block message from FIPS sha512 examples"""

    message: str = "abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu"

    hash_core = sha512(digest_width=digest_width, debug=True, encoding="ascii")

    hash_core.process(message)

    expected_digest = {
        512: "8e959b75dae313da8cf4f72814fc143f8f7779c6eb9f7fa17299aeadb6889018501d289e4900f7e4331b99dec4b5433ac7d329eeb6dd26545e96e55b874be909",
        384: "09330c33f71147e83d192fc782cd1b4753111b173b3b05d22fa08086e3b0f712fcc7c71a557e2db966c3e9fa91746039",
        256: "3928e184fb8690f840da3988121d31be65cb9d3ef83ee6146feac861e19b563a",
        224: "23fec5bb94d60b23308192640b0c453335d664734fe40e7268674af9",
    }

    assert hash_core.digest() == expected_digest[digest_width]
