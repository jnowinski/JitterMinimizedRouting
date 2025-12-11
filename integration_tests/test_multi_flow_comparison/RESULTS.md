# Multi-Flow Algorithm Comparison Results

## Overview

Successfully ran comprehensive comparison of three routing algorithms across 5 diverse ground station pairs on the Kuiper-630 constellation.

## Test Configuration

- **Constellation**: Kuiper-630 (630 satellites, 21 orbits × 30 satellites/orbit)
- **Duration**: 100 seconds
- **Update Interval**: 1000ms
- **Flow Size**: 1000 Mbit (125 MB)
- **Data Rate**: 10 Mbps
- **TCP**: TcpNewReno
- **Ground Stations**: 8 locations
  - Manila (630)
  - Tokyo (631) 
  - Sydney (632)
  - London (633)
  - NewYork (634)
  - LosAngeles (635)
  - SaoPaulo (636)
  - Nairobi (637)

## Algorithms Tested

### 1. Anchor-based LMSR (`anchor_lmsr`)
- **Anchors**: 60 satellites (every 10th: 0, 10, 20, ..., 590)
- **Lookahead**: 10 timesteps (10 seconds)
- **Complexity**: O(N × (V log V + E))
- **Strategy**: Minimize maximum distance across all lookahead timesteps
- **Routing**: Source → Ingress Anchor → Egress Anchor → Destination

### 2. Naive LMSR (`naive_lmsr`)
- **Complexity**: O(N × V² × (V log V + E))
- **Strategy**: Full LMSR for all source-destination pairs
- **Lookahead**: 10 timesteps
- **Routing**: Direct shortest path per timestep

### 3. Free GS (`free_gs`)
- **Complexity**: O(N × V³) using Floyd-Warshall
- **Strategy**: Standard shortest path (no jitter minimization)
- **Routing**: Recompute shortest paths each timestep

## Flow Pairs Tested

1. **Manila → London**: Long distance, cross-hemisphere (~10,800 km)
2. **Tokyo → NewYork**: Trans-Pacific (~10,850 km)
3. **Sydney → Nairobi**: Cross-equator (~11,600 km)
4. **Manila → LosAngeles**: Pacific crossing (~11,600 km)
5. **Sydney → SaoPaulo**: Southern hemisphere (~13,300 km)

## Results Location

All results are in `temp/` directory:

### RTT Plots
```
temp/pdf/<algorithm>_<src>_to_<dst>_TcpNewReno_10Mbps/plot_tcp_flow_time_vs_rtt_0.pdf
```

Example paths:
- `temp/pdf/anchor_lmsr_Manila_to_London_TcpNewReno_10Mbps/plot_tcp_flow_time_vs_rtt_0.pdf`
- `temp/pdf/naive_lmsr_Sydney_to_Nairobi_TcpNewReno_10Mbps/plot_tcp_flow_time_vs_rtt_0.pdf`
- `temp/pdf/free_gs_Tokyo_to_NewYork_TcpNewReno_10Mbps/plot_tcp_flow_time_vs_rtt_0.pdf`

### Additional Plots
Each run also includes:
- `plot_tcp_flow_time_vs_cwnd_0.pdf` - Congestion window evolution
- `plot_tcp_flow_time_vs_progress_0.pdf` - Data transfer progress
- `plot_tcp_flow_time_vs_rate_0.pdf` - Throughput over time

### Raw Data
CSV files in `temp/data/<run_name>/` including:
- `tcp_flow_0_rtt.csv` - RTT measurements
- `tcp_flow_0_progress.csv` - Transfer progress
- `tcp_flow_0_cwnd.csv` - Congestion window data
- `tcp_flow_0_rate_in_intervals.csv` - Throughput measurements

## Key Findings

### Computation Time Comparison
From previous Manila-Dalian benchmarks:
- **Anchor-based LMSR**: ~21.5s (3.39× speedup)
- **Naive LMSR**: ~73.1s
- **Free GS**: ~64.3s

### Algorithm Characteristics

**Anchor-based LMSR Advantages**:
- 3.39× faster computation than naive LMSR
- Scalable to large constellations
- Reduces routing table size through anchor aggregation

**Anchor-based LMSR Limitations**:
- Suboptimal path length due to routing through anchors
- Fixed anchor selection may miss optimal routes
- Benefits most visible on routes with high topology variance

**Naive LMSR**:
- Optimal jitter minimization
- Computationally expensive at scale
- Impractical for large constellations

**Free GS**:
- Fastest per-timestep computation
- No jitter minimization
- Standard baseline for comparison

## Verification

All 15 simulations completed successfully:
- 5 flows × 3 algorithms = 15 runs
- All RTT plots generated
- Raw CSV data available for analysis

## Next Steps

To analyze specific routes:
1. Compare RTT plots for the same flow across algorithms
2. Check RTT variance (jitter) in the CSV files
3. Examine routes with highest topology dynamics (e.g., Sydney↔Nairobi)
4. Look for cases where anchor-based LMSR shows jitter reduction benefits

## Viewing Results

```bash
# View summary
cat temp/comparison_summary.txt

# Open specific RTT plot
xdg-open temp/pdf/anchor_lmsr_Sydney_to_Nairobi_TcpNewReno_10Mbps/plot_tcp_flow_time_vs_rtt_0.pdf

# Analyze RTT data
head temp/runs/anchor_lmsr_Sydney_to_Nairobi_TcpNewReno_10Mbps/logs_ns3/tcp_flow_0_rtt.csv
```
