# Cocotb makefile

TOPLEVEL_LANG = verilog
SIM = verilator

# Directories definition
ITF_TB_DIRECTORY = $(shell pwd)
TB_DIRECTORY = $(shell dirname $(ITF_TB_DIRECTORY))
ITF_DIRECTORY = $(shell dirname $(TB_DIRECTORY))/hw/interface

# Default verilog file to test
VERILOG_FILE = reg_interface.sv
TOPLEVEL     = reg_interface

# Test to simulate
MODULE = test_regs

# Pointing to the verilog files to test
VERILOG_SOURCES = $(ITF_DIRECTORY)/$(VERILOG_FILE)

### Testbench arguments
ITERATIONS := 10 # Number of random tests ran

# Verilator extra arguments to build waves
EXTRA_ARGS += --trace --trace-structs

include $(shell cocotb-config --makefiles)/Makefile.sim

