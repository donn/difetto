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

struct SDFFCutPass : public DifettoPass {
  SDFFCutPass()
      : DifettoPass("sdff_cut", "create cutaway netlist for ATPG") {}
  
  const std::map<std::string, Arg> args = {
    {"liberty", Arg{"Liberty files containing definitions of scan cells.", "filename", false, true}},
    {"json_mapping", Arg{"The JSON mapping file.", "filename"}},
    {"test_mode", Arg{"Name of wire (port or otherwise) to be used as the test mode select.", "wire", true}},
    {"clock", Arg{"Name of wire (port or otherwise) to be used as the clock for the boundary scan registers. Prefix with ! for negative edge.", "wire", true}},
    // {"macro", Arg{"Macro instances to also add boundary scan around. To ignore certain ports, pass them as \"-exclude_io instance_name/port_name\"", "instance", true}},
    {"exclude_io", Arg{"Top-level pins to ignore. The clock and test_mode wires will always be added to this list. Inputs will be coerced low for the purposes of the cut netlist unless prefixed with !, which will be coerced high.", "io", false, true}},
  };
  const std::string description = "\n";
  
  virtual const std::map<std::string, Arg>& get_args() override { return args; }
  virtual std::string_view get_description() override { return description; }

  void sdff_cut(RTLIL::Module *module, std::string test_mode_wire_name_raw, std::string clock_wire_name_raw, const dict<IdString, bool>& exclusions, pool<IdString>& scan_flops) {
    ModWalker mw(module->design, module);
    
    // Resolve target wires
    IdString test_mode_wire_id;
    RTLIL::Wire *test_mode_wire = nullptr;
    bool test_inverted = false;
    resolve_wire(test_mode_wire_name_raw, module, test_mode_wire_id, test_mode_wire, test_inverted);

    IdString clock_wire_id;
    RTLIL::Wire *clock_wire = nullptr;
    bool clock_negedge = false;
    resolve_wire(clock_wire_name_raw, module, clock_wire_id, clock_wire, clock_negedge);
    
    // Collect and destroy IOs
    vector<RTLIL::Wire*> inputs, outputs;
    for (auto [id, wire]: module->wires_) {
      if (wire->port_output) {
        outputs.push_back(wire);
      } else if (wire->port_input) {
        inputs.push_back(wire);
      }
    }
    
    for (auto input: inputs) {
      if (!exclusions.count(input->name)) {
        continue;
      }
      // de-input and coerce
      input->port_input = false;
      
      RTLIL::Const coerced_constant(exclusions.at(input->name) ? State::S1 : State::S0, input->width);
      module->connect(input, coerced_constant);
    }
    
    for (auto output: outputs) {
      if (!exclusions.count(output->name)) {
        continue;
      }
      output->port_output = false;
    }
    module->fixup_ports();

    vector<RTLIL::Cell *> marked;
    for (auto pair: module->cells_) {
      auto [instance_name, instance] = pair;
      if (scan_flops.count(instance->type) == 0) {
        continue;
      }
      marked.push_back(instance);
      auto output_bits = mw.cell_outputs[instance];
      std::optional<std::string> io_name;
      std::optional<SigBit> input_bsr;
      std::optional<SigBit> output_bsr;
      for (auto bit: output_bits) {
        auto wire_name = bit.wire->name.str();
        auto ibsr_pos = wire_name.rfind(".ibsr_out");
        if (ibsr_pos != std::string::npos) {
          io_name = bit.wire->name.str();
          io_name->erase(ibsr_pos, std::string::npos);
          input_bsr = bit;
          break;
        }
        auto obsr_pos = wire_name.rfind(".obsr_out");
        if (obsr_pos != std::string::npos) {
          io_name = bit.wire->name.str();
          io_name->erase(obsr_pos, std::string::npos);
          output_bsr = bit;
          break;
        }
      }
      auto d_spec = instance->getPort(IdString("\\D"));
      auto q_spec = instance->getPort(IdString("\\Q"));
      if (input_bsr) {
        log("identified input bsr %s for %s[%i], replacing muxed value with 0...\n", instance_name.c_str(), io_name->c_str(), input_bsr->offset);
        RTLIL::Const coerced_constant(State::S0, q_spec.size());
        module->connect(q_spec, coerced_constant);
      } else if (output_bsr) {
        log("identified output bsr %s for %s[%i], not cutting...\n", instance_name.c_str(), io_name->c_str(), output_bsr->offset);
      } else {
        std::string bsr_name = instance_name.str();
        IdString q(bsr_name + ".q");
        IdString d(bsr_name + ".d");
        RTLIL::Wire *q_port = module->addWire(q, 1);
        q_port->port_input = true;
        RTLIL::Wire *d_port = module->addWire(d, 1);
        d_port->port_output = true;
        module->connect(d_port, d_spec);
        module->connect(q_spec, q_port);
      }
    }
    
    for (auto cell: marked) {
      module->remove(cell);
    }
    
    module->fixup_ports();
  }

  virtual void execute(std::vector<std::string> args,
                       RTLIL::Design *design) override {
    log_header(design, "Executing SDFF_CUT pass.\n");
    auto parsed_args = parse_args(args, design);

    if (parsed_args.find("json_mapping") == parsed_args.end()) {
      if (parsed_args.find("liberty") == parsed_args.end()) {
        log_cmd_error("One of `-json_mapping mapping_json' and `-liberty "
                      "liberty_file' are required!\n");
      } else {
        log_cmd_error(
            "`-liberty liberty_file' option is currently unsupported.\n");
      }
    }
    
    std::string mapping_json = parsed_args["json_mapping"].at(0);

    // std::ifstream f;
    // f.open(liberty_file.c_str());
    // if (f.fail())
    //   log_cmd_error("Can't open liberty file `%s': %s\n",
    //   liberty_file.c_str(),
    //                 strerror(errno));
    // LibertyParser libparser(f);
    // f.close();

    std::ifstream f(mapping_json.c_str());
    if (f.fail())
      log_error("Cannot open file `%s`\n", mapping_json.c_str());
    std::stringstream buf;
    buf << f.rdbuf();
    std::string err;
    json11::Json json = json11::Json::parse(buf.str(), err);
    if (!err.empty())
      log_error("Failed to parse `%s`: %s\n", mapping_json.c_str(),
                err.c_str());
    
    pool<IdString> scanflops;
    for (auto& pair: json["mapping"].object_items()) {
      scanflops.insert(IdString(std::string("\\") + pair.second.string_value()));
    }
    
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
      sdff_cut(module, test_mode_wire_name, clock_wire_name, exclusions, scanflops);
    }
  }
} SDFFCutPass;
