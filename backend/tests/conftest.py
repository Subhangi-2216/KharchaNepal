"""
Shared test fixtures for all tests.
"""

import pytest
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Create a fixture to set up logging for tests
@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Set up logging for tests."""
    import logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    yield
