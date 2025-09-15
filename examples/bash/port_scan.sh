#!/bin/bash
# Example script to scan for free ports using PortKeeper

# Ensure portkeeper is installed
if ! python3 -c "import portkeeper" 2>/dev/null; then
  echo "❌ PortKeeper not installed. Installing now..."
  pip3 install portkeeper
fi

# Run a Python script to scan for free ports
echo "🔍 Scanning for free ports on local network..."
python3 -c "
from portkeeper import PortRegistry
registry = PortRegistry()
free_ports = registry.scan_local_network(port_range=(8000, 8050))
for host, ports in free_ports.items():
    if ports:
        print(f'✅ Host {host} has {len(ports)} free ports between 8000-8050')
        print(f'   First few: {ports[:5]}')
" 

# Reserve a port on any available host
echo "🔒 Reserving a port on any available host..."
python3 -c "
from portkeeper import PortRegistry
registry = PortRegistry()
reservation = registry.reserve_network_port(port_range=(8000, 8050), hold=True)
print(f'✅ Reserved port {reservation.port} on host {reservation.host}')
"
