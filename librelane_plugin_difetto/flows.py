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
    ]


@Flow.factory.register()
class DifettoATPG(SequentialFlow):
    Steps = [Difetto.WriteBench, Difetto.QuaighATPG, Difetto.QuaighSim]


@Flow.factory.register()
class DifettoTest(SequentialFlow):
    Steps = [Difetto.ValidateChain]
