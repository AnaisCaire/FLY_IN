"""Pathfinding logic: Dijkstra for single shortest path, Yen's for k-shortest.

No external graph libraries (subject Chapter V).
"""

import heapq
from typing import Dict, List, Optional, Set, Tuple

from src.models import Manager, Zone, ZoneType
from src.exceptions import MapLogicError


class Pathfinder:
    """Finds optimal drone paths through the zone graph.

    Args:
        manager: Populated Manager instance from the parser.
    """

    def __init__(self, manager: Manager) -> None:
        self.manager = manager

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _reconstruct_path(
        self,
        predecessors: Dict[str, Optional[str]],
        goal_name: str,
    ) -> List[Zone]:
        """Walk the predecessor map backwards to build start→goal path.

        Args:
            predecessors: Map of zone_name → zone_name it was reached from.
            goal_name: Name of the destination zone.

        Returns:
            Ordered list of Zone objects from start to goal.
        """
        path: List[Zone] = []
        current: Optional[str] = goal_name
        while current is not None:
            path.append(self.manager.zone[current])
            current = predecessors[current]
        return path[::-1]

    def _path_cost(self, path: List[Zone]) -> int:
        """Sum the movement costs for every zone entered on a path.

        Skips index 0 (start hub) because you never 'enter' it.

        Args:
            path: Ordered list of Zone objects.

        Returns:
            Total turn cost as an integer.
        """
        if len(path) < 2:
            return 0
        return sum(zone.movement_cost for zone in path[1:])

    def _make_edge_key(self, a: str, b: str) -> Tuple[str, str]:
        """Return a canonical (sorted) edge key for a pair of zone names.

        Args:
            a: First zone name.
            b: Second zone name.

        Returns:
            Tuple with the lexicographically smaller name first.
        """
        return (min(a, b), max(a, b))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_shortest_turn_path(
        self,
        ignore_edges: Optional[Set[Tuple[str, str]]] = None,
        start_override: Optional[Zone] = None,
    ) -> List[Zone]:
        """Dijkstra: find the path with the fewest simulation turns.

        Respects zone movement costs (RESTRICTED=2, others=1).
        Skips BLOCKED zones entirely.

        Args:
            ignore_edges: Set of canonical edge keys to treat as removed.
                          Used by Yen's algorithm to force alternate routes.
            start_override: Treat this zone as the start instead of
                            manager.start_hub. Used by Yen's algorithm.
                            Does NOT mutate the manager.

        Returns:
            Ordered list of Zone objects start→goal, or [] if unreachable.

        Raises:
            MapLogicError: If start or end hub is not set on the manager.
        """
        if ignore_edges is None:
            ignore_edges = set()

        # FIX 3: start_override avoids mutating manager.start_hub entirely
        start = start_override if start_override is not None else self.manager.start_hub
        goal = self.manager.end_hub

        if start is None or goal is None:
            raise MapLogicError("start_hub or end_hub is not set on the manager.")

        distances: Dict[str, float] = {
            name: float('inf') for name in self.manager.zone
        }
        distances[start.name] = 0.0

        predecessors: Dict[str, Optional[str]] = {
            name: None for name in self.manager.zone
        }

        # (cost, zone_name) — heapq is a min-heap by first element
        pq: List[Tuple[float, str]] = [(0.0, start.name)]

        while pq:
            curr_dist, curr_name = heapq.heappop(pq)

            if curr_name == goal.name:
                break

            # Skip stale entries (a cheaper path was already found)
            if curr_dist > distances[curr_name]:
                continue

            # FIX 1: use adjacency_list (new name) not adjency_list
            for conn in self.manager.adjacency_list.get(curr_name, []):
                edge = self._make_edge_key(
                    conn.prev_zone.name, conn.next_zone.name
                )
                if edge in ignore_edges:
                    continue

                neighbor = (
                    conn.next_zone
                    if conn.prev_zone.name == curr_name
                    else conn.prev_zone
                )

                # FIX 2: skip BLOCKED zones using movement_cost property
                if neighbor.zone_type == ZoneType.BLOCKED:
                    continue

                # FIX 2: use zone.movement_cost — single source of truth
                new_cost = curr_dist + neighbor.movement_cost

                if new_cost < distances[neighbor.name]:
                    distances[neighbor.name] = new_cost
                    predecessors[neighbor.name] = curr_name
                    heapq.heappush(pq, (new_cost, neighbor.name))

        if distances[goal.name] == float('inf'):
            return []
        return self._reconstruct_path(predecessors, goal.name)

    def find_k_shortest_paths(self, k: int) -> List[List[Zone]]:
        """Yen's algorithm: find the k lowest-cost paths start→goal.

        Args:
            k: Maximum number of paths to return.

        Returns:
            List of up to k paths, each an ordered list of Zone objects,
            sorted ascending by total turn cost. May return fewer than k
            if the graph has fewer distinct simple paths.
        """
        best = self.find_shortest_turn_path()
        if not best:
            return []

        confirmed: List[List[Zone]] = [best]
        candidates: List[List[Zone]] = []

        for _ in range(1, k):
            previous = confirmed[-1]

            for j in range(len(previous) - 1):
                spur_node = previous[j]
                root = previous[: j + 1]

                # Build the set of edges to block at this spur point
                blocked_edges: Set[Tuple[str, str]] = set()
                for p in confirmed:
                    if len(p) > j and p[: j + 1] == root:
                        blocked_edges.add(
                            self._make_edge_key(p[j].name, p[j + 1].name)
                        )

                # FIX 3: pass start_override — never touch manager.start_hub
                spur_path = self.find_shortest_turn_path(
                    ignore_edges=blocked_edges,
                    start_override=spur_node,
                )

                if not spur_path:
                    continue

                # root[:-1] avoids duplicating the spur_node
                full_path = root[:-1] + spur_path

                # Guard: reject paths that revisit zones (no cycles)
                zone_names = [z.name for z in full_path]
                if len(zone_names) != len(set(zone_names)):
                    continue

                if full_path not in confirmed and full_path not in candidates:
                    candidates.append(full_path)

            if not candidates:
                break

            # FIX 2: sort uses _path_cost which uses movement_cost
            candidates.sort(key=self._path_cost)
            confirmed.append(candidates.pop(0))

        return confirmed