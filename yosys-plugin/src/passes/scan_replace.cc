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
#include "json11.hpp"
#include "kernel/modtools.h"
#include <fstream>

USING_YOSYS_NAMESPACE

struct ScanReplacePass : public DifettoPass {
	ScanReplacePass() : DifettoPass("scan_replace", "replaces flip-flops with scannable flip-flops") {}

	const dict<std::string, Arg> args = {{"liberty", Arg{"Liberty files containing replacement scan cells.", "filename", false, true}},
					     {"json_mapping", Arg{"The JSON mapping file.", "filename"}}};
	const std::string description = "Replaces standard flip-flops with scannable"
					"flip-flops. The scannable flip-flops can either be obtained from a "
					"liberty "
					"file (unimplemented) or from a JSON mapping file.\n \n" // there's a
												 // bug with
												 // consecutive
												 // \n in
												 // TextFlow
					"Cells marked no_scan, as well as cells driving wires marked no_scan "
					"will "
					"not be affected by scan_replace.\n \n"
					"It is intended that you run this pass after the final abc "
					"technology "
					"mapping.";

	virtual const dict<std::string, Arg> &get_args() override { return args; }
	virtual std::string_view get_description() override { return description; }

	void scan_replace(Module *module, dict<IdString, IdString> &mapping)
	{
		if (module->has_attribute(ID(no_scan))) {
			if (module->get_bool_attribute(ID(no_scan))) {
				return;
			}
		}

		ModWalker mw(module->design, module);

		for (auto pair : module->cells_) {
			auto cell = pair.second;
			auto counterpart = mapping[cell->type];
			if (counterpart.empty()) {
				continue;
			}

			// check if cell proper (if declared) has no_scan
			if (cell->get_bool_attribute(ID(no_scan))) {
				log("Skipping %s (cell has no_scan "
				    "attribute)...\n",
				    pair.first.c_str());
				continue;
			}

			// check if any outputs have no_scan
			auto output_bits = mw.cell_outputs[cell];
			bool no_scan_found = false;
			for (auto bit : output_bits) {
				auto wire = bit.wire;
				if (wire->get_bool_attribute(ID(no_scan))) {
					no_scan_found = true;
					break;
				}
			}
			if (no_scan_found) {
				log("Skipping %s (connected to no_scan "
				    "output)...\n",
				    pair.first.c_str());
				continue;
			}

			auto scannable = mapping[cell->type];
			log("%s: %s -> %s\n", pair.first.c_str(), cell->type.c_str(), scannable.c_str());
			cell->type = scannable;
		}
	}

	virtual void execute(std::vector<std::string> args, Design *design) override
	{
		log_header(design, "Executing SCAN_REPLACE pass.\n");
		auto parsed_args = parse_args(args, design);

		if (!parsed_args.count("json_mapping")) {
			if (!parsed_args.count("liberty")) {
				log_cmd_error("One of `-json_mapping "
					      "mapping_json' and `-liberty "
					      "liberty_file' are required!\n");
			} else {
				log_cmd_error("`-liberty liberty_file' option "
					      "is currently unsupported.\n");
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
			log_error("Failed to parse `%s`: %s\n", mapping_json.c_str(), err.c_str());

		dict<IdString, IdString> mapping;
		for (auto &pair : json["mapping"].object_items()) {
			mapping[IdString(std::string("\\") + pair.first)] = IdString(std::string("\\") + pair.second.string_value());
		}

		for (auto module : design->selected_modules()) {
			scan_replace(module, mapping);
		}
	}
} ScanReplacePass;
