# Copyright 2023 - cryptopen contributors 
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

# Cocotb makefile

TOPLEVEL_LANG = verilog
SIM = verilator

# Default verilog file to test
TOPLEVEL ?= sha1

# Test to simulate
MODULE ?= test_tops

# Directories definition
TB_DIRECTORY  = $(shell pwd)
ROOT_DIRECTORY = $(shell dirname $(TB_DIRECTORY))
HW_DIRECTORY  = $(ROOT_DIRECTORY)/hw
ITF_DIRECTORY = $(HW_DIRECTORY)/interface
CORE_DIRECTORY = $(HW_DIRECTORY)/$(TOPLEVEL)

CORE_SOURCES := $(shell cat $(CORE_DIRECTORY)/Flist.$(TOPLEVEL))

# Pointing to the verilog files to test
VERILOG_SOURCES = $(addprefix $(ROOT_DIRECTORY)/, $(CORE_SOURCES)) $(ITF_DIRECTORY)/simple_reg_interface.sv

# Verilator extra arguments to build waves
EXTRA_ARGS += --trace --trace-structs

include $(shell cocotb-config --makefiles)/Makefile.sim

