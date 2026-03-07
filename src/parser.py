from typing import Dict
import os
from .models import Manager, Connection, Zone, ZoneType
from .exceptions import (
    MapSyntaxError,
    MapLogicError,
    MapConnectionError,
    FlyInError)
import re


class Parser:
    """Reads a map file line-by-line and populates a Manager instance."""

    def __init__(self, path: str) -> None:
        """Initialize the parser with a file path.

        Args:
            path: Path to the map file.
        """
        self.path = path
        self.manager = Manager()

    def _handle_metadata(self, line: str) -> Dict[str, str]:
        """Extract key=value pairs from a [...] metadata block.

        Args:
            line: Raw line string potentially containing [...].

        Returns:
            Dict of metadata keys to values. Empty if no block found.
        """
        pattern = r"\[(.*?)\]"
        metadata_dic: Dict[str, str] = {}
        match = re.search(pattern, line)
        if not match:
            return metadata_dic
        content = match.group(1)
        tags = content.split()
        for tag in tags:
            if '=' in tag:
                key, value = tag.split('=', 1)
                metadata_dic[key.strip()] = value.strip()
            else:
                metadata_dic[tag.strip()] = "true"
        return metadata_dic

    def _handle_hub(self, key: str, value: str, line_num: int) -> None:
        """Parse a hub/start_hub/end_hub line and register the zone.

        Args:
            key: Line prefix — 'hub', 'start_hub', or 'end_hub'.
            value: Everything after the ':' on the line.
            line_num: Current line number for error messages.

        Raises:
            MapSyntaxError: If name contains a dash, or fields are
                missing/invalid.
            MapLogicError: If a second start or end hub is declared.
        """
        metadata = self._handle_metadata(value)
        clean_line = re.sub(r"\[.*?\]", "", value).strip()
        value_list = clean_line.split()

        if len(value_list) < 3:
            raise MapSyntaxError(
                f"Line {line_num}: hub needs name, x and y — got: '{value}'")

        name, x_str, y_str = value_list[0], value_list[1], value_list[2]

        if "-" in name:
            raise MapSyntaxError(
                f"Line {line_num}: zone name '{name}' cannot contain dashes.")
        if " " in name:
            raise MapSyntaxError(
                f"Line {line_num}: zone name '{name}' cannot contain spaces.")

        try:
            x, y = int(x_str), int(y_str)
        except ValueError:
            raise MapSyntaxError(
                f"Line {line_num}: coordinates must be integers, got "
                f"'{x_str}' '{y_str}'"
            )

        raw_zone_type = metadata.get("zone", "normal")
        try:
            zone_type = ZoneType(raw_zone_type)
        except ValueError:
            raise MapSyntaxError(
                f"Line {line_num}: invalid zone type '{raw_zone_type}'. "
                "Must be one of: normal, blocked, restricted, priority."
            )

        raw_capacity = metadata.get("max_drones", "1")
        try:
            max_drones = int(raw_capacity)
            if max_drones <= 0:
                raise ValueError
        except ValueError:
            raise MapSyntaxError(
                f"Line {line_num}: max_drones must be a positive integer, "
                f"got '{raw_capacity}'"
            )

        # FIX 1: set is_start / is_end flags HERE, in the parser, before
        # passing to the manager — the parser is the only layer that knows
        # which prefix keyword was used.
        new_zone = Zone(
            name=name,
            x=x,
            y=y,
            is_start=(key == "start_hub"),
            is_end=(key == "end_hub"),
            zone_type=zone_type,
            color=metadata.get("color", None),
            max_drones=max_drones,
        )

        self.manager.add_zone(new_zone)

        if key == "start_hub":
            if self.manager.start_hub is not None:
                raise MapLogicError(
                    f"Line {line_num}: a start_hub is already defined.")
            self.manager.start_hub = new_zone
        elif key == "end_hub":
            if self.manager.end_hub is not None:
                raise MapLogicError(
                    f"Line {line_num}: an end_hub is already defined.")
            self.manager.end_hub = new_zone

    def _handle_nb_drones(self, value: str, line_num: int) -> None:
        """Parse the nb_drones line and store the count.

        Args:
            value: String value after 'nb_drones:'.
            line_num: Current line number for error messages.

        Raises:
            MapSyntaxError: If value is not a positive integer.
        """
        try:
            number_drones = int(value)
            if number_drones <= 0:
                raise ValueError
        except ValueError:
            raise MapSyntaxError(
                f"Line {line_num}: nb_drones must be a positive integer, "
                f"got '{value}'"
            )
        self.manager.total_drone_count = number_drones

    def _handle_connection(self, value: str, line_num: int) -> None:
        """Parse a connection line and register the edge.

        Args:
            value: String value after 'connection:'.
            line_num: Current line number for error messages.

        Raises:
            MapSyntaxError: If the connection line has no dash separator.
            MapConnectionError: If either zone name is not defined.
        """
        metadata = self._handle_metadata(value)
        clean_value = re.sub(r"\[.*?\]", "", value).strip()

        # FIX 2: missing dash is a hard syntax error, not a silent pass
        if '-' not in clean_value:
            raise MapSyntaxError(
                f"Line {line_num}: connection must use 'zone1-zone2' format, "
                f"got '{value}'"
            )

        first, second = clean_value.split('-', 1)
        first, second = first.strip(), second.strip()

        zone_a = self.manager.zone.get(first)
        zone_b = self.manager.zone.get(second)

        if zone_a is None:
            raise MapConnectionError(
                f"Line {line_num}: zone '{first}' is not defined.")
        if zone_b is None:
            raise MapConnectionError(
                f"Line {line_num}: zone '{second}' is not defined.")

        raw_capacity = metadata.get("max_link_capacity", "1")
        try:
            max_link_capacity = int(raw_capacity)
            if max_link_capacity <= 0:
                raise ValueError
        except ValueError:
            raise MapSyntaxError(
                f"Line {line_num}: max_link_capacity must be a positive "
                f"integer, got '{raw_capacity}'"
            )

        new_connect = Connection(
            prev_zone=zone_a,
            next_zone=zone_b,
            max_link_capacity=max_link_capacity,
        )
        self.manager.add_connection(new_connect)

    def parsing(self) -> None:
        """Read the map file and populate the manager.

        Raises:
            FileNotFoundError: If the file path does not exist.
            MapSyntaxError: On any structural / format error.
            MapLogicError: If start or end hub is missing.
            MapConnectionError: If a connection references an undefined zone.
        """
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"File not found: '{self.path}'")

        # FIX 3: line_num is declared before the loop so it's always in scope
        line_num = 0
        try:
            with open(self.path, 'r') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' not in line:
                        raise MapSyntaxError(
                            f"Line {line_num}: missing ':' in '{line}'")

                    prefix, val = line.split(':', 1)
                    prefix, val = prefix.strip(), val.strip()

                    if prefix == "nb_drones":
                        self._handle_nb_drones(val, line_num)
                    elif prefix in ("hub", "start_hub", "end_hub"):
                        self._handle_hub(prefix, val, line_num)
                    elif prefix == "connection":
                        self._handle_connection(val, line_num)
                    else:
                        raise MapSyntaxError(
                            f"Line {line_num}: unknown keyword '{prefix}'")

            if not self.manager.start_hub or not self.manager.end_hub:
                raise MapLogicError(
                    "Map is missing a start_hub or an end_hub."
                )

            self.manager.initialize_drones()

        except FlyInError as e:
            raise FlyInError(f"Parsing failed at line {line_num}: {e}") from e
