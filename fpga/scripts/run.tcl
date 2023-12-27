
# Add RTL sources from generated file
source scripts/read_rtl_sources.tcl

set_property top $::env(TOP_LEVEL) [current_fileset]

if {$::env(BOARD) eq "genesys2"} {
    read_verilog -sv util/genesysii.svh
    set file "util/genesysii.svh"
} elseif {$::env(BOARD) eq "spartan7"} {
    read_verilog -sv util/spartan7.svh
    set file "util/spartan7.svh"
} else {
    exit 1
}

set file_obj [get_files -of_objects [get_filesets sources_1] [list "*$file"]]
set_property -dict { file_type {Verilog Header} is_global_include 1} -objects $file_obj

update_compile_order -fileset sources_1

add_files -fileset constrs_1 -norecurse constraints/$project.xdc

synth_design -rtl -name rtl_1

set_property STEPS.SYNTH_DESIGN.ARGS.RETIMING true [get_runs synth_1]

launch_runs synth_1
wait_on_run synth_1
open_run synth_1

exec mkdir -p reports/
exec rm -rf reports/*

check_timing -verbose                                                   -file reports/$project.check_timing.rpt
report_timing -max_paths 100 -nworst 100 -delay_type max -sort_by slack -file reports/$project.timing_WORST_100.rpt
report_timing -nworst 1 -delay_type max -sort_by group                  -file reports/$project.timing.rpt
report_utilization -hierarchical                                        -file reports/$project.utilization.rpt
report_cdc                                                              -file reports/$project.cdc.rpt
report_clock_interaction                                                -file reports/$project.clock_interaction.rpt

launch_runs impl_1
wait_on_run impl_1
launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1
open_run impl_1

# reports
exec mkdir -p reports/
exec rm -rf reports/*
check_timing                                                            -file reports/${project}.check_timing.rpt
report_timing -max_paths 20 -nworst 20 -delay_type max -sort_by slack   -file reports/${project}.timing_WORST_100.rpt
report_timing -nworst 1 -delay_type max -sort_by group                  -file reports/${project}.timing.rpt
report_utilization -hierarchical                                        -file reports/${project}.utilization.rpt