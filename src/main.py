import sys
from src.parser import Parser
from src.engine import EngineSimulation
from src.exceptions import FlyInError, MapSyntaxError
from src.renderer import Renderer


def main() -> None:
    """ The activation script"""
    # 1 parse the output file:

    if len(sys.argv) != 2:
        sys.stderr.write("Usage: python3 -m src.main <map_file>\n")
        sys.exit(1)
    file_path = sys.argv[1]
    try:
        parser = Parser(file_path)  # instantiate a parsing class
        parser.parsing()  # activate parser
        manager = parser.manager  # add to the managerz
    except MapSyntaxError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    # 3 activate the engine
    try:
        engine = EngineSimulation(manager)
        result = engine.run()
        for i, turn_moves in enumerate(result, 1):
            moves = " ".join(f"{label}-{dest}" for label, dest in turn_moves)
            print(moves)

    except FlyInError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)
    # 4 the renderre
    try:
        rend = Renderer(manager, engine)
        rend.render(result)
    except Exception as e:
        sys.stderr.write(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
