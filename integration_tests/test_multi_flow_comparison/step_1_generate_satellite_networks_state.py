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

# Clean slate start
local_shell.remove_force_recursive("temp/gen_data")
local_shell.make_full_dir("temp/gen_data")

# Use jitter-minimized algorithm
dynamic_state_algorithm = "algorithm_jitter_minimized"

# Configuration
output_generated_data_dir = "temp/gen_data"
num_threads = 1
time_step_ms = 1000  # 1 second timestep
duration_s = 101  # 101 seconds (need t=0 through t=100 for 100s simulation)

name = "kuiper_630_isls_" + dynamic_state_algorithm

# Ground stations - Multiple diverse locations for high topology variation
print("Generating ground stations...")
local_shell.make_full_dir(output_generated_data_dir + "/" + name)
with open(output_generated_data_dir + "/" + name + "/ground_stations.basic.txt", "w+") as f_out:
    # Diverse ground stations across different latitudes and longitudes
    f_out.write("0,Manila,14.6042,120.9822,0\n")          # Southeast Asia
    f_out.write("1,Tokyo,35.6762,139.6503,0\n")           # East Asia (different latitude)
    f_out.write("2,Sydney,-33.8688,151.2093,0\n")         # Southern Hemisphere
    f_out.write("3,London,51.5074,-0.1278,0\n")           # Europe
    f_out.write("4,NewYork,40.7128,-74.0060,0\n")         # North America (East)
    f_out.write("5,LosAngeles,34.0522,-118.2437,0\n")     # North America (West)
    f_out.write("6,SaoPaulo,-23.5505,-46.6333,0\n")       # South America
    f_out.write("7,Nairobi,-1.2864,36.8172,0\n")          # Africa (near equator)
satgen.extend_ground_stations(
    output_generated_data_dir + "/" + name + "/ground_stations.basic.txt",
    output_generated_data_dir + "/" + name + "/ground_stations.txt"
)

# TLEs for Kuiper-630 (21 planes × 30 sats)
print("Generating TLEs...")
satgen.generate_tles_from_scratch_with_sgp(
    output_generated_data_dir + "/" + name + "/tles.txt",
    "Kuiper-630",
    NUM_ORBS,
    NUM_SATS_PER_ORB,
    True,  # phase diff
    51.9,  # inclination
    0.0000001,  # eccentricity (near-circular)
    0.0,  # arg of perigee
    14.80  # mean motion (rev/day)
)

# ISLs (plus-grid topology)
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

# GSL interfaces - each satellite can see all ground stations
gsl_interfaces_per_satellite = len(ground_stations)
gsl_satellite_max_agg_bandwidth = len(ground_stations)

print("Generating GSL interfaces info...")
satgen.generate_simple_gsl_interfaces_info(
    output_generated_data_dir + "/" + name + "/gsl_interfaces_info.txt",
    NUM_ORBS * NUM_SATS_PER_ORB,  # 630 satellites
    len(ground_stations),  # 2 ground stations
    gsl_interfaces_per_satellite,
    1,  # Interfaces per ground station
    gsl_satellite_max_agg_bandwidth,
    1
)

# Forwarding state with jitter-minimized algorithm
print("Generating forwarding state with jitter-minimized routing...")
satgen.help_dynamic_state(
    output_generated_data_dir,
    num_threads,
    name,
    time_step_ms,
    duration_s,
    MAX_GSL_LENGTH_M,
    MAX_ISL_LENGTH_M,
    dynamic_state_algorithm,
    True  # Enable verbose logging to see sat-to-sat entry generation
)

print("Done!")
