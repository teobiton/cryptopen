# Cryptopen  🔐

Welcome to Cryptopen, a library of hardware implementations of cryptographic algorithms. All implementations are made using SystemVerilog, and focus is on the most widely used algorithms where hardware accelerators shine.

🚧 **Work in Progress:** The open source IP library is a work in progress and current focus is on FPGA development flow, synthesis flow, security features, SHA-3, whirlpool implementations. Feel free to join in!

🚀 The ultimate goal is to deliver functional open-source implementations ready for integration into System on Chips. To achieve this, we're investing in comprehensive testbenches and a seamless flow with synthesis tools. All of this using other cool open source projects. Also, the main idea behind this project is to learn as much as possible on ASIC/FPGA projects.

Cryptopen is organized as follows:

- **hw** - RTL source files (SystemVerilog)
- **tb** - Testbenches for the RTL files using Cocotb
- **fpga** - FPGA makefile flow based on Vivado 2020.1
- **doc** - Documentation with high-level specifications and technical documents

In the *hw* folder, you'll find the top-level implementations as well as supported bus interfaces.

## Tools

Several tools for hardware development are used for various part of the project.

**[Cocotb](https://github.com/cocotb/cocotb)** is a powerful Python framework for hardware verification, seamlessly integrating with SystemVerilog testbenches to streamline the testing process and ensure robust functionality in hardware implementations. Cryptopen fully relies on cocotb to test the IPs and uses version 1.8.0. Runners using pytest and makefile flows are supported for all IPs.

**[Verilator](https://github.com/verilator/verilator)** is a fast and open-source simulator that translates synthesizable Verilog code to efficient C++ or SystemC models, offering rapid simulation for hardware design verification. It is the simulator paired with cocotb in Cryptopen testbenches. The version required is v5.006 or later.

**[Vivado](https://www.xilinx.com/products/design-tools/vivado.html)** is an (not open source but) advanced FPGA design and implementation tool. The FPGA flow relies on Vivado 2020.1.

## FPGA results

Synthesis and implementation done on Spartan-7 and Artix-7 boards give the following estimations.


| IP      | LUTs | FF   | Frequency estimation |
|---------|------|------|----------------------|
| SHA-1   | 1485 | 1504 | 144 MHz              |
| SHA-256 | 2025 | 1863 | 99 MHz               |
| SHA-512 | 4235 | 3503 | 90 MHz               |