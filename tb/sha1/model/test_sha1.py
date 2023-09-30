from sha1 import sha1


def test_one_block_message() -> None:
    """One-block message from FIPS SHA1 examples"""

    message: str = "abc"

    sha1_model = sha1(debug=True, encoding="ascii")

    sha1_model.process(message)
    sha1_model._dbg_digest()

    assert sha1_model.digest() == "a9993e364706816aba3e25717850c26c9cd0d89d"


def test_multi_block_message() -> None:
    """Multi-block message from FIPS SHA1 examples"""

    message: str = "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"

    sha1_model = sha1(debug=True, encoding="ascii")

    sha1_model.process(message)
    sha1_model._dbg_digest()

    assert sha1_model._dbg_hash_values[0] == "f4286818c37b27ae0408f581846771484a566572"
    assert sha1_model.digest() == "84983e441c3bd26ebaae4aa1f95129e5e54670f1"


def test_long_message() -> None:
    """Long message from FIPS SHA1 examples"""

    message: str = "a" * 1_000_000

    # This message is too long to display debug logs
    sha1_model = sha1(debug=True, encoding="ascii")

    sha1_model.process(message)

    assert sha1_model.digest() == "34aa973cd4c4daa4f61eeb2bdbad27316534016f"
