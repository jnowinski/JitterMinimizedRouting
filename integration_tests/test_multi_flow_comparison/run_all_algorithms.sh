#!/bin/bash
# Run complete test suite comparing anchor-based LMSR, naive LMSR, and free_gs algorithms
# across multiple diverse ground station pairs

set -e

echo "========================================="
echo "Multi-Flow Algorithm Comparison Test"
echo "========================================="
echo ""
echo "This test will:"
echo "- Generate 8 ground stations globally distributed"
echo "- Create forwarding states for 3 algorithms:"
echo "  1. Anchor-based LMSR (jitter minimized)"
echo "  2. Naive LMSR"
echo "  3. Free GS (standard shortest path)"
echo "- Run 5 diverse TCP flows for each algorithm (15 total)"
echo "- Generate RTT comparison plots"
echo ""
echo "Flows:"
echo "  1. Manila -> London (long distance, cross-hemisphere)"
echo "  2. Tokyo -> NewYork (trans-Pacific)"
echo "  3. Sydney -> Nairobi (cross-equator)"
echo "  4. Manila -> LosAngeles (Pacific crossing)"
echo "  5. Sydney -> SaoPaulo (southern hemisphere)"
echo ""
read -p "Press Enter to continue..."

# Clean up previous runs
echo ""
echo "Cleaning up previous runs..."
rm -rf temp

# Generate satellite network states for all three algorithms
echo ""
echo "========================================="
echo "Step 1: Generating Network States"
echo "========================================="

# Generate anchor-based LMSR
echo ""
echo "--- Generating Anchor-based LMSR state ---"
python3 step_1_generate_anchor_lmsr.py

# Generate naive LMSR
echo ""
echo "--- Generating Naive LMSR state ---"
python3 step_1_generate_naive_lmsr.py

# Generate free_gs
echo ""
echo "--- Generating Free GS state ---"
python3 step_1_generate_free_gs.py

# Generate run configurations
echo ""
echo "========================================="
echo "Step 2: Generating Run Configurations"
echo "========================================="
python3 step_2_generate_runs.py

# Run simulations
echo ""
echo "========================================="
echo "Step 3: Running NS3 Simulations"
echo "========================================="
echo "This will run 15 simulations (3 algorithms × 5 flows)"
echo "Running up to 4 in parallel..."
python3 step_3_run.py

# Generate plots
echo ""
echo "========================================="
echo "Step 4: Generating Performance Plots"
echo "========================================="
python3 step_4_generate_plots.py

# Generate comparison summary
echo ""
echo "========================================="
echo "Step 5: Generating Comparison Summary"
echo "========================================="
python3 step_5_generate_summary.py

echo ""
echo "========================================="
echo "Test Complete!"
echo "========================================="
echo ""
echo "Results are in temp/pdf/"
echo "Summary is in temp/comparison_summary.txt"
echo ""
