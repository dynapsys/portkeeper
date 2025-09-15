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
        self.registry = PortRegistry(registry_file=self.registry_file)

    def tearDown(self):
        """Clean up temporary files after each test."""
        if os.path.exists(self.registry_file):
            os.remove(self.registry_file)
        os.rmdir(self.temp_dir)

    def test_reserve_port_default_range(self):
        """Test reserving a port in the default range."""
        port = self.registry.reserve()
        self.assertTrue(8000 <= port <= 9000, f"Reserved port {port} is outside default range 8000-9000")
        with open(self.registry_file, 'r') as f:
            data = json.load(f)
            self.assertIn(str(port), data, f"Port {port} not found in registry file")

    def test_reserve_port_custom_range(self):
        """Test reserving a port in a custom range."""
        port = self.registry.reserve(port_range=(5000, 5100))
        self.assertTrue(5000 <= port <= 5100, f"Reserved port {port} is outside custom range 5000-5100")
        with open(self.registry_file, 'r') as f:
            data = json.load(f)
            self.assertIn(str(port), data, f"Port {port} not found in registry file")

    def test_reserve_preferred_port_available(self):
        """Test reserving a preferred port when it's available."""
        port = self.registry.reserve(preferred_port=8080, port_range=(8000, 8100))
        self.assertEqual(port, 8080, f"Preferred port 8080 was not reserved")
        with open(self.registry_file, 'r') as f:
            data = json.load(f)
            self.assertIn("8080", data, "Preferred port 8080 not found in registry file")

    def test_reserve_preferred_port_unavailable(self):
        """Test reserving a preferred port when it's already taken."""
        # Reserve the preferred port first
        self.registry.reserve(preferred_port=8080, port_range=(8000, 8100))
        # Try to reserve it again
        port = self.registry.reserve(preferred_port=8080, port_range=(8000, 8100))
        self.assertNotEqual(port, 8080, f"Preferred port 8080 was reserved despite being taken")
        self.assertTrue(8000 <= port <= 8100, f"Fallback port {port} is outside range 8000-8100")

    def test_release_port(self):
        """Test releasing a reserved port."""
        port = self.registry.reserve()
        self.registry.release(port)
        with open(self.registry_file, 'r') as f:
            data = json.load(f)
            self.assertNotIn(str(port), data, f"Released port {port} still found in registry file")

if __name__ == '__main__':
    unittest.main()
