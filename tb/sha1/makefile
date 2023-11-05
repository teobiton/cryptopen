# Cocotb makefile

TOPLEVEL_LANG = verilog
SIM = verilator

# Directories definition
SHA_TB_DIRECTORY = $(shell pwd)
TB_DIRECTORY = $(shell dirname $(SHA_TB_DIRECTORY))
ITF_DIRECTORY = $(shell dirname $(TB_DIRECTORY))/hw/interface
SHA_DIRECTORY = $(shell dirname $(TB_DIRECTORY))/hw/sha1

# Default verilog file to test
TOPLEVEL = sha1

# Test to simulate
MODULE = test_top

# Pointing to the verilog files to test
VERILOG_SOURCES = $(SHA_DIRECTORY)/sha1.sv $(ITF_DIRECTORY)/simple_reg_interface.sv

### Testbench arguments
ITERATIONS := 10 # Number of random tests ran

# Verilator extra arguments to build waves
EXTRA_ARGS += --trace --trace-structs

include $(shell cocotb-config --makefiles)/Makefile.sim

