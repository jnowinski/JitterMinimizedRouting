#!/bin/bash

echo "=========================================="
echo "FORWARDING STATE GENERATION BENCHMARK"
echo "=========================================="
echo ""

# Free GS
echo "[1/3] Benchmarking Free GS..."
START=$(date +%s)
python3 step_1_generate_free_gs.py > /tmp/free_gs.log 2>&1
END=$(date +%s)
FREE_GS_TIME=$((END - START))
echo "      Time: ${FREE_GS_TIME}s"
echo ""

# LMSR
echo "[2/3] Benchmarking LMSR (Jitter-Minimized)..."
START=$(date +%s)
python3 step_1_generate_naive_lmsr.py > /tmp/naive_lmsr.log 2>&1
END=$(date +%s)
LMSR_TIME=$((END - START))
echo "      Time: ${LMSR_TIME}s"
echo ""

# Anchor LMSR
echo "[3/3] Benchmarking Anchor LMSR..."
START=$(date +%s)
python3 step_1_generate_anchor_lmsr.py > /tmp/anchor_lmsr.log 2>&1
END=$(date +%s)
ANCHOR_TIME=$((END - START))
echo "      Time: ${ANCHOR_TIME}s"
echo ""

# Results
echo "=========================================="
echo "RESULTS (101 timesteps)"
echo "=========================================="
printf "%-25s %10s %15s\n" "Algorithm" "Time" "vs Free GS"
echo "------------------------------------------"
printf "%-25s %10ss %15s\n" "Free GS" "$FREE_GS_TIME" "baseline"

if [ $FREE_GS_TIME -gt 0 ]; then
    LMSR_PCT=$(awk "BEGIN {printf \"+%.1f%%\", (($LMSR_TIME - $FREE_GS_TIME) / $FREE_GS_TIME) * 100}")
    ANCHOR_PCT=$(awk "BEGIN {printf \"+%.1f%%\", (($ANCHOR_TIME - $FREE_GS_TIME) / $FREE_GS_TIME) * 100}")
else
    LMSR_PCT="N/A"
    ANCHOR_PCT="N/A"
fi

printf "%-25s %10ss %15s\n" "LMSR" "$LMSR_TIME" "$LMSR_PCT"
printf "%-25s %10ss %15s\n" "Anchor LMSR" "$ANCHOR_TIME" "$ANCHOR_PCT"
echo "=========================================="
