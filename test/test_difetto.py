import os
import pytest

from decimal import Decimal
from librelane.flows import Flow


@pytest.mark.parametrize("design", (("spm", 100),))
def test_difetto(design):
    os.environ["YOSYS_PLUGIN_PATH"] = str(pytest.test_root.parent / "yosys-plugin")

    design_name, expected_coverage = design
    ATPG = Flow.factory.get("DifettoATPG")
    PNR = Flow.factory.get("DifettoPNR")
    Test = Flow.factory.get("DifettoTest")

    cfg = str(pytest.test_root / design_name / "config.yaml")

    pnr = PNR(cfg, pdk="sky130A")
    pnr_out = pnr.start(run_tag="pnr_test", overwrite=True)

    atpg = ATPG(cfg, pdk="sky130A")
    atpg_out = atpg.start(
        run_tag="atpg_test", overwrite=True, with_initial_state=pnr_out
    )

    test = Test(cfg, pdk="sky130A")
    test_out = test.start(
        run_tag="test_test", overwrite=True, with_initial_state=atpg_out
    )

    assert test_out.metrics["design__atpg__coverage"] >= Decimal(
        expected_coverage
    ), "Failed to meet expected coverage"
