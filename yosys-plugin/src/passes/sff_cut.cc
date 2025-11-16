// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2025 Mohamed Gaber
#include "difetto_pass.h"
#include "json11.hpp"
#include "kernel/modtools.h"
#include <fstream>

USING_YOSYS_NAMESPACE

struct SDFFCutPass : public DifettoPass {
	SDFFCutPass() : DifettoPass("sdff_cut", "create cutaway netlist for ATPG") {}

	const dict<std::string, Arg> args = {
	  {"liberty", Arg{"Liberty files containing definitions of scan cells.", "filename", false, true}},
	  {"json_mapping", Arg{"The JSON mapping file.", "filename"}},
	  {"test_mode", Arg{"Available for consistency with other commands, ignored.", "wire", true}},
	  {"clock", Arg{"Available for consistency with other commands, ignored.", "wire", true}},
	  {"macro", Arg{"Macro instances to also cut away and treat as a series of inputs and outputs to the circuit.", "instance", false, true}},
	  {"exclude_io", Arg{"Ports to omit as inputs/outputs to the cutaway circuit, in the format <port_name> for top-level ports and "
			     "<macro_instance>/<macro_port>. Will be coerced low in the final netlist assuming they're still consumed by anything, "
			     "but you may prefix them with ! to coerce them high instead.",
			     "io", false, true}},
	};
	const std::string description = "From a netlist with scannable flipflops, "
					"this pass creates a so-called cutaway netlist for automatic test "
					"pattern "
					"generation, i.e., each scannable flip-flop will be replaced by an "
					"input/output pair.\n \n"
					"This requires you to have kept the _difetto_ibsr parameterized "
					"modules "
					"from the boundary_scan pass intact and emitted with attributes (so"
					"the hdlname may be detected.)\n \n"
					"Intended to be run on the final netlist immediately before PnR. Do "
					"note "
					"that you should not pass this input on to PnR and you should pass "
					"the true"
					"netlist instead.";

	virtual const dict<std::string, Arg> &get_args() override { return args; }
	virtual std::string_view get_description() override { return description; }

