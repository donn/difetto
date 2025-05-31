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
            syntax << "-" << name << " " << arg.argument->c_str();
            if (arg.multiple) {
                syntax << " [-" << name << " " << arg.argument->c_str() << " [-" << name << " " << arg.argument->c_str() << " [...]]]";
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
        if (arg_definition.multiple && result.find(name) != result.end()) {
            result[name].push_back(args[++argidx]);
        } else {
            result[name] = {args[++argidx]};
        }        
        continue;
      }
      break;
    }
    
    extra_args(args, argidx, design);
    return result;
}
