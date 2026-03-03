from typing import Dict
import os
from .models import Manager, Connection, Zone
from .exceptions import (
    MapSyntaxError,
    MapLogicError,
    MapConnectionError,
    FlyInError)
import re


class Parser():
    """
    will read the file line-by-line and populate a MAP class as it goes
    """
    def __init__(self, path: str) -> None:
        """ turn strings into objects for the MAP class """
        self.path = path
        self.manager = Manager()

    def _handle_metadata(self, line: str) -> Dict[str, str]:
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

    def _handle_hub(self, key: str, value: str) -> None:
        """
        Extract line info and add it to the zone object
        """
        metadata = self._handle_metadata(value)
        # remove the meta data
        clean_line = re.sub(r"\[(.*?)\]", "", value).strip()
        value_list = clean_line.split()
        if len(value_list) < 3:
            raise MapSyntaxError(f"Hub ({value}) needs name, x and y")
        name, x_str, y_str = value_list[0], value_list[1], value_list[2]

        # is this really necessary?
        if "-" in name:
            raise MapSyntaxError("Zone names cannot contain dashes")

        try:
            x, y = int(x_str), int(y_str)
        except ValueError:
            raise ValueError("coordinates need to be int")
        # creating a Zone object
        new_zone = Zone(
            name=name,
            x=x,
            y=y,
            zone_type=metadata.get("zone", "normal"),
            color=metadata.get("color", "yellow"),
            max_drones=int(metadata.get("max_drones", 1)))

        # add to manager the general zone and link to adjency list:
        self.manager.add_zone(new_zone)

        if key == "start_hub":
            if self.manager.start_hub is not None:
                raise MapLogicError("There is already a starting hub...")
            self.manager.start_hub = new_zone
        elif key == "end_hub":
            if self.manager.end_hub is not None:
                raise MapLogicError("There is already an end hub...")
            self.manager.end_hub = new_zone

    def _handle_nb_drones(self, value: str) -> None:
        """handle any number of Drones and add it to the start_hub"""
        try:
            number_drones = int(value)
            if number_drones <= 0:
                raise ValueError("Number of drones should be positive")
            self.manager.total_drone_count = number_drones
        except FlyInError:
            raise FlyInError("could not add drone to object Drone")

    def _handle_connection(self, value: str) -> None:
        """handle connection and add it to the object class"""
        metadata = self._handle_metadata(value)
        clean_value = re.sub(r"\[.*?\]", "", value).strip()
        if '-' in clean_value:
            first, second = clean_value.split('-', 1)
            first, second = first.strip(), second.strip()
            # here was pass from strings to objects for the manager
            zone_a = self.manager.zone.get(first)
            zone_b = self.manager.zone.get(second)
            if zone_a is None:
                raise MapConnectionError(f"Zone ({first}): is not defined")
            if zone_b is None:
                raise MapConnectionError(f"Zone ({second}) is not defined")
            new_connect = Connection(
                prev_zone=zone_a,
                next_zone=zone_b,
                max_link_capacity=int(metadata.get("max_link_capacity", 1)))
            self.manager.add_connection(new_connect)

    def parsing(self) -> None:
        """ do the parsing and populate the manager """

        if not os.path.exists(self.path):
            raise FileNotFoundError(f"The file was not found: {self.path}")

        try:
            with open(self.path, 'r') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' not in line:
                        raise MapSyntaxError(
                            f"Invalid format line ({line_num}) in: {line}")

                    name, val = line.split(':', 1)
                    name, val = name.strip(), val.strip()

                    if name == "nb_drones":
                        self._handle_nb_drones(val)
                    elif name in ["hub", "start_hub", "end_hub"]:
                        self._handle_hub(name, val)
                    elif name == "connection":
                        self._handle_connection(val)
            if not self.manager.start_hub or not self.manager.end_hub:
                raise MapLogicError("Map missing a start_hub or an end_hub.")
            # if all is confirmed, add the drones to the start_hub
            self.manager.initialize_drones()

        except FlyInError as e:
            raise FlyInError(f"Input file has failed: {e}")
