#!/usr/bin/env python3
"""
Example script demonstrating how to use PortKeeper to scan for free ports
and reserve them on local network hosts.
"""

import sys

try:
    from portkeeper import PortRegistry
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install --user portkeeper")
    sys.exit(1)


def main():
    """Main function to demonstrate network scanning and port reservation."""
    registry = PortRegistry()
    
    # Scan local network for free ports
    print("🔍 Scanning local network for free ports...")
    free_ports_by_host = registry.scan_local_network(port_range=(8000, 8050), timeout=0.1)
    
    # Display results
    for host, ports in free_ports_by_host.items():
        if ports:
            print(f"✅ Host {host} has {len(ports)} free ports between 8000-8050")
            print(f"   First few: {ports[:5]}")
    
    # Reserve a port on any available host
    if free_ports_by_host:
        print("🔒 Reserving a port on any available host...")
        reservation = registry.reserve_network_port(port_range=(8000, 8050), hold=True)
        print(f"✅ Reserved port {reservation.port} on host {reservation.host}")
    else:
        print("❌ No free ports found on local network hosts.")


if __name__ == "__main__":
    main()
