# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Mohamed Gaber
import os
import subprocess
from abc import abstractmethod
from librelane.steps import Step, StepException
from librelane.steps.tclstep import TclStep
from librelane.steps.pyosys import PyosysStep
from librelane.steps.openroad import OpenROADStep
from librelane.state import DesignFormat
from librelane.config import Variable
from librelane.common import Path, get_script_dir, process_list_file
from librelane.logging import warn

from typing import ClassVar, List, Literal, Optional, Set

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
        out_type = self.outputs[0]
        out_file = os.path.join(
            self.step_dir,
            f"{self.config['DESIGN_NAME']}.{out_type.extension}",
        )
        cmd = super().get_command(state_in)
        return cmd + ["--output", out_file, state_in[DesignFormat.nl]]

    def run(self, state_in, **kwargs):
        kwargs, env = self.extract_env(kwargs)
        env["PYTHONPATH"] = os.path.join(get_script_dir(), "pyosys")
        scl_lib_list = self.toolbox.filter_views(
            self.config, self.config["LIB"], self.config.get("SYNTH_CORNER")
        )
        excluded_cells: Set[str] = set(self.config["EXTRA_EXCLUDED_CELLS"] or [])
        excluded_cells.update(
            process_list_file(self.config["SYNTH_EXCLUDED_CELL_FILE"])
        )
        excluded_cells.update(process_list_file(self.config["PNR_EXCLUDED_CELL_FILE"]))
        libs_synth = self.toolbox.remove_cells_from_lib(
            frozenset([str(lib) for lib in scl_lib_list]),
            excluded_cells=frozenset(excluded_cells),
        )
        env["_libs_synth"] = TclStep.value_to_tcl(libs_synth)
        state_out, metrics = super().run(state_in, env=env, **kwargs)
        out_type = self.outputs[0]
        state_out[out_type] = Path(
            os.path.join(
                self.step_dir,
                f"{self.config['DESIGN_NAME']}.{out_type.extension}",
            )
        )
        return state_out, metrics


@Step.factory.register()
class BoundaryScan(DFTCommon):
    """
    Uses Yosys with the Difetto plugin to create boundary scan registers
    on all inputs and outputs (except excluded IOs.)

    These registers allow for controlling inputs and capturing outputs as part
    of the scan chain.
    """

    id = "Difetto.BoundaryScan"
    name = "Create Boundary Scan Flip-flops"

    config_vars = DFTCommon.config_vars + dft_pin_vars

    def get_script_path(self):
        return os.path.join(__file_dir__, "scripts", "pyosys", "boundary_scan.py")


@Step.factory.register()
class ScanReplace(DFTCommon):
    """
    Uses Yosys with the Difetto plugin to replace flip-flops in the desired
    module with scannable versions. The scan chain is not created yet.
    """

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
class Cut(DFTCommon):
    """
    Uses Yosys with the Difetto plugin to create a combinational "cut-away"
    netlist that can be used with automatic test pattern generation (ATPG)
    tools.

    Excluded IOs are coerced to high (or low if prefixed with !.)
    """

    id = "Difetto.Cut"
    name = "Create Cutaway Netlist"

    inputs = [DesignFormat.nl]
    outputs = [DesignFormat.cut_nl]

    config_vars = DFTCommon.config_vars + dft_pin_vars

    def get_script_path(self):
        return os.path.join(__file_dir__, "scripts", "pyosys", "cut.py")


DesignFormat("bench", "bench", "DFT Bench Format").register()


@Step.factory.register()
class WriteBench(Step):
    """
    Converts cutaway combinational netlists into the BENCH format popular with
    academic ATPG utilities using a tool named nl2bench.
    """

    id = "Difetto.WriteBench"
    name = "Write Cutaway Netlist in BENCH format"

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
    """
    Performs analytic automatic test pattern generation using Quaigh to produce
    test vectors in the port order of inputs in cutaway netlists.
    """

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
    """
    Analytically simulates test patterns using Quaigh to generate expected
    "golden" outputs in the port order of inputs in cutaway netlists.
    """

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
    """
    Uses OpenROAD to create scan chain(s) between registers.

    Currently only one scan chain is supported.

    The chain's instance order is dumped into a YAML file.
    """

    id = "Difetto.Chain"
    name = "Create Scan Chain(s)"

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
            "--step-dir",
            self.step_dir,
            "--config",
            self.config_path,
            *[str(model) for model in self.config["CELL_VERILOG_MODELS"]],
        ]

    @abstractmethod
    def get_script_path(self):
        pass

    def run(self, state_in, **kwargs):
        command = self.get_command(state_in)
        kwargs, env = self.extract_env(kwargs)
        subprocess_result = self.run_subprocess(
            command,
            **kwargs,
            env=env,
        )
        generated_metrics = subprocess_result["generated_metrics"]
        return {}, generated_metrics


