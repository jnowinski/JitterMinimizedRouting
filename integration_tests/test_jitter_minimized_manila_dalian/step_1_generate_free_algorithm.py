# The MIT License (MIT)
# Copyright (c) 2020 ETH Zurich

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

# Kuiper-630 constellation: 21 orbital planes × 30 satellites/plane = 630 satellites
NUM_ORBS = 21
NUM_SATS_PER_ORB = 30

local_shell = exputil.LocalShell()

# Use FREE GS ONE SAT MANY algorithm (matches our jitter-minimized GSL config)
dynamic_state_algorithm = "algorithm_free_gs_one_sat_many_only_over_isls"

# Configuration
output_generated_data_dir = "temp/gen_data"
num_threads = 1
time_step_ms = 1000  # 1 second timestep
duration_s = 100  # 100 seconds

name = "kuiper_630_isls_" + dynamic_state_algorithm

# Ground stations
print("Generating ground stations...")
local_shell.make_full_dir(output_generated_data_dir + "/" + name)
with open(output_generated_data_dir + "/" + name + "/ground_stations.basic.txt", "w+") as f_out:
    f_out.write("0,Manila,14.6042,120.9822,0\n")
    f_out.write("1,Dalian,38.913811,121.602322,0\n")
satgen.extend_ground_stations(
    output_generated_data_dir + "/" + name + "/ground_stations.basic.txt",
    output_generated_data_dir + "/" + name + "/ground_stations.txt"
)

# TLEs for Kuiper-630 (21 planes × 30 sats)
print("Generating TLEs...")
satgen.generate_tles_from_scratch_manual(
    output_generated_data_dir + "/" + name + "/tles.txt",
    "Kuiper-630",
    NUM_ORBS,
    NUM_SATS_PER_ORB,
    EARTH_RADIUS + ALTITUDE_M,
    51.9,
    eccentricity=0.0000001,
    arg_of_perigee_degree=0.0,
    mean_motion_rev_per_day=14.80
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

# Extended ground stations
ground_stations = satgen.read_ground_stations_extended(
    output_generated_data_dir + "/" + name + "/ground_stations.txt"
)

# GSL interfaces - must match algorithm requirements
print("Generating GSL interfaces info...")
satgen.generate_simple_gsl_interfaces_info(
    output_generated_data_dir + "/" + name + "/gsl_interfaces_info.txt",
    NUM_ORBS * NUM_SATS_PER_ORB,
    len(ground_stations),
    len(ground_stations),  # Satellites have N GSL interfaces (one per GS)
    1,  # Ground stations have 1 GSL interface
    float(len(ground_stations)),  # Aggregate max. bandwidth satellite = N
    1.0   # Aggregate max. bandwidth ground station = 1.0
)

# Forwarding state
print("Generating forwarding state...")
satgen.help_dynamic_state(
    output_generated_data_dir,
    num_threads,
    name,
    time_step_ms,
    duration_s,
    MAX_GSL_LENGTH_M,
    MAX_ISL_LENGTH_M,
    dynamic_state_algorithm,
    True  # Verbose
)

print("Done!")
