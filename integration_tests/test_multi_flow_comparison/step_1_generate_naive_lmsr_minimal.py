# Minimal test: Generate satellite network state for Naive-based LMSR algorithm
# ONLY 2 ground stations to test caching speedup
import sys
sys.path.append("../../satgenpy")
import satgen
import math
import exputil

# WGS72 value
EARTH_RADIUS = 6378135.0

# Kuiper-630 parameters
ALTITUDE_M = 630000
# Increase satellite cone angle to 50 degrees for maximum coverage
# (Lower elevation angle means satellites further from zenith are visible)
SATELLITE_CONE_RADIUS_M = ALTITUDE_M / math.tan(math.radians(50.0))
MAX_GSL_LENGTH_M = math.sqrt(math.pow(SATELLITE_CONE_RADIUS_M, 2) + math.pow(ALTITUDE_M, 2))
MAX_ISL_LENGTH_M = 2 * math.sqrt(math.pow(EARTH_RADIUS + ALTITUDE_M, 2) - math.pow(EARTH_RADIUS + 80000, 2))

# Reduced constellation for testing: 420 satellites (21 orbits × 20 sats/orbit)
# Increased from 10 to 20 sats/orbit for better coverage
NUM_ORBS = 21  # Keep original number of orbits
NUM_SATS_PER_ORB = 20  # Increase from 10 to 20 for better coverage
# Total satellites: 21 * 20 = 420 (2/3 of original 630)

local_shell = exputil.LocalShell()

dynamic_state_algorithm = "algorithm_lmsr"
output_generated_data_dir = "temp/gen_data"
num_threads = 1
time_step_ms = 1000
duration_s = 41  # 41 seconds for quick test (t=0 through t=40)
name = "kuiper_420_minimal_" + dynamic_state_algorithm  # Minimal test with 420 sats

print(f"\n{'='*60}")
print(f"Generating: {dynamic_state_algorithm} (MINIMAL TEST - 2 GS)")
print(f"{'='*60}\n")

# Create directory
local_shell.make_full_dir(output_generated_data_dir + "/" + name)

# Ground stations - ONLY 2 for fast testing
print("Generating ground stations...")
with open(output_generated_data_dir + "/" + name + "/ground_stations.basic.txt", "w+") as f_out:
    f_out.write("0,Manila,14.6042,120.9822,0\n")
    f_out.write("1,Tokyo,35.6762,139.6503,0\n")

satgen.extend_ground_stations(
    output_generated_data_dir + "/" + name + "/ground_stations.basic.txt",
    output_generated_data_dir + "/" + name + "/ground_stations.txt"
)

# TLEs
print("Generating TLEs...")
satgen.generate_tles_from_scratch_with_sgp(
    output_generated_data_dir + "/" + name + "/tles.txt",
    "Kuiper-210-minimal",
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
print("Generating GSL interfaces info...")
ground_stations = satgen.read_ground_stations_extended(
    output_generated_data_dir + "/" + name + "/ground_stations.txt"
)
satgen.generate_simple_gsl_interfaces_info(
    output_generated_data_dir + "/" + name + "/gsl_interfaces_info.txt",
    NUM_ORBS * NUM_SATS_PER_ORB,
    len(ground_stations),
    len(ground_stations),
    1,
    len(ground_stations),
    1
)

# Dynamic state
print("Generating forwarding state with Naive LMSR...")
satgen.help_dynamic_state(
    output_generated_data_dir,
    num_threads,
    name,
    time_step_ms,
    duration_s,
    MAX_GSL_LENGTH_M,
    MAX_ISL_LENGTH_M,
    dynamic_state_algorithm,
    True  # Enable verbose logs to see caching stats
)

print("\nDone! Check cache statistics in output.")
