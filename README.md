# PortKeeper

Reserve and manage localhost hosts/ports for starting servers. Transparently updates `.env` and `config.json` files and keeps a local registry so multiple processes and users can coordinate port reservations.

## Features
- Reserve a free port (optionally with preferred port or a search range)
- Optionally hold the port by binding a dummy socket (prevents others from taking it)
- Release reservation
- Atomic updates to `.env` and `config.json` (with backup)
- Simple file locking to avoid races
- Context manager API and a tiny CLI (`portkeeper`)

## Quickstart
```bash
pip install portkeeper

# Reserve preferred 8888 or a port in 8888-8988, hold it, and print JSON
portkeeper reserve --preferred 8888 --range 8888 8988 --hold --owner myapp

# From Python
from portkeeper import PortRegistry
with PortRegistry().reserve(preferred=8888, port_range=(8888, 8988), hold=True) as r:
    PortRegistry().write_env({'PORT': str(r.port)})
```

## CLI
- `reserve [--preferred P] [--range START END] [--hold] [--owner OWNER] [--write-env KEY]`
- `release PORT`
- `status` (list reserved ports in registry)
- `gc` (garbage-collect stale registry entries)

## License
MIT
