# Cocotb makefile

TOPLEVEL_LANG = verilog
SIM = verilator

# Directories definition
SHA_TB_DIRECTORY = $(shell pwd)
TB_DIRECTORY = $(shell dirname $(SHA_TB_DIRECTORY))
SHA_DIRECTORY = $(shell dirname $(TB_DIRECTORY))/hw/sha256

# Default verilog file to test
TOPLEVEL = sha256_core

# Test to simulate
MODULE = test_core

# Pointing to the verilog files to test
VERILOG_SOURCES = $(SHA_DIRECTORY)/sha256_core.sv

# Verilator extra arguments to build waves
EXTRA_ARGS += --trace --trace-structs -Wno-WIDTH

include $(shell cocotb-config --makefiles)/Makefile.sim

