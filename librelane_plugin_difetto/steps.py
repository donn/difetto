# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Mohamed Gaber
import os
import subprocess
from abc import abstractmethod
from librelane.steps import Step, StepException
from librelane.steps.pyosys import PyosysStep
from librelane.steps.openroad import OpenROADStep
from librelane.state import DesignFormat
from librelane.config import Variable
from librelane.common import Path
from librelane.logging import warn

from typing import ClassVar, List, Literal, Optional

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


dft_common_vars = [
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

dft_pin_vars = [
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
        "DFT_SCAN_ENABLE_PATTERN",
        str,
        "Formatting pattern for scan-enable signals to be found/created. Can either be the name of a top-level pin for the ENTIRE DESIGN (not necessarily the DFT top module) or an instance pin in the format instance/pin. You may include up to one set of braces {} which will be replaced with 0.",
    ),
    Variable(
        "DFT_SCAN_IN_PATTERN",
        str,
        "Formatting pattern for scan-in signals to be found/created. Can either be the name of a top-level pin for the ENTIRE DESIGN (not necessarily the DFT top module) or an instance pin in the format instance/pin. You may include up to one set of braces {} which will be replaced with the chain number. Currently, only one chain is supported, so there's no good reason to do that.",
    ),
    Variable(
        "DFT_SCAN_OUT_PATTERN",
        str,
        "Formatting pattern for scan-out signals to be found/created. Can either be the name of a top-level pin for the ENTIRE DESIGN (not necessarily the DFT top module) or an instance pin in the format instance/pin. You may include up to one set of braces {} which will be replaced with the chain number. Currently, only one chain is supported, so there's no good reason to do that.",
    ),
    Variable(
        "DFT_BSCAN_EXCLUDE_IO",
        Optional[List[str]],
        "Names of pins on the DFT top module to exclude boundary scan registers for. You must explicitly list the test mode and scan pins.",
    ),
]


class DFTCommon(PyosysStep):
    inputs = [DesignFormat.nl]
    outputs = [DesignFormat.nl]

    config_vars = PyosysStep.config_vars + dft_common_vars

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
    name = "Create Boundary Scan Flipflops"

    config_vars = DFTCommon.config_vars + dft_pin_vars

    def get_script_path(self):
        return os.path.join(__file_dir__, "scripts", "pyosys", "boundary_scan.py")


@Step.factory.register()
class ScanReplace(DFTCommon):
    id = "Difetto.ScanReplace"
    name = "Replace Flipflops with Scannable Flipflops"

    def get_script_path(self):
        return os.path.join(__file_dir__, "scripts", "pyosys", "scan_replace.py")


DesignFormat(
    "cut_nl",
    "cut_nl.v",
    "Netlist with Cutaway Scannable Elements",
).register()


@Step.factory.register()
class Cut(PyosysStep):
    id = "Difetto.Cut"
    name = "Create Cutaway Netlist"

    inputs = [DesignFormat.nl]
    outputs = [DesignFormat.cut_nl]

    config_vars = DFTCommon.config_vars + dft_pin_vars

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


DesignFormat("bench", "bench", "DFT Bench Format").register()


@Step.factory.register()
class WriteBench(Step):
    id = "Difetto.WriteBench"

    inputs = [DesignFormat.cut_nl]
    outputs = [DesignFormat.bench]

    def run(self, state_in, **kwargs):
        lib_list = self.toolbox.filter_views(self.config, self.config["LIB"])
        out_path = os.path.join(
            self.step_dir,
            f"{self.config['DESIGN_NAME']}.{DesignFormat.bench.extension}",
        )
        cmd = [
            "nl2bench",
            "--output",
            out_path,
            "--msb-first",
            str(state_in[DesignFormat.cut_nl]),
        ]
        for lib in lib_list:
            cmd.extend(["--lib-file", lib])
        self.run_subprocess(cmd)
        return {DesignFormat.bench: Path(out_path)}, {}


DesignFormat(
    "raw_tvs",
    "raw_tvs.txt",
    "Test Vectors (Cut Netlist Port Order)",
).register()


