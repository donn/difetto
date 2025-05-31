difetto.so: src/passes/difetto_pass.cc src/passes/scan_replace.cc src/passes/boundary_scan.cc
	yosys-config --build $@ -Iinclude $^

.PHONY: test
test:
	cd test && yosys ./spm.ys
