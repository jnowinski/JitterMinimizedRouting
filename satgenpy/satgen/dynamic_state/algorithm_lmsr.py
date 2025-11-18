from .fstate_calculation import *


class LMSRRouter:
    def __init__(self, lookahead_steps=10, jitter_threshold=10):
        """
        Initialize jitter-minimized router with configurable parameters
        """
        self.lookahead_steps = lookahead_steps
        self.jitter_threshold = jitter_threshold

        # Persistent state
        self.future_graphs_cache = []
        self.current_graph_index = 0

    def validate_interface_conditions(self, list_gsl_interfaces_info, satellites, ground_stations):
        """
        Validate interface conditions (same as free_gs_one_sat_many_only_over_isls)
        """
        for i in range(len(list_gsl_interfaces_info)):
            if i < len(satellites):
                if list_gsl_interfaces_info[i]["number_of_interfaces"] != len(ground_stations):
                    raise ValueError("Satellites must have the same amount of GSL interfaces as ground stations exist")
                if list_gsl_interfaces_info[i]["aggregate_max_bandwidth"] != len(ground_stations):
                    raise ValueError("Satellite aggregate max. bandwidth is not equal to 1.0 times number of GSs")
            else:
                if list_gsl_interfaces_info[i]["number_of_interfaces"] != 1:
                    raise ValueError("Ground stations must have exactly one interface")
                if list_gsl_interfaces_info[i]["aggregate_max_bandwidth"] != 1.0:
                    raise ValueError("Ground station aggregate max. bandwidth is not equal to 1.0")

    def initialize_graphs(
            self,
            epoch,
            time_since_epoch_ns,
            time_step_ns,
            satellites,
            ground_stations,
            list_isls,
            list_gsl_interfaces_info,
            max_gsl_length_m,
            max_isl_length_m,
            enable_verbose_logs,
            generate_graph_state_at,
    ):
        """
        Fill graph cache for initial look ahead
        """
        if enable_verbose_logs:
            print(f"  > Initializing first {self.lookahead_steps} future network states")
        for i in range(self.lookahead_steps):
            if enable_verbose_logs:
                print(
                    f"  > Generating network state graph for T = {time_since_epoch_ns + time_step_ns * i}")
            self.future_graphs_cache.append(generate_graph_state_at(
                epoch,
                time_since_epoch_ns + time_step_ns * i,
                satellites,
                ground_stations,
                list_isls,
                list_gsl_interfaces_info,
                max_gsl_length_m,
                max_isl_length_m,
                enable_verbose_logs
            ))

    def write_bandwidth_files(self, output_dynamic_state_dir, time_since_epoch_ns,
                              satellites, ground_stations, list_gsl_interfaces_info,
                              num_isls_per_sat, enable_verbose_logs):
        """
        Write GSL interface bandwidth allocation files (same as free_gs_one_sat_many_only_over_isls)
        """
        output_filename = output_dynamic_state_dir + "/gsl_if_bandwidth_" + str(time_since_epoch_ns) + ".txt"

        if enable_verbose_logs:
            print("  > Writing interface bandwidth state to: " + output_filename)

        with open(output_filename, "w+") as f_out:
            if time_since_epoch_ns == 0:
                # Satellite have <# of GSs> interfaces besides their ISL interfaces
                for node_id in range(len(satellites)):
                    for i in range(list_gsl_interfaces_info[node_id]["number_of_interfaces"]):
                        f_out.write("%d,%d,%f\n" % (
                            node_id,
                            num_isls_per_sat[node_id] + i,
                            list_gsl_interfaces_info[node_id]["aggregate_max_bandwidth"]
                            / float(list_gsl_interfaces_info[node_id]["number_of_interfaces"])
                        ))

                # Ground stations have one GSL interface: 0
                for node_id in range(len(satellites), len(satellites) + len(ground_stations)):
                    f_out.write("%d,%d,%f\n" % (
                        node_id,
                        0,
                        list_gsl_interfaces_info[node_id]["aggregate_max_bandwidth"]
                    ))

    def step(
            self,
            epoch,
            time_since_epoch_ns,
            time_step_ns,
            satellites,
            ground_stations,
            list_isls,
            list_gsl_interfaces_info,
            max_gsl_length_m,
            max_isl_length_m,
            enable_verbose_logs,
            generate_graph_state_at,
    ):
        if enable_verbose_logs:
            print(
                f"  > Generating network state graph for T = {time_since_epoch_ns + time_step_ns * self.lookahead_steps}")

        # Replace the oldest graph state in cache
        self.future_graphs_cache[self.current_graph_index] = generate_graph_state_at(
            epoch,
            time_since_epoch_ns + time_step_ns * self.lookahead_steps,
            satellites,
            ground_stations,
            list_isls,
            list_gsl_interfaces_info,
            max_gsl_length_m,
            max_isl_length_m,
            enable_verbose_logs
        )

        # Increment the current graph state index
        self.current_graph_index = (self.current_graph_index + 1) % self.lookahead_steps

    def calculate_forwarding_state(self, output_dynamic_state_dir, time_since_epoch_ns, satellites, ground_stations,
                                   sat_net_graph_only_satellites_with_isls,
                                   ground_station_satellites_in_range, num_isls_per_sat,
                                   sat_neighbor_to_if, list_gsl_interfaces_info, prev_fstate,
                                   enable_verbose_logs):
        """
        Calculate forwarding state using LMSR algorithm from
        S. Sun, R. Zhang, K. Liu, Z. Sun, Q. Tang, and T. Huang,
        ‘LMSR: A Low-Jitter Multiple Slots Routing Algorithm in LEO Satellite Networks’,
        in 2025 IEEE Wireless Communications and Networking Conference (WCNC), 2025, pp. 1–6.
        """

        if enable_verbose_logs:
            print("  > Calculating forwarding state")

        # Check the graph (same validation as existing algorithms)
        if sat_net_graph_only_satellites_with_isls.number_of_nodes() != len(satellites):
            raise ValueError("Number of nodes in the graph does not match the number of satellites")
        for sid in range(len(satellites)):
            for n in sat_net_graph_only_satellites_with_isls.neighbors(sid):
                if n >= len(satellites):
                    raise ValueError("Graph cannot contain satellite-to-ground-station links")

        # GID to satellite GSL interface index (same as free_gs_one_sat_many_only_over_isls)
        # Each ground station has a GSL interface on every satellite allocated only for itself
        gid_to_sat_gsl_if_idx = list(range(len(ground_stations)))

        # Calculate routing paths
        # TODO: Replace with LMSR path selection
        fstate = calculate_lmsr_path_without_gs_relaying(
            output_dynamic_state_dir,
            time_since_epoch_ns,
            len(satellites),
            len(ground_stations),
            sat_net_graph_only_satellites_with_isls,
            num_isls_per_sat,
            gid_to_sat_gsl_if_idx,
            ground_station_satellites_in_range,
            sat_neighbor_to_if,
            prev_fstate,
            enable_verbose_logs
        )

        if enable_verbose_logs:
            print(f"  > Generated forwarding state with {len(fstate)} entries")

        return fstate


