<h1 align="center">Difetto (ALPHA)</h1>
<p align="center">
    <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0"/></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code Style: black"/></a>
    <a href="https://nixos.org/"><img src="https://img.shields.io/static/v1?logo=nixos&logoColor=white&label=&message=Built%20with%20Nix&color=41439a" alt="Built with Nix"/></a>
</p>
<p align="center">
    <a href="https://fossi-chat.org"><img src="https://img.shields.io/badge/Community-FOSSi%20Chat-1bb378?logo=element" alt="Invite to FOSSi Chat"/></a>
</p>

Difetto is a work-in-progress design-for-test (DFT) flow based on the
development version of [LibreLane](https://github.com/librelane/librelane). It
is a complete rewrite of [Fault](https://github.com/aucohl/fault).

It uses [OpenROAD](https://github.com/The-OpenROAD-Project/OpenROAD),
[Quaigh](https://github.com/coloquinte/quaigh),
[cocotb](https://github.com/cocotb/cocotb), a custom
[Yosys](https://github.com/yosyshq/yosys) plugin, custom methodology scripts,
and a custom  OpenDB-based script all for the implementation of test-enabled
ASIC circuits.

## Yosys Plugin

See documentation for the Yosys plugin [here](./yosys-plugin/Readme.md).

## LibreLane Plugin

You will need Nix installed as per the LibreLane documentation.

`nix develop` will drop you into an environment where both LibreLane, Difetto
and all requisite plugins are installed.

The plugin provides three flows:

* `DifettoPNR`: Modified classic flow to handle chain insertion
* `DifettoATPG`: Using data available after `Difetto.Cut` in `Difetto.PNR`,
  performs ATPG for a given chip.
* `DifettoTest`: Using data from `DifettoATPG` and `Difetto.PNR`'s
  `Difetto.Chain`, verify the integrity of the scan chain and run test vectors
  to ensure everything is A-OK.

While this three-flow approach may be inconvenient to some, it allows engineers
to tackle ATPG and Testing, both very time consuming, in parallel with routing.

You may invoke `librelane.help` on any of the mentioned flows or steps for more
info, e.g. `librelane.help DifettoPNR` or `librelane.help Difetto.Chain`.

There are a number of DFT-specific configuration variables you can find using
`librelane.help`, check the `# DFT` section of `test/spm/config.yaml` for an
example.

Here are the commands for the included example:

```bash
python3 -m librelane ./test/spm/config.yaml --run-tag new_pnr --flow DifettoPNR --overwrite
python3 -m librelane ./test/spm/config.yaml --run-tag atpg --flow DifettoATPG --overwrite\
    --with-initial-state ./test/spm/runs/new_pnr/*-difetto-cut/state_out.json
python3 -m librelane ./test/spm/config.yaml --run-tag test --flow DifettoTest --overwrite\
    --with-initial-state ./test/spm/runs/atpg/*-difetto-quaighsim/state_out.json\
    --with-initial-state ./test/spm/runs/new_pnr/*-difetto-chain/state_out.json
```

# Current Limitations

* Compatible with a certain LibreLane WIP branch, not upstream.
* No support for a different "test" SDC for chain and signoff
* Only confirmed to work with the Google/Skywater 130nm PDK
* Requires an explicit tech mapping file — automatic scan cell identification
  not supported.
* There is currently no support for Macros.
* Variable names are not final.

# License

The Apache License, version 2.0. See 'License'.
