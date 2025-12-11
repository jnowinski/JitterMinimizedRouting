# Comparison: WCNC 2025 Paper vs Your LMSR

## The Paper's Approach

**Algorithm: "Low-Jitter Multiple Slots Routing"**

### What it does:
1. **Initial routing**: Computes shortest path for each snapshot independently
2. **Finds max delay**: Identifies `Dmax` (the largest delay across all snapshots)
3. **Path elongation**: For snapshots with delay < Dmax, **intentionally makes paths longer** by:
   - Finding the most congested link in the current path
   - Detouring around it to use idle links
   - **Increasing delay** to get closer to Dmax
4. **Goal**: Make all snapshot delays approximately equal to Dmax

### Optimization objective:
```
min α * Σ(Dp - Dmax) + β * Σ(link_utilization)
```

- **First term**: Minimize difference from maximum delay (make all delays equal)
- **Second term**: Minimize link utilization (load balance)

### Key insight from paper:
> "In order to achieve the goal of making the difference in delay over different snapshots smaller, the delay in snapshots needs to be increased."

**They intentionally add delay to reduce jitter!**

---

## Your LMSR Approach

**Algorithm: "Least Maximum Segment Routing"**

### What it does:
1. **For each destination**: Computes shortest path across multiple timesteps
2. **Path cost metric**: Uses **worst-case (maximum)** distance across all lookahead timesteps
3. **Route selection**: Picks path that minimizes the worst-case distance
4. **Goal**: Minimize maximum delay while keeping routes stable

### Optimization objective:
```python
cost = max(distance[t] for t in timesteps)  # Worst-case distance
```

- Minimizes the **peak delay** across timesteps
- Assumes this reduces jitter by avoiding route changes

---

## Critical Differences

| Aspect | Paper's Algorithm | Your LMSR |
|--------|------------------|-----------|
| **Primary goal** | **Equalize delays** across snapshots | **Minimize max delay** |
| **Strategy** | **Lengthen short paths** to match Dmax | Find stable path with lowest worst-case |
| **Jitter definition** | `Dmax - Dmin` (range of delays) | Assumed from route stability |
| **Path modification** | **Actively increases delay** | Only considers existing paths |
| **Load balancing** | Uses idle links (explicit objective) | No load balancing mechanism |
| **Route changes** | May change routes to add delay | Tries to keep same route |

---

## Why LMSR Doesn't Work (But Paper's Does)

### The Paper's Key Insight:
**Jitter = variation in delay = Dmax - Dmin**

To reduce jitter, you need to make delays **similar**, not just stable.

### Example:
```
Snapshot 1: 140ms (shortest path = 7 hops)
Snapshot 2: 150ms (shortest path = 8 hops)  
Snapshot 3: 240ms (shortest path = 12 hops)  ← Dmax

Jitter = 240 - 140 = 100ms
```

**Paper's approach:**
- Snapshot 1: Detour to make it 235ms (add 5 hops)
- Snapshot 2: Detour to make it 238ms (add 4 hops)
- Snapshot 3: Keep at 240ms (already max)
- **New jitter = 240 - 235 = 5ms** ✓

**Your LMSR approach:**
- Finds path with stable worst-case = 240ms
- Uses that path in all snapshots → 240ms, 240ms, 240ms
- **Jitter = 0ms** (theoretically)

**But in practice:**
- Even on "same route", satellite motion causes distance variation
- You get 240ms ± 35ms due to link length changes
- **Actual jitter = 70ms** ✗

---

## Why the Paper's Algorithm Works

### 1. **Addresses the right problem**
- Jitter = delay variation across snapshots
- Directly minimizes `max(D) - min(D)`

### 2. **Accepts longer paths for jitter reduction**
- Trades delay for jitter control
- Uses network capacity more evenly

### 3. **Explicitly considers all snapshots jointly**
- Not just current + lookahead
- Computes routing for entire service duration

### 4. **Load balancing side benefit**
- Detouring around congested links improves throughput
- Your LMSR has no load balancing

---

## What Your LMSR Actually Does

Based on the code analysis:

```python
# Line 780-792: LMSR finds worst-case distance
lengths = [dist_sat_net_without_gs[i][curr][b[1]] for i in range(len(...))]
max_length = max(lengths)  # Worst-case across timesteps
```

**This optimizes for:**
- Minimizing worst-case delay
- Route stability (same next-hop across timesteps)

**This does NOT optimize for:**
- Delay variance across timesteps
- Equalizing delays
- Load balancing

**Result:**
- Routes are stable (same path topology)
- But path distances still vary due to satellite motion
- Jitter remains high (30-40ms) even with stable routes

---

## The Fundamental Issue

### Paper's definition of jitter:
> "The average jitter is defined as the difference between the maximum and minimum end-to-end delays over the entire duration of the service"
> 
> `Jitter = max(Dk) - min(Dk)`

This is about **snapshot-to-snapshot variation**.

### Your LMSR's implicit assumption:
- Jitter comes from route changes
- Stable routes = low jitter

**But your analysis proved this wrong:**
- 100% of jitter comes from path length variation
- 0.1% comes from route changes

---

## Could You Implement Their Algorithm?

**Yes, but it requires:**

1. **Change optimization metric** from:
   ```python
   cost = max(distance[t] for t in timesteps)
   ```
   to:
   ```python
   delays = [distance[t] for t in timesteps]
   cost_jitter = max(delays) - min(delays)
   cost_load = sum(link_utilizations)
   cost = α * cost_jitter + β * cost_load
   ```

2. **Compute paths for entire service duration**
   - Not just next 10 timesteps
   - Need to know service start/end time

3. **Path elongation mechanism**
   - Find paths longer than shortest path
   - Detour around congested/varying-length links
   - Target specific delay values

4. **Multi-objective optimization**
   - Balance jitter vs delay vs load

---

## Bottom Line

### Paper's algorithm:
✅ **Makes delays equal** → reduces jitter  
✅ Explicitly optimizes `max(D) - min(D)`  
✅ Accepts longer paths for stability  
✅ Load balances as side effect  

### Your LMSR:
✅ Makes **routes stable** → doesn't reduce jitter  
✗ Optimizes wrong metric (`max(D)` instead of `range(D)`)  
✗ Doesn't account for satellite motion  
✗ No load balancing  

**Your LMSR is fundamentally solving a different problem than jitter reduction.**
