# Generate test run for free_gs_one_sat_many algorithm

import exputil

local_shell = exputil.LocalShell()

# Prepare run directory for free algorithm test
run_dir = "temp/runs/free_gs_one_sat_many_630_to_631_with_TcpNewReno_at_10_Mbps"
local_shell.remove_force_recursive(run_dir)
local_shell.make_full_dir(run_dir)

# config_ns3.properties
with open(run_dir + "/config_ns3.properties", "w") as f:
    f.write("""simulation_end_time_ns=100000000000
simulation_seed=123456789

satellite_network_dir="../../gen_data/kuiper_630_isls_algorithm_free_gs_one_sat_many_only_over_isls"
satellite_network_routes_dir="../../gen_data/kuiper_630_isls_algorithm_free_gs_one_sat_many_only_over_isls/dynamic_state_1000ms_for_100s"
dynamic_state_update_interval_ns=1000000000

isl_data_rate_megabit_per_s=10.0
gsl_data_rate_megabit_per_s=10.0
isl_max_queue_size_pkts=100
gsl_max_queue_size_pkts=100

enable_isl_utilization_tracking=true
isl_utilization_tracking_interval_ns=1000000000

tcp_socket_type=TcpNewReno

enable_tcp_flow_scheduler=true
tcp_flow_schedule_filename="schedule.csv"
tcp_flow_enable_logging_for_tcp_flow_ids=set(0)
""")

# schedule.csv
with open(run_dir + "/schedule.csv", "w") as f:
    f.write("0,630,631,10000000,0,,\n")  # 80 Mbit from Manila to Dalian

print(f"Generated run configuration in {run_dir}")
