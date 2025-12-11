# Naive LMSR Routing Loop Issue

## Problem Summary

Naive LMSR creates **routing loops** that cause simulations to crash. Analysis shows:

- **4 out of 5 routes fail** with routing loops
- **Only Tokyo→NewYork succeeds** (happens to be loop-free)
- Crash occurs at runtime when packets enter the loop

## Root Cause

### Example: Manila → London Loop

```
Path: 630 → 103 → 102 → 101 → 100 → 99 → 100 (LOOP!)
                                      ↑______|
```

Satellites 99 and 100 each think the other provides the lowest-jitter route to London, creating an infinite loop.

### Why This Happens

**Naive LMSR uses greedy local selection**:
- Each satellite independently picks its neighbor with lowest jitter
- No global path computation
- No loop detection
- Result: Locally optimal ≠ Globally valid

**Free GS uses Floyd-Warshall**:
- Computes all-pairs shortest paths globally
- Then uses greedy next-hop selection based on global distances
- Guaranteed loop-free because based on global shortest path tree

## The Fundamental Problem

Naive LMSR implements:
```python
for each satellite S:
    for each neighbor N of S:
        jitter_to_dest_via_N = calculate_jitter(S → N → dest)
    best_neighbor = neighbor with minimum jitter
    forward_to[dest] = best_neighbor
```

This is **NOT** a shortest-path algorithm! It's purely greedy and can create loops.

## Correct Approaches

### 1. Anchor LMSR (WORKS)
- Uses anchor satellites as waypoints
- Computes anchor-to-anchor paths with BFS
- Provides global routing structure
- **Result: 5/5 routes succeed, no loops**

### 2. What Naive LMSR Should Do
Replace greedy selection with proper shortest-path algorithm:

```python
# Compute jitter-aware distances
for each timestep t:
    for each edge (u,v):
        jitter[u][v] = max_delay(u,v) - min_delay(u,v)

# Run Dijkstra/Floyd-Warshall with jitter metric
shortest_jitter_paths = dijkstra(source=each_satellite, metric=jitter)

# Use shortest-jitter-path tree for forwarding
for each satellite S:
    forward_to[dest] = next_hop_on_shortest_jitter_path(S, dest)
```

## Test Results

| Algorithm | Routes Tested | Succeeded | Failed | Success Rate |
|-----------|---------------|-----------|--------|--------------|
| Free GS | 5 | 5 | 0 | 100% |
| Anchor LMSR | 5 | 5 | 0 | 100% |
| Naive LMSR | 5 | 1 | 4 | 20% |

### Failing Routes (Naive LMSR)
- Manila → London (loop at sat 99↔100)
- Manila → Los Angeles (routing loop)
- Sydney → Nairobi (routing loop)  
 São Paulo (routing loop)

### Successful Route (Naive LMSR)
- Tokyo → New York (happens to be loop-free)

## Recommendation

**Do NOT use Naive LMSR** - it creates routing loops in realistic satellite topologies.

**Use Anchor LMSR** - it provides jitter minimization with guaranteed loop-free routing.

## Fix Required

To make Naive LMSR work, it needs a complete redesign:
1. Compute global shortest-jitter-path tree (using Dijkstra/Floyd-Warshall)
2. Use tree-based forwarding (guaranteed loop-free)
3. Update metric calculation to use pre-computed paths

This is essentially a different algorithm and would be computationally expensive for large networks.
