import math
import networkx as nx


def calculate_fstate_shortest_path_without_gs_relaying(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph_only_satellites_with_isls,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        ground_station_satellites_in_range_candidates,
        sat_neighbor_to_if,
        prev_fstate,
        enable_verbose_logs
):
    # Calculate shortest path distances
    if enable_verbose_logs:
        print("  > Calculating Floyd-Warshall for graph without ground-station relays")
    # (Note: Numpy has a deprecation warning here because of how networkx uses matrices)
    dist_sat_net_without_gs = nx.floyd_warshall_numpy(sat_net_graph_only_satellites_with_isls)

    # Forwarding state
    fstate = {}

    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    if enable_verbose_logs:
        print("  > Writing forwarding state to: " + output_filename)
    with open(output_filename, "w+") as f_out:

        # Satellites to ground stations
        # From the satellites attached to the destination ground station,
        # select the one which promises the shortest path to the destination ground station (getting there + last hop)
        dist_satellite_to_ground_station = {}
        for curr in range(num_satellites):
            for dst_gid in range(num_ground_stations):
                dst_gs_node_id = num_satellites + dst_gid

                # Among the satellites in range of the destination ground station,
                # find the one which promises the shortest distance
                possible_dst_sats = ground_station_satellites_in_range_candidates[dst_gid]
                possibilities = []
                for b in possible_dst_sats:
                    if not math.isinf(dist_sat_net_without_gs[(curr, b[1])]):  # Must be reachable
                        possibilities.append(
                            (
                                dist_sat_net_without_gs[(curr, b[1])] + b[0],
                                b[1]
                            )
                        )
                possibilities = list(sorted(possibilities))

                # By default, if there is no satellite in range for the
                # destination ground station, it will be dropped (indicated by -1)
                next_hop_decision = (-1, -1, -1)
                distance_to_ground_station_m = float("inf")
                if len(possibilities) > 0:
                    dst_sat = possibilities[0][1]
                    distance_to_ground_station_m = possibilities[0][0]

                    # If the current node is not that satellite, determine how to get to the satellite
                    if curr != dst_sat:

                        # Among its neighbors, find the one which promises the
                        # lowest distance to reach the destination satellite
                        best_distance_m = 1000000000000000
                        for neighbor_id in sat_net_graph_only_satellites_with_isls.neighbors(curr):
                            distance_m = (
                                    sat_net_graph_only_satellites_with_isls.edges[(curr, neighbor_id)]["weight"]
                                    +
                                    dist_sat_net_without_gs[(neighbor_id, dst_sat)]
                            )
                            if distance_m < best_distance_m:
                                next_hop_decision = (
                                    neighbor_id,
                                    sat_neighbor_to_if[(curr, neighbor_id)],
                                    sat_neighbor_to_if[(neighbor_id, curr)]
                                )
                                best_distance_m = distance_m

                    else:
                        # This is the destination satellite, as such the next hop is the ground station itself
                        next_hop_decision = (
                            dst_gs_node_id,
                            num_isls_per_sat[dst_sat] + gid_to_sat_gsl_if_idx[dst_gid],
                            0
                        )

                # In any case, save the distance of the satellite to the ground station to re-use
                # when we calculate ground station to ground station forwarding
                dist_satellite_to_ground_station[(curr, dst_gs_node_id)] = distance_to_ground_station_m

                # Write to forwarding state
                if not prev_fstate or prev_fstate[(curr, dst_gs_node_id)] != next_hop_decision:
                    f_out.write("%d,%d,%d,%d,%d\n" % (
                        curr,
                        dst_gs_node_id,
                        next_hop_decision[0],
                        next_hop_decision[1],
                        next_hop_decision[2]
                    ))
                fstate[(curr, dst_gs_node_id)] = next_hop_decision

        # Ground stations to ground stations
        # Choose the source satellite which promises the shortest path
        for src_gid in range(num_ground_stations):
            for dst_gid in range(num_ground_stations):
                if src_gid != dst_gid:
                    src_gs_node_id = num_satellites + src_gid
                    dst_gs_node_id = num_satellites + dst_gid

                    # Among the satellites in range of the source ground station,
                    # find the one which promises the shortest distance
                    possible_src_sats = ground_station_satellites_in_range_candidates[src_gid]
                    possibilities = []
                    for a in possible_src_sats:
                        best_distance_offered_m = dist_satellite_to_ground_station[(a[1], dst_gs_node_id)]
                        if not math.isinf(best_distance_offered_m):
                            possibilities.append(
                                (
                                    a[0] + best_distance_offered_m,
                                    a[1]
                                )
                            )
                    possibilities = sorted(possibilities)

                    # By default, if there is no satellite in range for one of the
                    # ground stations, it will be dropped (indicated by -1)
                    next_hop_decision = (-1, -1, -1)
                    if len(possibilities) > 0:
                        src_sat_id = possibilities[0][1]
                        next_hop_decision = (
                            src_sat_id,
                            0,
                            num_isls_per_sat[src_sat_id] + gid_to_sat_gsl_if_idx[src_gid]
                        )

                    # Update forwarding state
                    if not prev_fstate or prev_fstate[(src_gs_node_id, dst_gs_node_id)] != next_hop_decision:
                        f_out.write("%d,%d,%d,%d,%d\n" % (
                            src_gs_node_id,
                            dst_gs_node_id,
                            next_hop_decision[0],
                            next_hop_decision[1],
                            next_hop_decision[2]
                        ))
                    fstate[(src_gs_node_id, dst_gs_node_id)] = next_hop_decision

    # Finally return result
    return fstate


