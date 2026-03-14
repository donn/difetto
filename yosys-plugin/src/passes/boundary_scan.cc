// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2025 Mohamed Gaber
#include "bsr_info.h"
#include "difetto_pass.h"
#include "json11.hpp"
#include "kernel/modtools.h"
#include <fstream>

USING_YOSYS_NAMESPACE

struct BoundaryScanPass : public DifettoPass {
	BoundaryScanPass() : DifettoPass("boundary_scan", "adds boundary scan to selection") {}

	const dict<std::string, Arg> args = {
	  {"test_mode", Arg{"Name of wire (port or otherwise) to be used as "
			    "the test mode select. Prefix with ! to invert.",
			    "wire", true}},
	  {"clock", Arg{"Name of wire (port or otherwise) to be used as the clock for "
			"the boundary scan registers. Prefix with ! for negative edge.",
			"wire", true}},
	  {"macro", Arg{"Macro instances to also add boundary scan around.", "instance", false, true}},
	  {"exclude_io", Arg{"Ports to omit boundary scans for, in the format <port_name> for top-level ports and <macro_instance>/<macro_port>. May "
			     "be prefixed with ! for consistency with other commands, but has no effect.",
			     "io", false, true}},
	};

	const std::string description = "Creates boundary scan unmapped Yosys "
					"primitives for inputs and outputs for all selected modules. "
					"Modules with the attribute no_boundary_scan will be skipped.\n \n"
					"Intended to be run after initial hierarchy and optionally "
					"flattening.";

	virtual const dict<std::string, Arg> &get_args() override { return args; }
	virtual std::string_view get_description() override { return description; }

