from sha256 import sha256


def test_one_block_message() -> None:
    """One-block message from FIPS sha256 examples"""

    message: str = "abc"

    sha256_model = sha256(debug=True, encoding="ascii")

    sha256_model.process(message)
    sha256_model._dbg_digest()

    assert (
        sha256_model.digest()
        == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_multi_block_message() -> None:
    """Multi-block message from FIPS sha256 examples"""

    message: str = "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"

    sha256_model = sha256(debug=True, encoding="ascii")

    sha256_model.process(message)
    sha256_model._dbg_digest()

    assert (
        sha256_model._dbg_hash_values[0]
        == "85e655d6417a17953363376a624cde5c76e09589cac5f811cc4b32c1f20e533a"
    )

    assert (
        sha256_model.digest()
        == "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"
    )