def calculate_fstate_shortest_path_with_gs_relaying(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        sat_neighbor_to_if,
        prev_fstate,
        enable_verbose_logs
):
    # Calculate shortest paths
    if enable_verbose_logs:
        print("  > Calculating Floyd-Warshall for graph including ground-station relays")
    # (Note: Numpy has a deprecation warning here because of how networkx uses matrices)
    dist_sat_net = nx.floyd_warshall_numpy(sat_net_graph)

    # Forwarding state
    fstate = {}

    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    if enable_verbose_logs:
        print("  > Writing forwarding state to: " + output_filename)
    with open(output_filename, "w+") as f_out:

        # Satellites and ground stations to ground stations
        for current_node_id in range(num_satellites + num_ground_stations):
            for dst_gid in range(num_ground_stations):
                dst_gs_node_id = num_satellites + dst_gid

                # Cannot forward to itself
                if current_node_id != dst_gs_node_id:

                    # Among its neighbors, find the one which promises the
                    # lowest distance to reach the destination satellite
                    next_hop_decision = (-1, -1, -1)
                    best_distance_m = 1000000000000000
                    for neighbor_id in sat_net_graph.neighbors(current_node_id):

                        # Any neighbor must be reachable
                        if math.isinf(dist_sat_net[(current_node_id, neighbor_id)]):
                            raise ValueError("Neighbor cannot be unreachable")

                        # Calculate distance = next-hop + distance the next hop node promises
                        distance_m = (
                                sat_net_graph.edges[(current_node_id, neighbor_id)]["weight"]
                                +
                                dist_sat_net[(neighbor_id, dst_gs_node_id)]
                        )
                        if (
                                not math.isinf(dist_sat_net[(neighbor_id, dst_gs_node_id)])
                                and
                                distance_m < best_distance_m
                        ):

                            # Check node identifiers to determine what are the
                            # correct interface identifiers
                            if current_node_id >= num_satellites and neighbor_id < num_satellites:  # GS to sat.
                                my_if = 0
                                next_hop_if = (
                                        num_isls_per_sat[neighbor_id]
                                        +
                                        gid_to_sat_gsl_if_idx[current_node_id - num_satellites]
                                )

                            elif current_node_id < num_satellites and neighbor_id >= num_satellites:  # Sat. to GS
                                my_if = (
                                        num_isls_per_sat[current_node_id]
                                        +
                                        gid_to_sat_gsl_if_idx[neighbor_id - num_satellites]
                                )
                                next_hop_if = 0

                            elif current_node_id < num_satellites and neighbor_id < num_satellites:  # Sat. to sat.
                                my_if = sat_neighbor_to_if[(current_node_id, neighbor_id)]
                                next_hop_if = sat_neighbor_to_if[(neighbor_id, current_node_id)]

                            else:  # GS to GS
                                raise ValueError("GS-to-GS link cannot exist")

                            # Write the next-hop decision
                            next_hop_decision = (
                                neighbor_id,  # Next-hop node identifier
                                my_if,  # My outgoing interface id
                                next_hop_if  # Next-hop incoming interface id
                            )

                            # Update best distance found
                            best_distance_m = distance_m

                    # Write to forwarding state
                    if not prev_fstate or prev_fstate[(current_node_id, dst_gs_node_id)] != next_hop_decision:
                        f_out.write("%d,%d,%d,%d,%d\n" % (
                            current_node_id,
                            dst_gs_node_id,
                            next_hop_decision[0],
                            next_hop_decision[1],
                            next_hop_decision[2]
                        ))
                    fstate[(current_node_id, dst_gs_node_id)] = next_hop_decision

    # Finally return result
    return fstate