	void boundary_scan(Design *design, Module *module_, std::string test_mode_wire_name_raw, std::string clock_wire_name_raw,
			   const pool<IdString> &macros, const dict<IdString, dict<IdString, bool>> &exclusions)
	{
		if (module_->has_attribute(ID(no_boundary_scan))) {
			if (module_->get_bool_attribute(ID(no_boundary_scan))) {
				return;
			}
		}

		// Resolve target wires
		IdString test_mode_signal_container, test_mode_signal_id;
		SigSpec test_mode_signal;
		bool test_inverted = false;
		resolve_signal(test_mode_wire_name_raw, &test_mode_signal_container, &test_mode_signal_id, &test_inverted, module_,
			       &test_mode_signal);

		IdString clock_signal_container, clock_signal_id;
		SigSpec clock_signal;
		bool clock_negedge = false;
		resolve_signal(clock_wire_name_raw, &clock_signal_container, &clock_signal_id, &clock_negedge, module_, &clock_signal);

		// Handle top-level IOs
		IdString empty;
		const dict<IdString, bool> *top_exclusions = nullptr;
		if (exclusions.count(IdString())) {
			top_exclusions = &exclusions.at(IdString());
		}

		vector<Wire *> inputs, outputs;
		for (auto [id, wire] : module_->wires_) {
			if (top_exclusions && top_exclusions->count(id)) {
				continue;
			}
			if (wire->port_output) {
				outputs.push_back(wire);
			} else if (wire->port_input) {
				inputs.push_back(wire);
			}
		}

		for (auto resolved_input : inputs) {
			// rename old wire
			auto input_id = resolved_input->name;

			std::string resolved_name = input_id.str() + ".resolved";
			IdString resolved_id(resolved_name);
			module_->rename(resolved_input, resolved_id);
			resolved_input->port_input = false;

			// create new input
			auto input = module_->addWire(input_id, resolved_input);
			input->port_input = true;

			// create new ibsr
			std::string bsr_name = input_id.str() + ".ibsr";
			IdString bsr_id(bsr_name);
			auto bsr = module_->addCell(bsr_id, ID(_difetto_ibsr));
			bsr->setParam(ID(WIDTH), resolved_input->width);
			bsr->setParam(ID(CLK_POLARITY), clock_negedge ? Const(State::S0, 1) : Const(State::S1, 1));
			bsr->setParam(ID(TEST_POLARITY), test_inverted ? Const(State::S0, 1) : Const(State::S1, 1));
			bsr->setPort(ID(D), input);
			bsr->setPort(ID(Q), resolved_input);
			bsr->setPort(ID(CLK), clock_signal);
			bsr->setPort(ID(TEST), test_mode_signal);
			bsr->set_bool_attribute(ID(keep), true);
		}

		for (auto output : outputs) {
			auto input_id = output->name;

			std::string bsr_name = input_id.str() + ".obsr";
			IdString bsr_id(bsr_name);

			auto bsr = module_->addCell(bsr_id, ID(_difetto_obsr));
			bsr->setParam(ID(WIDTH), output->width);
			bsr->setParam(ID(CLK_POLARITY), clock_negedge ? Const(State::S0, 1) : Const(State::S1, 1));
			bsr->setPort(ID(D), output);
			bsr->setPort(ID(CLK), clock_signal);
			bsr->set_bool_attribute(ID(keep), true);
		}

		// Handle macros
		for (auto macro : macros) {
			auto macro_cell = module_->cell(macro);
			if (!macro_cell) {
				log_error("No cell with instance name %s found.\n", macro.c_str());
			}

			auto macro_module = design->module(macro_cell->type);
			if (!macro_module) {
				log_error("Macro %s's type %s has no definition.\n", macro.c_str(), macro_cell->type.c_str());
			}

			vector<IdString> inputs, outputs;

			// collect: disconnections will cause connections_ to be rehashed
			const dict<IdString, bool> *current_exclusions = nullptr;
			if (exclusions.count(macro)) {
				current_exclusions = &exclusions.at(macro);
			}
			for (const auto &[port_name, port_sigspec] : macro_cell->connections_) {
				auto port_info = macro_module->wires_[port_name];
				if (current_exclusions && current_exclusions->count(port_name)) {
					continue;
				} else if (port_info->port_output) {
					outputs.push_back(port_name);
				} else if (port_info->port_input) {
					inputs.push_back(port_name);
				}
			}

			// remember: an output from a macro is an input to our circuit
			// and vice versa.
			for (auto input : inputs) {
				auto sigspec = macro_cell->connections_[input];
				std::stringstream bsr_name;
				bsr_name << "\\" << macro.c_str() + 1 << "/" << input.c_str() + 1;
				bsr_name << ".obsr";
				IdString bsr_id(bsr_name.str());

				auto bsr = module_->addCell(bsr_id, ID(_difetto_obsr));
				bsr->setParam(ID(WIDTH), sigspec.size());
				bsr->setParam(ID(CLK_POLARITY), clock_negedge ? Const(State::S0, 1) : Const(State::S1, 1));
				bsr->setPort(ID(D), sigspec);
				bsr->setPort(ID(CLK), clock_signal);
				bsr->set_bool_attribute(ID(keep), true);
			}

			for (auto output : outputs) {
				auto sigspec = macro_cell->connections_[output];
				std::stringstream bsr_name;
				bsr_name << "\\" << macro.c_str() + 1 << "/" << output.c_str() + 1;

				IdString bsr_id(bsr_name.str() + ".ibsr");
				IdString pre_ibsr(bsr_name.str() + ".pre_ibsr");

				auto pre_ibsr_wire = module_->addWire(pre_ibsr, sigspec.size());
				macro_cell->setPort(output, pre_ibsr_wire);

				auto bsr = module_->addCell(bsr_id, ID(_difetto_ibsr));
				bsr->setParam(ID(WIDTH), sigspec.size());
				bsr->setParam(ID(CLK_POLARITY), clock_negedge ? Const(State::S0, 1) : Const(State::S1, 1));
				bsr->setParam(ID(TEST_POLARITY), test_inverted ? Const(State::S0, 1) : Const(State::S1, 1));
				bsr->setPort(ID(D), pre_ibsr_wire);
				bsr->setPort(ID(Q), sigspec);
				bsr->setPort(ID(CLK), clock_signal);
				bsr->setPort(ID(TEST), test_mode_signal);
			}
		}

		module_->fixup_ports();
	}

	virtual void execute(std::vector<std::string> args, Design *design) override
	{
		log_header(design, "Executing BOUNDARY_SCAN pass.\n");
		log_push();
		auto parsed_args = parse_args(args, design);

		pool<IdString> macros;
		for (const auto &macro_raw : parsed_args["macro"]) {
			macros.insert("\\"s + macro_raw);
		}

		std::string test_mode_wire_name = parsed_args["test_mode"].at(0);
		std::string clock_wire_name = parsed_args["clock"].at(0);
		pool<std::string> raw_exclusions{};
		for (auto &el : parsed_args["exclude_io"]) {
			raw_exclusions.insert(el);
		}
		auto exclusions = process_exclusions(raw_exclusions);

		auto bsr_idstring = ID(_difetto_bsr);
		if (design->modules_.count(bsr_idstring) == 0) {
			load_ibsr_definitions(design);
		}

		for (auto module : design->selected_modules()) {
			boundary_scan(design, module, test_mode_wire_name, clock_wire_name, macros, exclusions);
		}

		Pass::call(design, "hierarchy");

		log_pop();
	}
} BoundaryScanPass;
