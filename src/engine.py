from src.models import Manager, Zone, Drone, Connection, ZoneType
from src.pathfinder import Pathfinder
from src.exceptions import DijkstraPathError
from typing import List, Union, Dict, Tuple


class EngineSimulation:
    """The simulation engine: assigns paths, prepares and applies turns."""

    def __init__(self, manager: Manager) -> None:
        self.manager = manager
        self.drones = manager.drones
        self.turn = 0
        self.pathfinder = Pathfinder(manager)

    def _give_paths(self) -> None:
        """Assign each drone a path using latency-based distribution."""
        paths = self.pathfinder.find_k_shortest_paths(100)
        path_cost: List[int] = []
        for path in paths:
            path_cost.append(sum(zone.movement_cost for zone in path[1:]))
        path_occupancy = [0] * len(paths)
        for i, drone in enumerate(self.drones):
            best_idx = 0
            min_latency = float('inf')
            for j, cost in enumerate(path_cost):
                latency = cost + path_occupancy[j]
                if latency < min_latency:
                    min_latency = latency
                    best_idx = j
            drone.defined_path = paths[best_idx]
            drone.path_index = 0
            drone.arrival_turn = 0
            path_occupancy[best_idx] += 1

    def _net_occupancy(
        self,
        next_zone: Zone,
        planned: Dict[Drone, Union[Zone, Connection]],
    ) -> int:
        """Compute net occupancy of next_zone after this turn's moves.

        KEY FIX: drones moving to a Connection are also leaving their zone,
        so they no longer block the zone for incoming drones this turn.
        """
        current = sum(1 for d in self.drones if d.current_zone == next_zone)
        # Any drone that has a planned move is leaving its current zone
        leaving = sum(
            1 for d, move in planned.items()
            if d.current_zone == next_zone
        )
        entering = sum(
            1 for d, move in planned.items()
            if (move if isinstance(move, Zone)
                else move.next_zone) == next_zone
        )
        return current - leaving + entering

    def _prepare_turn(
        self,
    ) -> Dict[Drone, Union[Zone, Connection]]:
        """Decide each drone's move for this turn.

        Returns a dict mapping drone → intended move.
        A move is either a Zone (normal step) or a
        Connection (entering a 2-turn restricted transit).
        Drones not in this dict simply wait this turn.
        """
        # planned: commits made so far this turn.
        # Used by _net_occupancy to avoid double-booking.
        planned: Dict[Drone, Union[Zone, Connection]] = {}

        for drone in self.drones:

            # --- CATEGORY 1 ---
            # Drone already at end hub — skip entirely.
            if drone.current_zone == self.manager.end_hub:
                continue

            # --- CATEGORY 2 ---
            # Drone is in transit over a restricted zone.
            # arrival_turn > 0 means it MUST land this turn.
            elif drone.arrival_turn > 0:

                # The landing zone is always the next step
                # on the drone's pre-assigned path.
                next_zone = drone.defined_path[
                    drone.path_index + 1
                ]

                # Check if landing zone has room.
                has_cap = (
                    self._net_occupancy(next_zone, planned)
                    < next_zone.effective_capacity()
                )

                if has_cap:
                    # Zone has room — commit the landing.
                    planned[drone] = next_zone
                else:
                    # Zone is full — this should never happen
                    # because we validated before entering
                    # the restricted zone. Raise an error.
                    raise DijkstraPathError(
                        f"{drone.label} forced landing at "
                        f"'{next_zone.name}' blocked — "
                        f"zone full on turn {self.turn}"
                    )

            # --- CATEGORY 3 ---
            # Drone is free and has more steps on its path.
            elif drone.path_index < len(drone.defined_path) - 1:

                # The next zone on the pre-assigned path.
                next_zone = drone.defined_path[
                    drone.path_index + 1
                ]

                # Check if that zone has capacity this turn.
                has_cap = (
                    self._net_occupancy(next_zone, planned)
                    < next_zone.effective_capacity()
                )

                if has_cap:
                    # Zone has room — but is it restricted?
                    if next_zone.zone_type == ZoneType.RESTRICTED:
                        # Restricted zones need a 2-turn transit
                        # via a Connection object.
                        # Find the connection between current
                        # zone and next_zone.
                        for connect in self.manager.adjacency_list[
                            drone.current_zone.name
                        ]:
                            is_our_conn = (
                                connect.prev_zone == next_zone
                                or connect.next_zone == next_zone
                            )
                            if not is_our_conn:
                                continue

                            # Check connection capacity —
                            # how many drones already using it?
                            link_usage = sum(
                                1 for d, move in planned.items()
                                if isinstance(move, Connection)
                                and move == connect
                            )

                            if link_usage < connect.max_link_capacity:
                                # Connection has room — commit.
                                planned[drone] = connect
                                break
                    else:
                        # Normal or priority zone —
                        # move directly, no connection needed.
                        planned[drone] = next_zone

                # else: next_zone is full — drone waits.
                # Nothing added to planned = drone stays put.

        return planned

    def _apply_turn(
        self,
        planned_moves: Dict[Drone, Union[Zone, Connection]],
    ) -> List[Tuple[str, str]]:
        output: List[Tuple[str, str]] = []
        for drone, move in planned_moves.items():
            if isinstance(move, Zone):
                drone.move_to(move)
                drone.arrival_turn = 0
                output.append((drone.label, move.name))
            elif isinstance(move, Connection):
                drone.arrival_turn = self.turn + 1
                in_transit = f"{move.prev_zone.name}-{move.next_zone.name}"
                output.append((drone.label, in_transit))
        return output

    def run(self) -> List[List[Tuple[str, str]]]:
        result: List[List[Tuple[str, str]]] = []
        self._give_paths()
        while not all(d.current_zone == self.manager.end_hub
                      for d in self.drones):
            self.turn += 1
            if self.turn > 500:
                break
            plan_dict = self._prepare_turn()
            output = self._apply_turn(plan_dict)
            result.append(output)
        return result

    def run_with_snapshots(
            self,
    ) -> Tuple[List[List[Tuple[str, str]]], List[Dict[str, str]]]:
        """Same as run but records each drone's position per turn
        for the visualiser."""
        result: List[List[Tuple[str, str]]] = []
        snapshots: List[Dict[str, str]] = []
        self._give_paths()
        while not all(
            d.current_zone == self.manager.end_hub
            for d in self.drones
        ):
            self.turn += 1
            if self.turn > 500:
                break
            plan_dict = self._prepare_turn()
            output = self._apply_turn(plan_dict)
            snapshots.append(
                {d.label: d.current_zone.name for d in self.drones}
            )
            result.append(output)
        return result, snapshots