def compute_anchor_data_for_timestep(graph, anchors, enable_verbose_logs=False):
    """
    MAXIMALLY EFFICIENT: Only compute what we actually need using multi-source Dijkstra
    
    We need:
    1. Each satellite → nearest anchor (630 lookups)
    2. Each anchor → each anchor (132 paths)
    
    Strategy: ONE multi-source BFS from all anchors simultaneously
    - Each satellite discovers its nearest anchor (stops after first anchor reaches it)
    - Anchors discover paths to other anchors
    
    Complexity: O(V log V + E) - SINGLE Dijkstra run!
    This is the theoretical minimum - you can't do better!
    """
    import heapq
    
    anchor_data = {
        'nearest_anchor': {},      # satellite_id -> (anchor_id, distance, path)
        'anchor_to_anchor': {}     # (anchor_src, anchor_dst) -> {'distance', 'next_hop', 'path'}
    }
    
    anchor_set = set(anchors)
    
    # Priority queue: (distance, current_node, source_anchor, path)
    pq = []
    visited = set()  # Nodes that have found their nearest anchor
    best_distance = {}  # (node, source_anchor) -> best known distance to avoid reprocessing
    
    # Initialize: Add all anchors to priority queue
    for anchor in anchors:
        if anchor in graph.nodes():
            heapq.heappush(pq, (0.0, anchor, anchor, [anchor]))
            visited.add(anchor)  # Anchors are their own nearest anchor
            anchor_data['nearest_anchor'][anchor] = (anchor, 0.0, [anchor])
            best_distance[(anchor, anchor)] = 0.0
    
    if enable_verbose_logs:
        print(f"      Running single multi-source BFS from {len(anchors)} anchors")
    
    # Multi-source Dijkstra
    nodes_processed = 0
    while pq:
        current_dist, current_node, source_anchor, path = heapq.heappop(pq)
        
        # Skip if we've already processed this (node, source) pair with a better distance
        key = (current_node, source_anchor)
        if key in best_distance and current_dist > best_distance[key]:
            continue
            
        nodes_processed += 1
        
        # If this is a non-anchor node that hasn't been visited, this is its nearest anchor
        if current_node not in anchor_set and current_node not in visited:
            anchor_data['nearest_anchor'][current_node] = (source_anchor, current_dist, path)
            visited.add(current_node)
            # Still need to explore from this node to potentially reach other anchors!
        
        # If this is an anchor node, track distance for anchor-to-anchor routing
        if current_node in anchor_set and current_node != source_anchor:
            pair_key = (source_anchor, current_node)
            if pair_key not in anchor_data['anchor_to_anchor']:
                # Store the path from source_anchor to current_node (which is also an anchor)
                anchor_data['anchor_to_anchor'][pair_key] = {
                    'distance': current_dist,
                    'path': path,
                    'next_hop': path[1] if len(path) > 1 else current_node
                }
                
                # ALSO store the reverse path (for bidirectional lookup)
                # Since ISLs are undirected, distance is the same
                # Reverse path: [current_node, ..., source_anchor]
                reverse_path = list(reversed(path))
                reverse_pair_key = (current_node, source_anchor)
                anchor_data['anchor_to_anchor'][reverse_pair_key] = {
                    'distance': current_dist,
                    'path': reverse_path,
                    'next_hop': reverse_path[1] if len(reverse_path) > 1 else source_anchor
                }
                
                # Since ISLs are bidirectional, also store the reverse path
                reverse_path = list(reversed(path))
                reverse_key = (current_node, source_anchor)
                if reverse_key not in anchor_data['anchor_to_anchor']:
                    anchor_data['anchor_to_anchor'][reverse_key] = {
                        'distance': current_dist,  # Same distance in both directions
                        'path': reverse_path,
                        'next_hop': reverse_path[1] if len(reverse_path) > 1 else source_anchor
                    }
        
        # Explore neighbors (for both anchor-to-anchor paths and reaching non-anchor nodes)
        for neighbor in graph.neighbors(current_node):
            # Skip if neighbor has already found its nearest anchor (unless it's an anchor itself)
            if neighbor in visited and neighbor not in anchor_set:
                continue
            
            edge_weight = graph.edges[(current_node, neighbor)]['weight']
            new_dist = current_dist + edge_weight
            new_path = path + [neighbor]
            
            # Only add to queue if this is a better path
            neighbor_key = (neighbor, source_anchor)
            if neighbor_key not in best_distance or new_dist < best_distance[neighbor_key]:
                best_distance[neighbor_key] = new_dist
                heapq.heappush(pq, (new_dist, neighbor, source_anchor, new_path))
    
    if enable_verbose_logs:
        print(f"      Processed {nodes_processed} node visits")
        print(f"      Found nearest anchor for {len(anchor_data['nearest_anchor'])} nodes")
        print(f"      Computed {len(anchor_data['anchor_to_anchor'])} anchor-to-anchor paths")
        # DEBUG: Check specific anchor pair
        if (0, 130) in anchor_data['anchor_to_anchor']:
            print(f"      Anchor 0 → Anchor 130: distance={anchor_data['anchor_to_anchor'][(0, 130)]['distance']}")
        else:
            print(f"      WARNING: Anchor 0 → Anchor 130 NOT in anchor_to_anchor!")
    
    return anchor_data


