# Copyright 2023 - cryptopen contributors 
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

set project cryptopen

# Default part and board values
set part  xc7s100fgga676-2
set board xilinx.com:sp701:part0:1.0

# Process tclargs field
set num_arg $argc
if {$num_arg > 0} {
    for {set i 0} {$i < $num_arg} {incr i} {
        set arg [lindex $argv $i]
        if {[regexp {^part=(.*)$} $arg match val] == 1} {
            set part $val
        }
        if {[regexp {^board=(.*)$} $arg match val] == 1} {
            set board $val
        }
    }
}

create_project $project . -force -part $part
set_property board_part $board [current_project]

set_param general.maxThreads 8