# Jitter-Minimized Routing (JMR) for LEO Satellite Networks

This repository contains implementations and optimizations of jitter-minimized routing algorithms for Low Earth Orbit (LEO) satellite networks, building on the Hypatia framework.

## Overview

### Routing Algorithms

This project implements and compares three routing algorithms for LEO satellite networks:

1. **LMSR (Low-jitter Multiple Slots Routing)**
   - Per-timestep k-shortest paths using Yen's algorithm (k=3)
   - Jitter minimization through anchor-based delay equalization
   - Sliding window cache optimization for efficient path computation
   - Reference: S. Sun et al., "LMSR: A Low-Jitter Multiple Slots Routing Algorithm in LEO Satellite Networks", WCNC 2025

2. **Anchor LMSR (JMR - Jitter Minimized Routing)**
   - Enhanced version with improved jitter minimization
   - Optimized for long-term delay stability across time windows

3. **Free Ground Station (Free-GS)**
   - Baseline shortest-path routing
   - Each satellite independently routes to nearest ground station

### Key Optimizations

**Sliding Window Cache for K-Shortest Paths:**
- Global persistent cache across timesteps: `_global_k_paths_cache`
- Keyed by `(src, dst, absolute_timestep)` instead of relative indices
- **Performance**: ~90% cache hit rate after initialization
  - First timestep: Computes all paths for 10-timestep lookahead window
  - Subsequent timesteps: Reuses 90% of paths, only computes new edge
  - Example: 3,762 hits + 418 new computations vs 4,180 total

**Bidirectional Route Generation:**
- Automatically generates reverse Sat↔GS routes
- Computes GS↔GS routes in both directions
- Ensures complete forwarding tables for ns-3 compatibility

## Installation

### Prerequisites

```bash
# System dependencies
sudo apt-get update
sudo apt-get install -y \
    python3 python3-pip \
    libproj-dev proj-data proj-bin libgeos-dev \
    openmpi-bin openmpi-common libopenmpi-dev \
    lcov gnuplot

# Python dependencies
pip3 install -r requirements.txt
```
- Python version 3.7-3.11 must be used

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd hypatia

# Install dependencies
./hypatia_install_dependencies.sh

# Build ns-3 simulator
cd ns3-sat-sim/simulator
./build.sh
cd ../..

# Build Hypatia
./hypatia_build.sh
```

## Running Tests

### Quick Start - Minimal Test (2 Ground Stations, 210 Satellites)

```bash
cd integration_tests/test_multi_flow_comparison

# Generate LMSR forwarding state (Manila ↔ Tokyo)
python step_1_generate_naive_lmsr_minimal.py

# Check cache performance (should see ~90% hit rate)
# Output shows: "K-paths cache: 3762 hits, 418 new computations"

# Generate ns-3 run configuration
python step_2_generate_runs_minimal.py

# Run simulation
python step_3_run_minimal.py

# Generate plots
python step_4_generate_plots.py
```

### Full Multi-Flow Comparison (630 Satellites, 8 Ground Stations)

```bash
cd integration_tests/test_multi_flow_comparison

# Generate network states for all algorithms
python step_1_generate_anchor_lmsr.py    # Anchor LMSR (JMR)
python step_1_generate_naive_lmsr.py     # Naive LMSR
python step_1_generate_free_gs.py        # Free-GS baseline

# Generate test runs
python step_2_generate_runs.py

# Execute simulations
python step_3_run.py

# Generate comparative plots
python step_4_generate_plots.py

# Generate summary statistics
python step_5_generate_summary.py
```

### Test Flows

The multi-flow comparison tests diverse paths:
- **Manila → London**: Long distance, cross-hemisphere
- **Tokyo → New York**: Trans-Pacific
- **Sydney → Nairobi**: Cross-equator
- **Manila → Los Angeles**: Pacific crossing
- **Sydney → São Paulo**: Southern hemisphere

## Configuration

### Satellite Constellation Parameters

Edit in `step_1_generate_*.py`:

```python
# Constellation size
NUM_ORBS = 21              # Number of orbital planes
NUM_SATS_PER_ORB = 10      # Satellites per orbit
# Total: 21 × 10 = 210 satellites

# Orbital parameters
ALTITUDE_M = 630000        # 630 km altitude
INCLINATION_DEGREE = 53.0  # Orbital inclination
```

### Ground Station Configuration

```python
# Example: Adding ground stations
ground_stations = [
    satgen.extend_ground_station(0, "Manila", 14.6042, 120.9822, 0),
    satgen.extend_ground_station(1, "Tokyo", 35.6762, 139.6503, 0),
    # Add more as needed
]
```

### Routing Algorithm Parameters

```python
# LMSR configuration
k_paths = 3                          # Number of shortest paths to consider
lookahead_steps = 10                 # Lookahead window size (timesteps)
dynamic_state_update_interval_ms = 1000  # Update every 1 second
```

### Link Parameters

```python
# Maximum link distances
MAX_GSL_LENGTH_M = 1260000.0         # Ground-to-satellite: ~1260 km
MAX_ISL_LENGTH_M = 5016297.0         # Inter-satellite: ~5016 km

