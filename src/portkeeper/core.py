from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple, Iterator, List, Set, Union
import threading
import queue
import ipaddress
from typing import List, Tuple, Dict, Optional

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
        self._network_scan_cache = {}

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

    def _find_free_port(self, port_range: Tuple[int, int], host: str, used_ports: Optional[Set[int]] = None) -> Optional[int]:
        """Find a free port in the given range that's not currently reserved or used."""
        start, end = port_range
        used_ports = used_ports or set()
        # First, try to find a port that was previously released and can be reused
        for port in range(start, end + 1):
            if port in used_ports:
                continue
            key = f"{host}:{port}"
            registry = self._read_registry()
            if key not in registry:
                # Verify the port is actually free on the system
                if self._is_port_free(host, port):
                    return port
        # If no free port is found, return None
        return None

    # --- public API ---
    def reserve(self, port_range: Optional[Tuple[int, int]] = None, host: str = DEFAULT_HOST, hold: bool = False, owner: Optional[str] = None, count: int = 1) -> Union[Reservation, List[Reservation]]:
        """Reserve one or more ports, returning a single Reservation object if count=1, or a list of Reservation objects if count>1."""
        with FileLock(self.lock_path):
            registry = self._read_registry()
            port_range = port_range or (1024, 65535)
            reservations = []
            used_ports = set()
            for _ in range(count):
                port = self._find_free_port(port_range, host, used_ports)
                if port is None:
                    raise PortKeeperError(f"No free port in range {port_range}")
                used_ports.add(port)
                key = f"{host}:{port}"
                registry[key] = { 'host': host, 'port': port, 'owner': owner or '', 'timestamp': time.time() }
                reservations.append(Reservation(host=host, port=port, held=False))
            self._write_registry(registry)

        # Handle holding of ports if requested
        if hold:
            for res in reservations:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                try:
                    sock.bind((host, res.port))
                    sock.listen(1)
                    res.held = True
                    res._holder_socket = sock
                except OSError as e:
                    print(f"Warning: Could not hold port {res.port} on {host}: {e}")
                    res.held = False
        return reservations[0] if count == 1 else reservations

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
    def reserve_context(self, *args, count: int = 1, **kwargs):
        """Context manager for reserving one or more ports."""
        class _Ctx:
            def __init__(self, reg, args, kwargs, count):
                self.reg = reg
                self.args = args
                self.kwargs = kwargs
                self.count = count
                self.reservations = []
            def __enter__(self):
                self.reservations = self.reg.reserve(*self.args, count=self.count, **self.kwargs)
                return self.reservations if self.count > 1 else self.reservations[0] if self.reservations else None
            def __exit__(self, exc_type, exc, tb):
                if self.reservations:
                    if isinstance(self.reservations, list):
                        for res in self.reservations:
                            self.reg.release(res)
                    else:
                        self.reg.release(self.reservations)
        return _Ctx(self, args, kwargs, count)

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

    def scan_local_network(self, port_range: Tuple[int, int] = (8000, 9000), timeout: float = 0.1) -> Dict[str, List[int]]:
        """
        Scan the local network for free ports on all available hosts within the specified port range.
        Returns a dictionary mapping host IP addresses to lists of free ports.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import netifaces

        free_ports_by_host = {}
        local_hosts = []

        # Get all local network interfaces and their IP addresses
        try:
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                for family in (netifaces.AF_INET, netifaces.AF_INET6):
                    if family in addrs:
                        for addr in addrs[family]:
                            ip = addr.get('addr')
                            if ip and not ip.startswith('127.') and not ip == '::1':
                                local_hosts.append(ip)
        except Exception as e:
            print(f"Warning: Could not enumerate local network interfaces: {e}")
            local_hosts = ['127.0.0.1']

        def scan_host_ports(host: str, start_port: int, end_port: int, timeout: float) -> Tuple[str, List[int]]:
            free_ports = []
            for port in range(start_port, end_port + 1):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(timeout)
                    result = s.connect_ex((host, port))
                    if result != 0:  # Port is not in use
                        free_ports.append(port)
                    s.close()
                except Exception:
                    pass
            return host, free_ports

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for host in local_hosts:
                futures.append(executor.submit(scan_host_ports, host, port_range[0], port_range[1], timeout))

            for future in as_completed(futures):
                host, free_ports = future.result()
                if free_ports:
                    free_ports_by_host[host] = free_ports

        self._network_scan_cache = free_ports_by_host
        return free_ports_by_host

    def get_free_host_port(self, port_range: Tuple[int, int] = (8000, 9000), timeout: float = 0.1) -> Tuple[str, int]:
        """
        Find a free host and port combination in the local network.
        Returns a tuple of (host, port) that is available.
        """
        if not self._network_scan_cache or not any(self._network_scan_cache.values()):
            self.scan_local_network(port_range, timeout)

        for host, ports in self._network_scan_cache.items():
            if ports:
                port = ports.pop(0)  # Take the first available port
                return host, port

        raise PortKeeperError(f"No free ports found in range {port_range[0]}-{port_range[1]} on local network hosts")

    def reserve_network_port(self, port_range: Optional[Tuple[int, int]] = None, host: Optional[str] = None, hold: bool = False, owner: Optional[str] = None) -> Reservation:
        """
        Reserve a port on a specific host or any available host in the local network.
        If host is not specified, it will find a free host and port combination.
        """
        if host is None:
            host, port = self.get_free_host_port(port_range or (8000, 9000))
        else:
            port = self._find_free_port(port_range or (1024, 65535), host)

        reservation = Reservation(host=host, port=port, held=hold)
        if hold:
            reservation._holder_socket = self._hold_port(host, port)
        self._add_to_registry(reservation, owner=owner)
        return reservation

    def _hold_port(self, host: str, port: int) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(1)
        return sock

    def _add_to_registry(self, reservation: Reservation, owner: Optional[str] = None) -> None:
        key = f"{reservation.host}:{reservation.port}"
        with FileLock(self.lock_path):
            registry = self._read_registry()
            registry[key] = { 'host': reservation.host, 'port': reservation.port, 'owner': owner or '', 'timestamp': time.time() }
            self._write_registry(registry)
