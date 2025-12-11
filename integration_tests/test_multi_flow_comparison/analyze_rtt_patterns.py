#!/usr/bin/env python3
"""Analyze RTT patterns to understand peaks and routing behavior"""

import sys
import numpy as np
from scipy import signal

def analyze_rtt_file(csv_file, algo_name):
    rtts = []
    times = []
    
    with open(csv_file) as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 3:
                times.append(float(parts[1]) / 1e9)  # Convert to seconds
                rtts.append(float(parts[2]) / 1e6)   # Convert to milliseconds
    
    rtts = np.array(rtts)
    times = np.array(times)
    
    # Basic statistics
    mean_rtt = np.mean(rtts)
    std_rtt = np.std(rtts)
    
    # Find peaks using scipy
    # A peak is a local maximum that stands out
    peaks, properties = signal.find_peaks(rtts, prominence=5)  # 5ms prominence
    
    # Find valleys (inverse peaks)
    valleys, _ = signal.find_peaks(-rtts, prominence=5)
    
    # Detect route changes (significant RTT level shifts)
    rtt_diff = np.abs(np.diff(rtts))
    route_changes = np.where(rtt_diff > 5)[0]  # >5ms sudden changes
    
    # Calculate peak-to-peak variation
    if len(peaks) > 0:
        peak_rtts = rtts[peaks]
        avg_peak_height = np.mean(peak_rtts)
    else:
        avg_peak_height = 0
    
    # Calculate path stability (coefficient of variation)
    cv = std_rtt / mean_rtt if mean_rtt > 0 else 0
    
    # Detect distinct routing states
    # Round to 5ms bins to identify states
    binned = np.round(rtts / 5) * 5
    unique_states = len(np.unique(binned))
    
    # Calculate how much time is spent in each state
    from collections import Counter
    state_counts = Counter(binned)
    dominant_state_pct = max(state_counts.values()) / len(binned) * 100
    
    print(f"\n{'='*60}")
    print(f"Algorithm: {algo_name}")
    print(f"{'='*60}")
    print(f"Total RTT samples: {len(rtts)}")
    print(f"Mean RTT: {mean_rtt:.2f} ms")
    print(f"StdDev RTT: {std_rtt:.2f} ms")
    print(f"Coefficient of Variation: {cv:.4f}")
    print(f"\nPeak Analysis:")
    print(f"  Number of peaks (local maxima >5ms): {len(peaks)}")
    print(f"  Number of valleys: {len(valleys)}")
    print(f"  Peak frequency: {len(peaks)/times[-1]:.2f} peaks/second")
    if len(peaks) > 0:
        print(f"  Average peak RTT: {avg_peak_height:.2f} ms")
    print(f"\nRouting Stability:")
    print(f"  Significant RTT changes (>5ms): {len(route_changes)}")
    print(f"  Route change frequency: {len(route_changes)/times[-1]:.3f} changes/second")
    print(f"  Distinct routing states: {unique_states}")
    print(f"  Time in dominant state: {dominant_state_pct:.1f}%")
    print(f"  Average time between route changes: {times[-1]/len(route_changes):.1f}s" if len(route_changes) > 0 else "  No route changes detected")
    
    return {
        'algo': algo_name,
        'num_peaks': len(peaks),
        'num_valleys': len(valleys),
        'peak_freq': len(peaks)/times[-1],
        'route_changes': len(route_changes),
        'unique_states': unique_states,
        'cv': cv,
        'mean': mean_rtt,
        'std': std_rtt
    }

if __name__ == "__main__":
    results = []
    
    routes = [
        ("Manila_to_London", "Manila→London"),
        ("Sydney_to_Nairobi", "Sydney→Nairobi"),
        ("Tokyo_to_NewYork", "Tokyo→NewYork")
    ]
    
    for route_name, route_display in routes:
        print(f"\n{'#'*60}")
        print(f"# Route: {route_display}")
        print(f"{'#'*60}")
        
        for algo in ['anchor_lmsr', 'naive_lmsr', 'free_gs']:
            csv_file = f"temp/runs/{algo}_{route_name}_TcpNewReno_10Mbps/logs_ns3/tcp_flow_0_rtt.csv"
            result = analyze_rtt_file(csv_file, algo)
            result['route'] = route_display
            results.append(result)
    
    # Summary comparison
    print(f"\n{'='*80}")
    print("SUMMARY COMPARISON")
    print(f"{'='*80}")
    print(f"\n{'Route':<20} {'Algorithm':<15} {'Peaks':<10} {'Peak/s':<10} {'Changes':<10} {'States':<10} {'CV':<10}")
    print("-" * 80)
    for r in results:
        print(f"{r['route']:<20} {r['algo']:<15} {r['num_peaks']:<10} {r['peak_freq']:<10.2f} {r['route_changes']:<10} {r['unique_states']:<10} {r['cv']:<10.4f}")
