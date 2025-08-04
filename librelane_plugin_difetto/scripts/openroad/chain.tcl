source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb

set_dft_config\
    -max_chains 1\
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

puts "\[INFO\] Writing chains in a YAML format…"

set yaml_out [open "$::env(STEP_DIR)/$::env(DESIGN_NAME).chains.yml" "w"]
set ::dft [$::block getDft]
set chains [$::dft getScanChains]
foreach chain $chains {
puts $yaml_out "- name: '[$chain getName]'"
puts $yaml_out "  partitions:"
    set partitions [$chain getScanPartitions]
    foreach partition $partitions {
puts $yaml_out "  - name: '[$partition getName]'"
puts $yaml_out "    lists:"
        set lists [$partition getScanLists]
        foreach list $lists {
puts $yaml_out "    - insts:"
            set insts [$list getScanInsts]
            set last_clk "\$"
            set last_edge "\$"
            foreach inst $insts {
                set current_clk [$inst getScanClock]
                set current_edge [$inst getClockEdge]
                if { "$last_clk" != "$current_clk" || "$last_edge" != "$current_edge" } {
puts $yaml_out "      - name: '[[$inst getInst] getName]'"
                    set inv_string ""
                    if { "$current_edge" == "1" } {
                        set inv_string "!"
                    }
puts $yaml_out "        clk: '$inv_string$current_clk'"
                    set last_clk "$current_clk"
                    set last_edge "$current_edge"
                } else {
puts $yaml_out "      - '[[$inst getInst] getName]'"
                }
            }
        }
    }
}
close $yaml_out

write_views
