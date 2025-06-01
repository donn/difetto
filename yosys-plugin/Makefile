difetto.so: src/passes/difetto_pass.o src/passes/scan_replace.o src/passes/boundary_scan.o src/passes/sff_cut.o
	yosys-config --build $@ $^

%.o: %.cc
	$(shell yosys-config --cxx) $(shell yosys-config --cxxflags) -Iinclude -c -o $@ $<

.PHONY: test
test: venv/manifest.txt
	./venv/bin/pytest

venv: venv/manifest.txt
venv/manifest.txt:
	rm -rf venv
	python3 -m venv ./venv
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade pip
	PYTHONPATH= ./venv/bin/python3 -m pip install --upgrade pytest libparse
	PYTHONPATH= ./venv/bin/python3 -m pip freeze > $@
	@echo ">> Venv prepared."
