# The MIT License (MIT)
#
# Copyright (c) 2020 ETH Zurich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Core values
dynamic_state_update_interval_ms = 1000                         # 1 second update interval
simulation_end_time_s = 100                                     # 100 seconds
dynamic_state_generation_duration_s = 101                       # Generate 101s to have state for t=100
enable_isl_utilization_tracking = True                          # Enable utilization tracking
isl_utilization_tracking_interval_ns = 1 * 1000 * 1000 * 1000   # 1 second utilization intervals

# Derivatives
dynamic_state_update_interval_ns = dynamic_state_update_interval_ms * 1000 * 1000
simulation_end_time_ns = simulation_end_time_s * 1000 * 1000 * 1000
dynamic_state = "dynamic_state_" + str(dynamic_state_update_interval_ms) + "ms_for_" + str(dynamic_state_generation_duration_s) + "s"

# Ground station node IDs: Manila=630, Tokyo=631, Sydney=632, London=633, NewYork=634, LosAngeles=635, SaoPaulo=636, Nairobi=637

# Test flows with diverse characteristics:
# 1. Long distance, cross-hemisphere (Manila -> London)
# 2. Medium distance, different orbital planes (Tokyo -> NewYork) 
# 3. Cross-equator (Sydney -> Nairobi)
# 4. Trans-Pacific (Manila -> LosAngeles)
# 5. South hemisphere (Sydney -> SaoPaulo)

def get_tcp_run_list():
    """Generate run configurations for all three algorithms with multiple flows"""
    
    algorithms = [
        ("anchor_lmsr", "kuiper_630_isls_algorithm_jitter_minimized"),
        ("naive_lmsr", "kuiper_630_isls_algorithm_lmsr"),
        ("free_gs", "kuiper_630_isls_algorithm_free_gs_one_sat_many_only_over_isls")
    ]
    
    # Diverse flow pairs: (src_name, src_id, dst_name, dst_id)
    flow_pairs = [
        ("Manila", 630, "London", 633),           # Long distance cross-hemisphere
        ("Tokyo", 631, "NewYork", 634),           # Trans-Pacific
        ("Sydney", 632, "Nairobi", 637),          # Cross-equator
        ("Manila", 630, "LosAngeles", 635),       # Pacific crossing
        ("Sydney", 632, "SaoPaulo", 636),         # Southern hemisphere
    ]
    
    run_list = []
    for algo_name, satellite_network in algorithms:
        for src_name, src_id, dst_name, dst_id in flow_pairs:
            run_list.append({
                "name": f"{algo_name}_{src_name}_to_{dst_name}_TcpNewReno_10Mbps",
                "satellite_network": satellite_network,
                "dynamic_state": dynamic_state,
                "dynamic_state_update_interval_ns": dynamic_state_update_interval_ns,
                "simulation_end_time_ns": simulation_end_time_ns,
                "data_rate_megabit_per_s": 10.0,
                "queue_size_pkt": 100,
                "enable_isl_utilization_tracking": enable_isl_utilization_tracking,
                "isl_utilization_tracking_interval_ns": isl_utilization_tracking_interval_ns,
                "from_id": src_id,
                "to_id": dst_id,
                "tcp_socket_type": "TcpNewReno",
                "algorithm": algo_name,
                "flow_pair": f"{src_name}_to_{dst_name}"
            })
    
    return run_list

