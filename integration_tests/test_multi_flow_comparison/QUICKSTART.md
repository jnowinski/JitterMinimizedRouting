# Quick Start Guide

## Run Everything (Automated)

```bash
./run_all_algorithms.sh
```

This runs all 5 steps automatically. Takes ~45 minutes first time.

## View Results

```bash
# Summary statistics
cat temp/comparison_summary.txt

# View RTT plots (compare algorithms for Manila→London)
ls temp/pdf/*Manila_to_London*/plot_tcp_flow_time_vs_rtt_0.pdf
```

## What You'll See

For each of the 5 flows, you'll have 3 RTT graphs (one per algorithm):
- **anchor_lmsr_***: Your optimized jitter-minimized algorithm
- **naive_lmsr_***: Reference LMSR implementation  
- **free_gs_***: Baseline shortest-path routing

**Look for:**
- Smoother lines = less jitter
- Lower variance = more stable
- Similar completion rates = all work correctly

## Expected Differences

Routes with high topology variation (Manila→London, Sydney→Nairobi) will show:
- **LMSR algorithms**: Smooth, consistent RTT curves
- **Free GS**: More jagged, variable RTT curves

This demonstrates jitter reduction working!

## Files Generated

**Per Run** (4 plots each):
- `plot_tcp_flow_time_vs_rtt_0.pdf` - **RTT graph (main comparison metric)**
- `plot_tcp_flow_time_vs_cwnd_0.pdf` - Congestion window
- `plot_tcp_flow_time_vs_progress_0.pdf` - Data transfer progress
- `plot_tcp_flow_time_vs_rate_0.pdf` - Throughput intervals

**Total**: 15 runs × 4 plots = **60 PDF files**

**Example - To compare RTT for Manila→London across all 3 algorithms:**
```bash
open temp/pdf/anchor_lmsr_Manila_to_London_TcpNewReno_10Mbps/plot_tcp_flow_time_vs_rtt_0.pdf
open temp/pdf/naive_lmsr_Manila_to_London_TcpNewReno_10Mbps/plot_tcp_flow_time_vs_rtt_0.pdf
open temp/pdf/free_gs_Manila_to_London_TcpNewReno_10Mbps/plot_tcp_flow_time_vs_rtt_0.pdf
```

This gives you 3 RTT graphs (one per algorithm) for the same flow - compare them side-by-side!
