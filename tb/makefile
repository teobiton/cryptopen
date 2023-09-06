# Cocotb makefile

TOPLEVEL_LANG = verilog
SIM = verilator

# Directories definition
TB_DIRECTORY = $(shell pwd)
HW_DIRECTORY = $(shell dirname $(TB_DIRECTORY))/hw

# Default verilog file to test
VERILOG_FILE = prim/ch.sv
TOPLEVEL     = prim_generic_ch

# Test to simulate
MODULE = test_prim_ch

# Pointing to the VHDL file to test
VERILOG_SOURCES = $(HW_DIRECTORY)/$(VERILOG_FILE)

### Testbench arguments
ITERATIONS := 10 # Number of random tests ran

# Plus arguments retrieved in Cocotb tests
PLUSARGS = +ITERATIONS=$(ITERATIONS)

# Verilator extra arguments to build waves
EXTRA_ARGS += --trace --trace-structs

include $(shell cocotb-config --makefiles)/Makefile.sim