@Step.factory.register()
class ValidateChain(CocotbStep):
    """
    Uses Cocotb to validate a netlist with a scan-chain.
    """

    name = "Validate Scan Chain (with Cocotb)"
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


DesignFormat(
    "tvs",
    "tvs.bin",
    "Test Vectors (Binary Format)",
).register()

DesignFormat(
    "au",
    "au.bin",
    "Test Vector Golden Output (Binary Format)",
).register()

DesignFormat(
    "mask",
    "mask.bin",
    "Golden Output Mask (Binary Format)",
).register()


@Step.factory.register()
class AssemblePatterns(PyosysStep):
    """
    Uses Yosys, the chain YAML file, the cutaway netlist, and raw test vectors
    to generate:
    - Test Vectors
    - Expected (Golden) Outputs
    - Output Mask

    …all based on the order of the chain. The mask excludes uncontrollable bits
    such as input boundary scan registers.
    """

    id = "Difetto.AssemblePatterns"
    name = "Test Pattern Assembly"

    inputs = [
        DesignFormat.cut_nl,
        DesignFormat.chain_yml,
        DesignFormat.raw_au,
        DesignFormat.raw_tvs,
    ]
    outputs = [DesignFormat.au, DesignFormat.tvs, DesignFormat.mask]

    def get_script_path(self):
        return os.path.join(__file_dir__, "scripts", "pyosys", "assemble.py")

    def get_command(self, state_in) -> List[str]:
        out_pfx = os.path.join(
            self.step_dir,
            f"{self.config['DESIGN_NAME']}",
        )

        cmd = super().get_command(state_in)
        for input in self.inputs:
            cmd.extend(["--" + input.id.replace("_", "-"), str(state_in[input])])
        for output in self.outputs:
            cmd.extend(
                [
                    "--" + output.id.replace("_", "-") + "-out",
                    f"{out_pfx}.{output.extension}",
                ]
            )

        cmd.remove("--cut-nl")

        return cmd

    def run(self, state_in, **kwargs):
        kwargs, env = self.extract_env(kwargs)
        env["PYTHONPATH"] = os.path.join(get_script_dir(), "pyosys")
        state_out, metrics = super().run(state_in, env=env, **kwargs)
        out_pfx = os.path.join(
            self.step_dir,
            f"{self.config['DESIGN_NAME']}",
        )
        state_out[DesignFormat.au] = Path(f"{out_pfx}.{DesignFormat.au.extension}")
        state_out[DesignFormat.tvs] = Path(f"{out_pfx}.{DesignFormat.tvs.extension}")
        state_out[DesignFormat.mask] = Path(f"{out_pfx}.{DesignFormat.mask.extension}")
        return state_out, metrics


@Step.factory.register()
class SimulateTestVectors(CocotbStep):
    """
    The "finale" - uses all data from all three flows to:

    - Feed in a test vector to the scan chain
    - Wait one cycle
    - Scan out
    - Compare the output with the expected output
    """

    id = "Difetto.SimulateTestVectors"
    name = "Simulate Test Vectors"

    inputs = CocotbStep.inputs + [DesignFormat.au, DesignFormat.tvs, DesignFormat.mask]

    config_vars = CocotbStep.config_vars + dft_pin_vars

    def get_command(self, state_in):
        return super().get_command(state_in) + [
            "--tvs",
            str(state_in[DesignFormat.tvs]),
            "--mask",
            str(state_in[DesignFormat.mask]),
            "--au",
            str(state_in[DesignFormat.au]),
            str(state_in[DesignFormat.nl]),
        ]

    def get_script_path(self):
        return os.path.join(__file_dir__, "scripts", "cocotb", "run_tvs.py")
