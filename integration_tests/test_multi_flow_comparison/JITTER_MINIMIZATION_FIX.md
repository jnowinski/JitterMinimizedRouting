# Jitter Minimization Fix - Algorithm Update

## Problem Identified

The original LMSR (Least Maximum Segment Routing) implementation **did not reduce jitter** because it optimized the wrong metric:

### Old Algorithm (WRONG):
```python
# Minimized WORST-CASE delay
max_length = max([distances[t] for t in timesteps])
cost = max_length  # ← Minimizes peak delay, NOT jitter
```

**Why this failed:**
- Jitter = RTT variance over time
- Minimizing max delay ≠ minimizing variance
- Analysis showed 100% of jitter came from path length variation on stable routes
- Route stability didn't help because satellite motion causes distance changes

## Solution Implemented

Changed both naive LMSR and anchor-based LMSR to minimize **delay variance (jitter)** instead of maximum delay:

### New Algorithm (CORRECT):
```python
# Minimize delay RANGE (jitter)
min_distance = min([distances[t] for t in timesteps])
max_distance = max([distances[t] for t in timesteps])
jitter = max_distance - min_distance  # ← Actual jitter metric
cost = jitter  # Primary: minimize jitter
```

## Changes Made

### 1. Naive LMSR (`calculate_lmsr_path_without_gs_relaying`)

**Destination satellite selection:**
- **Before:** Selected satellite with lowest max distance across timesteps
- **After:** Selects satellite with lowest delay range (max - min) across timesteps
- **Tie-breaking:** Uses mean delay as secondary criterion

**Next-hop selection:**
- **Before:** Chose neighbor minimizing max distance to destination
- **After:** Chooses neighbor minimizing delay range to destination

### 2. Anchor-based LMSR (`calculate_anchor_lmsr_path_complete_forwarding`)

**Path cost metric:**
- **Before:** `max_distance` across all timesteps
- **After:** `jitter_metric = max_distance - min_distance`

**Satellite selection:**
- **Before:** `(max_distance + gsl_distance, dst_sat)`
- **After:** `(jitter, mean_distance + gsl_distance, dst_sat)`

## Implementation Details

### File Modified:
`/home/hypatia-user/hypatia/satgenpy/satgen/dynamic_state/fstate_calculation.py`

### Key Code Sections:

#### Naive LMSR - Lines ~770-800:
```python
# Calculate jitter metric: range of delays (max - min)
min_length = min(lengths)
max_length = max(lengths)
delay_range = max_length - min_length  # This is the jitter

# Also calculate mean delay for tie-breaking
mean_length = sum(lengths) / len(lengths)

# Primary: minimize jitter (delay range)
# Secondary: minimize mean delay (for tie-breaking)
possibilities.append((
    delay_range,           # Minimize jitter first
    mean_length + b[0],    # Then minimize average delay
    b[1]
))
```

#### Anchor LMSR - Lines ~620-640:
```python
# Calculate jitter: range of delays (max - min)
min_distance = min(distances_across_time)
max_distance = max(distances_across_time)
jitter = max_distance - min_distance
mean_distance = sum(distances_across_time) / len(distances_across_time)

# Primary: minimize jitter, Secondary: minimize mean delay
possibilities.append((jitter, mean_distance + gsl_distance, dst_sat))
```

## Theoretical Basis

### Paper Reference: WCNC 2025
**Title:** "Low-Jitter Multiple Slots Routing Algorithm in LEO Satellite Networks"

**Their approach:**
1. Compute shortest path for each snapshot
2. Find maximum delay (Dmax) across all snapshots
3. **Intentionally lengthen shorter paths** to match Dmax
4. Result: All snapshots have similar delay → low jitter

**Our approach:**
- Same goal (minimize delay variance)
- Different method (select naturally stable paths instead of padding)
- More efficient (no path elongation needed)
- Direct optimization of jitter metric

### Jitter Definition

Both approaches use the same definition:
```
Jitter = max(delay[t] for t in timesteps) - min(delay[t] for t in timesteps)
```

## Expected Results

### Before Fix:
- Naive LMSR ≈ Free GS (both converged to same routes)
- Anchor LMSR had 2.5× more peaks due to anchor constraints
- Jitter: ~35ms for all algorithms
- **Conclusion:** LMSR provided no benefit

### After Fix:
- **Naive LMSR:** Should select paths with inherently stable distances
- **Anchor LMSR:** Should prefer anchor pairs with stable distances
- **Expected:** Lower jitter than Free GS and old LMSR
- **Trade-off:** May accept slightly longer paths if they have lower variance

## Testing

### Test Configuration:
- Route: Manila → LosAngeles (and others)
- Simulation time: 200 seconds
- Update interval: 1000ms
- Flow size: 2500 Mbit
- TCP: NewReno, 10 Mbps

### Metrics to Compare:
1. **RTT Standard Deviation:** Overall jitter
2. **RTT Range:** max(RTT) - min(RTT)
3. **Peak count:** Number of local maxima
4. **10s window jitter:** Average jitter within sliding windows

## Why This Works

### Root Cause Analysis showed:
```
100.0% of jitter from path length variation on STABLE routes
  0.1% of jitter from route changes
```

### Therefore:
- ✗ Minimizing route changes doesn't help
- ✗ Minimizing max delay doesn't help
- ✓ **Minimizing delay variance DOES help**

The fix directly addresses the root cause by selecting paths whose distance stays constant over time, even as satellites move.

## Comparison to Paper's Algorithm

| Aspect | WCNC 2025 Paper | Our Implementation |
|--------|----------------|-------------------|
| **Goal** | Minimize delay variance | Minimize delay variance |
| **Method** | Pad short paths to match Dmax | Select naturally stable paths |
| **Metric** | max(D) - min(D) across snapshots | max(D) - min(D) across lookahead |
| **Path changes** | Accepts longer paths | Accepts longer paths |
| **Computation** | O(N × V²) + path padding | O(N × V² × E) |
| **Trade-off** | Higher mean delay | Balanced delay vs jitter |

Both are valid approaches to the same problem. The paper's method requires post-processing to add delay, while ours selects paths with inherent stability during route computation.
