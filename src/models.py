from typing import Dict, List, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from src.exceptions import MapSyntaxError


class ZoneType(Enum):
    """Classify each zone with its traversal type."""
    NORMAL = "normal"
    BLOCKED = "blocked"
    RESTRICTED = "restricted"
    PRIORITY = "priority"


@dataclass
class Zone:
    """A single node in the routing graph.

    Args:
        name: Unique identifier. No dashes or spaces allowed (VII.4).
        x: X coordinate (positive integer).
        y: Y coordinate (positive integer).
        is_start: True if this is the start_hub.
        is_end: True if this is the end_hub.
        color: Optional display color for the renderer.
        max_drones: Maximum simultaneous occupancy (default 1, VII.2).
        zone_type: Traversal cost/rule type (Section VI).
    """
    name: str
    x: int
    y: int
    is_start: bool = False
    is_end: bool = False
    color: Optional[str] = None
    max_drones: int = 1
    zone_type: ZoneType = ZoneType.NORMAL

    @property
    def movement_cost(self) -> int:
        """Return the turn cost to ENTER this zone.

        Returns:
            2 for RESTRICTED, 1 for NORMAL and PRIORITY.

        Raises:
            ValueError: If zone is BLOCKED — it must never be entered.
        """
        if self.zone_type == ZoneType.BLOCKED:
            raise ValueError(
                f"Zone '{self.name}' is BLOCKED and cannot be entered.")
        if self.zone_type == ZoneType.RESTRICTED:
            return 2
        return 1

    def effective_capacity(self) -> int:
        """Return actual capacity, with start/end exception.

        The start and end hubs accept unlimited drones by spec.

        Returns:
            999 for start/end zones, max_drones otherwise.
        """
        if self.is_start or self.is_end:
            return 999
        return self.max_drones


@dataclass
class Connection:
    """A bidirectional edge between two zones.

    Args:
        prev_zone: First endpoint Zone.
        next_zone: Second endpoint Zone.
        max_link_capacity: Max drones traversing simultaneously (default 1).
    """
    prev_zone: Zone
    next_zone: Zone
    max_link_capacity: int = 1


@dataclass(eq=False)
class Drone:
    """A single drone navigating the zone graph.

    Args:
        drone_id: Unique integer identifier (output label is D<drone_id>).
        current_zone: The zone the drone currently occupies.
    """
    drone_id: int
    current_zone: Zone
    defined_path: List[Zone] = field(default_factory=list)
    path_index: int = 0
    arrival_turn: int = 0  # 0 = drone not in transit, N = must land at N turns

    @property
    def label(self) -> str:
        """Return the output-formatted drone ID."""
        return f"D{self.drone_id}"

    def move_to(self, next_zone: Zone) -> None:
        """Update current position and record the move in history.

        Args:
            next_zone: The zone this drone is moving into.
        """
        self.current_zone = next_zone
        self.path_index += 1


class Manager:
    """Holds the full graph state: zones, connections, and drones.

    Uses an adjacency list for neighbor lookups.
    """

    def __init__(self) -> None:
        """Initialize an empty graph manager."""
        self.zone: Dict[str, Zone] = {}
        self.adjacency_list: Dict[str, List[Connection]] = {}
        self.drones: List[Drone] = []
        self.start_hub: Optional[Zone] = None
        self.end_hub: Optional[Zone] = None
        self.total_drone_count: int = 0
        self._seen_connections: Set[Tuple[str, str]] = set()

    def add_zone(self, zone: Zone) -> None:
        """Register a zone and prepare adjacency entry.

        Args:
            zone: The Zone object to register.

        Raises:
            ValueError: If a zone with the same name already exists.
        """
        if zone.name in self.zone:
            raise MapSyntaxError(f"Duplicate zone name: '{zone.name}'")
        self.zone[zone.name] = zone
        self.adjacency_list[zone.name] = []

    def add_connection(self, connection: Connection) -> None:
        """Register a bidirectional connection between two zones.

        Args:
            connection: The Connection object to register.

        Raises:
            ValueError: If this connection already exists.
        """
        a, b = connection.prev_zone.name, connection.next_zone.name
        connection_key: Tuple[str, str] = (min(a, b), max(a, b))
        if connection_key in self._seen_connections:
            raise ValueError(f"Duplicate connection: '{a}' <-> '{b}'")
        self.adjacency_list[a].append(connection)
        self.adjacency_list[b].append(connection)
        self._seen_connections.add(connection_key)

    def initialize_drones(self) -> None:
        """Spawn all drones at the start hub.

        Raises:
            ValueError: If start_hub has not been set yet.
        """
        if not self.start_hub:
            raise ValueError("Cannot initialize drones without a start_hub.")
        for i in range(1, self.total_drone_count + 1):
            self.drones.append(Drone(drone_id=i, current_zone=self.start_hub))