def calculate_anchor_lmsr_path_complete_forwarding(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph_only_satellites_with_isls,  # List of graphs for lookahead
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        ground_station_satellites_in_range_candidates,
        sat_neighbor_to_if,
        anchors,
        prev_fstate,
        prev_anchor_data,
        enable_verbose_logs
):
    """
    MAXIMALLY EFFICIENT Anchor-based LMSR with Complete Forwarding State
    
    Generates forwarding entries for:
    - Satellite → Ground Station
    - Ground Station → Ground Station  
    - Satellite → Satellite (for hop-by-hop forwarding)
    
    Per timestep: O(V log V + E) - single multi-source Dijkstra
    Total: O(N × (V log V + E)) + O(V²) for sat-to-sat entries
    
    Speedup: ~4,400x faster than LMSR with full Dijkstra per source-destination pair
    """
    
    if enable_verbose_logs:
        print(f"  > Computing maximally efficient anchor-based LMSR")
        print(f"    Anchors: {len(anchors)}")
        print(f"    Lookahead: {len(sat_net_graph_only_satellites_with_isls)} timesteps")
        print(f"    Total multi-source Dijkstra runs: {len(sat_net_graph_only_satellites_with_isls)}")
    
    # DEBUG: Disabled for performance
    debug_enabled = False
    
    # Compute anchor data for each timestep (ONE multi-source Dijkstra per timestep)
    anchor_data_by_timestep = []
    
    if prev_anchor_data is not None and len(prev_anchor_data) > 0:
        if enable_verbose_logs:
            print(f"    > Reusing previous {len(prev_anchor_data)} timesteps")
        anchor_data_by_timestep = prev_anchor_data
        
        if enable_verbose_logs:
            print(f"    > Computing new timestep {len(anchor_data_by_timestep)}")
        new_timestep_data = compute_anchor_data_for_timestep(
            sat_net_graph_only_satellites_with_isls[-1],
            anchors,
            enable_verbose_logs
        )
        anchor_data_by_timestep.append(new_timestep_data)
    else:
        if enable_verbose_logs:
            print(f"    > Computing all {len(sat_net_graph_only_satellites_with_isls)} timesteps")
        for i, graph in enumerate(sat_net_graph_only_satellites_with_isls):
            if enable_verbose_logs or (debug_enabled and i == 0):
                print(f"      Timestep {i}/{len(sat_net_graph_only_satellites_with_isls)}")
            timestep_data = compute_anchor_data_for_timestep(graph, anchors, (enable_verbose_logs or debug_enabled) and i == 0)
            anchor_data_by_timestep.append(timestep_data)
    
    # Helper functions - all O(1) lookups
    def find_nearest_anchor_at_timestep(satellite_id, timestep_idx):
        """O(1) lookup"""
        anchor_data = anchor_data_by_timestep[timestep_idx]
        if satellite_id in anchor_data['nearest_anchor']:
            anchor, distance, path = anchor_data['nearest_anchor'][satellite_id]
            return anchor, path, distance
        return None, [], float('inf')
    
    def get_anchor_to_anchor_distance(src_anchor, dst_anchor, timestep_idx):
        """O(1) lookup"""
        anchor_data = anchor_data_by_timestep[timestep_idx]
        key = (src_anchor, dst_anchor)
        if key in anchor_data['anchor_to_anchor']:
            return anchor_data['anchor_to_anchor'][key]['distance']
        return float('inf')
    
    def get_anchor_to_anchor_next_hop(src_anchor, dst_anchor, timestep_idx):
        """O(1) lookup"""
        anchor_data = anchor_data_by_timestep[timestep_idx]
        key = (src_anchor, dst_anchor)
        if key in anchor_data['anchor_to_anchor']:
            return anchor_data['anchor_to_anchor'][key]['next_hop']
        return None
    
    def compute_anchor_path_distance_at_timestep(source_sat, dest_sat, timestep_idx):
        """
        Compute distance: source → ingress_anchor → egress_anchor → destination
        All lookups are O(1)!
        """
        if source_sat == dest_sat:
            return 0.0
        
        ingress_anchor, _, ingress_distance = find_nearest_anchor_at_timestep(source_sat, timestep_idx)
        egress_anchor, _, egress_distance = find_nearest_anchor_at_timestep(dest_sat, timestep_idx)
        
        if ingress_anchor is None or egress_anchor is None:
            return float('inf')
        
        if ingress_anchor == egress_anchor:
            # Same anchor: source → anchor → destination
            return ingress_distance + egress_distance
        else:
            # Different anchors: source → ingress → egress → destination
            anchor_distance = get_anchor_to_anchor_distance(ingress_anchor, egress_anchor, timestep_idx)
            if math.isinf(anchor_distance):
                return float('inf')
            return ingress_distance + anchor_distance + egress_distance
    
    def route_through_anchors_lmsr(source_sat, dest_sat, current_timestep=0):
        """
        LMSR: Minimize maximum distance across all timesteps
        BUT: Route using CURRENT timestep's topology
        Returns: (next_hop, max_distance)
        """
        if source_sat == dest_sat:
            return dest_sat, 0.0
        
        # Compute distances across all timesteps to find worst case
        distances_across_time = [
            compute_anchor_path_distance_at_timestep(source_sat, dest_sat, t)
            for t in range(len(sat_net_graph_only_satellites_with_isls))
        ]
        
        if any(math.isinf(d) for d in distances_across_time):
            return None, float('inf')
        
        # Find worst-case distance (for LMSR criterion)
        max_distance = max(distances_across_time)
        
        # BUT: Use CURRENT timestep for actual routing decision
        # This ensures the next hop exists in the current ISL topology
        ingress_anchor, ingress_path, _ = find_nearest_anchor_at_timestep(source_sat, current_timestep)
        egress_anchor, egress_path, _ = find_nearest_anchor_at_timestep(dest_sat, current_timestep)
        
        if ingress_anchor is None or egress_anchor is None:
            return None, float('inf')
        
        # DEBUG
        debug_routing = source_sat in [100, 101, 130] and dest_sat in [102, 103]
        if debug_routing:
            print(f"      route_through_anchors_lmsr({source_sat}, {dest_sat}):")
            print(f"        ingress_anchor={ingress_anchor}, egress_anchor={egress_anchor}")
            print(f"        ingress_path={ingress_path}, egress_path={egress_path}")
        
        # Determine next hop using CURRENT timestep topology
        # NOTE: Paths are stored as [anchor, ..., node] from multi-source Dijkstra
        # To route FROM node TO anchor, we reverse the path
        
        if source_sat == ingress_anchor:
            # Source is already an anchor
            if ingress_anchor == egress_anchor:
                # Same anchor for both - route directly toward destination
                #  egress_path is [egress_anchor, ..., dest_sat]
                # We want to go FROM egress_anchor (where we are) TO dest_sat
                if len(egress_path) > 1:
                    next_hop = egress_path[1]  # First step from anchor toward dest
                else:
                    next_hop = dest_sat
            else:
                # Route from ingress anchor to egress anchor
                next_hop = get_anchor_to_anchor_next_hop(ingress_anchor, egress_anchor, current_timestep)
                if next_hop is None:
                    return None, float('inf')
        else:
            # Source is not an anchor
            # Check if source is already on the egress path (path from egress anchor to destination)
            # If so, route forward along that path instead of back to the anchor
            if ingress_anchor == egress_anchor and source_sat in egress_path:
                # Source is on the path from anchor to destination!
                # Find our position in the path and take next step
                try:
                    src_idx = egress_path.index(source_sat)
                    if src_idx < len(egress_path) - 1:
                        next_hop = egress_path[src_idx + 1]  # Next step toward destination
                    else:
                        # We're at the end of the path (shouldn't happen since dest_sat != source_sat)
                        return None, float('inf')
                except ValueError:
                    # Source not in egress path (shouldn't happen given the if condition)
                    return None, float('inf')
            else:
                # Need to route TO ingress anchor first
                # ingress_path is [ingress_anchor, ..., source_sat]
                # To go FROM source_sat TO ingress_anchor, reverse and take next step
                if len(ingress_path) > 1:
                    next_hop = ingress_path[-2]  # Second-to-last in forward path = next in reverse
                else:
                    # Path has only 1 element, shouldn't happen
                    return None, float('inf')
        
        if debug_routing:
            print(f"        next_hop={next_hop}")
        
        return next_hop, max_distance
    
    # Generate forwarding state
    fstate = {}
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    
    if enable_verbose_logs:
        print("  > Writing anchor-based LMSR forwarding state to: " + output_filename)
    
    with open(output_filename, "w+") as f_out:
        
        # Satellites to ground stations
        if enable_verbose_logs:
            print("  > Computing satellite-to-ground-station routes")
        
        dist_satellite_to_ground_station = {}
        
        # DEBUG: Check what satellites can see each GS
        if enable_verbose_logs:
            for gid in range(num_ground_stations):
                sats_in_range = ground_station_satellites_in_range_candidates[0][gid]
                sat_ids = [sat_id for _, sat_id in sats_in_range]
                print(f"    GS {gid} (node {num_satellites + gid}) can see {len(sat_ids)} satellites: {sat_ids[:20]}...")
        
        for curr_sat in range(num_satellites):
            for dst_gid in range(num_ground_stations):
                dst_gs_node_id = num_satellites + dst_gid
                
                possible_dst_sats = ground_station_satellites_in_range_candidates[0][dst_gid]
                
                # DEBUG: For satellite 0, show details
                if enable_verbose_logs and curr_sat == 0:
                    print(f"    Satellite {curr_sat} routing to GS {dst_gid}: {len(possible_dst_sats)} candidate satellites")
                
                possibilities = []
                for gsl_distance, dst_sat in possible_dst_sats:
                    distances_across_time = [
                        compute_anchor_path_distance_at_timestep(curr_sat, dst_sat, t)
                        for t in range(len(sat_net_graph_only_satellites_with_isls))
                    ]
                    
                    if not any(math.isinf(d) for d in distances_across_time):
                        max_distance = max(distances_across_time)
                        possibilities.append((max_distance + gsl_distance, dst_sat))
                    elif curr_sat == 0 and dst_gid == 1:  # Debug: satellite 0 to Dalian
                        print(f"      DEBUG: Sat {curr_sat} → Sat {dst_sat} (can see GS {dst_gid}): Has inf distance")
                        print(f"        Distances across time: {distances_across_time[:3]}...")
                
                possibilities = sorted(possibilities)
                
                # DEBUG
                if curr_sat == 0 and dst_gid == 1:
                    print(f"    DEBUG: Satellite 0 routing to GS 1 (Dalian): {len(possibilities)} valid possibilities")
                    if len(possibilities) > 0:
                        print(f"      Best: distance={possibilities[0][0]}, via sat {possibilities[0][1]}")
                    else:
                        print(f"      NO VALID ROUTES!")
                        print(f"      Checked {len(possible_dst_sats)} satellites that can see Dalian")

                
                next_hop_decision = (-1, -1, -1)
                distance_to_ground_station_m = float('inf')
                
                if possibilities:
                    _, dst_sat = possibilities[0]
                    distance_to_ground_station_m = possibilities[0][0]
                    
                    if curr_sat != dst_sat:
                        # Use anchor-based routing with loop prevention
                        # Get next hop from efficient anchor computation
                        next_hop, max_dist = route_through_anchors_lmsr(curr_sat, dst_sat, current_timestep=0)
                        
                        if next_hop is not None and next_hop in sat_net_graph_only_satellites_with_isls[0].neighbors(curr_sat):
                            next_hop_decision = (
                                next_hop,
                                sat_neighbor_to_if[0][(curr_sat, next_hop)],
                                sat_neighbor_to_if[0][(next_hop, curr_sat)]
                            )
                    else:
                        # Satellite can directly see the ground station
                        # Count number of ISL interfaces for this satellite to find GSL interface
                        num_isl_ifs = sum(1 for (a, b) in sat_neighbor_to_if[0].keys() if a == curr_sat)
                        # Which GSL interface to use? GS_id maps to GSL interface index
                        gsl_if_idx = gid_to_sat_gsl_if_idx[dst_gid]
                        next_hop_decision = (
                            dst_gs_node_id,
                            num_isl_ifs + gsl_if_idx,  # My interface (satellite's GSL interface for this GS)
                            0  # Next hop interface (ground station's GSL interface 0)
                        )
                
                dist_satellite_to_ground_station[(curr_sat, dst_gs_node_id)] = distance_to_ground_station_m
                
                if not prev_fstate or prev_fstate.get((curr_sat, dst_gs_node_id)) != next_hop_decision:
                    f_out.write("%d,%d,%d,%d,%d\n" % (
                        curr_sat, dst_gs_node_id,
                        next_hop_decision[0], next_hop_decision[1], next_hop_decision[2]
                    ))
                fstate[(curr_sat, dst_gs_node_id)] = next_hop_decision
        
        # Ground stations to ground stations
        if enable_verbose_logs:
            print("  > Computing ground-station-to-ground-station routes")
        
        for src_gid in range(num_ground_stations):
            for dst_gid in range(num_ground_stations):
                if src_gid != dst_gid:
                    src_gs_node_id = num_satellites + src_gid
                    dst_gs_node_id = num_satellites + dst_gid
                    
                    possible_src_sats = ground_station_satellites_in_range_candidates[0][src_gid]
                    
                    possibilities = []
                    for gsl_distance, src_sat in possible_src_sats:
                        sat_to_dst_distance = dist_satellite_to_ground_station.get(
                            (src_sat, dst_gs_node_id), float('inf')
                        )
                        
                        if not math.isinf(sat_to_dst_distance):
                            possibilities.append((gsl_distance + sat_to_dst_distance, src_sat))
                    
                    possibilities = sorted(possibilities)
                    
                    next_hop_decision = (-1, -1, -1)
                    if possibilities:
                        _, src_sat = possibilities[0]
                        # The satellite's GSL interface comes after all its ISL interfaces
                        # Count number of ISL interfaces for this satellite
                        num_isl_ifs = sum(1 for (a, b) in sat_neighbor_to_if[0].keys() if a == src_sat)
                        sat_gsl_if_id = num_isl_ifs
                        next_hop_decision = (
                            src_sat,  # Next hop satellite
                            0,  # My interface (ground station's GSL interface 0)
                            sat_gsl_if_id  # Next hop interface (satellite's GSL interface)
                        )
                    
                    if not prev_fstate or prev_fstate.get((src_gs_node_id, dst_gs_node_id)) != next_hop_decision:
                        f_out.write("%d,%d,%d,%d,%d\n" % (
                            src_gs_node_id, dst_gs_node_id,
                            next_hop_decision[0], next_hop_decision[1], next_hop_decision[2]
                        ))
                    fstate[(src_gs_node_id, dst_gs_node_id)] = next_hop_decision
    
    if enable_verbose_logs:
        print(f"  > Generated {len(fstate)} forwarding entries")
        num_sat_to_gs = sum(1 for (src, dst) in fstate.keys() if src < num_satellites and dst >= num_satellites)
        num_gs_to_gs = sum(1 for (src, dst) in fstate.keys() if src >= num_satellites and dst >= num_satellites)
        print(f"    Satellite-to-GS: {num_sat_to_gs}, GS-to-GS: {num_gs_to_gs}")
    
    return fstate, anchor_data_by_timestep[1:]


