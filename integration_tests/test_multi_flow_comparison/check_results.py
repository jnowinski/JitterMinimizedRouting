#!/usr/bin/env python3
"""
Check results from all three algorithms and compare jitter metrics
"""

import numpy as np
import os
import sys

routes = [
    ('Manila_to_LosAngeles', 'Manila → Los Angeles'),
    ('Manila_to_London', 'Manila → London'),
    ('Tokyo_to_NewYork', 'Tokyo → New York'),
    ('Sydney_to_Nairobi', 'Sydney → Nairobi'),
    ('Sydney_to_SaoPaulo', 'Sydney → São Paulo'),
]

print('\n' + '='*90)
print('JITTER-MINIMIZED LMSR: COMPLETE RESULTS')
print('='*90)
print('\nAlgorithm Comparison:')
print('  - Free GS: Baseline shortest-path routing')
print('  - Naive LMSR: Full jitter-minimized LMSR (minimizes delay variance)')
print('  - Anchor LMSR: Anchor-based jitter-minimized LMSR (60 anchors)')
print('='*90)

all_results = {}

for route_id, route_name in routes:
    print(f'\n{route_name}:')
    print('-' * 90)
    
    results = {}
    for algo in ['free_gs', 'naive_lmsr', 'anchor_lmsr']:
        csv_file = f'temp/runs/{algo}_{route_id}_TcpNewReno_10Mbps/logs_ns3/tcp_flow_0_rtt.csv'
        
        if not os.path.exists(csv_file):
            print(f'  {algo:15s}: No data')
            continue
        
        rtts = []
        times = []
        with open(csv_file) as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 3:
                    times.append(float(parts[1]) / 1e9)
                    rtts.append(float(parts[2]) / 1e6)
        
        if len(rtts) == 0:
            print(f'  {algo:15s}: Empty data')
            continue
        
        rtts = np.array(rtts)
        times = np.array(times)
        
        results[algo] = {
            'mean': np.mean(rtts),
            'std': np.std(rtts),
            'min': np.min(rtts),
            'max': np.max(rtts),
            'jitter': np.max(rtts) - np.min(rtts),
            'completion': (times[-1] / 200.0) * 100,
            'samples': len(rtts)
        }
    
    all_results[route_id] = results
    
    # Print results
    algo_names = {'free_gs': 'Free GS', 'naive_lmsr': 'Naive LMSR', 'anchor_lmsr': 'Anchor LMSR'}
    for algo in ['free_gs', 'naive_lmsr', 'anchor_lmsr']:
        if algo in results:
            r = results[algo]
            print(f'  {algo_names[algo]:15s}: Mean={r["mean"]:6.2f}ms  Std={r["std"]:5.2f}ms  '
                  f'Jitter={r["jitter"]:6.2f}ms  Complete={r["completion"]:5.1f}%')
    
    # Calculate improvements
    if 'free_gs' in results and len(results) > 1:
        print(f'\n  Improvements vs Free GS:')
        for algo in ['naive_lmsr', 'anchor_lmsr']:
            if algo in results:
                std_imp = ((results['free_gs']['std'] - results[algo]['std']) / results['free_gs']['std']) * 100
                jit_imp = ((results['free_gs']['jitter'] - results[algo]['jitter']) / results['free_gs']['jitter']) * 100
                print(f'    {algo_names[algo]:15s}: Std Dev {std_imp:+6.1f}%   Jitter {jit_imp:+6.1f}%')

# Summary statistics
print('\n' + '='*90)
print('SUMMARY STATISTICS ACROSS ALL ROUTES')
print('='*90)

for algo in ['free_gs', 'naive_lmsr', 'anchor_lmsr']:
    stds = []
    jitters = []
    for route_id, _ in routes:
        if route_id in all_results and algo in all_results[route_id]:
            stds.append(all_results[route_id][algo]['std'])
            jitters.append(all_results[route_id][algo]['jitter'])
    
    if stds:
        algo_names = {'free_gs': 'Free GS', 'naive_lmsr': 'Naive LMSR', 'anchor_lmsr': 'Anchor LMSR'}
        print(f'\n{algo_names[algo]}:')
        print(f'  Routes tested: {len(stds)}')
        print(f'  Avg Std Dev:   {np.mean(stds):6.2f} ms  (range: {np.min(stds):5.2f} - {np.max(stds):5.2f})')
        print(f'  Avg Jitter:    {np.mean(jitters):6.2f} ms  (range: {np.min(jitters):5.2f} - {np.max(jitters):5.2f})')

print('\n' + '='*90)
print('CONCLUSION')
print('='*90)
print('Algorithm update: Both LMSR variants now minimize delay variance (max-min RTT)')
print('instead of minimizing maximum delay. This directly targets jitter reduction.')
print('='*90)
