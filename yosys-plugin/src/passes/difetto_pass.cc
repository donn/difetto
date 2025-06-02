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

#include "difetto_pass.h"
#include "bsr_info.h"
#include "TextFlow.hpp"

USING_YOSYS_NAMESPACE

DifettoPass::DifettoPass(std::string name, std::string short_help): Pass(name, short_help) {}

void DifettoPass::help() {
    log("\n");
    log("    %s\n", pass_name.c_str());
    
    log("\n");
    auto desc_column = TextFlow::Column(get_description()).width(80).indent(4);
    for (auto line: desc_column) {
        log("%s\n", line.c_str());
    }
    
    log("\n");
    for (auto& [name, arg]: get_args()) {
        std::stringstream syntax;
        if (arg.argument.has_value()) {
            if (!arg.required) {
                syntax << "[";
            } 
            syntax << "-" << name << " " << arg.argument->c_str();
            if (arg.multiple) {
                syntax << " [-" << name << " " << arg.argument->c_str() << " [-" << name << " " << arg.argument->c_str() << " [...]]]";
            }
            if (!arg.required) {
                syntax << "]";
            } 
        } else {
            syntax << "-" << name;
        }
        std::string syntax_str = syntax.str();
        auto syntax_column = TextFlow::Column(syntax_str).width(80).indent(4);
        for (auto line: syntax_column) {
            log("%s\n", line.c_str());
        }
        
        log("\n");
        auto help_column = TextFlow::Column(arg.help).width(80).indent(8);
        for (auto line: help_column) {
            log("%s\n", line.c_str());
        }
        log("\n");
    }
}

const std::unordered_map<std::string, std::vector<std::string>> DifettoPass::parse_args(std::vector<std::string>& args, RTLIL::Design *design) {
    size_t argidx;
    auto arg_definitions = get_args();
    pool<std::string> remaining_required_args;
    
    for (auto& [name, arg]: arg_definitions) {
        if (arg.required) {
            remaining_required_args.insert(name);
        }
    }
    
    std::unordered_map<std::string, std::vector<std::string>> result;
    
    for (argidx = 1; argidx < args.size(); argidx++) {
      std::string arg = args[argidx];
      if (arg[0] == '-') {
        std::string name { arg.c_str() + 1 };
        auto found = arg_definitions.find(name);
        if (found == arg_definitions.end()) {
            log_cmd_error("Unknown option %s provided.\n", arg.c_str());
        }
        auto& [_, arg_definition] = *found;
        if (!arg_definition.argument.has_value()) {
            result[name] = {"SET"};
            continue;
        }
        if (argidx + 1 >= args.size()) {
            log_cmd_error("Option %s requires an argument.\n", arg.c_str());
        }
        if (remaining_required_args.count(name)) {
            remaining_required_args.erase(name);
        }
        if (arg_definition.multiple && result.find(name) != result.end()) {
            result[name].push_back(args[++argidx]);
        } else {
            result[name] = {args[++argidx]};
        }        
        continue;
      }
      break;
    }
    
    if (remaining_required_args.size()) {
        auto any = remaining_required_args.pop();
        log_cmd_error("Option %s requires an argument.\n", any.c_str());
    }
    
    extra_args(args, argidx, design);
    return result;
}

void DifettoPass::resolve_wire(
    const std::string &target_wire_raw,
    Yosys::RTLIL::Module *module,
    IdString &wire_id,
    Yosys::RTLIL::Wire *&wire,
    bool &inverted
) {
    const char *wire_name = target_wire_raw.c_str();
    inverted = false;
    if (wire_name[0] == '!') {
      inverted = true;
      wire_name++;
    }
    wire_id = IdString(std::string("\\") + wire_name);
    if (module) {   
        if (module->wires_.count(wire_id) == 0) {
            log_error("No wire %s found in module %s.\n", wire_id.c_str(), module->name.c_str());
        }
        wire = module->wires_[wire_id];
    }
}

dict<IdString, bool> DifettoPass::process_exclusions(const pool<std::string>& raw_exclusions) {
    dict<IdString, bool> result;
    for (size_t i = 0; i < raw_exclusions.size(); i += 1) {
        auto &wire = *raw_exclusions.element(i);
        IdString id;
        Wire *dont_care = nullptr;
        bool inverted;
        resolve_wire(wire, nullptr, id, dont_care, inverted);
        result[id] = inverted;
    }
    return result;
}

void DifettoPass::load_ibsr_definitions(Yosys::RTLIL::Design *design) {
    using namespace std::filesystem;
    path temp_dir = temp_directory_path();
    path difetto_temp = temp_dir / "difetto";
    if (!exists(difetto_temp) && !create_directories(difetto_temp)) {
    log_error("Could not create temporary directory: %s", difetto_temp.c_str());
    }
    path bsr_temp = difetto_temp / "bsr.v";
    std::ofstream outpath(bsr_temp);
    if (outpath.fail()) {
    log_error("Could not open temporary file for writing: %s", bsr_temp.c_str());
    }
    std::string_view bsr_v_view((const char*)src_bsr_v, src_bsr_v_len);
    outpath << bsr_v_view;
    outpath.close();
    Pass::call(design, {"read_verilog", "-icells", bsr_temp});
    remove(bsr_temp);
}
