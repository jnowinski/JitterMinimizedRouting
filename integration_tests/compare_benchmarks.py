#!/usr/bin/env python3
"""
Compare benchmark results across all three algorithms
"""

import os

def read_benchmark(filepath):
    """Read benchmark data from file"""
    data = {}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    data[key.strip()] = value.strip()
    except FileNotFoundError:
        return None
    return data

print("\n" + "="*80)
print("ALGORITHM PERFORMANCE BENCHMARK COMPARISON")
print("Manila to Dalian - 100 seconds, 630 satellites")
print("="*80 + "\n")

benchmarks = [
    ("Anchor-based LMSR", "test_jitter_minimized_manila_dalian/temp/gen_data/benchmark_anchor_lmsr.txt", "O(N × (V log V + E))"),
    ("Naive LMSR", "test_naive_lmsr_manila_dalian/temp/gen_data/benchmark_naive_lmsr.txt", "O(N × V² × (V log V + E))"),
    ("Free GS", "test_free_gs_manila_dalian/temp/gen_data/benchmark_free_gs.txt", "O(N × V³)"),
]

results = []
for name, path, complexity in benchmarks:
    data = read_benchmark(path)
    if data:
        total_time = float(data['Total time'].split()[0])
        per_timestep = float(data['Time per timestep'].split()[0])
        results.append((name, total_time, per_timestep, complexity))
        print(f"{name}")
        print("-" * 80)
        print(f"  Algorithm:        {data.get('Algorithm', 'N/A')}")
        print(f"  Total time:       {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print(f"  Per timestep:     {per_timestep:.3f} seconds")
        print(f"  Complexity:       {complexity}")
        if 'Anchors' in data:
            print(f"  Anchors used:     {data['Anchors']}")
        print()
    else:
        print(f"{name}: Benchmark data not found at {path}")
        print(f"  Run: python3 {os.path.dirname(path).replace('temp/gen_data', 'step_1_generate_satellite_networks_state.py')}\n")

if len(results) >= 2:
    print("="*80)
    print("SPEEDUP COMPARISON")
    print("="*80 + "\n")
    
    # Use the slowest as baseline
    slowest = max(results, key=lambda x: x[1])
    
    for name, total, per_ts, complexity in sorted(results, key=lambda x: x[1]):
        speedup = slowest[1] / total
        print(f"{name:20s} {total:8.2f}s  ({speedup:5.2f}x vs {slowest[0]})")
    
    print()
    
    # Anchor vs Naive comparison if both exist
    anchor_data = next((r for r in results if "Anchor" in r[0]), None)
    naive_data = next((r for r in results if "Naive" in r[0]), None)
    
    if anchor_data and naive_data:
        speedup = naive_data[1] / anchor_data[1]
        time_saved = naive_data[1] - anchor_data[1]
        print(f"Anchor-based vs Naive LMSR:")
        print(f"  Speedup: {speedup:.2f}x faster")
        print(f"  Time saved: {time_saved:.2f} seconds ({time_saved/60:.2f} minutes)")
        print(f"  Reduction: {((naive_data[1] - anchor_data[1]) / naive_data[1] * 100):.1f}% less time\n")

print("="*80)
print("\nNote: Times measured for 100 timesteps (1 second intervals) on Kuiper-630")
print("      constellation with 2 ground stations (Manila, Dalian)\n")
