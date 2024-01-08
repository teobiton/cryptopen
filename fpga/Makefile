# Copyright 2023 @ cryptopen contributors 
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

# Root path
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
FPGA_DIR := $(dir $(MAKEFILE_PATH))
ROOT_DIR := $(shell dirname $(FPGA_DIR))

SCRIPTS_DIR := $(ROOT_DIR)/fpga/scripts
HW_DIR      := $(ROOT_DIR)/hw

# Board name for synthesis and implementation
BOARD ?= spartan7

ifeq ($(BOARD), genesys2)
	XILINX_PART   := xc7k325tffg900-2
	XILINX_BOARD  := digilentinc.com:genesys2:part0:1.1
else ifeq ($(BOARD), spartan7)
	XILINX_PART   := xc7s100fgga676-2
	XILINX_BOARD  := xilinx.com:sp701:part0:1.0
else ifeq ($(BOARD), artix7)
	XILINX_PART   := xc7a200tfbg676-2
	XILINX_BOARD  := xilinx.com:ac701:part0:1.4
else
$(error Unknown board - supported: genesys2, spartan7)
endif

# Top level module to compile
TOP_LEVEL  ?= sha256

# RTL parameters
DATA_WIDTH   ?= 64
ADDR_WIDTH   ?= 32
BYTE_ALIGN   ?= 1
DIGEST_WIDTH ?= 256

# RTL sources paths
CORE_DIR := $(HW_DIR)/$(TOP_LEVEL)

# Gather all RTL sources
CORE_SRC := $(shell cat $(CORE_DIR)/Flist.$(TOP_LEVEL))
FPGA_SRC := $(addprefix $(ROOT_DIR)/, $(CORE_SRC))

# Vivado command and flags
VIVADO      ?= vivado
VIVADOFLAGS ?= -nojournal -mode batch -source $(SCRIPTS_DIR)/project.tcl

# Tcl arguments
TCLARGS = -tclargs \
		  top_level=$(TOP_LEVEL)   \
		  part=$(XILINX_PART)      \
		  board=$(XILINX_BOARD)    \
		  data_width=$(DATA_WIDTH) \
		  addr_width=$(ADDR_WIDTH) \
		  byte_align=$(BYTE_ALIGN) \
		  digest_width=$(DIGEST_WIDTH)

fpga:
	@bash $(SCRIPTS_DIR)/checker.sh $(TOP_LEVEL) $(DIGEST_WIDTH) $(DATA_WIDTH) $(ADDR_WIDTH) $(BYTE_ALIGN)
	
	@echo "[FPGA] Generate sources"
	@rm -f $(SCRIPTS_DIR)/read_rtl_sources.tcl
	@echo read_verilog -sv {$(FPGA_SRC)} > $(SCRIPTS_DIR)/read_rtl_sources.tcl
	
	@echo "[FPGA] Run synthesis, implementation and generate bitstream"
	@echo "[FPGA] Top level = $(TOP_LEVEL)"
	@echo "[FPGA] Board     = $(BOARD)"
	@echo "[FPGA] RTL parameters :"
	@echo "       DataWidth   = $(DATA_WIDTH)"
	@echo "       AddrWidth   = $(ADDR_WIDTH)"
	@echo "       ByteAlign   = $(BYTE_ALIGN)"
	@echo "       DigestWidth = $(DIGEST_WIDTH)"
	
	$(VIVADO) $(VIVADOFLAGS) -source $(SCRIPTS_DIR)/run.tcl $(TCLARGS)

.PHONY: fpga

clean:
	rm -rf *.log *.jou *.str *.mif *.xpr $(SCRIPTS_DIR)/vivado*
	rm -rf cryptopen.*
	rm -rf reports
	rm -f $(SCRIPTS_DIR)/read_rtl_sources.tcl