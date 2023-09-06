# Running the tests suite

To test the SystemVerilog design, only open-source software are used.

## Cocotb installation

Cocotb provides an easier way of writing testbenches using Python.
Cocotb installation: https://docs.cocotb.org/en/stable/install.html

```
sudo apt-get install make python3 python3-pip
pip install cocotb
```

## Verilator installation
/!\ verilator is required!
Only version 5.006 or later is supported by Cocotb (v1.8.0).

Verilator installation (on Ubuntu): https://verilator.org/guide/latest/install.html

```
# Prerequisites:
sudo apt-get install git perl python3 make autoconf g++ flex bison ccache help2man
sudo apt-get install libgoogle-perftools-dev numactl perl-doc
sudo apt-get install libfl2  # Ubuntu only (ignore if gives error)
sudo apt-get install libfl-dev  # Ubuntu only (ignore if gives error)
sudo apt-get install zlibc zlib1g zlib1g-dev  # Ubuntu only (ignore if gives error)

git clone https://github.com/verilator/verilator   # Only first time

# Every time you need to build:
unset VERILATOR_ROOT  # For bash
cd verilator
git pull         # Make sure git repository is up-to-date
git tag          # See what versions exist
git checkout master      # Use development branch (e.g. recent bug fixes)
git checkout stable      # Use most recent stable release
git checkout v5.006      # Switch to specified release version

autoconf         # Create ./configure script
./configure      # Configure and create Makefile
make -j `nproc`  # Build Verilator itself (if error, try just 'make')
sudo make install
```
## Run tests

```
make TEST=<test_to_sim>
```

By default: executing `make` runs the tests for the choose primitive function.
This results in the creation of a `dump.vcd` file that can be opened with gtkwave:

```
sudo apt-get install gtkwave
gtkwave dump.vcd
```