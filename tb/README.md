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
Only version **5.006** or later is supported by **cocotb v1.8.0**.

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
git checkout v5.006      # Switch to specified release version

autoconf         # Create ./configure script
./configure      # Configure and create Makefile
make -j `nproc`  # Build Verilator itself (if error, try just 'make')
sudo make install
```
## Run tests

It is assumed that verilator is used.

### Makefile flow

```
make TEST=<test_to_sim>
```

By default: executing `make` runs the tests for the Choose primitive function.

### Cocotb runners

Cocotb tests are also written using runners.
This enables support for usage with `pytest`.

`pytest` can be install with `pip install pytest`.
To display cocotb logs when running the tests, the `-s` option must be passed.

### Waves

Both methods result in the creation of a `dump.vcd` file that can be opened with gtkwave:

```
sudo apt-get install gtkwave
gtkwave dump.vcd
```

With `pytest`, the vcd file will be in the test's associated simulation build directory.

## Development

All tests must support both the makefile based and runner based testing.
This allows flexibility and does not require a lot of additional work.
This is also a way to ensure that all tests are run during CI runs.

Moreover, lint checks are enabled using `black` formatter.
`black` can be installed with `pip install blavk`.
