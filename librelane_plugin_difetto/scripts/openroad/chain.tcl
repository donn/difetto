source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb

proc write_chain_yml {fptr} {
    set ::dft [$::block getDft]
    set chains [$::dft getScanChains]
    foreach chain $chains {
puts $fptr "- name: '[$chain getName]'"
puts $fptr "  partitions:"
        set partitions [$chain getScanPartitions]
        foreach partition $partitions {
puts $fptr "  - name: '[$partition getName]'"
puts $fptr "    scan_lists:"
            set lists [$partition getScanLists]
            foreach list $lists {
puts $fptr "    - insts:"
                set insts [$list getScanInsts]
                set last_clk "\$"
                set last_edge "\$"
                foreach inst [lreverse $insts] {
                    set current_clk [$inst getScanClock]
                    set current_edge [$inst getClockEdge]
                    if { "$last_clk" != "$current_clk" || "$last_edge" != "$current_edge" } {
puts $fptr "      - name: '[[$inst getInst] getName]'"
                        set inv_string ""
                        if { "$current_edge" == "1" } {
                            set inv_string "!"
                        }
puts $fptr "        clk: '$inv_string$current_clk'"
                        set last_clk "$current_clk"
                        set last_edge "$current_edge"
                    } else {
puts $fptr "      - '[[$inst getInst] getName]'"
                    }
                }
            }
        }
    }
}

set_dft_config\
    -max_length 10\
    -scan_enable_name_pattern $::env(DFT_SCAN_ENABLE_PATTERN)\
    -scan_in_name_pattern $::env(DFT_SCAN_IN_PATTERN)\
    -scan_out_name_pattern $::env(DFT_SCAN_OUT_PATTERN)

puts "%OL_CREATE_REPORT dft.rpt"
report_dft_config
if {[expr [llength [info procs report_dft_plan]] > 0]} {
    report_dft_plan -verbose
} else {
    preview_dft -verbose
}
puts "%OL_END_REPORT"


if {[expr [llength [info procs execute_dft_plan]] > 0]} {
    execute_dft_plan
} else {
    insert_dft
}

if { $::env(DFT_SCAN_OPT) } {
    puts "\[INFO\] Writing chain pre-optimization…"
    set yaml_out [open "$::env(STEP_DIR)/$::env(DESIGN_NAME).chain_pre_opt.yml" "w"]
    write_chain_yml $yaml_out
    close $yaml_out

    puts "\[INFO\] Running optimizations…"
    scan_opt
}

puts "\[INFO\] Writing chains in a YAML format…"

set yaml_out [open "$::env(STEP_DIR)/$::env(DESIGN_NAME).chain.yml" "w"]
write_chain_yml $yaml_out
close $yaml_out

puts "\[INFO\] Improving placement..."
improve_placement -max_displacement 50

write_views
