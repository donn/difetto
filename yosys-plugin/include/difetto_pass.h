// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2025 Mohamed Gaber
#pragma once

#include "kernel/yosys.h"
#include <filesystem>
#include <optional>

struct DifettoPass : public Yosys::Pass {
	struct Arg {
		std::string help;
		std::optional<std::string> argument = std::nullopt;
		bool required = false;
		bool multiple = false;
	};

	DifettoPass(std::string name, std::string short_help = "** document me **");

	void resolve_wire(const std::string &target_wire_raw, Yosys::RTLIL::Module *module, Yosys::IdString &wire_id, Yosys::RTLIL::Wire *&wire,
			  bool &inverted);
	Yosys::dict<Yosys::RTLIL::IdString, bool> process_exclusions(const Yosys::pool<std::string> &raw_exclusions);
	void load_ibsr_definitions(Yosys::RTLIL::Design *design);

	virtual const Yosys::dict<std::string, Arg> &get_args() = 0;
	virtual std::string_view get_description() = 0;
	virtual void help() override;
	virtual const Yosys::dict<std::string, Yosys::vector<std::string>> parse_args(Yosys::vector<std::string> &args, Yosys::RTLIL::Design *design);
};
