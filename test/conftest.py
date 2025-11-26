import pytest
from pathlib import Path


def pytest_configure():
    pytest.test_root = Path(__file__).resolve().parent
