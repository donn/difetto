# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Mohamed Gaber
from librelane.config import Variable
from librelane.flows import Flow, SequentialFlow
from . import steps as Difetto


Classic = Flow.factory.get("Classic")


@Flow.factory.register()
class DifettoPNR(Classic):
    Substitutions = [
        ("Yosys.Synthesis", "Difetto.Synthesis"),
        ("+Difetto.Synthesis", "Difetto.BoundaryScan"),
        ("+Difetto.BoundaryScan", "Difetto.Resynthesis"),
        ("+Difetto.Resynthesis", "Difetto.ScanReplace"),
        ("+Difetto.ScanReplace", "Difetto.Cut"),
        ("+Difetto.Cut", "Difetto.TopologicalChain"),
        ("-OpenROAD.CTS", "Difetto.Chain"),
        (
            "+Difetto.Chain",
            "OpenROAD.RepairDesign",
        ),  # SCE has |scannable_element_count| fanout
        ("+OpenROAD.ResizerTimingPostGRT", "OpenROAD.DumpCongestionHeatmap"),
    ]

    config_vars = Classic.config_vars + [
        Variable(
            "RUN_NL_CHAIN",
            bool,
            "Enables constructing a scan-chain based on the netlist order immediately after synthesis. Mostly for benchmarking, you probably want to keep this one off.",
            default=False,
        ),
        Variable(
            "RUN_PL_CHAIN",
            bool,
            "Enables constructing a chain based on data from the detailed placement.",
            default=True,
        ),
        Variable(
            "RUN_DUMP_CONGESTION_HEATMAP",
            bool,
            "Dumps the congestion heatmap using the OpenROAD GUI, but requires a non-headless environment.",
            default=False,
        ),
    ]

    gating_config_vars = {
        **Classic.gating_config_vars,
        "Difetto.Chain": ["RUN_PL_CHAIN"],
        "Difetto.TopologicalChain": ["RUN_NL_CHAIN"],
        "OpenROAD.DumpCongestionHeatmap": ["RUN_DUMP_CONGESTION_HEATMAP"],
    }


@Flow.factory.register()
class DifettoATPG(SequentialFlow):
    Steps = [Difetto.WriteBench, Difetto.QuaighATPG, Difetto.QuaighSim]


@Flow.factory.register()
class DifettoTest(SequentialFlow):
    Steps = [
        Difetto.AssemblePatterns,
        Difetto.ValidateChain,
        Difetto.SimulateTestVectors,
    ]