# Data rates
isl_data_rate_megabit_per_s = 10.0   # ISL bandwidth
gsl_data_rate_megabit_per_s = 10.0   # GSL bandwidth
```

## Output Files

### Generated Data Structure

```
temp/gen_data/kuiper_<sats>_algorithm_<name>/
├── ground_stations.txt              # Ground station coordinates
├── tles.txt                          # Satellite orbital elements (TLE format)
├── isls.txt                          # Inter-satellite link definitions
├── gsl_interfaces_info.txt          # GSL interface configuration
└── dynamic_state_1000ms_for_<duration>s/
    ├── fstate_0.txt                  # Forwarding state at t=0
    ├── fstate_1000000000.txt         # Forwarding state at t=1s
    └── ...                           # One file per timestep
```

### Forwarding State Format

Each line in `fstate_*.txt`:
```
<current_node>,<destination_node>,<next_hop>,<my_interface>,<their_interface>
```

Example:
```
210,211,34,0,4    # Manila (210) → Tokyo (211) via satellite 34
34,211,35,2,1     # Satellite 34 → Tokyo (211) via satellite 35
```

### Simulation Results

```
temp/runs/<algorithm>_<flow>/
├── logs_ns3/
│   ├── finished.txt                 # Completion status
│   ├── timing_results.txt           # Execution time
│   └── console.txt                  # Simulation output
├── logs_ns3/
│   ├── tcp_flow_0.csv              # TCP flow statistics
│   ├── tcp_flow_0_progress.txt     # Flow progress log
│   └── tcp_flow_0_rtt.csv          # RTT measurements
└── config_ns3.properties           # Simulation configuration
```

## Performance Benchmarks

### Sliding Window Cache Performance

| Metric | Value |
|--------|-------|
| Initial computation (t=0) | 4,180 path sets |
| Cache hit rate | ~90% |
| Typical timestep computation | 418-627 new + 3,762-7,524 cached |
| Speedup after t=0 | ~10x reduction in path computations |

### Constellation Processing Time

| Configuration | Network Generation | Forwarding State (41s) |
|--------------|-------------------|----------------------|
| 210 satellites, 2 GS | ~30s | ~2-3 minutes |
| 630 satellites, 8 GS | ~2 minutes | ~15-20 minutes |

## Algorithm Details

### LMSR Jitter Minimization

1. **Path Discovery**: Find k-shortest paths at each timestep using Yen's algorithm
2. **Delay Calculation**: Compute path delay D_i(t) for each candidate i at each timestep t
3. **Anchor Selection**: Find "anchor" timestep with maximum of minimum delays
4. **Path Selection**: For each timestep, select path closest to anchor delay
5. **Result**: Minimizes max(D) - min(D) across time horizon

### Sliding Window Cache

```
Timestep 0: [t=0, t=1, ..., t=9]    → Compute all 10 timesteps
Timestep 1: [t=1, t=2, ..., t=10]   → Reuse t=1-9, compute t=10
Timestep 2: [t=2, t=3, ..., t=11]   → Reuse t=2-10, compute t=11
...
```

Cache key: `(source_sat, dest_sat, absolute_timestep)`
- Enables reuse across sliding window
- Shared across all ground station pairs
- Persistent throughout simulation run

## Troubleshooting

### Common Issues

**Issue**: `KeyboardInterrupt` during generation
- **Cause**: Generation cancelled by user (Ctrl+C)
- **Solution**: Re-run the script; cache will speed up subsequent runs

**Issue**: `NameError: name '_global_k_paths_cache' is not defined`
- **Cause**: Missing global cache initialization
- **Solution**: Ensure fstate_calculation.py has cache defined before calculate_lmsr()

**Issue**: `ns-3 aborted: Forwarding state is not set`
- **Cause**: Incomplete forwarding tables (missing routes)
- **Solution**: Ensure all GS have satellite coverage or use larger GSL_LENGTH_M

**Issue**: Low cache hit rate
- **Cause**: Constellation changes or varying ground station visibility
- **Solution**: Expected behavior; hit rate improves with stable topology

## References

1. S. Sun, R. Zhang, K. Liu, Z. Sun, Q. Tang, and T. Huang, "LMSR: A Low-Jitter Multiple Slots Routing Algorithm in LEO Satellite Networks", IEEE WCNC 2025
2. S. Kassing et al., "Exploring the 'Internet from space' with Hypatia", IMC 2020
3. Hypatia Framework: https://github.com/snkas/hypatia

## License

This project extends the Hypatia framework and maintains compatibility with its licensing:
- satgenpy: MIT License
- ns3-sat-sim: GNU GPL v2
- Additional JMR/LMSR implementations: MIT License

## Contributing

When contributing optimizations:
1. Maintain backward compatibility with Hypatia
2. Document cache performance metrics
3. Include integration tests for new algorithms
4. Update this README with configuration changes
