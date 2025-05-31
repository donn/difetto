/*
    Difetto Yosys Plugin
    
    Copyright (C) 2025 Mohamed Gaber <me@donn.website>

    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 3 of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program; if not, write to the Free Software Foundation,
    Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/

#include "json11.hpp"
#include "difetto_pass.h"
#include "kernel/modtools.h"
#include <fstream>

USING_YOSYS_NAMESPACE

struct BoundaryScanPass : public DifettoPass {
  BoundaryScanPass()
      : DifettoPass("boundary_scan", "adds boundary scan to selection") {}
  
  const std::map<std::string, Arg> args = {
    {"test_mode", Arg{"Name of wire (port or otherwise) to be used as the test mode select. Prefix with ! to invert.", "wire", true}},
    {"clock", Arg{"Name of wire (port or otherwise) to be used as the clock for the boundary scan registers. Prefix with ! for negative edge.", "wire", true}},
    // {"macro", Arg{"Macro instances to also add boundary scan around. To ignore certain ports, pass them as \"-exclude_io instance_name/port_name\"", "instance", true}},
    {"exclude_io", Arg{"Top-level pins to ignore. The clock and test_mode wires will always be added to this list.", "io", false, true}},
  };
  const std::string description = "Creates boundary scan Yosys primitives for "
    "inputs and outputs. ";
  
  virtual const std::map<std::string, Arg>& get_args() override { return args; }
  virtual std::string_view get_description() override { return description; }
  
  void boundary_scan(RTLIL::Module *module, std::string test_mode_wire_name_raw, std::string clock_wire_name_raw, const dict<IdString, bool>& exclusions) {
    // Resolve target wires
    IdString test_mode_wire_id;
    RTLIL::Wire *test_mode_wire = nullptr;
    bool test_inverted = false;
    resolve_wire(test_mode_wire_name_raw, module, test_mode_wire_id, test_mode_wire, test_inverted);

    IdString clock_wire_id;
    RTLIL::Wire *clock_wire = nullptr;
    bool clock_negedge = false;
    resolve_wire(clock_wire_name_raw, module, clock_wire_id, clock_wire, clock_negedge);
    
    // Collect IOs
    vector<RTLIL::Wire*> inputs, outputs;
    for (auto [id, wire]: module->wires_) {
      if (exclusions.count(id)) {
        continue;
      } 
      if (wire->port_output) {
        outputs.push_back(wire);
      } else if (wire->port_input) {
        inputs.push_back(wire);
      }
    }
    
    for (auto resolved_input: inputs) {
      // rename old wire
      auto input_id = resolved_input->name;
      
      std::string resolved_name = input_id.str() + ".resolved";
      IdString resolved_id(resolved_name);
      module->rename(resolved_input, resolved_id);
      resolved_input->port_input = false;
      
      // create stored value
      std::string stored_name = input_id.str() + ".ibsr_out";
      IdString stored_id(stored_name);
      auto stored = module->addWire(stored_id, resolved_input);
      
      // create new input
      auto input = module->addWire(input_id, resolved_input);
      input->port_input = true;
      
      // multiplex true input with stored value
      std::string mux_name = input_id.str() + ".ibsr_mux";
      IdString mux_id(mux_name);
      auto muxed_spec = module->Mux(
        mux_id,
        test_inverted ? SigSpec(stored): SigSpec(input),
        test_inverted ? SigSpec(input) : SigSpec(stored),
        test_mode_wire
      );
      module->connect(resolved_input, muxed_spec);
      
      // create bsr
      std::string bsr_name = input_id.str() + ".ibsr";
      IdString bsr_id(bsr_name);
      module->addDff(
        bsr_id,
        clock_wire,
        SigSpec(resolved_input),
        SigSpec(stored),
        !clock_negedge
      );
    }
    
    for (auto output: outputs) {
      // Create dummy wire for stored value
      std::string stored_name = output->name.str() + ".obsr_out";
      IdString stored_id(stored_name);
      auto stored = module->addWire(stored_id, output);
      stored->port_output = false;
      
      // Prevent opt passes from pruning wire and driving dff
      stored->set_bool_attribute(ID(keep), true);
      
      // Create dummy 
      std::string bsr_name = output->name.str() + ".obsr";
      IdString bsr_id(bsr_name);
      module->addDff(
        bsr_id,
        clock_wire,
        SigSpec(output),
        SigSpec(stored),
        !clock_negedge
      );
      
    }
    module->fixup_ports();
  }
  
  virtual void execute(std::vector<std::string> args,
                       RTLIL::Design *design) override {
    log_header(design, "Executing BOUNDARY_SCAN pass.\n");
    auto parsed_args = parse_args(args, design);
    
    std::string test_mode_wire_name = parsed_args["test_mode"].at(0);
    std::string clock_wire_name = parsed_args["clock"].at(0);
    pool<std::string> raw_exclusions = {
      test_mode_wire_name,
      clock_wire_name
    };
    for (auto& el: parsed_args["exclude_io"]) {
      raw_exclusions.insert(el);
    }
    auto exclusions = process_exclusions(raw_exclusions);
    
    for (auto module : design->selected_modules()) {
      boundary_scan(module, test_mode_wire_name, clock_wire_name, exclusions);
    }
  }
} BoundaryScanPass;
