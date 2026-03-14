import os
import pytest

from decimal import Decimal
from librelane.flows import Flow


def run_difetto(design_name, expected_coverage):
    os.environ["YOSYS_PLUGIN_PATH"] = str(pytest.test_root.parent / "yosys-plugin")

    ATPG = Flow.factory.get("DifettoATPG")
    PNR = Flow.factory.get("DifettoPNR")
    Test = Flow.factory.get("DifettoTest")

    cfg = str(pytest.test_root / design_name / "config.yaml")

    pnr = PNR(cfg, pdk="sky130A")
    pnr_out = pnr.start(tag="pnr_test", overwrite=True)

    atpg = ATPG(cfg, pdk="sky130A")
    atpg_out = atpg.start(tag="atpg_test", overwrite=True, with_initial_state=pnr_out)

    test = Test(cfg, pdk="sky130A")
    test_out = test.start(tag="test_test", overwrite=True, with_initial_state=atpg_out)

    assert test_out.metrics["design__atpg__coverage"] >= Decimal(
        expected_coverage
    ), "Failed to meet expected coverage"


def test_spm():
    run_difetto("spm", 99.5)


@pytest.mark.large
def test_picorv32():
    run_difetto("picorv32", 98)
