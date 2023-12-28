# Copyright 2023 @ cryptopen contributors 
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

# Cocotb makefile

TOPLEVEL_LANG = verilog
SIM = verilator

# Directories definition
SHA_TB_DIRECTORY = $(shell pwd)
TB_DIRECTORY = $(shell dirname $(SHA_TB_DIRECTORY))
SHA_DIRECTORY = $(shell dirname $(TB_DIRECTORY))/hw/sha1

# Default verilog file to test
TOPLEVEL = sha1_core

# Test to simulate
MODULE = test_sha1_core

# Pointing to the verilog files to test
VERILOG_SOURCES = $(SHA_DIRECTORY)/sha1_core.sv

# Verilator extra arguments to build waves
EXTRA_ARGS += --trace --trace-structs -Wno-WIDTH

include $(shell cocotb-config --makefiles)/Makefile.sim
