# cryptopen

## Introduction

This project is a library of hardware implementation of cryptographic algorithms.
The primary language used is SystemVerilog.
The chosen algorithms are the most commonly used and the ones where hardware accelerators are appreciated.

The implementation is still a work in progress.
Current development is for the sha1 algorithm.
The next ones will be other secure hash algorithms.

## Implementation details

The cryptopen project is organized as following:
- hw - RTL source files (SystemVerilog)
- tb  - Testbenches for the RTL files using Cocotb
- doc - documentation with high-level specification and technical documents

The *hw* folder contains the top-level implementations.
The primitives are algorithmic functions that are used in several places.

## Cocotb

The modules and their submodules are tested using cocotb.
Cocotb is a Python framework for verification.

All cocotb tests are in *tb*.
Every submodule has its own test suite with Python implementations of their function and randomized tests.

## Purpose

The final goal is to provide functional OpenSource implementations that can be used in System on Chips. 
This will require extensive testbenches and a flow with synthesis tools.