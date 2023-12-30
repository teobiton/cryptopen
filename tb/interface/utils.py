from typing import Dict

# Base addresses
CTRL_ADDR = 0x000
BLOCK_ADDR = 0x100
DIGEST_ADDR = 0x200


MAPPING: Dict[str, str] = {
    "reqdata": "reqdata_i",
    "reqaddr": "reqaddr_i",
    "reqvalid": "reqvalid_i",
    "reqwrite": "reqwrite_i",
    "reqready": "reqready_o",
    "reqstrobe": "reqstrobe_i",
    "rspready": "rspready_i",
    "rspvalid": "rspvalid_o",
    "rspdata": "rspdata_o",
    "rsperror": "rsperror_o",
}


def align(addr: int, bytealign: bool):
    step = 8 if bytealign else 32
    return int(addr / step)
