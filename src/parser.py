from typing import Dict, List, Set
import os
from models import Manager
import regex as re

class Parser():
    """
    will read the file line-by-line and populate a MAP class as it goes
    """
    def __init__(self, path: str) -> None:
        """ turn strings into objects for the MAP class """
        self.path = path
        self.map = Manager()

    def _handle_metadata(self, line: str) -> Dict[str, str]:
        pattern = r"\[(.*?)\]"
        match = re.search(pattern, line)
        if not match:
            raise ValueError(f"the line is not formatted properly: {line}")
        content = match.group(1)
        key, value = content.split('=')
        return {key: value}

    def _handle_nb_drones(self, line_num: int):
        pass

    def _handle_hub():
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
                    line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if ':' not in line:
                        raise ValueError(
                            f"Invalid format line ({line_num}) in: {line}")
                    name, value = line.split(':', 1)
                    if name == "nb_drones":
                        


        except ValueError as e:
            raise ValueError(f"Input file has failed: {e}")
