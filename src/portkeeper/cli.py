import json
import argparse
from .core import PortRegistry, Reservation

def main():
    parser = argparse.ArgumentParser(
        description="PortKeeper - Reserve and manage TCP ports for local development.",
        epilog="""Examples:
  Reserve a port in the default range (8000-9000):
    $ portkeeper reserve
    {"port": 8000, "host": "localhost", "range": [8000, 9000]}

  Reserve a port in a specific range and write to .env:
    $ portkeeper reserve --range 5000-6000 --write-env
    {"port": 5000, "host": "localhost", "range": [5000, 6000]}
    # .env updated with PORT=5000

  Reserve a preferred port if available, with fallback range:
    $ portkeeper reserve --preferred 8080 --range 8000-8100
    {"port": 8080, "host": "localhost", "range": [8000, 8100]}

  Check status of reserved ports:
    $ portkeeper status
    [{"port": 8000, "host": "localhost", "pid": 1234, "since": "2025-09-15T10:00:00"}]

  Release a specific port:
    $ portkeeper release 8000
    {"status": "released", "port": 8000}

  Garbage collect stale reservations:
    $ portkeeper gc
    {"released": [8001, 8002], "message": "Stale reservations cleaned."}

Visit https://pypi.org/project/portkeeper/ for more documentation and advanced usage.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest='cmd')

    p_res = sub.add_parser('reserve', help='Reserve a port')
    p_res.add_argument('--preferred', type=int)
    p_res.add_argument('--range', nargs=2, type=int, metavar=('START', 'END'))
    p_res.add_argument('--host', default='127.0.0.1')
    p_res.add_argument('--hold', action='store_true')
    p_res.add_argument('--owner')
    p_res.add_argument('--write-env', metavar='KEY', help='write KEY=PORT to .env')
    p_res.add_argument('--env-path', default='.env')

    p_rel = sub.add_parser('release', help='Release a port')
    p_rel.add_argument('port', type=int)
    p_rel.add_argument('--host', default='127.0.0.1')

    p_status = sub.add_parser('status', help='List reserved ports')

    p_gc = sub.add_parser('gc', help='Clean stale registry entries')

    args = parser.parse_args()
    reg = PortRegistry()

    if args.cmd == 'reserve':
        rng = tuple(args.range) if args.range else None
        res = reg.reserve(preferred=args.preferred, port_range=rng, host=args.host, hold=args.hold, owner=args.owner)
        print(json.dumps({'host': res.host, 'port': res.port, 'held': res.held}))
        if args.write_env:
            reg.write_env({args.write_env: str(res.port)}, path=args.env_path)

    elif args.cmd == 'release':
        # Best-effort release from registry only; cannot close foreign process socket
        fake = Reservation(host=args.host, port=args.port, held=False)
        reg.release(fake)
        print('released')

    elif args.cmd == 'status':
        # Print registry content
        from pathlib import Path
        try:
            import os
            path = Path('.port_registry.json')
            if path.exists():
                print(path.read_text())
            else:
                print('{}')
        except Exception:
            print('{}')

    elif args.cmd == 'gc':
        # Trigger reserve with no allocation to clean stale entries (simple approach)
        reg._write_registry({k: v for k, v in reg._read_registry().items() if not reg._is_port_free(v['host'], int(v['port']))})
        print('ok')

    else:
        parser.print_help()
