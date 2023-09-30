# Cocotb makefile

TOPLEVEL_LANG = verilog
SIM = verilator

# Directories definition
PRIM_TB_DIRECTORY = $(shell pwd)
TB_DIRECTORY = $(shell dirname $(PRIM_TB_DIRECTORY))
PRIM_DIRECTORY = $(shell dirname $(TB_DIRECTORY))/hw/prim

# Default verilog file to test
VERILOG_FILE = ch.sv
TOPLEVEL     = prim_generic_ch

# Test to simulate
MODULE = test_prim_ch

# Pointing to the verilog files to test
VERILOG_SOURCES = $(PRIM_DIRECTORY)/$(VERILOG_FILE)

### Testbench arguments
ITERATIONS := 10 # Number of random tests ran

# Verilator extra arguments to build waves
EXTRA_ARGS += --trace --trace-structs

include $(shell cocotb-config --makefiles)/Makefile.sim

