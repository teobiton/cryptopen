# board name for bitstream generation. Currently supported: genesys2
BOARD       ?= spartan7
# Top level module to compile
TOP_LEVEL   ?= sha256
# Interface choice
INTERFACE   ?= simple

# root path
mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
fpga-dir := $(dir $(mkfile_path))
root-dir := $(fpga-dir)..

work-dir := work-dir
hw-dir  := $(root-dir)/hw
itf-dir := $(hw-dir)/interface
acc-dir := $(hw-dir)/$(TOP_LEVEL)

acc_src := $(acc-dir)/$(TOP_LEVEL).sv \
           $(acc-dir)/$(TOP_LEVEL)_core.sv

itf_src := $(itf-dir)/$(INTERFACE)_reg_interface.sv

fpga_src = $(acc_src) $(itf_src)

ifeq ($(BOARD), genesys2)
	XILINX_PART   := xc7k325tffg900-2
	XILINX_BOARD  := digilentinc.com:genesys2:part0:1.1
	CLK_PERIOD_NS := 10
else ifeq ($(BOARD), spartan7)
	XILINX_PART   := xc7s100fgga676-2
	XILINX_BOARD  := xilinx.com:sp701:part0:1.0
	CLK_PERIOD_NS := 10
else
$(error Unknown board - supported: genesys2, spartan7)
endif

ifeq ($(filter $(INTERFACE), simple apb),)
$(error Unknown interface protocol - supported: simple, apb)
endif

VIVADO ?= vivado
VIVADOFLAGS ?= -nojournal -mode batch -source scripts/project.tcl

fpga:
	@echo "[FPGA] Generate sources"
	@echo read_verilog -sv {$(acc_src)} > scripts/read_rtl_sources.tcl
	@echo read_verilog -sv {$(itf_src)} >> scripts/read_rtl_sources.tcl
	@echo "[FPGA] Run synthesis, implementation and generate bitstream"
	mkdir -p $(work-dir)
	TOP_LEVEL=$(TOP_LEVEL) \
	BOARD=$(BOARD) XILINX_PART=$(XILINX_PART) \
	XILINX_BOARD=$(XILINX_BOARD) CLK_PERIOD_NS=$(CLK_PERIOD_NS) \
	$(VIVADO) $(VIVADOFLAGS) -source scripts/run.tcl

.PHONY: fpga

clean:
	rm -rf *.log *.jou *.str *.mif *.xpr $(work-dir) cryptopen.cache cryptopen.hw cryptopen.ip_user_files scripts/vivado*
	rm -rf cryptopen.hbs cryptopen.runs
	rm -rf reports
	rm -f scripts/read_rtl_sources.tcl