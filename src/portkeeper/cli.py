import json
import argparse
from .core import PortRegistry, Reservation

def main():
    parser = argparse.ArgumentParser(prog='portkeeper', description='Reserve ports and update .env/config.json')
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
