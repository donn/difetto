# Copyright 2021-2022 Efabless Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# flake8: noqa E402
import odb
from openroad import Tech, Design

import re
import sys
import json
import locale
import inspect
from functools import wraps
from decimal import Decimal
from fnmatch import fnmatch
from typing import Callable, Dict

# -- START: Environment Fixes
try:
    locale.setlocale(locale.LC_ALL, "C.UTF-8")
except locale.Error:
    # We tried. :)
    pass
# -- END


class OdbReader(object):
    def __init__(self, *args, **kwargs):
        self.ord_tech = Tech()
        self.design = Design(self.ord_tech)

        if len(args) == 1:
            db_in = args[0]
            self.design.readDb(db_in)
        elif len(args) == 2:
            lef_in, def_in = args
            if not (isinstance(lef_in, list) or isinstance(lef_in, tuple)):
                lef_in = [lef_in]
            for lef in lef_in:
                self.ord_tech.readLef(lef)
            if def_in is not None:
                self.design.readDef(def_in)

        self.config = None
        if "config_path" in kwargs and kwargs["config_path"] is not None:
            self.config = json.load(
                open(kwargs["config_path"], encoding="utf8"),
                parse_float=Decimal,
            )

        self.db = self.ord_tech.getDB()
        self.tech = self.db.getTech()
        self.chip = self.db.getChip()
        self.layers = {l.getName(): l for l in self.tech.getLayers()}
        self.libs = self.db.getLibs()
        self.cells = {}
        for lib in self.libs:
            self.cells.update({m: m for m in lib.getMasters()})
        if self.chip is not None:
            self.block = self.db.getChip().getBlock()
            self.name = self.block.getName()
            self.rows = self.block.getRows()
            self.dbunits = self.block.getDefUnits()
            self.instances = self.block.getInsts()

        busbitchars = re.escape("[]")  # TODO: Get alternatives from LEF parser
        # dividerchar = re.escape("/")  # TODO: Get alternatives from LEF parser
        self.escape_verilog_rx = re.compile(rf"([{busbitchars}])")

    def add_lef(self, new_lef):
        self.ord_tech.readLef(new_lef)

    def escape_verilog_name(self, name_in: str) -> str:
        return self.escape_verilog_rx.sub(r"\\\1", name_in)
