import sys
from typing import List
from src.parser import Parser
from src.models import Manager, Zone
from src.pathfinder import Pathfinder


def test_parsing(file_path: str) -> Manager:
    """Tests the parsing logic and prints the map summary."""
    print(f"--- 1. Testing Parsing: {file_path} ---")
    parser = Parser(file_path)
    parser.parsing()
    manager = parser.manager

    print(f"Drones: {manager.total_drone_count} | Zones: {len(manager.zone)}")
    print(f"Start: {manager.start_hub.name} -> Goal: {manager.end_hub.name}")

    # Optional: Brief check of types
    restricted = [n for n, z in manager.zone.items() if z.zone_type.name == "RESTRICTED"]
    print(f"Restricted Zones found: {len(restricted)} ({', '.join(restricted[:3])}...)")
    print("✅ Parsing OK\n")
    return manager


def test_single_path(manager: Manager):
    """Tests the standard Dijkstra (absolute best path)."""
    print("--- 2. Testing Single Optimal Path ---")
    finder = Pathfinder(manager)
    path = finder.find_shortest_turn_path()

    if not path:
        print("❌ No path found!")
        return

    path_names = [zone.name for zone in path]
    print(f"Best Path: {' -> '.join(path_names)}")
    # We calculate the cost using the logic we discussed (Restricted=2, Normal=1)
    cost = sum(2 if z.zone_type.name == "RESTRICTED" else 1 for z in path[1:])
    print(f"Total Turns: {cost} | Hubs: {len(path)}")
    print("✅ Single Path OK\n")


def test_k_shortest_paths(manager: Manager, k: int = 3):
    """Tests Yen's Algorithm to find multiple alternative paths."""
    print(f"--- 3. Testing Top {k} Shortest Paths ---")
    finder = Pathfinder(manager)
    all_paths = finder.find_k_shortest_paths(k)

    if not all_paths:
        print("❌ No alternative paths found.")
        return

    for i, path in enumerate(all_paths, 1):
        names = [z.name for z in path]
        cost = sum(2 if z.zone_type.name == "RESTRICTED" else 1 for z in path[1:])
        print(f"Path #{i} ({cost} turns): {' -> '.join(names)}")

    print(f"✅ Multi-Path OK (Found {len(all_paths)} paths)\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: python parser_tester.py <map_file> [k_paths]")
        sys.exit(1)

    file_path = sys.argv[1]
    k_value = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    try:
        # Step 1: Parse
        manager = test_parsing(file_path)

        # Step 2: Single Dijkstra
        test_single_path(manager)

        # Step 3: Multi-path (Yen's)
        test_k_shortest_paths(manager, k=k_value)

    except Exception as e:
        print(f"💥 Critical Failure: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
