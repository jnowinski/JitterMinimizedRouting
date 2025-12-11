#!/usr/bin/env python3
"""Analyze RTT temporal patterns - why stable initially then fluctuations"""

import numpy as np
import sys

def analyze_temporal_pattern(csv_file, algo_name):
    times = []
    rtts = []
    
    with open(csv_file) as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 3:
                times.append(float(parts[1]) / 1e9)  # seconds
                rtts.append(float(parts[2]) / 1e6)   # milliseconds
    
    times = np.array(times)
    rtts = np.array(rtts)
    
    print(f"\n{'='*70}")
    print(f"Algorithm: {algo_name}")
    print(f"{'='*70}")
    
    # Analyze in time windows
    time_windows = [
        (0, 25, "0-25s (Initial)"),
        (25, 50, "25-50s"),
        (50, 100, "50-100s"),
        (100, 150, "100-150s"),
        (150, 200, "150-200s (End)")
    ]
    
    for start, end, label in time_windows:
        mask = (times >= start) & (times < end)
        window_rtts = rtts[mask]
        
        if len(window_rtts) == 0:
            continue
            
        mean_rtt = np.mean(window_rtts)
        std_rtt = np.std(window_rtts)
        min_rtt = np.min(window_rtts)
        max_rtt = np.max(window_rtts)
        range_rtt = max_rtt - min_rtt
        
        # Count significant changes within this window
        if len(window_rtts) > 1:
            diffs = np.abs(np.diff(window_rtts))
            big_changes = np.sum(diffs > 5)  # >5ms changes
            change_rate = big_changes / len(window_rtts) * 100
        else:
            big_changes = 0
            change_rate = 0
        
        print(f"\n{label}:")
        print(f"  Mean RTT: {mean_rtt:.2f} ms")
        print(f"  StdDev: {std_rtt:.2f} ms")
        print(f"  Range: {min_rtt:.2f} - {max_rtt:.2f} ms ({range_rtt:.2f} ms)")
        print(f"  Route changes (>5ms): {big_changes} ({change_rate:.2f}% of samples)")
        print(f"  Samples: {len(window_rtts)}")
    
    # Look at first 50 samples to understand initial behavior
    print(f"\n{'Initial RTT Evolution (first 50 samples)':}")
    print(f"{'Time(s)':<10} {'RTT(ms)':<12} {'Change':<12}")
    print("-" * 40)
    for i in range(min(50, len(rtts))):
        change = ""
        if i > 0:
            diff = rtts[i] - rtts[i-1]
            if abs(diff) > 5:
                change = f"{diff:+.1f}ms ⚠️"
            else:
                change = f"{diff:+.1f}ms"
        print(f"{times[i]:<10.3f} {rtts[i]:<12.2f} {change:<12}")
    
    # Look at the transition around 25s
    print(f"\n{'Transition around 25s (samples 20s-30s)':}")
    print(f"{'Time(s)':<10} {'RTT(ms)':<12} {'Change':<12}")
    print("-" * 40)
    transition_mask = (times >= 20) & (times <= 30)
    transition_times = times[transition_mask]
    transition_rtts = rtts[transition_mask]
    
    for i in range(min(100, len(transition_rtts))):
        change = ""
        if i > 0:
            diff = transition_rtts[i] - transition_rtts[i-1]
            if abs(diff) > 5:
                change = f"{diff:+.1f}ms ⚠️ ROUTE CHANGE"
            else:
                change = f"{diff:+.1f}ms"
        print(f"{transition_times[i]:<10.3f} {transition_rtts[i]:<12.2f} {change:<12}")

if __name__ == "__main__":
    route = "Manila_to_LosAngeles"
    
    print(f"\n{'#'*70}")
    print(f"# Temporal Analysis: Manila → Los Angeles")
    print(f"# Understanding the 0-25s stability vs later fluctuations")
    print(f"{'#'*70}")
    
    for algo in ['anchor_lmsr', 'naive_lmsr', 'free_gs']:
        csv_file = f"temp/runs/{algo}_{route}_TcpNewReno_10Mbps/logs_ns3/tcp_flow_0_rtt.csv"
        analyze_temporal_pattern(csv_file, algo)
