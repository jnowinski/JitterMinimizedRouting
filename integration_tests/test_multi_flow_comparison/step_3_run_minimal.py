import exputil
import os

local_shell = exputil.LocalShell()

run_name = "naive_lmsr_Manila_to_Tokyo"
run_dir = f"temp/runs_minimal/{run_name}"

# Prepare logs directory
logs_ns3_dir = f"{run_dir}/logs_ns3"
local_shell.remove_force_recursive(logs_ns3_dir)
local_shell.make_full_dir(logs_ns3_dir)

# Run the simulation
print(f"Running ns-3 simulation for {run_name}...")
print("This may take a few minutes...")

command = (
    f"cd ../../ns3-sat-sim/simulator && "
    f"./waf --run=\"main_satnet --run_dir='../../integration_tests/test_multi_flow_comparison/{run_dir}'\" "
    f"2>&1 | tee ../../integration_tests/test_multi_flow_comparison/{logs_ns3_dir}/console.txt"
)

local_shell.perfect_exec(command, output_redirect=exputil.OutputRedirect.CONSOLE)

print(f"\nSimulation complete! Results in {run_dir}")
