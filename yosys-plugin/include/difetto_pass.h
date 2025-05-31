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
#pragma once

#include "kernel/yosys.h"
#include <optional>

struct DifettoPass: public Yosys::Pass {
    struct Arg {
        std::string help;
        std::optional<std::string> argument = std::nullopt;
        bool required = false;
        bool multiple = false;
    };
    
    DifettoPass(std::string name, std::string short_help = "** document me **");
    
    void resolve_wire(
        const std::string &target_wire_raw,
        Yosys::RTLIL::Module *module,
        Yosys::IdString &wire_id,
        Yosys::RTLIL::Wire *&wire,
        bool &inverted
    );
    Yosys::dict<Yosys::RTLIL::IdString, bool> process_exclusions(
        const Yosys::pool<std::string>& raw_exclusions
    );
    
    virtual const std::map<std::string, Arg>& get_args() = 0;
    virtual std::string_view get_description() = 0;
    virtual void help() override;
    virtual const std::unordered_map<std::string, std::vector<std::string>> parse_args(std::vector<std::string>& args, Yosys::RTLIL::Design *design);
};