	void sdff_cut(Design *design, Module *module_, const pool<IdString> &macros, const dict<IdString, dict<IdString, bool>> &exclusions,
		      pool<IdString> &scan_flops)
	{
		if (module_->has_attribute(ID(no_boundary_scan))) {
			if (module_->get_bool_attribute(ID(no_boundary_scan))) {
				return;
			}
		}
		ModWalker mw(module_->design, module_);

		// Collect and destroy excluded IOs
		vector<Wire *> inputs, outputs;
		for (auto [id, wire] : module_->wires_) {
			if (wire->port_output) {
				outputs.push_back(wire);
			} else if (wire->port_input) {
				inputs.push_back(wire);
			}
		}

		IdString empty;
		if (exclusions.count(IdString())) {
			const dict<IdString, bool> *top_exclusions = &exclusions.at(IdString());
			for (auto input : inputs) {
				if (!top_exclusions->count(input->name)) {
					continue;
				}
				// de-input and coerce
				input->port_input = false;

				Const coerced_constant(top_exclusions->at(input->name) ? State::S1 : State::S0, input->width);
				module_->connect(input, coerced_constant);
			}

			for (auto output : outputs) {
				if (!top_exclusions->count(output->name)) {
					continue;
				}
				output->port_output = false;
			}
			module_->fixup_ports();
		}

		// Handle BSRs
		for (auto [id, cell] : module_->cells_) {
			if (!design->modules_.count(cell->type)) {
				continue;
			}
			auto target_module = design->modules_[cell->type];
			if ((target_module->has_attribute(ID(hdlname)) && target_module->get_string_attribute(ID(hdlname)) == "_difetto_ibsr") ||
			    target_module->name == ID(_difetto_ibsr)) {
				log_debug("identified difetto input bsr %s, shorting "
					  "D to Q...\n",
					  cell->name.c_str());
				cell->setParam(ID(WIDTH), cell->getPort(ID(D)).bits().size());
				cell->type = ID(_difetto_ibsr_dummy);
			}
			if ((target_module->has_attribute(ID(hdlname)) && target_module->get_string_attribute(ID(hdlname)) == "_difetto_obsr") ||
			    target_module->name == ID(_difetto_obsr)) {
				log_debug("identified difetto output bsr %s, shorting "
					  "D to Q...\n",
					  cell->name.c_str());
				cell->setParam(ID(WIDTH), cell->getPort(ID(D)).bits().size());
				cell->type = ID(_difetto_obsr_dummy);
			}
		}

		// Cut remaining scanflops
		vector<Cell *> marked;
		for (auto pair : module_->cells_) {
			auto [instance_name, instance] = pair;
			if (scan_flops.count(instance->type) == 0) {
				continue;
			}
			marked.push_back(instance);
			auto d_spec = instance->getPort(IdString("\\D"));
			auto q_spec = instance->getPort(IdString("\\Q"));
			std::string bsr_name = instance_name.str();
			IdString q(bsr_name + ".q");
			IdString d(bsr_name + ".d");
			Wire *q_port = module_->addWire(q, 1);
			q_port->port_input = true;
			Wire *d_port = module_->addWire(d, 1);
			d_port->port_output = true;
			module_->connect(d_port, d_spec);
			module_->connect(q_spec, q_port);
		}
		// Cut macros
		for (auto macro : macros) {
			log_debug("macro %s\n", macro.c_str());
			auto macro_cell = module_->cell(macro);
			if (!macro_cell) {
				log_error("No cell with instance name %s found.\n", macro.c_str());
			}
			marked.push_back(macro_cell);

			auto macro_module = design->module(macro_cell->type);
			if (!macro_module) {
				log_error("Macro %s's type %s has no definition.\n", macro.c_str(), macro_cell->type.c_str());
			}

			// remove at very end
			const dict<IdString, bool> *current_exclusions = nullptr;
			if (exclusions.count(macro)) {
				current_exclusions = &exclusions.at(macro);
			}
			for (const auto &[port_name, port_sigspec] : macro_cell->connections_) {
				std::stringstream bsr_name;
				bsr_name << "\\" << macro.c_str() + 1 << "/" << port_name.c_str() + 1;
				auto port_info = macro_module->wires_[port_name];
				// remember: an output from a macro is an input to our circuit
				// and vice versa.
				if (current_exclusions && current_exclusions->count(port_name)) {
					auto inverted = current_exclusions->at(port_name);
					if (port_info->port_input) {
						// no one will shed a tear for them when the macro's
						// gone.
					} else if (port_info->port_output) {
						log_debug("Coerced signal from %s to %s\n", bsr_name.str().c_str(), inverted ? "HI" : "LO");
						Const coerced_constant(inverted ? State::S1 : State::S0, port_sigspec.size());
						module_->connect(port_sigspec, coerced_constant);
					}
				} else if (port_info->port_output) {
					auto replacement_input = module_->addWire(bsr_name.str(), port_sigspec.size());
					replacement_input->port_input = true;
					module_->connect(port_sigspec, replacement_input);
				} else if (port_info->port_input) {
					auto replacement_output = module_->addWire(bsr_name.str(), port_sigspec.size());
					replacement_output->port_output = true;
					module_->connect(replacement_output, port_sigspec);
				}
			}
		}

		// Final cleanup
		for (auto cell : marked) {
			log_debug("removing %s\n", cell->name.c_str());
			module_->remove(cell);
		}

		module_->fixup_ports();
	}

	virtual void execute(std::vector<std::string> args, Design *design) override
	{
		log_header(design, "Executing SDFF_CUT pass.\n");
		log_push();

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

		pool<IdString> scanflops;
		for (auto &pair : json["mapping"].object_items()) {
			scanflops.insert(IdString(std::string("\\") + pair.second.string_value()));
		}

		pool<std::string> raw_exclusions{};
		for (auto &el : parsed_args["exclude_io"]) {
			raw_exclusions.insert(el);
		}
		auto exclusions = process_exclusions(raw_exclusions);

		pool<IdString> macros;
		for (const auto &macro_raw : parsed_args["macro"]) {
			macros.insert("\\"s + macro_raw);
		}

		auto bsr_idstring = ID(_difetto_bsr);
		if (design->modules_.count(bsr_idstring) == 0) {
			load_ibsr_definitions(design);
		}

		for (auto module : design->selected_modules()) {
			sdff_cut(design, module, macros, exclusions, scanflops);
		}

		Pass::call(design, "hierarchy");
		Pass::call(design, "flatten");
		log_pop();
	}
} SDFFCutPass;