class QuaighATPG(Step):
    id = "Difetto.QuaighATPG"

    name = "ATPG with Quaigh"

    inputs = [DesignFormat.bench]
    outputs = [DesignFormat.raw_tvs]

    def run(self, state_in, **kwargs):
        out_path = os.path.join(
            self.step_dir,
            f"{self.config['DESIGN_NAME']}.{DesignFormat.raw_tvs.extension}",
        )
        cmd = [
            "quaigh",
            "atpg",
            "--output",
            out_path,
            str(state_in[DesignFormat.bench]),
        ]
        self.run_subprocess(cmd)
        return {DesignFormat.raw_tvs: Path(out_path)}, {}


DesignFormat(
    "raw_au",
    "raw_au.txt",
    "Test Vector Golden Output (Cut Netlist Port Order)",
).register()


class QuaighSim(Step):
    id = "Difetto.QuaighSim"

    name = "Simulation for Golden Outputs"
    long_name = "Simulation for Golden Outputs (with Quaigh)"

    inputs = [DesignFormat.bench, DesignFormat.raw_tvs]
    outputs = [DesignFormat.raw_au]

    def run(self, state_in, **kwargs):
        out_path = os.path.join(
            self.step_dir,
            f"{self.config['DESIGN_NAME']}.{DesignFormat.raw_au.extension}",
        )
        cmd = [
            "quaigh",
            "sim",
            "--output",
            out_path,
            "--input",
            str(state_in[DesignFormat.raw_tvs]),
            str(state_in[DesignFormat.bench]),
        ]
        self.run_subprocess(cmd)
        return {DesignFormat.raw_au: Path(out_path)}, {}


DesignFormat(
    "chain_yml",
    "chain.yml",
    "Scan Chains (YAML format)",
).register()


@Step.factory.register()
class Chain(OpenROADStep):
    id = "Difetto.Chain"
    name = "Create Scan Chains"

    outputs = OpenROADStep.outputs + [DesignFormat.chain_yml]

    config_vars = OpenROADStep.config_vars + dft_common_vars + dft_pin_vars

    def get_script_path(self):
        return os.path.join(__file_dir__, "scripts", "openroad", "chain.tcl")

    def run(self, state_in, **kwargs):
        views, metrics = super().run(state_in, **kwargs)
        views[DesignFormat.chain_yml] = Path(
            os.path.join(
                self.step_dir,
                f"{self.config['DESIGN_NAME']}.{DesignFormat.chain_yml.extension}",
            )
        )
        return views, metrics


class CocotbStep(Step):
    inputs = [DesignFormat.nl]
    outputs = []

    _cocotb_python_bin: ClassVar[Optional[str]] = None

    config_vars = [
        Variable(
            "DFT_COCOTB_SIM",
            Literal["icarus"],
            "The simulator to use for Cocotb.",
            default="icarus",
        )
    ]

    @classmethod
    def get_cocotb_python_bin(Self):
        if cached := Self._cocotb_python_bin:
            return cached
        cocotb_python_bin = "python3"
        try:
            result = subprocess.run(
                ["cocotb-config", "--python-bin"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding="utf8",
            )
            if result.returncode != 0:
                warn(f"cocotb-config had an unexpected result: {result.stderr}")
            else:
                cocotb_python_bin = result.stdout.strip()
        except FileNotFoundError:
            warn("cocotb-config not found: may fail to run cocotb-based tests")
        Self._cocotb_python_bin = cocotb_python_bin
        return cocotb_python_bin

    def get_command(self, state_in):
        return [
            self.get_cocotb_python_bin(),
            self.get_script_path(),
            "--config",
            self.config_path,
            *[str(model) for model in self.config["CELL_VERILOG_MODELS"]],
        ]

    @abstractmethod
    def get_script_path(self):
        pass

    def run(self, state_in, **kwargs):
        command = self.get_command(state_in)
        subprocess_result = self.run_subprocess(
            command,
            **kwargs,
        )
        generated_metrics = subprocess_result["generated_metrics"]
        return {}, generated_metrics


@Step.factory.register()
class ValidateChain(CocotbStep):
    id = "Difetto.ValidateChain"

    inputs = CocotbStep.inputs + [DesignFormat.chain_yml]

    config_vars = CocotbStep.config_vars + dft_pin_vars

    def get_command(self, state_in):
        return super().get_command(state_in) + [
            "--chain-yml",
            str(state_in[DesignFormat.chain_yml]),
            str(state_in[DesignFormat.nl]),
        ]

    def get_script_path(self):
        return os.path.join(__file_dir__, "scripts", "cocotb", "validate_chain.py")
