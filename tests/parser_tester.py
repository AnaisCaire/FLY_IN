import sys
from src.parser import Parser
from src.models import Manager


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py <map_file>")
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        # 1. Initialize the Manager (The Graph)
        manager = Manager()

        # 2. Initialize the Parser with the Manager
        # Note: Ensure your Parser.__init__ matches this signature
        parser = Parser(file_path)
        parser.manager = manager

        # 3. Execute Parsing
        print(f"--- Parsing: {file_path} ---")
        parser.parsing()
        print("Parsing successful!\n")

        # 4. Verify the Data
        print("--- Map Summary ---")
        print(f"Drones: {manager.total_drone_count}")
        print(f"Zones found: {len(manager.zone)}")
        print(f"Start Hub: {manager.start_hub.name if manager.start_hub else 'None'}")
        print(f"End Hub: {manager.end_hub.name if manager.end_hub else 'None'}")

        print("\n--- Adjacency List (Connections) ---")
        # Change your print loop to see both:
        for zone_name, zone_obj in manager.zone.items():
            print(f"{zone_name} (max_drones: {zone_obj.max_drones})")
            connections = manager.adjency_list[zone_name]
            for conn in connections:
                neighbor = conn.next_zone.name if conn.prev_zone.name == zone_name else conn.prev_zone.name
                print(f"  -> {neighbor} (link_cap: {conn.max_link_capacity})")

    except Exception as e:
        print(f"Test Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
