import json
import argparse
import re
import os
from pathlib import Path
from .core import PortRegistry, Reservation


def _parse_range_str(s: str):
    try:
        parts = s.strip().split('-', 1)
        if len(parts) != 2:
            raise ValueError
        start, end = int(parts[0]), int(parts[1])
        if start > end:
            start, end = end, start
        return (start, end)
    except Exception:
        raise argparse.ArgumentTypeError("--range-str must be in format START-END, e.g., 8000-9000")


def _expand_vars(value: str, mapping: dict) -> str:
    def repl(m):
        key = m.group(1)
        return str(mapping.get(key, os.environ.get(key, m.group(0))))
    return re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", repl, value)


def _load_config(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    if p.suffix.lower() in {'.yaml', '.yml'}:
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise RuntimeError("PyYAML is required for YAML configs. Install with 'pip install pyyaml'.") from e
        with open(p, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    else:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)


def main():
    parser = argparse.ArgumentParser(
        description="PortKeeper - Reserve and manage TCP ports for local development.",
        epilog="""Examples:
  Reserve a port (defaults to 8000-9000):
    $ portkeeper reserve

  Reserve using a generic profile 'service' (8888-8988) and write SERVICE_PORT:
    $ portkeeper reserve --profile service --write-env

  Reserve 'frontend' (8080-8180) and update package.json:
    $ portkeeper reserve --profile frontend --write-env FRONTEND_PORT
    $ portkeeper prepare --config pk.config.json

  Check status of reserved ports:
    $ portkeeper status

  Release a specific port:
    $ portkeeper release 8000

  Garbage collect stale reservations:
    $ portkeeper gc

  Print a free port:
    $ portkeeper port

  Run a command with a reserved port injected:
    $ portkeeper run --profile service -- cmd

Visit https://pypi.org/project/portkeeper/ for docs.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest='cmd')

    p_res = sub.add_parser('reserve', help='Reserve a port')
    p_res.add_argument('--preferred', type=int)
    p_res.add_argument('--range', nargs=2, type=int, metavar=('START', 'END'))
    p_res.add_argument('--range-str', type=_parse_range_str, help='Range as START-END (e.g., 8000-9000)')
    p_res.add_argument('--host', default='127.0.0.1')
    p_res.add_argument('--hold', action='store_true')
    p_res.add_argument('--owner')
    p_res.add_argument('--write-env', nargs='?', const='PORT', metavar='KEY', help='write KEY=PORT to .env (default KEY=PORT)')
    p_res.add_argument('--env-path', default='.env')
    p_res.add_argument('--profile', choices=['default', 'service', 'frontend'], help='Preset defaults (default=8000-9000, service=8888-8988 & SERVICE_PORT, frontend=8080-8180 & FRONTEND_PORT)')

    p_port = sub.add_parser('port', help='Print a free port')
    p_port.add_argument('--preferred', type=int)
    p_port.add_argument('--range', nargs=2, type=int, metavar=('START', 'END'))
    p_port.add_argument('--range-str', type=_parse_range_str, help='Range as START-END (e.g., 8000-9000)')
    p_port.add_argument('--host', default='127.0.0.1')
    p_port.add_argument('--owner')
    p_port.add_argument('--profile', choices=['default', 'service', 'frontend'], help='Preset defaults (default=8000-9000, service=8888-8988, frontend=8080-8180)')
    p_port.add_argument('--write-env', nargs='?', const='PORT', metavar='KEY', help='Also write KEY=PORT to .env (default KEY=PORT)')
    p_port.add_argument('--env-path', default='.env')

    p_run = sub.add_parser('run', help='Reserve a port and exec a command with it')
    p_run.add_argument('--preferred', type=int)
    p_run.add_argument('--range', nargs=2, type=int, metavar=('START', 'END'))
    p_run.add_argument('--range-str', type=_parse_range_str, help='Range as START-END (e.g., 8000-9000)')
    p_run.add_argument('--host', default='127.0.0.1')
    p_run.add_argument('--owner')
    p_run.add_argument('--profile', choices=['default', 'service', 'frontend'], help='Preset defaults (default=8000-9000, service=8888-8988, frontend=8080-8180)')
    p_run.add_argument('--env-key', default='PORT', help='Name of env var to export with the chosen port (default: PORT)')
    p_run.add_argument('--write-env', nargs='?', const='PORT', metavar='KEY', help='Also write KEY=PORT to .env (default KEY=PORT)')
    p_run.add_argument('--env-path', default='.env')
    p_run.add_argument('cmd', nargs=argparse.REMAINDER, help='Command to exec. Use -- to separate options, and {PORT}/{HOST} placeholders inside args')

    p_rel = sub.add_parser('release', help='Release a port')
    p_rel.add_argument('port', type=int)
    p_rel.add_argument('--host', default='127.0.0.1')

    p_status = sub.add_parser('status', help='List reserved ports')

    p_gc = sub.add_parser('gc', help='Clean stale registry entries')

    p_prep = sub.add_parser('prepare', help='Preflight: reserve multiple ports and update outputs from config (JSON/YAML)')
    p_prep.add_argument('--config', '-c', required=True, help='Path to pk.config.json or .yaml')
    p_prep.add_argument('--dry-run', action='store_true', help='Compute and print changes without writing files')

    args = parser.parse_args()
    reg = PortRegistry()

    if args.cmd == 'reserve':
        # Apply presets
        preferred = args.preferred
        rng = tuple(args.range) if args.range else None
        if rng is None and getattr(args, 'range_str', None):
            rng = args.range_str
        if args.profile == 'service':
            if preferred is None:
                preferred = 8888
            if rng is None:
                rng = (8888, 8988)
            if args.write_env is None:
                args.write_env = 'SERVICE_PORT'
        if args.profile == 'frontend':
            if preferred is None:
                preferred = 8080
            if rng is None:
                rng = (8080, 8180)
            if args.write_env is None:
                args.write_env = 'FRONTEND_PORT'
        if args.profile == 'default' and rng is None:
            rng = (8000, 9000)
        if preferred is None and rng is None:
            rng = (8000, 9000)

        res = reg.reserve(preferred=preferred, port_range=rng, host=args.host, hold=args.hold, owner=args.owner)
        print(json.dumps({'host': res.host, 'port': res.port, 'held': res.held}))
        if args.write_env:
            reg.write_env({args.write_env: str(res.port)}, path=args.env_path)

    elif args.cmd == 'port':
        # Compute defaults as in reserve
        preferred = args.preferred
        rng = tuple(args.range) if args.range else None
        if rng is None and getattr(args, 'range_str', None):
            rng = args.range_str
        if args.profile == 'service':
            if preferred is None:
                preferred = 8888
            if rng is None:
                rng = (8888, 8988)
        if args.profile == 'frontend':
            if preferred is None:
                preferred = 8080
            if rng is None:
                rng = (8080, 8180)
        if args.profile == 'default' and rng is None:
            rng = (8000, 9000)
        if preferred is None and rng is None:
            rng = (8000, 9000)

        res = reg.reserve(preferred=preferred, port_range=rng, host=args.host, hold=False, owner=args.owner)
        # Print only the port number for easy command substitution
        print(res.port)
        if args.write_env:
            reg.write_env({args.write_env: str(res.port)}, path=args.env_path)
        # Release immediately to avoid lingering registry entry
        reg.release(Reservation(host=res.host, port=res.port, held=False))

    elif args.cmd == 'run':
        # Reserve and then exec the given command with token replacement
        preferred = args.preferred
        rng = tuple(args.range) if args.range else None
        if rng is None and getattr(args, 'range_str', None):
            rng = args.range_str
        if args.profile == 'service':
            if preferred is None:
                preferred = 8888
            if rng is None:
                rng = (8888, 8988)
        if args.profile == 'frontend':
            if preferred is None:
                preferred = 8080
            if rng is None:
                rng = (8080, 8180)
        if args.profile == 'default' and rng is None:
            rng = (8000, 9000)
        if preferred is None and rng is None:
            rng = (8000, 9000)

        res = reg.reserve(preferred=preferred, port_range=rng, host=args.host, hold=False, owner=args.owner)
        port_str = str(res.port)
        host_str = res.host

        if args.write_env:
            reg.write_env({args.write_env: port_str}, path=args.env_path)

        # Prepare command args, replacing tokens
        cmd = list(args.cmd)
        if cmd and cmd[0] == '--':
            cmd = cmd[1:]
        if not cmd:
            print('❌ No command provided. Use: portkeeper run [opts] -- <cmd> [args]')
            return
        cmd = [a.replace('{PORT}', port_str).replace('{HOST}', host_str) for a in cmd]

        # Export env var for child
        os.environ[args.env_key] = port_str
        os.environ.setdefault('HOST', host_str)

        # Release immediately; the child will bind to the port
        reg.release(Reservation(host=res.host, port=res.port, held=False))

        # Replace current process with the target command
        try:
            os.execvp(cmd[0], cmd)
        except Exception as e:
            print(f"❌ Failed to exec command: {e}")
            return 1

    elif args.cmd == 'release':
        # Best-effort release from registry only; cannot close foreign process socket
        fake = Reservation(host=args.host, port=args.port, held=False)
        reg.release(fake)
        print('released')

    elif args.cmd == 'status':
        # Print registry content
        path = Path('.port_registry.json')
        try:
            if path.exists():
                print(path.read_text())
            else:
                print('{}')
        except Exception:
            print('{}')

    elif args.cmd == 'gc':
        # Keep only currently bound entries (simple GC)
        reg._write_registry({k: v for k, v in reg._read_registry().items() if not reg._is_port_free(v['host'], int(v['port']))})
        print('ok')

    elif args.cmd == 'prepare':
        cfg = _load_config(args.config)
        host_default = cfg.get('host', '127.0.0.1')
        env_map = {}
        # Reserve ports
        for spec in cfg.get('ports', []):
            key = spec['key']
            preferred = spec.get('preferred')
            rng = tuple(spec['range']) if 'range' in spec else None
            host = spec.get('host', host_default)
            res = reg.reserve(preferred=preferred, port_range=rng, host=host, hold=False, owner=spec.get('owner'))
            env_map[key] = str(res.port)
        # Write outputs
        if not args.dry_run:
            for out in cfg.get('outputs', []):
                otype = out.get('type', 'env')
                if otype in ('env', 'dotenv', 'compose_env'):
                    reg.write_env(env_map, path=out.get('path', '.env'))
                elif otype in ('json', 'package_json'):
                    mapping = out.get('map', {})
                    expanded = {k: (_expand_vars(v, env_map) if isinstance(v, str) else v) for k, v in mapping.items()}
                    reg.update_config_json(expanded, path=out.get('path', 'config.json'), backup=True)
                elif otype in ('runtime_js', 'js'):
                    mapping = out.get('map', {})
                    expanded = {k: (_expand_vars(v, env_map) if isinstance(v, str) else v) for k, v in mapping.items()}
                    p = Path(out.get('path', 'runtime-config.js'))
                    content = "// Generated by portkeeper prepare\nwindow.RUNTIME = " + json.dumps(expanded, indent=2) + ";\n"
                    tmp = p.with_suffix(p.suffix + '.tmp')
                    with open(tmp, 'w', encoding='utf-8') as f:
                        f.write(content)
                        f.flush()
                        os.fsync(f.fileno())
                    os.replace(tmp, p)
        print(json.dumps({'reserved': env_map}, indent=2))

    else:
        parser.print_help()
