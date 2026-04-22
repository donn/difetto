# picorv32

I copied this from LibreLane sources I have no provenance for this

## Modifications

* Top-level interface modified to add scan chain signals.

## Commands

```
$ python3 -m librelane test/picorv32/config.yaml \
    --overwrite --run-tag synth \
    --to difetto.cut
$ python3 -m librelane test/picorv32/config.yaml \
    --overwrite --run-tag fault \
    -c RUN_NL_CHAIN=1 -c RUN_PL_CHAIN=0 \
    --from difetto.topologicalchain --to openroad.stapostpnr -j4 \
    -i $(librelane.state latest ./test/picorv32/runs/synth) 
$ python3 -m librelane test/picorv32/config.yaml \
    --overwrite --run-tag opt \
    -c RUN_NL_CHAIN=0 -c RUN_PL_CHAIN=1 \
    --from checker.yosysunmappedcells --to openroad.stapostpnr -j4 \
    -i $(librelane.state latest ./test/picorv32/runs/synth)
$ python3 -m librelane test/picorv32/config.yaml \
    --overwrite --run-tag basic \
    -c RUN_NL_CHAIN=0 -c RUN_PL_CHAIN=1 -c DFT_SCAN_OPT=0\
    --from difetto.chain --to openroad.stapostpnr \
    -i test/picorv32/runs/opt/*-difetto-chain/state_in.json
$ python3 -m librelane test/picorv32/config.yaml \
    --overwrite --run-tag skip \
    -c RUN_NL_CHAIN=0 -c RUN_PL_CHAIN=0 \
    --from difetto.chain --to openroad.stapostpnr \
    -i test/picorv32/runs/opt/*-difetto-chain/state_in.json
```

## Legal

Copyright (C) 2015  Claire Xenia Wolf <claire@yosyshq.com>

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
