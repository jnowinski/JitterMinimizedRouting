# Generate satellite network state for Anchor-based LMSR algorithm
import sys
sys.path.append("../../satgenpy")
import satgen
import math
import exputil

# WGS72 value
EARTH_RADIUS = 6378135.0

# Kuiper-630 parameters
ALTITUDE_M = 630000
SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(30.0))
MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))
MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

NUM_ORBS = 21
NUM_SATS_PER_ORB = 30

local_shell = exputil.LocalShell()

dynamic_state_algorithm = "algorithm_jitter_minimized"
output_generated_data_dir = "temp/gen_data"
num_threads = 1
time_step_ms = 1000
duration_s = 101  # 101 seconds (need t=0 through t=100 for 100s simulation)
name = "kuiper_630_isls_" + dynamic_state_algorithm

print(f"\n{'='*60}")
print(f"Generating: {dynamic_state_algorithm}")
print(f"{'='*60}\n")

# Create directory
local_shell.make_full_dir(output_generated_data_dir + "/" + name)

# Ground stations
print("Generating ground stations...")
with open(output_generated_data_dir + "/" + name + "/ground_stations.basic.txt", "w+") as f_out:
    f_out.write("0,Manila,14.6042,120.9822,0\n")
    f_out.write("1,Tokyo,35.6762,139.6503,0\n")
    f_out.write("2,Sydney,-33.8688,151.2093,0\n")
    f_out.write("3,London,51.5074,-0.1278,0\n")
    f_out.write("4,NewYork,40.7128,-74.0060,0\n")
    f_out.write("5,LosAngeles,34.0522,-118.2437,0\n")
    f_out.write("6,SaoPaulo,-23.5505,-46.6333,0\n")
    f_out.write("7,Nairobi,-1.2864,36.8172,0\n")

satgen.extend_ground_stations(
    output_generated_data_dir + "/" + name + "/ground_stations.basic.txt",
    output_generated_data_dir + "/" + name + "/ground_stations.txt"
)

# TLEs
print("Generating TLEs...")
satgen.generate_tles_from_scratch_with_sgp(
    output_generated_data_dir + "/" + name + "/tles.txt",
    "Kuiper-630",
    NUM_ORBS,
    NUM_SATS_PER_ORB,
    True,
    51.9,
    0.0000001,
    0.0,
    14.80
)

# ISLs
print("Generating ISLs...")
satgen.generate_plus_grid_isls(
    output_generated_data_dir + "/" + name + "/isls.txt",
    NUM_ORBS,
    NUM_SATS_PER_ORB,
    isl_shift=0,
    idx_offset=0
)

# Description
print("Generating description...")
satgen.generate_description(
    output_generated_data_dir + "/" + name + "/description.txt",
    MAX_GSL_LENGTH_M,
    MAX_ISL_LENGTH_M
)

# GSL interfaces
ground_stations = satgen.read_ground_stations_extended(
    output_generated_data_dir + "/" + name + "/ground_stations.txt"
)

print("Generating GSL interfaces info...")
satgen.generate_simple_gsl_interfaces_info(
    output_generated_data_dir + "/" + name + "/gsl_interfaces_info.txt",
    NUM_ORBS * NUM_SATS_PER_ORB,
    len(ground_stations),
    len(ground_stations),
    1,
    len(ground_stations),
    1
)

# Forwarding state
print("Generating forwarding state with anchor-based LMSR...")
satgen.help_dynamic_state(
    output_generated_data_dir,
    num_threads,
    name,
    time_step_ms,
    duration_s,
    MAX_GSL_LENGTH_M,
    MAX_ISL_LENGTH_M,
    dynamic_state_algorithm,
    False  # Disable verbose to reduce output
)

print("Done!\n")
