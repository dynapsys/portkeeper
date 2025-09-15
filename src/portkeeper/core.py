from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple, Iterator

# Cross-platform locking
try:
    import fcntl  # type: ignore
    _HAS_FCNTL = True
except Exception:
    _HAS_FCNTL = False

try:
    import msvcrt  # type: ignore
    _HAS_MSVCRT = True
except Exception:
    _HAS_MSVCRT = False

DEFAULT_REGISTRY = os.environ.get("PORTKEEPER_REGISTRY", ".port_registry.json")
DEFAULT_LOCKFILE = os.environ.get("PORTKEEPER_LOCK", ".port_registry.lock")
DEFAULT_HOST = os.environ.get("PORTKEEPER_HOST", "127.0.0.1")


class PortKeeperError(Exception):
    pass


@dataclass
class Reservation:
    host: str
    port: int
    held: bool = False
    _holder_socket: Optional[socket.socket] = None


class FileLock:
    def __init__(self, path: str):
        self.path = path
        self.fd = None

    def __enter__(self):
        open(self.path, 'a').close()
        if _HAS_FCNTL:
            self.fd = open(self.path, 'r+')
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX)
        elif _HAS_MSVCRT:
            self.fd = open(self.path, 'r+')
            msvcrt.locking(self.fd.fileno(), msvcrt.LK_LOCK, 1)
        else:
            # Fallback lock file
            while True:
                try:
                    self.fd = os.open(self.path + '.lck', os.O_CREAT | os.O_EXCL | os.O_RDWR)
                    break
                except FileExistsError:
                    time.sleep(0.05)
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if _HAS_FCNTL and self.fd:
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
                self.fd.close()
            elif _HAS_MSVCRT and self.fd:
                msvcrt.locking(self.fd.fileno(), msvcrt.LK_UN, 1)
                self.fd.close()
            else:
                if self.fd:
                    os.close(self.fd)
                    try:
                        os.remove(self.path + '.lck')
                    except Exception:
                        pass
        except Exception:
            pass


class PortRegistry:
    """Registry tracking reserved ports; updates .env and config.json atomically."""

    def __init__(self, registry_path: Optional[str] = None, lock_path: Optional[str] = None):
        self.registry_path = Path(registry_path or DEFAULT_REGISTRY)
        self.lock_path = lock_path or DEFAULT_LOCKFILE
        if not self.registry_path.exists():
            self._write_registry({})

    # --- registry helpers ---
    def _read_registry(self) -> Dict[str, Dict]:
        if not self.registry_path.exists():
            return {}
        try:
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _write_registry(self, data: Dict[str, Dict]):
        tmp = Path(str(self.registry_path) + '.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, self.registry_path)

    def _is_port_free(self, host: str, port: int) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.close()
            return True
        except OSError:
            return False

    def _find_free_in_range(self, host: str, rng: Tuple[int, int]) -> int:
        start, end = rng
        for p in range(start, end + 1):
            if self._is_port_free(host, p):
                return p
        raise PortKeeperError(f"No free ports in range {rng}")

    # --- public API ---
    def reserve(self, preferred: Optional[int] = None, port_range: Optional[Tuple[int, int]] = None,
                host: str = DEFAULT_HOST, hold: bool = False, owner: Optional[str] = None) -> Reservation:
        with FileLock(self.lock_path):
            registry = self._read_registry()
            # Clean stale
            cleaned = {}
            for key, meta in registry.items():
                try:
                    if self._is_port_free(meta['host'], int(meta['port'])):
                        continue
                except Exception:
                    continue
                cleaned[key] = meta
            registry = cleaned

            candidates = []
            if preferred is not None:
                candidates.append(int(preferred))
            if port_range is not None:
                start, end = port_range
                candidates.extend(list(range(start, end + 1)))

            chosen = None
            for p in candidates:
                if self._is_port_free(host, p) and not any((m['port'] == p and m['host'] == host) for m in registry.values()):
                    chosen = p
                    break
            if chosen is None:
                if port_range is not None:
                    chosen = self._find_free_in_range(host, port_range)
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.bind((host, 0))
                    chosen = s.getsockname()[1]
                    s.close()

            key = f"{host}:{chosen}"
            registry[key] = { 'host': host, 'port': chosen, 'owner': owner or '', 'timestamp': time.time() }
            self._write_registry(registry)

        res = Reservation(host=host, port=chosen, held=False)
        if hold:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, chosen))
                sock.listen(1)
                res.held = True
                res._holder_socket = sock
            except OSError:
                res.held = False
        return res

    def release(self, reservation: Reservation) -> None:
        key = f"{reservation.host}:{reservation.port}"
        with FileLock(self.lock_path):
            registry = self._read_registry()
            if key in registry:
                del registry[key]
                self._write_registry(registry)
        try:
            if reservation._holder_socket:
                try:
                    reservation._holder_socket.close()
                except Exception:
                    pass
            reservation.held = False
        except Exception:
            pass

    # Context manager
    def reserve_context(self, *args, **kwargs):
        class _Ctx:
            def __init__(self, reg, args, kwargs):
                self.reg = reg
                self.args = args
                self.kwargs = kwargs
                self.res = None
            def __enter__(self):
                self.res = self.reg.reserve(*self.args, **self.kwargs)
                return self.res
            def __exit__(self, exc_type, exc, tb):
                if self.res:
                    self.reg.release(self.res)
        return _Ctx(self, args, kwargs)

    # --- file helpers ---
    def write_env(self, data: Dict[str, str], path: str = '.env', merge: bool = True) -> None:
        p = Path(path)
        env: Dict[str, str] = {}
        if merge and p.exists():
            with open(p, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or '=' not in line:
                        continue
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
        env.update(data)
        tmp = p.with_suffix('.env.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            for k, v in env.items():
                f.write(f"{k}={v}\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)

    def update_config_json(self, changes: Dict, path: str = 'config.json', backup: bool = True) -> None:
        p = Path(path)
        data = {}
        if p.exists():
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {}
            if backup:
                bpath = p.with_suffix(p.suffix + '.bak')
                with open(bpath, 'w', encoding='utf-8') as bf:
                    json.dump(data, bf, indent=2)
        data.update(changes)
        tmp = p.with_suffix('.json.tmp')
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
