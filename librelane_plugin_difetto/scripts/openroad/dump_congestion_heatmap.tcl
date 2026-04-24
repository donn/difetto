source $::env(SCRIPTS_DIR)/openroad/common/io.tcl
read_current_odb

gui::set_heatmap "Routing" "Type" "Congestion"
gui::set_heatmap "Routing" rebuild
gui::dump_heatmap "Routing" $::env(STEP_DIR)/congestion.csv

write_views
