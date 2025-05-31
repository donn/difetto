difetto.so: src/passes/difetto_pass.o src/passes/scan_replace.o src/passes/boundary_scan.o src/passes/sff_cut.o
	yosys-config --build $@ $^

%.o: %.cc
	$(shell yosys-config --cxx) $(shell yosys-config --cxxflags) -Iinclude -c -o $@ $<

.PHONY: test
test:
	cd test && yosys -lsynth.log ./spm.ys
	cd test && yosys -lcut.log ./spm_cut.ys
	cd test && nl2bench -o spm.bench -l tech/sky130_fd_sc_hd__tt_025C_1v80.lib --msb-first spm.cut.v | tee bench.log
	cd test && quaigh atpg --output spm.raw_tvs.txt spm.bench
