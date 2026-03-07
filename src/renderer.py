from src.models import Manager, ZoneType
from src.engine import EngineSimulation
from src.exceptions import FlyInError
from typing import List, Tuple


class Renderer():
    """ renders drone map"""
    def __init__(self, manager: Manager, engine: EngineSimulation) -> None:
        self.manager = manager
        self.engine = engine

    def _color(self, text: str, zone_name: str) -> str:
        """ Give each zone a color """
        # get the zone with the name in the zone dict:
        the_zone = self.manager.zone.get(zone_name)
        if the_zone is None:
            return f"\033[90m{text}\033[0m"
        if the_zone.zone_type == ZoneType.RESTRICTED:
            return f"\033[31m{text}\033[0m"
        if the_zone.zone_type == ZoneType.PRIORITY:
            return f"\033[92m{text}\033[0m"
        if the_zone.zone_type == ZoneType.NORMAL:
            if the_zone.is_start:
                return f"\033[32m{text}\033[0m"
            if the_zone.is_end:
                return f"\033[91m{text}\033[0m"
            else:
                return f"\033[94m{text}\033[0m"
        else:
            return f"\033[0m{text}\033[0m"

    def render(self, result: List[List[Tuple[str, str]]]) -> None:
        """ will do the rendering """
        try:
            for turn in result:
                moves = []
                for label, zone in turn:
                    moves.append(f"{label}-{self._color(zone, zone)}")
                print(" ".join(moves))
        except FlyInError as e:
            raise FlyInError(f"rendering error as: {e}")
