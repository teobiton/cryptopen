#!/bin/bash

check_core_params() {
    local top=$1
    local digest_width=$2

    sha256_valid_widths=(224 256)
    sha512_valid_widths=(224 256 384 512)

    case $top in
        "sha1")
            if [ $digest_width -ne 160 ]; then
                echo "[FPGA] Error: $top digest width must be 160." >&2
                exit 1
            fi
            ;;
        "sha256")
            if [[ ! " ${sha256_valid_widths[@]} " =~ " ${digest_width} " ]]; then
                echo "[FPGA] Error: $top digest width must be in: ${sha256_valid_widths[@]}." >&2
                exit 1
            fi
            ;;
        "sha512")
            if [[ ! " ${sha512_valid_widths[@]} " =~ " ${digest_width} " ]]; then
                echo "[FPGA] Error: $top digest width must be in: ${sha512_valid_widths[@]}." >&2
                exit 1
            fi
            ;;
        *)
            echo "[FPGA] Error: Unknown top-level: $top." >&2
            exit 1
            ;;
    esac
}

check_bus_params() {
    local data_width=$1
    local addr_width=$2
    local byte_align=$3

    data_valid_widths=(8 16 32 64 128)
    addr_valid_widths=(16 32 64)

    if [[ ! " ${data_valid_widths[@]} " =~ " ${data_width} " ]]; then
        echo "[FPGA] Error: bus data width must be in: ${data_valid_widths[@]}." >&2
        exit 1
    fi

    if [[ ! " ${addr_valid_widths[@]} " =~ " ${addr_width} " ]]; then
        echo "[FPGA] Error: bus address width must be in: ${addr_valid_widths[@]}." >&2
        exit 1
    fi

    if [ $byte_align -eq 0 ] && [[ $data_width -eq 8 || $data_width -eq 16 ]]; then
        echo "[FPGA] Error: incompatible parameters: ByteAlign = 0, DataWidth must be 32 or more." >&2
        exit 1
    fi
}

# Parse command-line arguments
if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <top> <digest_width> <data_width> <addr_width> <byte_align>" >&2
    exit 1
fi

echo "[FPGA] Check top level and RTL parameters ..."

top=$1
digest_width=$2
data_width=$3
addr_width=$4
byte_align=$5

# Call the functions with command-line arguments
check_core_params "$top" "$digest_width"
echo "[FPGA] Core parameters OK"

check_bus_params "$data_width" "$addr_width" "$byte_align"
echo "[FPGA] Bus parameters  OK"
