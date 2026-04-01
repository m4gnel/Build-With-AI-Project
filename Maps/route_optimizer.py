"""
route_optimizer.py — A* Shortest Path Algorithm
================================================
Finds the optimal delivery route between warehouses using A* search,
guided by a Haversine-distance heuristic toward the destination.

A* advantages over Dijkstra:
  - Heuristic guides search toward the goal, dramatically cutting explored nodes.
  - Guarantees the optimal path on admissible heuristics (Haversine never
    overestimates real road distance).
  - Risk-aware edge weights ensure disrupted corridors are avoided naturally.

All routes follow the pre-defined ground road graph — no oversea shortcuts.
"""

import heapq
import math
from collections import defaultdict


# ── Haversine distance (km) between two lat/lng points ───────────────────────
def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Returns great-circle distance in km.  Used ONLY as A* admissible heuristic
    (actual road distance ≥ haversine distance, so heuristic never over-estimates).
    """
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class RouteOptimizer:
    """Route optimization using A* algorithm with Haversine admissible heuristic."""

    def __init__(self):
        self.graph = defaultdict(list)   # adjacency list  { node_id: [edge_dict, …] }
        self.warehouses = {}             # { id: {name, city, lat, lng} }
        self.routes_data = []            # raw route records (kept for reference)

    # ── Graph Construction ────────────────────────────────────────────────────
    def build_graph(self, warehouses, routes):
        """
        Build the ground-route graph from warehouse and route data.

        Args:
            warehouses : list of dicts  — id, name, city, lat, lng
            routes     : list of dicts  — source_id, dest_id, distance_km,
                                          travel_time_hours, cost, risk_factor
        """
        self.graph.clear()
        self.warehouses.clear()
        self.routes_data = routes

        for wh in warehouses:
            self.warehouses[wh["id"]] = {
                "name": wh["name"],
                "city": wh["city"],
                "lat":  wh["lat"],
                "lng":  wh["lng"],
            }

        for route in routes:
            src = route["source_id"]
            dst = route["dest_id"]
            # g-score edge weight: combine distance + risk penalty
            g_weight = route["distance_km"] * (1.0 + route["risk_factor"])

            self.graph[src].append({
                "dest":               dst,
                "g_weight":           g_weight,
                "distance_km":        route["distance_km"],
                "travel_time_hours":  route["travel_time_hours"],
                "cost":               route["cost"],
                "risk_factor":        route["risk_factor"],
            })

    # ── A* Core ───────────────────────────────────────────────────────────────
    def _astar(self, source_id: int, dest_id: int, blocked: set):
        """
        Run A* from source_id to dest_id on the ground-route graph.

        Priority queue entry: (f_score, g_score, node_id)
        f = g + h   where h = haversine(current → destination)

        Returns:
            (previous, previous_edge) dicts for path reconstruction, or None if no path.
        """
        dest_wh  = self.warehouses[dest_id]
        dest_lat = dest_wh["lat"]
        dest_lng = dest_wh["lng"]

        # h(n) — admissible heuristic scaled by (1 + 0) = no risk on heuristic
        def h(node_id):
            wh = self.warehouses[node_id]
            return _haversine(wh["lat"], wh["lng"], dest_lat, dest_lng)

        g_score     = {n: float("inf") for n in self.warehouses}
        g_score[source_id] = 0.0

        previous      = {n: None for n in self.warehouses}
        previous_edge = {n: None for n in self.warehouses}
        closed        = set()

        # heap: (f_score, g_score, node_id)
        open_heap = [(h(source_id), 0.0, source_id)]

        while open_heap:
            f_cur, g_cur, cur = heapq.heappop(open_heap)

            if cur in closed:
                continue
            closed.add(cur)

            if cur == dest_id:
                return previous, previous_edge   # 🎯 goal reached

            for edge in self.graph.get(cur, []):
                nbr = edge["dest"]

                if nbr in closed:
                    continue
                if (cur, nbr) in blocked:
                    continue

                tentative_g = g_cur + edge["g_weight"]

                if tentative_g < g_score[nbr]:
                    g_score[nbr]     = tentative_g
                    previous[nbr]    = cur
                    previous_edge[nbr] = edge
                    f_new = tentative_g + h(nbr)
                    heapq.heappush(open_heap, (f_new, tentative_g, nbr))

        return None, None   # no path found

    # ── Path Result Builder ───────────────────────────────────────────────────
    def _build_result(self, source_id, dest_id, previous, previous_edge):
        """Reconstruct path arrays and compute aggregate metrics."""
        path         = []
        route_details = []
        cur = dest_id

        while cur is not None:
            path.append(cur)
            if previous_edge[cur] is not None:
                edge = previous_edge[cur]
                route_details.append({
                    "from":               self.warehouses[previous[cur]]["city"],
                    "from_id":            previous[cur],
                    "to":                 self.warehouses[cur]["city"],
                    "to_id":              cur,
                    "distance_km":        edge["distance_km"],
                    "travel_time_hours":  edge["travel_time_hours"],
                    "cost":               edge["cost"],
                    "risk_factor":        edge["risk_factor"],
                })
            cur = previous[cur]

        path.reverse()
        route_details.reverse()

        total_distance = sum(r["distance_km"]       for r in route_details)
        total_time     = sum(r["travel_time_hours"]  for r in route_details)
        total_cost     = sum(r["cost"]               for r in route_details)
        avg_risk       = (sum(r["risk_factor"] for r in route_details)
                          / max(len(route_details), 1))

        path_coordinates = [
            {
                "id":   nid,
                "name": self.warehouses[nid]["name"],
                "city": self.warehouses[nid]["city"],
                "lat":  self.warehouses[nid]["lat"],
                "lng":  self.warehouses[nid]["lng"],
            }
            for nid in path
        ]

        return {
            "path":               path,
            "path_names":         [self.warehouses[n]["city"] for n in path],
            "path_coordinates":   path_coordinates,
            "route_details":      route_details,
            "total_distance_km":  round(total_distance, 1),
            "total_time_hours":   round(total_time,     1),
            "total_cost":         round(total_cost,     2),
            "average_risk_factor": round(avg_risk,       4),
            "num_stops":          len(path) - 1,
            "algorithm":          "A* (Haversine heuristic)",
        }

    # ── Public API ────────────────────────────────────────────────────────────
    def find_shortest_path(self, source_id: int, dest_id: int, blocked_routes=None):
        """
        Find the optimal ground route using A*.

        Args:
            source_id      : starting warehouse ID
            dest_id        : destination warehouse ID
            blocked_routes : list of (src, dst) edge tuples to avoid

        Returns:
            dict — path, path_names, route_details, aggregate metrics, algorithm tag
        """
        if source_id not in self.warehouses:
            return {"error": f"Source warehouse {source_id} not found"}
        if dest_id not in self.warehouses:
            return {"error": f"Destination warehouse {dest_id} not found"}
        if source_id == dest_id:
            return {"error": "Source and destination are the same"}

        blocked = set()
        if blocked_routes:
            for s, d in blocked_routes:
                blocked.add((s, d))

        previous, previous_edge = self._astar(source_id, dest_id, blocked)

        if previous is None or previous_edge[dest_id] is None and dest_id != source_id:
            return {"error": "No ground route found between source and destination"}

        return self._build_result(source_id, dest_id, previous, previous_edge)

    def find_alternative_route(self, source_id: int, dest_id: int, original_path: list):
        """
        Find an alternative ground route by blocking all edges of the original path.
        Falls back to blocking only the highest-risk edge if no full alternative exists.
        """
        # Block every edge in the primary path
        full_block = [(original_path[i], original_path[i + 1])
                      for i in range(len(original_path) - 1)]

        result = self.find_shortest_path(source_id, dest_id, blocked_routes=full_block)

        if "error" in result and len(original_path) > 2:
            # Fallback: block only the single highest-risk edge
            max_risk, max_edge = -1, None
            for i in range(len(original_path) - 1):
                for edge in self.graph.get(original_path[i], []):
                    if edge["dest"] == original_path[i + 1]:
                        if edge["risk_factor"] > max_risk:
                            max_risk = edge["risk_factor"]
                            max_edge = (original_path[i], original_path[i + 1])
            if max_edge:
                result = self.find_shortest_path(source_id, dest_id,
                                                 blocked_routes=[max_edge])

        if "error" not in result:
            result["is_alternative"] = True

        return result

    def get_all_warehouses(self):
        """Return all warehouses with their coordinates."""
        return [{"id": wh_id, **wh_data}
                for wh_id, wh_data in self.warehouses.items()]

    def update_risk_factor(self, source_id: int, dest_id: int,
                           new_risk_factor: float) -> bool:
        """Dynamically update the risk factor for a specific ground edge."""
        for edge in self.graph.get(source_id, []):
            if edge["dest"] == dest_id:
                edge["risk_factor"] = new_risk_factor
                edge["g_weight"]    = edge["distance_km"] * (1.0 + new_risk_factor)
                return True
        return False
