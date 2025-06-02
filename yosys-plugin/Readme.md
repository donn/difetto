# Difetto Yosys Plugin

## Building

### Dependencies

* [Yosys](https://github.com/yosyshq/yosys)
* [nl2bench](https://github.com/donn/nl2bench)
* [Quaigh](https://github.com/coloquinte/quaigh)

### Building and Activating

```sh
make difetto.so
```

Then to import it in Yosys…

```
~$ yosys
yosys> plugin -i </path/to/difetto.so>
yosys>
```

## Passes

The Difetto Yosys plugin adds 3 new passes to assist with DFT:

* `boundary_scan`
* `scan_replace`
* `sdff_cut`

Type `help <pass>` for instructions. 

## Limitations

* Macros are currently unsupported.
* `inout` ports are unsupported.
