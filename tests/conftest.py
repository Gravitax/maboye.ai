import sys
import os
import pytest

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def pytest_configure(config):
    """
    Called before test run starts.
    Use this to perform any global test setup.
    """
    print(f"\nSetting up pytest: Adding {sys.path[0]} to sys.path")
