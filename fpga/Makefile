# Copyright 2023 @ cryptopen contributors 
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

# root path
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
fpga-dir := $(dir $(mkfile_path))
root-dir := $(fpga-dir)..

scripts-dir := $(fpga-dir)/scripts
hw-dir      := $(root-dir)/hw

# Board name for synthesis and implementation
BOARD       ?= spartan7

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

# Interface choice
INTERFACE   ?= simple

_supported_itf = simple

ifeq ($(filter $(INTERFACE), $(_supported_itf)),)
$(error Unknown interface protocol - supported: $(_supported_itf))
endif

# Top level module to compile
TOP_LEVEL  ?= sha256
# Default parameters
DATA_WIDTH ?= 64
ADDR_WIDTH ?= 32
BYTE_ALIGN ?= 1
DIGEST_WIDTH ?= 256

acc-dir := $(hw-dir)/$(TOP_LEVEL)
itf-dir := $(hw-dir)/interface

acc_src := $(acc-dir)/$(TOP_LEVEL).sv \
		   $(acc-dir)/$(TOP_LEVEL)_core.sv

itf_src := $(itf-dir)/$(INTERFACE)_reg_interface.sv

fpga_src = $(acc_src) $(itf_src)

# Vivado cmd and flags
VIVADO ?= vivado
VIVADOFLAGS ?= -nojournal -mode batch -source $(scripts-dir)/project.tcl

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
	@echo "[FPGA] Generate sources"
	@echo read_verilog -sv {$(acc_src)} > $(scripts-dir)/read_rtl_sources.tcl
	@echo read_verilog -sv {$(itf_src)} >> $(scripts-dir)/read_rtl_sources.tcl
	@echo "[FPGA] Run synthesis, implementation and generate bitstream"
	@echo "[FPGA] Top level = $(TOP_LEVEL)"
	@echo "[FPGA] Board = $(BOARD)"
	@echo "[FPGA] RTL parameters :"
	@echo "       DataWidth = $(DATA_WIDTH)"
	@echo "       AddrWidth = $(ADDR_WIDTH)"
	@echo "       ByteAlign = $(BYTE_ALIGN)"
	@echo "       DigestWidth = $(DIGEST_WIDTH) (unused in SHA-1 implementation)"
	$(VIVADO) $(VIVADOFLAGS) -source $(scripts-dir)/run.tcl $(TCLARGS)

.PHONY: fpga

clean:
	rm -rf *.log *.jou *.str *.mif *.xpr cryptopen.cache cryptopen.hw cryptopen.ip_user_files $(scripts-dir)/vivado*
	rm -rf cryptopen.hbs cryptopen.runs
	rm -rf reports
	rm -f $(scripts-dir)/read_rtl_sources.tcl