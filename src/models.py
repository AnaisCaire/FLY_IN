from typing import Dict, List


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
    def __init__(self, id, location, history) -> None:
        """ A drone is an actor in the simulation """
        self.id = id
        self.location = location
        self.history = history


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
        self.adjency_list: Dict[Zone, List[Connection]] = {}
        self.nb_drones: list[Drone] = []
