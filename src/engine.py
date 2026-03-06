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

        for drone in self.drones:
            best_idx = 0
            min_latency = float('inf')
            for i, cost in enumerate(path_cost):
                latency = cost + path_occupancy[i]
                if latency < min_latency:
                    min_latency = latency
                    best_idx = i
            drone.defined_path = paths[best_idx]
            drone.path_index = 0
            path_occupancy[best_idx] += 1

    def _net_occupancy(
        self,
        next_zone: Zone,
        planned: Dict[Drone, Union[Zone, Connection]],
    ) -> int:
        """Compute the net occupancy of next_zone after this turn's moves.

        Accounts for drones currently in the zone, drones leaving it,
        and drones already planned to enter it this turn.

        Args:
            next_zone: The zone whose occupancy we are checking.
            planned: Moves already committed this turn.

        Returns:
            Net number of drones that will occupy next_zone after this turn.
        """
        current = sum(1 for d in self.drones if d.current_zone == next_zone)
        leaving = sum(
            1 for d, move in planned.items()
            if d.current_zone == next_zone and isinstance(move, Zone)
        )
        entering = sum(
            1 for d, move in planned.items()
            if (move if isinstance(move, Zone) else move.next_zone) == next_zone
        )
        return current - leaving + entering

    def _prepare_turn(self) -> Dict[Drone, Union[Zone, Connection]]:
        """Collect and validate intended moves for all active drones.

        Returns:
            Dict mapping each active drone to its intended move this turn.

        Raises:
            DijkstraPathError: If a drone in transit has no space to land.
        """
        planned: Dict[Drone, Union[Zone, Connection]] = {}

        for drone in self.drones:
            # Category 1: already delivered
            if drone.current_zone == self.manager.end_hub:
                continue

            # Category 2: in transit — must land this turn
            elif drone.arrival_turn > 0:
                next_zone = drone.defined_path[drone.path_index + 1]
                if self._net_occupancy(next_zone, planned) < next_zone.effective_capacity():
                    planned[drone] = next_zone
                else:
                    raise DijkstraPathError(
                        f"{drone.label} forced landing at '{next_zone.name}' "
                        f"blocked — zone full on turn {self.turn}"
                    )

            # Category 3: free to move — check capacity and pick next step
            elif drone.path_index < len(drone.defined_path) - 1:
                next_zone = drone.defined_path[drone.path_index + 1]
                if self._net_occupancy(next_zone, planned) < next_zone.effective_capacity():
                    if next_zone.zone_type == ZoneType.RESTRICTED:
                        for connect in self.manager.adjacency_list[drone.current_zone.name]:
                            if connect.prev_zone == next_zone or connect.next_zone == next_zone:
                                link_usage = sum(
                                    1 for d, move in planned.items()
                                    if isinstance(move, Connection) and move == connect
                                )
                                if link_usage < connect.max_link_capacity:
                                    planned[drone] = connect
                                    break
                    else:
                        planned[drone] = next_zone
                # else: drone waits — nothing added to planned

        return planned

    def _apply_turn(
        self,
        planned_moves: Dict[Drone, Union[Zone, Connection]],
    ) -> List[Tuple[str, str]]:
        """Commit all planned moves and return (label, destination) pairs.

        Args:
            planned_moves: Validated moves from _prepare_turn.

        Returns:
            List of (drone_label, destination_name) for the renderer.
        """
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
        """Run the simulation until all drones reach end_hub.

        Returns:
            One list of moves per turn, in simulation order.
        """
        result: List[List[Tuple[str, str]]] = []
        self._give_paths()
        while not all(d.current_zone == self.manager.end_hub for d in self.drones):
            self.turn += 1
            plan_dict = self._prepare_turn()
            output = self._apply_turn(plan_dict)
            result.append(output)
        return result

    def run_with_snapshots(self) -> Tuple[List[List[Tuple[str, str]]], List[Dict[str, str]]]:
        """
        same as run but needed for the visualiser to know the current position
        of each drone and not just the next position its going to be
        """
        result: List[List[Tuple[str, str]]] = []
        snapshots: List[Dict[str, str]] = []
        self._give_paths()
        while not all(d.current_zone == self.manager.end_hub for d in self.drones):
            self.turn += 1
            plan_dict = self._prepare_turn()
            output = self._apply_turn(plan_dict)
            snapshots.append({d.label: d.current_zone.name for d in self.drones})
            result.append(output)
        return result, snapshots
