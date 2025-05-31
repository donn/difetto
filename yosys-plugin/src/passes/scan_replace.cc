#include "json11.hpp"
#include "kernel/yosys.h"
#include "kernel/modtools.h"

#include <fstream>

USING_YOSYS_NAMESPACE

struct ScanReplacePass : public Pass {

  ScanReplacePass()
      : Pass("scan_replace", "replaces flip-flops with scannable flip-flops") {}

  void help() override {
    //   |---v---|---v---|---v---|---v---|---v---|---v---|---v---|---v---|---v---|---v---|
    log("\n");
    log("    scan_replace\n");
    log("\n");
    log("    \n");
    log("\n");
    log("    -liberty filename\n");
    log("        Currently unsupported - use liberty files\n");
    log("    -json_mapping filename\n");
    log("        The mapping JSON file.\n");
  }
  
  void scan_replace(RTLIL::Module *module, dict<IdString, IdString>& mapping) {
    
    ModWalker mw(module->design, module);
    
    const IdString no_scan("\\no_scan");
    for (auto pair: module->cells_) {
      auto cell = pair.second;
      auto counterpart = mapping[cell->type];
      if (counterpart.empty()) {
        continue;
      }
      // check if cell proper (if declared) has no_scan
      if (cell->get_bool_attribute(no_scan)) {
        log("Skipping %s (cell has no_scan attribute)...\n", pair.first.c_str());
        continue;
      }
      
      // check if any outputs have no_scan
      auto output_bits = mw.cell_outputs[cell];
      bool no_scan_found = false;
      for (auto bit: output_bits) {
        auto wire = bit.wire;
        if (wire->get_bool_attribute(no_scan)) {
          no_scan_found = true;
          break;
        }
      }
      if (no_scan_found) {
        log("Skipping %s (connected to no_scan output)...\n", pair.first.c_str());
        continue;
      }
      
      auto scannable = mapping[cell->type];
      log("%s: %s -> %s\n", pair.first.c_str(), cell->type.c_str(), scannable.c_str());
      cell->type = scannable;
    }
  }

  virtual void execute(std::vector<std::string> args,
                       RTLIL::Design *design) override {
    log_header(design, "Executing SCAN_REPLACE pass.\n");
    std::string liberty_file;
    std::string mapping_json;

    size_t argidx;
    for (argidx = 1; argidx < args.size(); argidx++) {
      std::string arg = args[argidx];
      if (arg == "-liberty" && argidx + 1 < args.size()) {
        liberty_file = args[++argidx];
        rewrite_filename(liberty_file);
        continue;
      }
      if (arg == "-json_mapping" && argidx + 1 < args.size()) {
        mapping_json = args[++argidx];
        rewrite_filename(mapping_json);
        continue;
      }
      break;
    }

    if (mapping_json.empty()) {
      if (liberty_file.empty()) {
        log_cmd_error("One of `-json_mapping mapping_json' and `-liberty "
                      "liberty_file' are required!\n");
      } else {
        log_cmd_error(
            "`-liberty liberty_file' option is currently unsupported.\n");
      }
    }

    // std::ifstream f;
    // f.open(liberty_file.c_str());
    // if (f.fail())
    //   log_cmd_error("Can't open liberty file `%s': %s\n",
    //   liberty_file.c_str(),
    //                 strerror(errno));
    // LibertyParser libparser(f);
    // f.close();

    extra_args(args, argidx, design);

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
    
    dict<IdString, IdString> mapping;
    for (auto& pair: json["mapping"].object_items()) {
      mapping[IdString(std::string("\\") + pair.first)] = IdString(std::string("\\") + pair.second.string_value());
    }
    
    for (auto module : design->selected_modules()) {
      scan_replace(module, mapping);
    }
  }
} ScanReplacePass;
