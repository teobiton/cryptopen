# Copyright 2023 - cryptopen contributors 
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

# Cocotb makefile

TOPLEVEL_LANG = verilog
SIM = verilator

# Directories definition
ITF_TB_DIRECTORY = $(shell pwd)
TB_DIRECTORY = $(shell dirname $(ITF_TB_DIRECTORY))
ITF_DIRECTORY = $(shell dirname $(TB_DIRECTORY))/hw/interface

# Default verilog file to test
VERILOG_FILE = simple_reg_interface.sv
TOPLEVEL     = simple_reg_interface

# Test to simulate
MODULE = test_simple_interface

# Pointing to the verilog files to test
VERILOG_SOURCES = $(ITF_DIRECTORY)/$(VERILOG_FILE)

### Testbench arguments
ITERATIONS := 10 # Number of random tests ran

# Verilator extra arguments to build waves
EXTRA_ARGS += --trace --trace-structs

include $(shell cocotb-config --makefiles)/Makefile.sim

clean::
	rm -f *.xml

