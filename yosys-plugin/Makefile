difetto.so: src/passes/difetto_pass.cc src/passes/scan_replace.cc
	yosys-config --build $@ -Iinclude $^

.PHONY: test
test:
	cd test && yosys ./module1.ys
	yosys -p "plugin -i ./difetto.so; help scan_replace"
