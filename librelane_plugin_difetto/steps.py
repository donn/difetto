import os
from librelane.steps import Step, StepException
from librelane.steps.pyosys import PyosysStep
from librelane.state import DesignFormat
from librelane.config import Variable
from librelane.common import Path
from librelane.common.misc import get_script_dir as get_lln_script_dir

from typing import List, Optional

__file_dir__ = os.path.dirname(os.path.abspath(__file__))


@Step.factory.register()
class Synthesis(Step.factory.get("Yosys.Synthesis")):
    """
    This is a one-for-one copy of ``Yosys.Synthesis`` with one change:
    ``SYNTH_WRITE_NOATTR`` throws a step exception. That's it.
    """

    id = "Difetto.Synthesis"

    def run(self, *args, **kwargs):
        if self.config["SYNTH_WRITE_NOATTR"]:
            raise StepException(
                "'SYNTH_WRITE_NOATTR' is not compatible with DFT flows. Please set it to 'false'."
            )
        return super().run(*args, **kwargs)


@Step.factory.register()
class Resynthesis(Step.factory.get("Yosys.Resynthesis")):
    """
    This is a one-for-one copy of ``Yosys.Resynthesis`` with one change:
    ``SYNTH_WRITE_NOATTR`` throws a step exception. That's it.
    """

    id = "Difetto.Resynthesis"

    def run(self, *args, **kwargs):
        if self.config["SYNTH_WRITE_NOATTR"]:
            raise StepException(
                "'SYNTH_WRITE_NOATTR' is not compatible with DFT flows. Please set it to 'false'."
            )
        return super().run(*args, **kwargs)


dft_exclude_vars = [
    Variable(
        "DFT_TEST_MODE_WIRE",
        str,
        "Name of the wire to be used as a test-mode select (distinct from the shift enable). Prefix with ! to invert.",
    ),
    Variable(
        "DFT_TEST_CLOCK_WIRE",
        str,
        "Name of the wire to use as a clock signal. Prefix with ! to invert.",
    ),
    Variable(
        "DFT_BSCAN_EXCLUDE_IO",
        Optional[List[str]],
        "Names of top-level pins to exclude boundary scan registers for. The contents of 'DFT_TEST_MODE_WIRE' and 'DFT_CLOCK_WIRE' will automatically be added to this list.",
    ),
]


class DFTCommon(PyosysStep):
    inputs = [DesignFormat.nl]
    outputs = [DesignFormat.nl]

    config_vars = PyosysStep.config_vars + [
        Variable(
            "DFT_TOP_MODULE",
            Optional[str],
            "An optional override for the top module for DFT, in case you would prefer only a submodule to have boundary scan and scannable flip-flops.",
        ),
        Variable(
            "DFT_JSON_MAPPING",
            Path,
            "A JSON file with the mapping from non-scannable flip-flops to scannable flip-flops.",
        ),
    ]

    def get_command(self, state_in) -> List[str]:
        out_file = os.path.join(
            self.step_dir,
            f"{self.config['DESIGN_NAME']}.{DesignFormat.nl.extension}",
        )
        cmd = super().get_command(state_in)
        return cmd + ["--output", out_file, state_in[DesignFormat.nl]]

    def run(self, state_in, **kwargs):
        kwargs, env = self.extract_env(kwargs)
        state_out, metrics = super().run(state_in, env=env, **kwargs)
        state_out[DesignFormat.nl] = Path(
            os.path.join(
                self.step_dir,
                f"{self.config['DESIGN_NAME']}.{DesignFormat.nl.extension}",
            )
        )
        return state_out, metrics


@Step.factory.register()
class BoundaryScan(DFTCommon):
    id = "Difetto.BoundaryScan"

    config_vars = DFTCommon.config_vars + dft_exclude_vars

    def get_script_path(self):
        return os.path.join(__file_dir__, "scripts", "pyosys", "boundary_scan.py")


@Step.factory.register()
class ScanReplace(DFTCommon):
    id = "Difetto.ScanReplace"

    def get_script_path(self):
        return os.path.join(__file_dir__, "scripts", "pyosys", "scan_replace.py")


DesignFormat("cut_nl", "cut_nl.v", "Netlist with Cutaway Scannable Elements").register()


@Step.factory.register()
class Cut(PyosysStep):
    id = "Difetto.Cut"

    inputs = [DesignFormat.nl]
    outputs = [DesignFormat.cut_nl]

    config_vars = DFTCommon.config_vars + dft_exclude_vars

    def get_script_path(self):
        return os.path.join(__file_dir__, "scripts", "pyosys", "cut.py")

    def get_command(self, state_in) -> List[str]:
        out_file = os.path.join(
            self.step_dir,
            f"{self.config['DESIGN_NAME']}.{DesignFormat.cut_nl.extension}",
        )
        cmd = super().get_command(state_in)
        return cmd + ["--output", out_file, state_in[DesignFormat.nl]]

    def run(self, state_in, **kwargs):
        kwargs, env = self.extract_env(kwargs)
        state_out, metrics = super().run(state_in, env=env, **kwargs)
        state_out[DesignFormat.cut_nl] = Path(
            os.path.join(
                self.step_dir,
                f"{self.config['DESIGN_NAME']}.{DesignFormat.cut_nl.extension}",
            )
        )
        return state_out, metrics
