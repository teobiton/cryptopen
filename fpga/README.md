# FPGA Implementation Flow

This Makefile facilitates the synthesis and implementation of IPs on FPGA boards using Xilinx Vivado. The primary purpose is to compile hardware description language (HDL) code into a bitstream for deployment on supported FPGA boards. The project is structured to support different FPGA boards and interface protocols.

### Project Structure

- **Root Path:** The root path of the project is determined dynamically by the Makefile.
- **Scripts Directory (`scripts`):** Contains Tcl and bash scripts essential for project setup and execution.
- **Hardware Directory (`../hw`):** Houses the hardware description files, organized by IP and interface.

### Board Configuration

The board for synthesis and implementation is specified using the `BOARD` variable. Supported boards include:

- genesys2
- spartan7
- artix7

```bash
make BOARD=genesys2 fpga
```

### Top-Level Module

Specify the top-level module to be compiled using the TOP_LEVEL variable.
This represents the main module in your design.

```bash
make TOP_LEVEL=sha256 fpga
```

The RTL sources for a particular TOP_LEVEL are gathered using its own Flist file, in `$PROJECT_ROOT/hw/$TOP_LEVEL/Flist.$TOP_LEVEL`.

### Interface Configuration

The interface protocol is chosen through the INTERFACE variable.
Currently, the only supported interface is "simple."

```bash
make INTERFACE=simple fpga
```

### RTL Parameters

Define RTL parameters such as data width, address width, byte alignment, and digest width using the corresponding variables (DATA_WIDTH, ADDR_WIDTH, BYTE_ALIGN, DIGEST_WIDTH).

```bash
make DATA_WIDTH=64 ADDR_WIDTH=32 BYTE_ALIGN=1 DIGEST_WIDTH=256 fpga
```

A bash script (`scripts/checker.sh`) is executed upon calling vivado to check that specified RTL parameters and top level are coherent.
