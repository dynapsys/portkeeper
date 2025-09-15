"""Configuration and fixtures for PortKeeper tests."""

import os
import sys
import pytest

# Add the src directory to PYTHONPATH so tests can import portkeeper directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

def pytest_configure(config):
    """Configure pytest settings."""
    # Set environment variables or other configurations if needed
    pass
