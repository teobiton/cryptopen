# Copyright 2023 - cryptopen contributors 
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

create_clock -period 10.000 -name clk -waveform {0.000 5.000} [get_ports clk_i]