def algorithm_lmsr(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        time_step_ns,
        satellites,
        ground_stations,
        list_gsl_interfaces_info,
        prev_output,
        enable_verbose_logs,
        epoch,
        list_isls,
        max_gsl_length_m,
        max_isl_length_m,
        generate_graph_state_at,  # Generator function (./generator_dynamic_state.generate_graph_state_at)
):
    """
    LMSR ALGORITHM

    Find the shortest path for each timestep and remove the most congested links
    until all paths are as close to the longest initial path as possible.

    "gs_one": Each ground station has exactly 1 GSL interface
    "sat_many": Each satellite has <number of ground stations> GSL interfaces
    "free": GSL interfaces can connect to any satellite in range
    "only_over_isls": Uses inter-satellite links, no ground station relays
    """

    if enable_verbose_logs:
        print("\nALGORITHM: LMSR")

    # Get or create router instance
    if prev_output and "router" in prev_output:
        router = prev_output["router"]
        if enable_verbose_logs:
            print("  > Reusing router from previous time step")
        router.step(
            epoch,
            time_since_epoch_ns,
            time_step_ns,
            satellites,
            ground_stations,
            list_isls,
            list_gsl_interfaces_info,
            max_gsl_length_m,
            max_isl_length_m,
            enable_verbose_logs,
            generate_graph_state_at,
        )
    else:
        router = LMSRRouter()

        if enable_verbose_logs:
            print("  > Created new jitter-minimized router instance")

        # Initialize graphs
        router.initialize_graphs(
            epoch,
            time_since_epoch_ns,
            time_step_ns,
            satellites,
            ground_stations,
            list_isls,
            list_gsl_interfaces_info,
            max_gsl_length_m,
            max_isl_length_m,
            enable_verbose_logs,
            generate_graph_state_at,
        )

    # Validate interface conditions (same as free_gs_one_sat_many_only_over_isls)
    router.validate_interface_conditions(list_gsl_interfaces_info, satellites, ground_stations)
    if enable_verbose_logs:
        print("  > Interface conditions are met")

    # Write bandwidth files
    router.write_bandwidth_files(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        satellites,
        ground_stations,
        list_gsl_interfaces_info,
        router.future_graphs_cache[router.current_graph_index]['num_isls_per_sat'],
        enable_verbose_logs
    )

    # Previous forwarding state (to only write delta)
    prev_fstate = None
    if prev_output is not None:
        prev_fstate = prev_output.get("fstate")

    # Calculate forwarding state using the router
    fstate = router.calculate_forwarding_state(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        satellites,
        ground_stations,
        # Need to pass all look-ahead states
        router.future_graphs_cache[router.current_graph_index]['sat_net_graph_only_satellites_with_isls'],
        router.future_graphs_cache[router.current_graph_index]['ground_station_satellites_in_range'],
        router.future_graphs_cache[router.current_graph_index]['num_isls_per_sat'],
        router.future_graphs_cache[router.current_graph_index]['sat_neighbor_to_if'],
        list_gsl_interfaces_info,
        prev_fstate,
        enable_verbose_logs
    )

    if enable_verbose_logs:
        print("")

    return {
        "fstate": fstate,
        "router": router  # Persist state for next time step
    }
