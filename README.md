# sha1

## Introduction

This project is a SystemVerilog implementation of the SHA-1 cryptographic hash function. 
It is based on the specification in [NIST FIPS 180-2](doc/fips180-2.pdf).

The implementation is still a work in progress.

## Implementation details

The **sha1** project is organized as following:
- hw - RTL source files (SystemVerilog)
- tb  - Testbenches for the RTL files using Cocotb
- doc - documentation with **sha1** high-level specification and technical document

The *hw* folder contains the top-level implementation as well as submodules in *prim*.
The submodules are **sha1** functions that are used in several places.

## Cocotb

The module and its submodules are tested using cocotb.
Cocotb is a Python framework for verification.

All cocotb tests are in *tb*.
Every submodule has its own test suite with Python implementations of their function and randomized tests.

## Purpose

The final goal is to provide a functional OpenSource implementation that can be used in System on Chips. This will require a extensive testbench and a flow with synthesis tools to use the **sha1** modules on a FPGA board.