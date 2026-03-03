from typing import Dict, List, Optional, Set, Tuple


class Zone():
    def __init__(self, name: str, x: int, y: int, zone_type: str,
                 color: str, max_drones: int) -> None:
        """ Identity and rules of each hub"""
        self.name: str = name
        self.x: int = x
        self.y: int = y
        self.color: str = color
        self.max_drones: int = max_drones
        self.zone_type: str = zone_type
        # self.cur_drones: int = cur_drones


class Connection():
    """ the edges between zones """
    def __init__(self, prev_zone, next_zone, max_link_capacity) -> None:
        self.max_link_capacity: int = max_link_capacity
        self.prev_zone = prev_zone
        self.next_zone = next_zone


class Drone():
    def __init__(self, id, start_zone) -> None:
        """ A drone is an actor in the simulation """
        self.id = f"D{id}"
        self.start_zone: Zone = start_zone
        self.history: List[str] = [start_zone.name]


class Manager():
    """
    The manager
    - use dict to store zone name during parsing
    - provide a way to find all zones connected to an other zone
    """
    def __init__(self):
        """
        - zone is used for parsing
        - adjency list is better for looping
        """
        self.zone: Dict[str, Zone] = {}  # store zones by name for parcing
        self.adjency_list: Dict[str, List[Connection]] = {}
        self.drones: list[Drone] = []
        self.start_hub: Optional[Zone] = None
        self.end_hub: Optional[Zone] = None
        self.total_drone_count: int = 0
        self.real_connections: set[Tuple[str, str]] = set()

    def add_zone(self, zone: Zone ) -> None:
        """ Just store a zone and add it to the adjency list"""
        self.zone[zone.name] = zone  # the name of the zone will be found in parcing
        self.adjency_list[zone.name] = []  # the zone is the key and connections will be the value

    def add_connection(self, connection: Connection) -> None:
        """ Adds connections bidirectionnaly """
        tuple = sorted([connection.prev_zone.name, connection.next_zone.name])
        connection_key = (tuple[0], tuple[1])
        if connection_key in self.real_connections:
            raise ValueError("this is not a real unique connection")

        self.adjency_list[connection.prev_zone.name].append(connection)
        self.adjency_list[connection.next_zone.name].append(connection)
        # We can now mark it as existent
        self.real_connections.add(connection_key)

    def initialize_drones(self) -> None:
        if not self.start_hub:
            raise ValueError("Cannot initialize drones without a start_hub")
        for i in range(1, self.total_drone_count + 1):
            self.drones.append(Drone(i, self.start_hub))
