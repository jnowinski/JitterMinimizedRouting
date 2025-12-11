import exputil
import os

local_shell = exputil.LocalShell()

# Cleanup
local_shell.remove_force_recursive("temp/runs_minimal")
local_shell.remove_force_recursive("temp/pdf_minimal")
local_shell.remove_force_recursive("temp/data_minimal")

# Create run directory for Manila -> Tokyo
run_dir = "temp/runs_minimal/naive_lmsr_Manila_to_Tokyo"
local_shell.remove_force_recursive(run_dir)
local_shell.make_full_dir(run_dir)

# Copy and configure template
local_shell.copy_file("templates/template_tcp_a_b_config_ns3.properties", run_dir + "/config_ns3.properties")

# Configure for minimal test
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[SATELLITE-NETWORK]", "kuiper_210_minimal_algorithm_lmsr")
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[DYNAMIC-STATE]", "dynamic_state_1000ms_for_41s")
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[DYNAMIC-STATE-UPDATE-INTERVAL-NS]", str(1000 * 1000 * 1000))
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[SIMULATION-END-TIME-NS]", str(40 * 1000 * 1000 * 1000))
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[ISL-DATA-RATE-MEGABIT-PER-S]", "10.0")
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[GSL-DATA-RATE-MEGABIT-PER-S]", "10.0")
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[ISL-MAX-QUEUE-SIZE-PKTS]", "100")
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[GSL-MAX-QUEUE-SIZE-PKTS]", "100")
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[ISL-UTILIZATION-TRACKING-INTERVAL-NS-COMPLETE]", 
                                      "isl_utilization_tracking_interval_ns=" + str(1000 * 1000 * 1000))
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[ENABLE-ISL-UTILIZATION-TRACKING]", "true")
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[TCP-SOCKET-TYPE]", "TcpNewReno")

# Manila (GS 0 = node 210) -> Tokyo (GS 1 = node 211)
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[FROM]", "210")
local_shell.sed_replace_in_file_plain(run_dir + "/config_ns3.properties",
                                      "[TO]", "211")

# TCP configuration
local_shell.copy_file("templates/template_tcp_a_b_schedule.csv", run_dir + "/schedule.csv")
local_shell.sed_replace_in_file_plain(run_dir + "/schedule.csv", "[FROM]", "210")
local_shell.sed_replace_in_file_plain(run_dir + "/schedule.csv", "[TO]", "211")
local_shell.sed_replace_in_file_plain(run_dir + "/schedule.csv", "[RATE-MEGABIT-PER-S]", "10.0")
# Start at t=2s when both GS have coverage
local_shell.sed_replace_in_file_plain(run_dir + "/schedule.csv", "[START-TIME-NS]", str(2 * 1000 * 1000 * 1000))
local_shell.sed_replace_in_file_plain(run_dir + "/schedule.csv", "[DURATION-NS]", str(38 * 1000 * 1000 * 1000))
local_shell.sed_replace_in_file_plain(run_dir + "/schedule.csv", "[TCP-SOCKET-TYPE]", "TcpNewReno")

print(f"Created minimal run configuration in {run_dir}")
print("Run directory ready for ns-3 simulation")
