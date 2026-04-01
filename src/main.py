import sys
from src.parser import Parser
from src.engine import EngineSimulation
from src.exceptions import FlyInError
from src.renderer import Renderer


def main() -> None:
    """ The activation script"""
    # 1 parse the output file:
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: python3 -m src.main <map_file>\n")
        sys.exit(1)
    file_path = sys.argv[1]
    try:
        parser = Parser(file_path)
        parser.parsing()
        manager = parser.manager
    except FlyInError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    # 2 activate the engine
    try:
        engine = EngineSimulation(manager)
        result, _ = engine.run()
    except FlyInError as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)

    # 3 the renderer
    try:
        rend = Renderer(manager, engine)
        rend.render(result)
        print(f"Simluation completed in: {engine.turn} turns!")
    except Exception as e:
        sys.stderr.write(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
