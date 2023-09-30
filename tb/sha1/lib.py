import cocotb
from cocotb.triggers import Timer

from typing import Dict


SHA_MAPPING: Dict[str, str] = {
    "reqdata": "sha_s_reqdata_i",
    "reqaddr": "sha_s_reqaddr_i",
    "reqvalid": "sha_s_reqvalid_i",
    "reqwrite": "sha_s_reqwrite_i",
    "reqready": "sha_s_reqready_o",
    "reqstrobe": "sha_s_reqstrobe_i",
    "rspready": "sha_s_rspready_i",
    "rspvalid": "sha_s_rspvalid_o",
    "rspdata": "sha_s_rspdata_o",
    "rsperror": "sha_s_rsperror_o",
}


@cocotb.coroutine
async def init(sha):
    """Initialize input signals value"""

    """ 

    This would be the correct way to do it.
    But verilator does not support it so the list must be maintained by hand.

    for signal in dir(sha):
        if signal.endswith('_i') and signal != "clk_i":
            print(f"signal found = {signal}")
            sha._id(signal, extended=False).value = 0 
            
    """

    sha.sha_process_i.value = 0
    sha.sha_digestack_i.value = 0

    sha.sha_s_reqdata_i.value = 0
    sha.sha_s_reqaddr_i.value = 0
    sha.sha_s_reqvalid_i.value = 0
    sha.sha_s_reqwrite_i.value = 0
    sha.sha_s_reqstrobe_i.value = 0
    sha.sha_s_rspready_i.value = 0

    sha.rst_ni.value = 0

    await Timer(1, units="ns")
