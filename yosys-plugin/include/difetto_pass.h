#pragma once

#include "kernel/yosys.h"
#include <optional>

struct DifettoPass: public Yosys::Pass {
    struct Arg {
        std::string help;
        std::optional<std::string> argument = std::nullopt;
        bool multiple = false;
    };
    
    DifettoPass(std::string name, std::string short_help = "** document me **");
    
    virtual const std::map<std::string, Arg>& get_args() = 0;
    virtual std::string_view get_description() = 0;
    
    virtual void help() override;
    virtual const std::unordered_map<std::string, std::vector<std::string>> parse_args(std::vector<std::string>& args, Yosys::RTLIL::Design *design);
};
