#!/usr/bin/env python3
"""
Generate comparison summary of RTT statistics across algorithms
"""

import csv
import statistics
import os

try:
    from .run_list import *
except (ImportError, SystemError):
    from run_list import *

def read_rtt_data(rtt_file):
    """Read RTT data from CSV file"""
    rtts = []
    try:
        with open(rtt_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    rtts.append(float(row[1]) / 1e6)  # Convert ns to ms
    except FileNotFoundError:
        pass
    return rtts

def calculate_stats(rtts):
    """Calculate RTT statistics"""
    if not rtts:
        return None
    return {
        'mean': statistics.mean(rtts),
        'stdev': statistics.stdev(rtts) if len(rtts) > 1 else 0,
        'min': min(rtts),
        'max': max(rtts),
        'range': max(rtts) - min(rtts),
        'variance': statistics.variance(rtts) if len(rtts) > 1 else 0
    }

def read_tcp_completion(tcp_flows_file):
    """Read TCP completion percentage"""
    try:
        with open(tcp_flows_file, 'r') as f:
            lines = f.readlines()
            if len(lines) > 1:
                parts = lines[1].split()
                if len(parts) >= 9:
                    progress = parts[8]
                    return float(progress.rstrip('%'))
    except:
        pass
    return None

# Collect results
print("\nCollecting results...")
results = {}

for run in get_tcp_run_list():
    run_name = run["name"]
    algorithm = run["algorithm"]
    flow_pair = run["flow_pair"]
    
    rtt_file = f"temp/runs/{run_name}/logs_ns3/tcp_flow_0_rtt.csv"
    tcp_file = f"temp/runs/{run_name}/logs_ns3/tcp_flows.txt"
    
    rtts = read_rtt_data(rtt_file)
    stats = calculate_stats(rtts)
    completion = read_tcp_completion(tcp_file)
    
    if algorithm not in results:
        results[algorithm] = {}
    
    results[algorithm][flow_pair] = {
        'stats': stats,
        'completion': completion,
        'num_samples': len(rtts)
    }

# Generate summary report
output_file = "temp/comparison_summary.txt"
print(f"Writing summary to {output_file}...")

with open(output_file, 'w') as f:
    f.write("="*80 + "\n")
    f.write("MULTI-FLOW ALGORITHM COMPARISON SUMMARY\n")
    f.write("="*80 + "\n\n")
    
    f.write("Test Configuration:\n")
    f.write("  - Constellation: Kuiper-630 (21 orbits × 30 sats)\n")
    f.write("  - Duration: 100 seconds\n")
    f.write("  - Flow size: 1000 Mbit\n")
    f.write("  - Rate: 10 Mbps\n")
    f.write("  - TCP: TcpNewReno\n")
    f.write("  - Ground Stations: 8 (Manila, Tokyo, Sydney, London, NewYork, LosAngeles, SaoPaulo, Nairobi)\n\n")
    
    f.write("Algorithms Tested:\n")
    f.write("  1. anchor_lmsr: Anchor-based LMSR (60 anchors, O(N*(VlogV+E)))\n")
    f.write("  2. naive_lmsr:  Naive LMSR (all satellites, O(N*V²*(VlogV+E)))\n")
    f.write("  3. free_gs:     Standard shortest path (no jitter minimization)\n\n")
    
    f.write("="*80 + "\n")
    f.write("RESULTS BY FLOW\n")
    f.write("="*80 + "\n\n")
    
    # Get all flow pairs
    flow_pairs = set()
    for algo_results in results.values():
        flow_pairs.update(algo_results.keys())
    flow_pairs = sorted(flow_pairs)
    
    for flow in flow_pairs:
        f.write(f"\n{flow}\n")
        f.write("-" * 80 + "\n")
        f.write(f"{'Algorithm':<15} {'Completion':<12} {'RTT Mean':<12} {'RTT StdDev':<12} {'RTT Range':<12} {'Jitter':<12}\n")
        f.write("-" * 80 + "\n")
        
        for algo in ['anchor_lmsr', 'naive_lmsr', 'free_gs']:
            if algo in results and flow in results[algo]:
                data = results[algo][flow]
                stats = data['stats']
                completion = data['completion']
                
                if stats and completion is not None:
                    f.write(f"{algo:<15} {completion:>10.1f}%  {stats['mean']:>10.2f}ms  "
                           f"{stats['stdev']:>10.2f}ms  {stats['range']:>10.2f}ms  {stats['variance']:>10.2f}ms²\n")
                else:
                    f.write(f"{algo:<15} {'N/A':<12} {'N/A':<12} {'N/A':<12} {'N/A':<12} {'N/A':<12}\n")
        f.write("\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("ALGORITHM COMPARISON ACROSS ALL FLOWS\n")
    f.write("="*80 + "\n\n")
    
    for algo in ['anchor_lmsr', 'naive_lmsr', 'free_gs']:
        if algo in results:
            f.write(f"\n{algo.upper()}\n")
            f.write("-" * 80 + "\n")
            
            all_stdevs = []
            all_variances = []
            all_completions = []
            
            for flow, data in results[algo].items():
                if data['stats'] and data['completion'] is not None:
                    all_stdevs.append(data['stats']['stdev'])
                    all_variances.append(data['stats']['variance'])
                    all_completions.append(data['completion'])
            
            if all_stdevs:
                f.write(f"  Average RTT StdDev:  {statistics.mean(all_stdevs):.2f} ms\n")
                f.write(f"  Average Jitter:      {statistics.mean(all_variances):.2f} ms²\n")
                f.write(f"  Average Completion:  {statistics.mean(all_completions):.1f}%\n")
                f.write(f"  Flows Completed:     {len(all_completions)}/{len(flow_pairs)}\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("PLOTS GENERATED\n")
    f.write("="*80 + "\n\n")
    f.write("RTT plots for each flow are in: temp/pdf/<run_name>/plot_tcp_flow_time_vs_rtt_0.pdf\n")
    f.write("\nTo compare algorithms for a specific flow, view:\n")
    for flow in flow_pairs:
        f.write(f"\n{flow}:\n")
        for algo in ['anchor_lmsr', 'naive_lmsr', 'free_gs']:
            if algo in results and flow in results[algo]:
                run_name = f"{algo}_{flow}_TcpNewReno_10Mbps"
                f.write(f"  - temp/pdf/{run_name}/plot_tcp_flow_time_vs_rtt_0.pdf\n")
    
    f.write("\n" + "="*80 + "\n")

print(f"\nSummary written to: {output_file}")
print("\nTo view summary:")
print(f"  cat {output_file}")
