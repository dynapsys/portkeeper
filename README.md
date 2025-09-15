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

## Author

**Tom Sapletta**  
🏢 Organization: softreck  
🌐 Website: [softreck.com](https://softreck.com)  

Tom Sapletta is a software engineer and the founder of softreck, specializing in system automation, DevOps tools, and infrastructure management solutions. 
With extensive experience in Python development and distributed systems, Tom focuses on creating tools that simplify complex development workflows.

### Professional Background
- **Expertise**: System Architecture, DevOps, Python Development
- **Focus Areas**: Port Management, Infrastructure Automation, Development Tools
- **Open Source**: Committed to building reliable, well-tested tools for the developer community

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at:

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

Copyright 2025 Tom Sapletta
