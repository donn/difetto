# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2025 Mohamed Gaber
from librelane.flows import Flow, SequentialFlow
from . import steps as Difetto


@Flow.factory.register()
class DifettoPNR(Flow.factory.get("Classic")):
    Substitutions = [
        ("Yosys.Synthesis", "Difetto.Synthesis"),
        ("+Difetto.Synthesis", "Difetto.BoundaryScan"),
        ("+Difetto.BoundaryScan", "Difetto.Resynthesis"),
        ("+Difetto.Resynthesis", "Difetto.ScanReplace"),
        ("+Difetto.ScanReplace", "Difetto.Cut"),
        ("-OpenROAD.CTS", "Difetto.Chain"),
        (
            "+Difetto.Chain",
            "OpenROAD.RepairDesign",
        ),  # SCE has |scannable_element_count| fanout
    ]


@Flow.factory.register()
class DifettoPNRNoChain(DifettoPNR):
    """
    For benchmarking
    """

    Substitutions = [
        ("Difetto.Chain", None),
        ("OpenROAD.RepairDesign", None),
        ("Checker.DisconnectedPins", None),
    ]


@Flow.factory.register()
class DifettoPNRTopologicalChain(DifettoPNRNoChain):
    """
    For benchmarking
    """

    Substitutions = [("+Difetto.Cut", "Difetto.TopologicalChain")]


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
