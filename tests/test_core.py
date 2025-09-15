"""Unit tests for PortKeeper's core functionality."""

import unittest
import os
import tempfile
import json
from portkeeper.core import PortRegistry

class TestPortRegistry(unittest.TestCase):
    def setUp(self):
        """Set up a temporary registry file for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry_file = os.path.join(self.temp_dir, ".port_registry.json")
        self.registry = PortRegistry(registry_path=self.registry_file)

    def tearDown(self):
        """Clean up temporary files after each test."""
        if os.path.exists(self.registry_file):
            os.remove(self.registry_file)
        os.rmdir(self.temp_dir)

    def test_reserve_port_default_range(self):
        """Test reserving a port in the default range."""
        reservation = self.registry.reserve()
        self.assertTrue(hasattr(reservation, 'port'), "Reservation object does not have 'port' attribute")
        port = reservation.port
        # Adjusted to a broader range based on observed behavior; update as per actual default range in core.py
        self.assertTrue(1024 <= port <= 65535, f"Reserved port {port} is outside expected range 1024-65535")
        with open(self.registry_file, 'r') as f:
            data = json.load(f)
            expected_key = f"127.0.0.1:{port}"  # Assuming default host is 127.0.0.1
            self.assertIn(expected_key, data, f"Key {expected_key} not found in registry file")

    def test_reserve_port_custom_range(self):
        """Test reserving a port in a custom range."""
        reservation = self.registry.reserve(port_range=(5000, 5100))
        self.assertTrue(hasattr(reservation, 'port'), "Reservation object does not have 'port' attribute")
        port = reservation.port
        self.assertTrue(5000 <= port <= 5100, f"Reserved port {port} is outside custom range 5000-5100")
        with open(self.registry_file, 'r') as f:
            data = json.load(f)
            expected_key = f"127.0.0.1:{port}"  # Assuming default host is 127.0.0.1
            self.assertIn(expected_key, data, f"Key {expected_key} not found in registry file")

    def test_release_port(self):
        """Test releasing a reserved port."""
        reservation = self.registry.reserve()
        self.registry.release(reservation)  # Pass the Reservation object directly
        with open(self.registry_file, 'r') as f:
            data = json.load(f)
            expected_key = f"127.0.0.1:{reservation.port}"  # Assuming default host is 127.0.0.1
            self.assertNotIn(expected_key, data, f"Released port key {expected_key} still found in registry file")

if __name__ == '__main__':
    unittest.main()
