set project cryptopen

create_project $project . -force -part $::env(XILINX_PART)
set_property board_part $::env(XILINX_BOARD) [current_project]

set_param general.maxThreads 8