difetto.so: src/passes/difetto_pass.o src/passes/scan_replace.o src/passes/boundary_scan.o src/passes/sff_cut.o src/bsr.gen.cc
	yosys-config --build $@ $^

%.o: %.cc
	$(shell yosys-config --cxx) $(shell yosys-config --cxxflags) -Iinclude -c -o $@ $<

%.gen.cc: %.v
	xxd -i $< > $@

.PHONY: format
format:
	clang-format -i --style=file include/*.h src/passes/*.cc

.PHONY: clean
clean:
	rm -f src/passes/*.d src/passes/*.o
	rm -f src/*.gen.cc
	rm -f difetto.d
	rm -f difetto.so

.PHONY: test
test: venv/manifest.txt
	./venv/bin/pytest -n auto -vv

venv: venv/manifest.txt
venv/manifest.txt:
	rm -rf venv
	python3 -m venv ./venv
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade pip
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade pytest libparse pytest-xdist
	PYTHONPATH= ./venv/bin/python3 -m pip freeze > $@
	@echo ">> Venv prepared."
