import cocotb
from cocotb.triggers import Timer

from random import getrandbits

ITERATIONS = int(cocotb.plusargs["ITERATIONS"])

from model.sha1 import ch


@cocotb.test()
async def directed_tests(dut) -> None:
    """Directed tests with explicit values"""

    in0: int = 0xFFFF_F000
    in1: int = 0x000F_FFFF
    in2: int = 0xF0F0_F0F0

    expected_ch: int = 0xF0FF_0000

    dut.in0_i.value = in0
    dut.in1_i.value = in1
    dut.in2_i.value = in2

    await Timer(10, units="ns")

    ch_o: int = int(dut.ch_o.value)

    assert ch_o == expected_ch, (
        f"Expected Choose function output to be {expected_ch:#x}, " f"got {ch_o:#x}"
    )


@cocotb.test()
async def random_tests(dut) -> None:
    """Tests with random values"""

    in0: int = 0x0
    in1: int = 0x0
    in2: int = 0x0

    dut._log.info(f"Random tests with {ITERATIONS} iterations.")

    for idx in range(ITERATIONS):
        in0 = getrandbits(32)
        in1 = getrandbits(32)
        in2 = getrandbits(32)

        expected_ch: int = ch(in0, in1, in2)

        dut.in0_i.value = in0
        dut.in1_i.value = in1
        dut.in2_i.value = in2

        await Timer(10, units="ns")

        ch_o: int = int(dut.ch_o.value)

        assert ch_o == expected_ch, (
            f"Index {idx}: "
            f"Expected Choose function output to be {expected_ch:#x}, "
            f"got {ch_o:#x}"
        )
