# The MIT License (MIT)
#
# Copyright (c) 2020 ETH Zurich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import exputil
import networkload
import random

try:
    from .run_list import *
except (ImportError, SystemError):
    from run_list import *

local_shell = exputil.LocalShell()

local_shell.remove_force_recursive("temp/runs")
local_shell.remove_force_recursive("temp/pdf")
local_shell.remove_force_recursive("temp/data")

# TCP runs
for run in get_tcp_run_list():

    # Prepare run directory
    run_dir = "temp/runs/" + run["name"]
    local_shell.remove_force_recursive(run_dir)
    local_shell.make_full_dir(run_dir)

    # config_ns3.properties
    # local_shell.copy_file("templates/template_tcp_a_b_config_ns3.properties", run_dir + "/config_ns3.properties")
    local_shell.copy_file("templates/template_config_ns3_tcp.properties", run_dir + "/config_ns3.properties")
    # local_shell.copy_file("templates/template_config_ns3_udp.properties", run_dir + "/config_ns3.properties")
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                          "[SATELLITE-NETWORK]", str(run["satellite_network"]))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                          "[DYNAMIC-STATE]", str(run["dynamic_state"]))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                          "[DYNAMIC-STATE-UPDATE-INTERVAL-NS]",
                                          str(run["dynamic_state_update_interval_ns"]))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                          "[SIMULATION-END-TIME-NS]", str(run["simulation_end_time_ns"]))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                          "[ISL-DATA-RATE-MEGABIT-PER-S]", str(run["data_rate_megabit_per_s"]))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                          "[GSL-DATA-RATE-MEGABIT-PER-S]", str(run["data_rate_megabit_per_s"]))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                          "[ISL-MAX-QUEUE-SIZE-PKTS]", str(run["queue_size_pkt"]))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                          "[GSL-MAX-QUEUE-SIZE-PKTS]", str(run["queue_size_pkt"]))
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                          "[ENABLE-ISL-UTILIZATION-TRACKING]",
                                          "true" if run["enable_isl_utilization_tracking"] else "false")
    if run["enable_isl_utilization_tracking"]:
        local_shell.sed_replace_in_file_plain(
            run_dir + "/config_ns3.properties",
            "[ISL-UTILIZATION-TRACKING-INTERVAL-NS-COMPLETE]",
            "isl_utilization_tracking_interval_ns=" + str(run["isl_utilization_tracking_interval_ns"])
        )
    else:
        local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                              "[ISL-UTILIZATION-TRACKING-INTERVAL-NS-COMPLETE]", "")
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                          "[TCP-SOCKET-TYPE]", str(run["tcp_socket_type"]))

    # schedule.csv
    local_shell.copy_file("templates/template_tcp_a_b_schedule.csv", run_dir + "/schedule.csv")
    local_shell.sed_replace_in_file_plain(run_dir + "/schedule.csv", "[FROM]", str(run["from_id"]))
    local_shell.sed_replace_in_file_plain(run_dir + "/schedule.csv", "[TO]", str(run["to_id"]))

    random.seed(123456789)
    random.randint(0, 100000000)  # Legacy reasons
    seed_from_to = random.randint(0, 100000000)
    a = set(range(630, 730))
    list_from_to = networkload.generate_from_to_reciprocated_random_pairing(list(a), seed_from_to)

    # tcp_flow_schedule.csv
    networkload.write_schedule(
        run_dir + "/schedule.csv",
        len(list_from_to),
        list_from_to,
        [1000000000000] * len(list_from_to),
        [0] * len(list_from_to)
    )
    local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                          "[tcp_flow_enable_logging_for_tcp_flow_ids]",
                                          f"set({','.join([str(i) for i in range(0,100)])})")

    # udp_burst_schedule.csv
    # with open(run_dir + "/schedule.csv", "w+") as f_out:
    #     for i in range(len(list_from_to)):
    #         f_out.write(
    #             "%d,%d,%d,%.10f,%d,%d,,\n" % (
    #                 i,
    #                 list_from_to[i][0],
    #                 list_from_to[i][1],
    #                 run["data_rate_megabit_per_s"],
    #                 0,
    #                 1000000000000
    #             )
    #         )
    # local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
    #                                       "[udp_burst_enable_logging_for_udp_burst_ids]",
    #                                       f"set({','.join([str(i) for i in range(0,100)])})")

# Print finish
print("Success: generated ns-3 runs")
