# conftest.py
import pytest
from unittest.mock import patch
import tempfile
import os


@pytest.fixture(scope="session")
def test_database():
    """Session-scoped test database"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(db_fd)
    yield db_path
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture(autouse=True)
def reset_auth_state():
    """Reset authentication state between tests"""
    yield
    # Cleanup any global state if needed


# Run configuration for pytest.ini
"""
[pytest.ini]
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    security: Security tests
"""