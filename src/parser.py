from typing import Dict, List, Set
import os
from models import Manager
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
            if '=' in tags:
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
            raise ValueError(f"Hub ({value}) needs name, x and y")
        name, x, y = value_list[0], value_list[1], value_list[2]
        name = name.lower()
        try:
            x, y = int(x), int(y)
            if x < 0 or y < 0:
                raise ValueError("coordinates needs to be positive")
        except ValueError:
            raise ValueError("coordinates need to be int")
        from models import Zone
        new_zone = Zone(
            name=name,
            x=x,
            y=y,
            zone_type=metadata.get("zone", "normal"),
            color=metadata.get("color", "yellow"),
            max_drones=int(metadata.get("max_drones", 1)))
        if key == "start_hub":
            self.manager()
        


    def _handle_nb_drones(self, line_num: int):
        pass


    def _handle_connection():
        pass


    def parsing(self, path: str) -> None:
        """ do the parsing """

        if not os.path.exists(path):
            raise FileNotFoundError(f"The file was not found: {path}")

        try:
            with open(path, 'r') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' not in line:
                        raise ValueError(
                            f"Invalid format line ({line_num}) in: {line}")
                    name, val = line.split(':', 1)
                    name, val = name.strip(), val.strip()
                    if name == "nb_drones":
                        self._handle_nb_drones
                    elif name in ["hub", "start_hub", "end_hub"]:
                        self._handle_hub(name, val)
                    elif name == "connection":
                        self._handle_connection(val)
                        


        except ValueError as e:
            raise ValueError(f"Input file has failed: {e}")
