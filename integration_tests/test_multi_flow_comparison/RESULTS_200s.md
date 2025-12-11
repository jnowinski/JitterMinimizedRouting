# Multi-Flow Algorithm Comparison Results (200s Simulation)

## Test Configuration

**Updated for 200-second simulation with sufficient flow data**

- **Constellation**: Kuiper-630 (630 satellites, 21 orbits × 30 satellites/orbit)
- **Duration**: 200 seconds (doubled from 100s)
- **Update Interval**: 1000ms
- **Flow Size**: 2500 Mbit (312.5 MB) - sized to last full 200s at 10 Mbps
- **Data Rate**: 10 Mbps
- **TCP**: TcpNewReno
- **Ground Stations**: 8 locations (Manila, Tokyo, Sydney, London, NewYork, LosAngeles, SaoPaulo, Nairobi)

## Flow Completion Results

All flows achieved **71-76% completion** over the 200-second simulation:

| Algorithm | Manila→London | Tokyo→NewYork | Sydney→Nairobi | Manila→LA | Sydney→SP | Avg |
|-----------|---------------|---------------|----------------|-----------|-----------|-----|
| **Anchor LMSR** | 74.6% | 74.3% | 75.4% | 74.4% | 71.5% | **74.0%** |
| **Naive LMSR** | 76.3% | 76.2% | 75.9% | 76.2% | 75.6% | **76.0%** |
| **Free GS** | 76.3% | 76.2% | 75.9% | 76.2% | 75.6% | **76.0%** |

**Key Observation**: Anchor-based LMSR achieves slightly lower throughput (~2% less) than naive LMSR and Free GS, consistent with the path-length penalty from routing through anchors.

## RTT Analysis

### Manila → London
| Algorithm | Mean RTT | StdDev (Jitter) | Min RTT | Max RTT | Range | Samples |
|-----------|----------|-----------------|---------|---------|-------|---------|
| **Anchor LMSR** | 162.68s | 33.40s | 86.00s | 218.00s | 132.00s | 82,749 |
| **Naive LMSR** | 163.15s | 32.20s | 85.00s | 215.77s | 130.77s | 85,050 |
| **Free GS** | 163.29s | 32.16s | 85.00s | 215.77s | 130.77s | 84,800 |

**Jitter Reduction**: Anchor LMSR shows ~3.7% higher jitter than naive LMSR (33.40s vs 32.20s)

### Sydney → Nairobi
| Algorithm | Mean RTT | StdDev (Jitter) | Min RTT | Max RTT | Range | Samples |
|-----------|----------|-----------------|---------|---------|-------|---------|
| **Anchor LMSR** | 179.54s | 35.40s | 109.00s | 245.63s | 136.63s | 83,536 |
| **Naive LMSR** | 172.73s | 34.90s | 99.00s | 235.16s | 136.16s | 84,122 |
| **Free GS** | 173.21s | 34.91s | 99.00s | 236.32s | 137.32s | 84,129 |

**Key Findings**:
- Anchor LMSR has **6.81s higher mean RTT** (3.9% worse) than naive LMSR
- Jitter is **1.4% higher** with anchor-based approach (35.40s vs 34.90s)
- Free GS and Naive LMSR show nearly identical performance

## Algorithm Performance Summary

### Anchor-based LMSR
- ✅ **3.39× faster** computation than naive LMSR (from previous benchmarks)
- ✅ **Scalable** to large constellations
- ❌ **2% lower throughput** due to suboptimal paths
- ❌ **1.4-3.7% higher jitter** than naive LMSR (counter to design goal)
- ❌ **3.9-4% higher mean RTT** on some routes

### Naive LMSR
- ✅ **Best jitter performance** across all routes
- ✅ **Highest throughput** (tied with Free GS)
- ❌ **3.39× slower** computation (impractical at scale)
- ❌ **O(N × V² × (V log V + E))** complexity

### Free GS (Shortest Path)
- ✅ **Simple and fast** per-timestep computation
- ✅ **Best throughput** (tied with Naive LMSR)
- ✅ **Comparable jitter** to Naive LMSR
- ❌ **No jitter optimization** (though performs well anyway)

## Critical Insights

### Why Anchor-Based LMSR Underperforms

1. **Path Suboptimality**: Routing through anchors violates triangle inequality
   - Sydney→Nairobi: 6.81s (3.9%) higher RTT due to detours
   
2. **Jitter Paradox**: Despite optimizing for jitter, it performs worse
   - Manila→London: 3.7% higher jitter than naive LMSR
   - Sydney→Nairobi: 1.4% higher jitter than naive LMSR
   
3. **Fixed Anchor Limitation**: Every-10th-satellite selection misses better routing opportunities
   
4. **Topology Stability**: Long-distance routes may be too stable for LMSR benefits to outweigh path penalties

### Algorithm Trade-offs

| Metric | Anchor LMSR | Naive LMSR | Free GS |
|--------|-------------|------------|---------|
| **Computation Time** | ✅ 21.5s | ❌ 73.1s | ⚠️ 64.3s |
| **Scalability** | ✅ O(N(VlogV+E)) | ❌ O(NV²(VlogV+E)) | ⚠️ O(NV³) |
| **Throughput** | ❌ 74% | ✅ 76% | ✅ 76% |
| **Mean RTT** | ❌ Higher | ✅ Lower | ✅ Lower |
| **Jitter** | ❌ Higher | ✅ Lowest | ⚠️ Low |

## Results Location

All plots available in:
```
temp/pdf/<algorithm>_<src>_to_<dst>_TcpNewReno_10Mbps/
```

Each run includes:
- `plot_tcp_flow_time_vs_rtt_0.pdf` - RTT over time
- `plot_tcp_flow_time_vs_progress_0.pdf` - Data transfer progress
- `plot_tcp_flow_time_vs_cwnd_0.pdf` - Congestion window evolution
- `plot_tcp_flow_time_vs_rate_0.pdf` - Throughput over time

## Recommendations

### For Current Implementation
The anchor-based LMSR approach **fails to achieve its jitter reduction goal** while incurring:
- 2% throughput penalty
- 1.4-3.7% higher jitter
- 3.9-4% higher RTT on some routes

**The computational speedup (3.39×) comes at too high a performance cost.**

### Potential Improvements

1. **Dynamic Anchor Selection**: Choose anchors based on traffic patterns, not fixed positions
2. **Adaptive Lookahead**: Adjust window size based on topology stability
3. **Hybrid Approach**: Use anchors for long-distance, direct routing for short-distance
4. **Per-Flow Anchors**: Different anchor sets for different ground station pairs
5. **Path Validation**: Only use anchor routing when it doesn't increase RTT beyond threshold

### Alternative Strategies

1. **Reduced LMSR**: Compute full LMSR for critical flows only, use Free GS for others
2. **Caching**: Exploit topology periodicity to cache and reuse routing decisions
3. **Approximate LMSR**: Sample subset of timesteps instead of full lookahead
4. **Zone-based**: Divide constellation into regions, optimize within zones

## Conclusion

For the **200-second, 2500 Mbit flow test**, the data shows:

1. **Naive LMSR** achieves best jitter and throughput but is computationally expensive
2. **Free GS** performs surprisingly well with simple shortest-path routing
3. **Anchor-based LMSR** trades off too much performance for its computational gains

The current anchor-based approach **should not be used in production** without addressing the fundamental path-length and jitter issues. The algorithm needs significant refinement to deliver on its jitter-minimization promise while maintaining the computational advantages.
