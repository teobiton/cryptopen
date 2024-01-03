# Copyright 2023 - cryptopen contributors 
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

# Default parameters values
set DataWidth   64
set AddrWidth   32
set ByteAlign   1
set DigestWidth 256

# Default top level
set top_level sha1

# Process tclargs field
set num_arg $argc
if {$num_arg > 0} {
    for {set i 0} {$i < $num_arg} {incr i} {
        set arg [lindex $argv $i]
        if {[regexp {^data_width=(.*)$} $arg match val] == 1} {
            set DataWidth $val
        }
        if {[regexp {^addr_width=(.*)$} $arg match val] == 1} {
            set AddrWidth $val
        }
        if {[regexp {^byte_align=(.*)$} $arg match val] == 1} {
            set ByteAlign $val
        }
        if {[regexp {^digest_width=(.*)$} $arg match val] == 1} {
            set DigestWidth $val
        }
        if {[regexp {^top_level=(.*)$} $arg match val] == 1} {
            set top_level $val
        }
    }
}

# Force DigestWidth parameter for the SHA-1 algorithm
if {$top_level == "sha1"} {
    set DigestWidth 160
}

# Add RTL sources from generated file
source scripts/read_rtl_sources.tcl

# Set top level module
set_property top $top_level [current_fileset]
update_compile_order -fileset sources_1

# Read global constraint file
add_files -fileset constrs_1 -norecurse constraints/$project.xdc

# Elaborate RTL design with generic values
synth_design -generic DataWidth=$DataWidth -generic AddrWidth=$AddrWidth -generic DigestWidth=$DigestWidth -generic ByteAlign=$ByteAlign -rtl -name rtl_1

set_property STEPS.SYNTH_DESIGN.ARGS.RETIMING true [get_runs synth_1]

# Synthesis
launch_runs synth_1
wait_on_run synth_1
open_run synth_1

exec mkdir -p reports/
exec rm -rf reports/*

# Timing checks and reports
check_timing -verbose                                                   -file reports/$project.check_timing.rpt
report_timing -max_paths 20 -nworst 20 -delay_type max -sort_by slack   -file reports/$project.timing_WORST_20.rpt
report_timing -nworst 1 -delay_type max -sort_by group                  -file reports/$project.timing.rpt
report_utilization -hierarchical                                        -file reports/$project.utilization.rpt
report_cdc                                                              -file reports/$project.cdc.rpt
report_clock_interaction                                                -file reports/$project.clock_interaction.rpt

# Implementation
launch_runs impl_1
wait_on_run impl_1

exec mkdir -p reports/
exec rm -rf reports/*

# Final timing checks and reports
check_timing                                                            -file reports/${project}.check_timing.rpt
report_timing -max_paths 20 -nworst 20 -delay_type max -sort_by slack   -file reports/${project}.timing_WORST_20.rpt
report_timing -nworst 1 -delay_type max -sort_by group                  -file reports/${project}.timing.rpt
report_utilization -hierarchical                                        -file reports/${project}.utilization.rpt