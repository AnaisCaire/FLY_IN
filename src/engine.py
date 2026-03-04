from src.models import Manager, Zone, Drone
from src.pathfinder import Pathfinder
from typing import List


class EngineSimulation:
    """
     the Active strategist
    """
    def __init__(self,
                 manager: Manager,
                 paths: List[List[Zone]],
                 path_costs: List[float]):
        self.manager = manager
        self.paths = paths
        self.drones = manager.drones  # take the list of drones from manager
        self.path_costs = path_costs  # Costs already calculated by Pathfinder
        self.turn = 0

    def pepare_drones(self) -> None:
        """ determine each drones path before starting moving """
        path_occupancy = [0] * len(self.paths)  # example [0, 0, 0]

        for drone in self.drones:
            best_idx = 0
            min_latency = float('inf')
            # 1. calculate latency
            for i, cost in enumerate(self.path_costs):
                latency = cost + path_occupancy[i]

                if latency < min_latency:
                    min_latency = latency
                    best_idx = i
            # 2 add the drones
            drone.defined_path = self.paths[best_idx]
            drone.path_index = 0
            # 3. Increase occupancy so the NEXT drone sees this path as "busier"
            path_occupancy[best_idx] += 1
            print(f"DEBUG: {drone.id} assigned to Path {best_idx} (Est. Arrival: Turn {min_latency})")
