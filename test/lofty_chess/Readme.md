# Lofty's 8-Core Chess Computer

Adapted from https://github.com/ravenslofty/gf180mcu-chess.

## Modifications

* Top-level interface modified to add scan chain signals.
* Removed the TAP controller and JTAG registers.

## Commands

```
$ python3 -m librelane test/lofty_chess/config.yaml \
    --overwrite --run-tag synth \
    --to difetto.cut
$ python3 -m librelane test/lofty_chess/config.yaml \
    --overwrite --run-tag fault \
    --from difetto.topologicalchain --to openroad.detailedrouting \
    -c RUN_NL_CHAIN=1 -c RUN_PL_CHAIN=0 \
    -i $(librelane.state latest ./test/lofty_chess/runs/synth) 
$ python3 -m librelane test/lofty_chess/config.yaml \
    --overwrite --run-tag opt \
    -c RUN_NL_CHAIN=0 -c RUN_PL_CHAIN=1 \
    --from checker.yosysunmappedcells --to openroad.detailedrouting \
    -i $(librelane.state latest ./test/lofty_chess/runs/synth)
$ python3 -m librelane test/lofty_chess/config.yaml \
    --overwrite --run-tag basic \
    -c RUN_NL_CHAIN=0 -c RUN_PL_CHAIN=1 -c DFT_SCAN_OPT=0\
    --from difetto.chain --to openroad.detailedrouting \
    -i test/lofty_chess/runs/opt/*-difetto-chain/state_in.json
```

## License

Copyright (c) 2024 Hannah Ravensloft

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
