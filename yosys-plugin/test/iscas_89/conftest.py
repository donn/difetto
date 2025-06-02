import glob
import os
import pytest
from pathlib import Path

cwd = Path(__file__).resolve().parent


def pytest_configure():
    pytest.iscas_89_tests = [os.path.basename(e) for e in (cwd / "rtl").glob("*.v")]
