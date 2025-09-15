import argparse
import sys
from typing import Optional

from .core import PortRegistry, Reservation


def main():
    """CLI interface for PortKeeper."""
    parser = argparse.ArgumentParser(description="PortKeeper - Manage and reserve free ports for your applications.")
    parser.add_argument("command", choices=["reserve", "release", "status"], help="Command to execute")
    parser.add_argument("--port", type=int, help="Preferred port to reserve")
    parser.add_argument("--range", type=str, help="Port range to reserve from (e.g., '8000-9000')")
    parser.add_argument("--host", default="127.0.0.1", help="Host to reserve port on (default: 127.0.0.1)")
    parser.add_argument("--hold", action="store_true", help="Hold the port open with a socket")
    parser.add_argument("--owner", help="Owner identifier for the reservation")
    parser.add_argument("--registry", help="Path to the registry file")
    parser.add_argument("--lock", help="Path to the lock file")

    args = parser.parse_args()

    registry = PortRegistry(registry_path=args.registry, lock_path=args.lock)

    if args.command == "reserve":
        port_range = None
        if args.range:
            try:
                start, end = map(int, args.range.split('-'))
                port_range = (start, end)
            except ValueError:
                print(f"❌ Invalid range format: {args.range}. Use 'start-end'.")
                sys.exit(1)

        try:
            reservation = registry.reserve(
                preferred=args.port,
                port_range=port_range,
                host=args.host,
                hold=args.hold,
                owner=args.owner
            )
            print(f"✅ Reserved port {reservation.port} on {reservation.host}")
            if reservation.held:
                print("🔒 Port is held open with a socket")
            print(f"Use 'portkeeper release' to release this port.")
        except Exception as e:
            print(f"❌ Failed to reserve port: {e}")
            sys.exit(1)

    elif args.command == "release":
        # This is a placeholder; actual release logic would need to track reservations
        print("⚠️ Release functionality is not fully implemented in CLI mode.")
        print("Please ensure you have a reservation to release.")
        sys.exit(1)

    elif args.command == "status":
        # This is a placeholder; actual status logic would need to read the registry
        print("⚠️ Status functionality is not fully implemented in CLI mode.")
        print("Check the registry file for current reservations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
