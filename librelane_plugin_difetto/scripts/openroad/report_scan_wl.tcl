source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb

puts "=== Total routed wirelength calculation is enabled ==="

# Collect all nets connected to SCD (scan-in) pins — one net per scan chain edge.
set block [ord::get_db_block]
set scan_net_names {}
foreach inst [$block getInsts] {
  foreach iterm [$inst getITerms] {
    if { [[$iterm getMTerm] getName] eq "SCD" } {
      set net [$iterm getNet]
      if { $net ne "NULL" } {
        lappend scan_net_names [$net getName]
      }
    }
  }
}
set scan_net_names [lsort -unique $scan_net_names]

set scan_wl_file $::env(STEP_DIR)/scan_chain_wl.rpt
report_wire_length -net $scan_net_names -detailed_route -file $scan_wl_file

set scan_total 0.0
set fp [open $scan_wl_file r]
while { [gets $fp line] >= 0 } {
  if { [regexp {^drt: \S+ ([0-9.]+)} $line -> wl] } {
    set scan_total [expr {$scan_total + $wl}]
  }
}
close $fp
puts "=== Scan chain nets ([llength $scan_net_names] nets) routed wirelength: ${scan_total} um ==="
puts "%OL_METRIC_F dft__scan_chain_routed_wl__um $scan_total"
