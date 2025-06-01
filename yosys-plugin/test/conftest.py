import glob
import os
import pytest
from pathlib import Path


def pytest_configure():
    pytest.test_root = Path(__file__).resolve().parent
    pytest.difetto = pytest.test_root.parent / "difetto.so"
