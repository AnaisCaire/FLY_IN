"""Manual integration test: parsing -> pathfinding -> simulation pipeline.

Run with:
    PYTHONPATH=. python3 tests/parser_tester.py <map_file> [k_paths]
"""

import sys
from typing import List
from src.parser import Parser
from src.models import Manager, Zone
from src.pathfinder import Pathfinder
from src.engine import EngineSimulation


def test_parsing(file_path: str) -> Manager:
    """Parse a map file and print a summary.

    Args:
        file_path: Path to the .map file.

    Returns:
        Populated Manager instance.
    """
    print(f"--- 1. Parsing: {file_path} ---")
    parser = Parser(file_path)
    parser.parsing()
    manager = parser.manager

    assert manager.start_hub is not None, "start_hub missing after parsing"
    assert manager.end_hub is not None, "end_hub missing after parsing"

    restricted = [
        name for name, zone in manager.zone.items()
        if zone.zone_type.name == "RESTRICTED"
    ]
    priority = [
        name for name, zone in manager.zone.items()
        if zone.zone_type.name == "PRIORITY"
    ]

    print(f"  Drones : {manager.total_drone_count}")
    print(f"  Zones  : {len(manager.zone)} total")
    print(f"  Start  : {manager.start_hub.name} "
          f"(is_start={manager.start_hub.is_start})")
    print(f"  End    : {manager.end_hub.name} "
          f"(is_end={manager.end_hub.is_end})")
    print(f"  Restricted zones ({len(restricted)}): "
          f"{', '.join(restricted) or 'none'}")
    print(f"  Priority zones   ({len(priority)}): "
          f"{', '.join(priority) or 'none'}")
    drone_labels = [d.label for d in manager.drones]
    print(f"  Drones spawned   : {drone_labels}")
    print("  ✅ Parsing OK\n")
    return manager


def test_single_path(manager: Manager) -> None:
    """Run Dijkstra and print the single shortest path.

    Args:
        manager: Populated Manager from the parser.
    """
    print("--- 2. Single Optimal Path (Dijkstra) ---")
    finder = Pathfinder(manager)
    path = finder.find_shortest_turn_path()

    if not path:
        print("  ❌ No path found!\n")
        return

    names = [zone.name for zone in path]
    cost = sum(zone.movement_cost for zone in path[1:])

    print(f"  Path  : {' -> '.join(names)}")
    print(f"  Turns : {cost}  |  Hops : {len(path) - 1}")
    print("  ✅ Single path OK\n")


def test_k_shortest_paths(manager: Manager, k: int) -> None:
    """Run Yen's k-shortest-paths and print all candidates.

    Args:
        manager: Populated Manager from the parser.
        k: Number of paths to find.
    """
    print(f"--- 3. Top {k} Shortest Paths (Yen's) ---")
    finder = Pathfinder(manager)
    all_paths: List[List[Zone]] = finder.find_k_shortest_paths(k)

    if not all_paths:
        print("  ❌ No paths found.\n")
        return

    for i, path in enumerate(all_paths, 1):
        names = [z.name for z in path]
        cost = sum(z.movement_cost for z in path[1:])
        print(f"  Path #{i} ({cost} turns): {' -> '.join(names)}")

    print(f"  ✅ Multi-path OK — found {len(all_paths)} path(s)\n")


def test_engine(manager: Manager) -> None:
    """Run the full simulation and print turn-by-turn output.

    Args:
        manager: Populated Manager from the parser.
    """
    print("--- 4. Full Simulation (Engine) ---")
    engine = EngineSimulation(manager)
    result = engine.run()

    for i, turn_moves in enumerate(result, 1):
        moves = "  ".join(f"{label}-{dest}" for label, dest in turn_moves)
        print(f"  Turn {i:>2}: {moves}")

    print(f"\n  Total turns : {engine.turn}")
    delivered = sum(
        1 for d in engine.drones if d.current_zone == manager.end_hub
    )
    print(
        f"  Drones delivered : {delivered}/{manager.total_drone_count}"
    )
    print("  ✅ Simulation OK\n")


def main() -> None:
    """Entry point: parse args and run all four test stages."""
    if len(sys.argv) < 2:
        print("Usage: python tests/parser_tester.py <map_file> [k_paths]")
        sys.exit(1)

    file_path = sys.argv[1]
    k_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    try:
        manager = test_parsing(file_path)
        test_single_path(manager)
        test_k_shortest_paths(manager, k=k_value)
        test_engine(manager)

    except Exception as e:
        print(f"\n💥 Critical failure: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
