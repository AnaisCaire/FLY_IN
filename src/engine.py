from src.models import Manager, Zone, Drone, Connection, ZoneType
from src.pathfinder import Pathfinder
from typing import List, Union, Dict, Tuple


class EngineSimulation:
    """
     the Active strategist
    """
    def __init__(self, manager: Manager):
        self.manager = manager
        self.drones = manager.drones  # take the list of drones from manager
        self.turn = 0
        self.pathfinder = Pathfinder(manager)

    def _give_paths(self) -> None:
        """ assing to each drone a defined path """
        paths = self.pathfinder.find_k_shortest_paths(100)
        path_cost = []
        for path in paths:
            cost = sum(zone.movement_cost for zone in path[1:])
            path_cost.append(cost)
        path_occupancy = [0] * len(paths)  # example [0, 0, 0]

        for drone in self.drones:
            best_idx = 0
            min_latency = float('inf')
            # 1. calculate latency
            for i, cost in enumerate(path_cost):
                latency = cost + path_occupancy[i]

                if latency < min_latency:
                    min_latency = latency
                    best_idx = i
            # 2 add the drones
            drone.defined_path = paths[best_idx]
            drone.path_index = 0
            # 3. Increase occupancy so the NEXT drone sees this path as "busier"
            path_occupancy[best_idx] += 1
            print(f"DEBUG: {drone.drone_id} assigned to Path {best_idx} (Est. Arrival: Turn {min_latency})")

    def _prepare_turn(self) -> Dict[Drone, Union[Zone, Connection]]:
        """ coolect and validate intended moves phase """
        planned: Dict[Drone, Union[Zone, Connection]] = {}
        for drone in self.drones:
            if drone.current_zone == self.manager.end_hub:
                continue
            elif drone.arrival_turn > 0:
                planned[drone] = drone.defined_path[drone.path_index + 1]
            elif drone.path_index < len(drone.defined_path) - 1:
                next_zone = drone.defined_path[drone.path_index + 1]
                if next_zone.zone_type == ZoneType.RESTRICTED:
                    for connect in self.manager.adjacency_list[drone.current_zone.name]:
                        if connect.prev_zone == next_zone:
                            planned[drone] = connect
                            break
                else:
                    planned[drone] = next_zone
        return planned

    def _apply_turn(self, planned_moves: Dict[Drone, Union[Zone, Connection]]) -> List[Tuple[str, str]]:
        """ commit the moves phase """
        drones_moving_list: List[Tuple[str, str]] = []
        for drone, move in planned_moves.items():
            if isinstance(move, Zone):
                drone.move_to(move)
                drone.arrival_turn = 0
                drones_moving_list.append((drone.label, move.name))
            elif isinstance(move, Connection):
                in_transit = f"{move.prev_zone.name}-{move.next_zone.name}"
                drone.arrival_turn = self.turn + 1
                drones_moving_list.append((drone.label, in_transit))
        return drones_moving_list

    def run(self) -> List[List[Tuple[str, str]]]:
        """ """
        self._give_paths()
        result: List[List[Tuple[str, str]]] = []
        while not (all(drone.current_zone == self.manager.end_hub for drone in self.drones)):
            self.turn += 1
            plan_dict = self._prepare_turn()
            output = self._apply_turn(plan_dict)
            result.append(output)
        return result
