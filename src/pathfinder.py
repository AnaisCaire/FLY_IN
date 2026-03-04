import heapq
from typing import List, Dict, Optional
from src.models import Manager, Zone, ZoneType
from src.exceptions import MapLogicError


class Pathfinder:
    def __init__(self, manager: Manager):
        self.manager = manager

    def _reconstruct_path(self, predecessors: Dict[str, Optional[str]],
                          goal_name: str) -> List[Zone]:
        path: List[Zone] = []
        current: Optional[str] = goal_name
        # Walk backward from goal to start
        while current is not None:
            path.append(self.manager.zone[current])
            current = predecessors[current]

        # Reverse it so it goes Start -> Goal
        return path[::-1]

    def _calculate_path_cost(self, path: List[Zone]) -> float:
        """ total cost of a path """
        if not path or len(path) < 2:
            return 0

        total_turns = 0
        # We skip the first element (start_hub) because you don't 'enter' it
        for zone in path[1:]:
            if zone.zone_type == ZoneType.RESTRICTED:
                total_turns += 2
            elif zone.zone_type == ZoneType.PRIORITY:
                total_turns += 0.9
            else:
                total_turns += 1

        return total_turns

    def find_shortest_turn_path(self, ignore_path: set = None) -> List[Zone]:
        """
        Uses Dijkstra to find the fastest path in terms of turns.
        """
        if ignore_path is None:
            ignore_path = set()

        start = self.manager.start_hub
        goal = self.manager.end_hub

        if not start or not goal:
            raise MapLogicError("start or end hub could not be acessed")

        # create a dic where each zone starts with infinity moves
        distances: Dict[str, float] = {name: float('inf') for name in self.manager.zone}
        distances[start.name] = 0  # this ensures the start is at 0

        # predecessors[zone_name] = so we remember where we passed
        predecessors: Dict[str, Optional[str]] = {name: None for name in self.manager.zone}

        # Priority Queue: (cost, zone_name)
        pq = [(0.0, start.name)]
        while pq:
            # here we find the cheapest hub of the graph
            curr_distance, curr_name = heapq.heappop(pq)
            # Print whenever we 'visit' a hub from the queue
            print(f"DEBUG: Visiting {curr_name} (Current turns: {curr_distance})")
            if curr_name == goal.name:
                break
            if curr_distance > distances[curr_name]:
                continue
            # Now lets look at the neihboors attention, this makes sure we see the connections as bidirectionnal
            for connection in self.manager.adjency_list.get(curr_name, []):
                path = tuple(sorted((connection.prev_zone.name, connection.next_zone.name)))
                if path in ignore_path:
                    continue
                if connection.prev_zone.name == curr_name:
                    neighbor = connection.next_zone
                else:
                    neighbor = connection.prev_zone

                # determine the costs for entering in neighbor
                if neighbor.zone_type == ZoneType.RESTRICTED:
                    move_cost = 2
                else:
                    move_cost = 1

                new_cost = curr_distance + move_cost

                # check if the new path is better:
                if new_cost < distances[neighbor.name]:
                    # Print when we find a better route than before
                    print(f"  -> Found better path to {neighbor.name}: {new_cost} turns (via {curr_name})")
                    distances[neighbor.name] = new_cost
                    predecessors[neighbor.name] = curr_name
                    heapq.heappush(pq, (new_cost, neighbor.name))

        if distances[goal.name] == float('inf'):
            return []
        return self._reconstruct_path(predecessors, goal.name)

    def find_k_shortest_paths(self, k: int) -> List[List[Zone]]:
        # 1. Find the absolute best path
        best_path = self.find_shortest_turn_path()
        if not best_path:
            return []

        all_paths = [best_path]
        potential_paths: List[List[Zone]] = []  # This is our "Sideboard" of alternatives
        actual_start_hub = self.manager.start_hub

        for i in range(1, k):

            previous_path = all_paths[-1]  # this is the most recent best path we found

            for j in range(len(previous_path) - 1):  # -1 because we cant detour at goal
                new_node = previous_path[j]  # if j is one, the new node is the second
                root_path = previous_path[:j + 1]  # the root path is then the first 2 nodes

                # Temporary list of edges to ignore to force a new route
                ignored = set()
                for path in all_paths:
                    if len(path) > j and path[:j + 1] == root_path:
                        edge = tuple(sorted((path[j].name, path[j+1].name)))
                        ignored.add(edge)
                try:
                    self.manager.start_hub = new_node
                    new_path = self.find_shortest_turn_path(ignore_path=ignored)
                    self.manager.start_hub = actual_start_hub

                    if new_path:
                        total_new_path = root_path + new_path[1:]
                        if len(total_new_path) > 1 and total_new_path[-1] == self.manager.end_hub:
                            if total_new_path not in all_paths and total_new_path not in potential_paths:
                                potential_paths.append(total_new_path)
                except MapLogicError:
                    self.manager.start_hub = actual_start_hub
                    continue

            if not potential_paths:
                break

            potential_paths.sort(key=lambda p: self._calculate_path_cost(p))
            all_paths.append(potential_paths.pop(0))

        return all_paths
