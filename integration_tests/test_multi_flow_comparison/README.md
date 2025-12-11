# Multi-Flow Algorithm Comparison Test Suite

This test suite compares three satellite routing algorithms across multiple diverse ground station pairs to demonstrate jitter reduction capabilities.

## Algorithms Tested

1. **Anchor-based LMSR** (`algorithm_jitter_minimized`)
   - Uses 60 anchor satellites
   - Complexity: O(N × (V log V + E))
   - ~4,400x faster than naive LMSR

2. **Naive LMSR** (`algorithm_lmsr`)
   - Uses all 630 satellites
   - Complexity: O(N × V² × (V log V + E))
   - Reference implementation for comparison

3. **Free GS** (`algorithm_free_gs_one_sat_many_only_over_isls`)
   - Standard shortest-path routing
   - No jitter minimization
   - Baseline for comparison

## Test Configuration

- **Constellation**: Kuiper-630 (21 orbits × 30 satellites = 630 total)
- **Duration**: 100 seconds
- **Update Interval**: 1 second
- **Flow Size**: 1000 Mbit (125 MB)
- **Rate**: 10 Mbps
- **TCP**: TcpNewReno

## Ground Stations (8 total)

Strategically placed for maximum topology variation:

1. **Manila** (14.60°N, 120.98°E) - Southeast Asia
2. **Tokyo** (35.68°N, 139.65°E) - East Asia
3. **Sydney** (33.87°S, 151.21°E) - Southern Hemisphere
4. **London** (51.51°N, 0.13°W) - Europe
5. **NewYork** (40.71°N, 74.01°W) - North America East
6. **LosAngeles** (34.05°N, 118.24°W) - North America West
7. **SaoPaulo** (23.55°S, 46.63°W) - South America
8. **Nairobi** (1.29°S, 36.82°E) - Africa (near equator)

## Test Flows (5 diverse pairs × 3 algorithms = 15 total)

1. **Manila → London**: Long distance, cross-hemisphere (volatile)
2. **Tokyo → NewYork**: Trans-Pacific, high orbital plane crossing
3. **Sydney → Nairobi**: Cross-equator, southern to northern
4. **Manila → LosAngeles**: Pacific crossing, moderate distance
5. **Sydney → SaoPaulo**: Southern hemisphere, different continents

These pairs were chosen to maximize:
- **Path length variation** over time
- **Orbital plane crossings**
- **Latitude differences**
- **Hemisphere transitions**

## Running the Test

### Quick Start

```bash
./run_all_algorithms.sh
```

This will:
1. Generate satellite network states for all 3 algorithms (~30 min)
2. Create NS3 run configurations
3. Execute 15 simulations (3 algorithms × 5 flows)
4. Generate RTT plots for all runs
5. Create comparison summary

### Step-by-Step Execution

```bash
# Generate network states
python3 step_1_generate_anchor_lmsr.py
python3 step_1_generate_naive_lmsr.py  
python3 step_1_generate_free_gs.py

# Generate run configs
python3 step_2_generate_runs.py

# Run simulations
python3 step_3_run.py

# Generate plots
python3 step_4_generate_plots.py

# Create summary
python3 step_5_generate_summary.py
```

## Results

### Output Structure

```
temp/
├── gen_data/
│   ├── kuiper_630_isls_algorithm_jitter_minimized/
│   ├── kuiper_630_isls_algorithm_lmsr/
│   └── kuiper_630_isls_algorithm_free_gs_one_sat_many_only_over_isls/
├── runs/
│   ├── anchor_lmsr_Manila_to_London_TcpNewReno_10Mbps/
│   ├── naive_lmsr_Manila_to_London_TcpNewReno_10Mbps/
│   ├── free_gs_Manila_to_London_TcpNewReno_10Mbps/
│   └── ... (15 total)
├── pdf/
│   ├── anchor_lmsr_Manila_to_London_TcpNewReno_10Mbps/
│   │   ├── plot_tcp_flow_time_vs_rtt_0.pdf
│   │   ├── plot_tcp_flow_time_vs_cwnd_0.pdf
│   │   ├── plot_tcp_flow_time_vs_progress_0.pdf
│   │   └── plot_tcp_flow_time_vs_rate_0.pdf
│   └── ... (15 directories)
└── comparison_summary.txt
```

### Viewing Results

**Summary Report**:
```bash
cat temp/comparison_summary.txt
```

**RTT Comparison for a specific flow**:
```bash
# Manila → London
open temp/pdf/anchor_lmsr_Manila_to_London_TcpNewReno_10Mbps/plot_tcp_flow_time_vs_rtt_0.pdf
open temp/pdf/naive_lmsr_Manila_to_London_TcpNewReno_10Mbps/plot_tcp_flow_time_vs_rtt_0.pdf
open temp/pdf/free_gs_Manila_to_London_TcpNewReno_10Mbps/plot_tcp_flow_time_vs_rtt_0.pdf
```

## Expected Results

**Jitter Metrics**:
- **Anchor-based LMSR**: Lowest RTT variance, smoothest graphs
- **Naive LMSR**: Similar to anchor-based (validation)
- **Free GS**: Higher RTT variance, more jagged graphs

**Key Comparisons**:
1. **RTT Standard Deviation**: Lower is better (less jitter)
2. **RTT Range** (max - min): Smaller is better (more stable)
3. **RTT Variance**: Lower is better (smoother delivery)
4. **TCP Completion**: All should be similar (>95%)

## Cleanup

```bash
rm -rf temp
```

## Notes

- First run takes ~30-45 minutes (generating 3 network states)
- Subsequent runs are faster (states cached)
- Use `--verbose` flag in step_1 scripts to see detailed progress
- Simulations run 4 in parallel by default
- Each algorithm generates ~300 MB of forwarding state files

## Interpretation

The test demonstrates that:
- LMSR algorithms maintain more stable RTT despite satellite motion
- Jitter reduction is most visible on long-distance, high-variation routes
- Anchor-based optimization maintains quality while reducing computation
- Multiple concurrent flows better demonstrate algorithm differences than single flows