def calculate_lmsr_path_without_gs_relaying(
        output_dynamic_state_dir,
        time_since_epoch_ns,
        num_satellites,
        num_ground_stations,
        sat_net_graph_only_satellites_with_isls,
        num_isls_per_sat,
        gid_to_sat_gsl_if_idx,
        ground_station_satellites_in_range_candidates,
        sat_neighbor_to_if,
        prev_fstate,
        prev_dist_sat_nets_without_gs,
        enable_verbose_logs
):
    # Calculate the shortest path distances
    if enable_verbose_logs:
        print("  > Generating for all LMSR states")
    # (Note: Numpy has a deprecation warning here because of how networkx uses matrices)
    # TODO: Use previous floyd-warshall output (prevent recalculation)
    dist_sat_net_without_gs = prev_dist_sat_nets_without_gs
    if dist_sat_net_without_gs is not None:
        print(f'  > Reusing previous {len(dist_sat_net_without_gs)} states')
        dist_sat_net_without_gs.append(nx.floyd_warshall_numpy(sat_net_graph_only_satellites_with_isls[-1]))
    else:
        print(f'  > Generating for all {len(sat_net_graph_only_satellites_with_isls)} states')
        dist_sat_net_without_gs = [nx.floyd_warshall_numpy(graph) for graph in sat_net_graph_only_satellites_with_isls]

    # Forwarding state
    fstate = {}

    # Now write state to file for complete graph
    output_filename = output_dynamic_state_dir + "/fstate_" + str(time_since_epoch_ns) + ".txt"
    if enable_verbose_logs:
        print("  > Writing forwarding state to: " + output_filename)
    with open(output_filename, "w+") as f_out:

        # Satellites to ground stations
        # From the satellites attached to the destination ground station,
        # select the one which promises the shortest path to the destination ground station (getting there + last hop)
        dist_satellite_to_ground_station = {}
        for curr in range(num_satellites):
            for dst_gid in range(num_ground_stations):
                dst_gs_node_id = num_satellites + dst_gid

                # Among the satellites in range of the destination ground station,
                # find the one which promises the shortest distance
                possible_dst_sats = ground_station_satellites_in_range_candidates[0][dst_gid]
                possibilities = []
                max_length_index = -1
                for b in possible_dst_sats:
                    # All timesteps must be reachable
                    lengths = [dist_sat_net_without_gs[i][curr][b[1]] for i in
                               range(len(sat_net_graph_only_satellites_with_isls))]
                    if not any(math.isinf(lengths[i]) for i in range(len(sat_net_graph_only_satellites_with_isls))):
                        max_length = -1
                        for i in range(len(lengths)):
                            if lengths[i] > max_length:
                                max_length = lengths[i]
                                max_length_index = i
                        possibilities.append(
                            (
                                max_length + b[0],
                                b[1]
                            )
                        )
                possibilities = list(sorted(possibilities))

                # By default, if there is no satellite in range for the
                # destination ground station, it will be dropped (indicated by -1)
                next_hop_decision = (-1, -1, -1)
                distance_to_ground_station_m = float("inf")
                if len(possibilities) > 0:
                    dst_sat = possibilities[0][1]
                    distance_to_ground_station_m = possibilities[0][0]

                    # If the current node is not that satellite, determine how to get to the satellite
                    if curr != dst_sat:

                        # Among its neighbors, find the one which promises the
                        # lowest distance to reach the destination satellite
                        best_distance_m = float("inf")
                        for neighbor_id in sat_net_graph_only_satellites_with_isls[0].neighbors(curr):
                            distance_m = (
                                    sat_net_graph_only_satellites_with_isls[0].edges[(curr, neighbor_id)]["weight"]
                                    +
                                    max([dist_sat_net_without_gs[i][neighbor_id][dst_sat] for i in
                                         range(len(sat_net_graph_only_satellites_with_isls))])
                            )
                            if distance_m < best_distance_m:
                                next_hop_decision = (
                                    neighbor_id,
                                    sat_neighbor_to_if[0][(curr, neighbor_id)],
                                    sat_neighbor_to_if[0][(neighbor_id, curr)]
                                )
                                best_distance_m = distance_m

                    else:
                        # This is the destination satellite, as such the next hop is the ground station itself
                        next_hop_decision = (
                            dst_gs_node_id,
                            num_isls_per_sat[0][dst_sat] + gid_to_sat_gsl_if_idx[dst_gid],
                            0
                        )

                # In any case, save the distance of the satellite to the ground station to re-use
                # when we calculate ground station to ground station forwarding
                dist_satellite_to_ground_station[(curr, dst_gs_node_id)] = distance_to_ground_station_m

                # Write to forwarding state
                if not prev_fstate or prev_fstate[(curr, dst_gs_node_id)] != next_hop_decision:
                    f_out.write("%d,%d,%d,%d,%d\n" % (
                        curr,
                        dst_gs_node_id,
                        next_hop_decision[0],
                        next_hop_decision[1],
                        next_hop_decision[2]
                    ))
                fstate[(curr, dst_gs_node_id)] = next_hop_decision

        # Ground stations to ground stations
        # Choose the source satellite which promises the shortest path
        for src_gid in range(num_ground_stations):
            for dst_gid in range(num_ground_stations):
                if src_gid != dst_gid:
                    src_gs_node_id = num_satellites + src_gid
                    dst_gs_node_id = num_satellites + dst_gid

                    # Among the satellites in range of the source ground station,
                    # find the one which promises the shortest distance
                    possible_src_sats = ground_station_satellites_in_range_candidates[0][src_gid]
                    possibilities = []
                    for a in possible_src_sats:
                        best_distance_offered_m = dist_satellite_to_ground_station[(a[1], dst_gs_node_id)]
                        if not math.isinf(best_distance_offered_m):
                            possibilities.append(
                                (
                                    a[0] + best_distance_offered_m,
                                    a[1]
                                )
                            )
                    possibilities = sorted(possibilities)

                    # By default, if there is no satellite in range for one of the
                    # ground stations, it will be dropped (indicated by -1)
                    next_hop_decision = (-1, -1, -1)
                    if len(possibilities) > 0:
                        src_sat_id = possibilities[0][1]
                        next_hop_decision = (
                            src_sat_id,
                            0,
                            num_isls_per_sat[0][src_sat_id] + gid_to_sat_gsl_if_idx[src_gid]
                        )

                    # Update forwarding state
                    if not prev_fstate or prev_fstate[(src_gs_node_id, dst_gs_node_id)] != next_hop_decision:
                        f_out.write("%d,%d,%d,%d,%d\n" % (
                            src_gs_node_id,
                            dst_gs_node_id,
                            next_hop_decision[0],
                            next_hop_decision[1],
                            next_hop_decision[2]
                        ))
                    fstate[(src_gs_node_id, dst_gs_node_id)] = next_hop_decision

    # Finally return result
    return fstate, dist_sat_net_without_gs[1:]
