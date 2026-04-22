# aes256

By Homer Hsing <homer.hsing@gmail.com>

## Modifications

* Top-level interface modified to add scan chain signals.

## Commands

```
$ python3 -m librelane test/aes256/config.yaml \
    --overwrite --run-tag synth \
    --to difetto.cut
$ python3 -m librelane test/aes256/config.yaml \
    --overwrite --run-tag fault \
    -c RUN_NL_CHAIN=1 -c RUN_PL_CHAIN=0 \
    --from difetto.topologicalchain --to openroad.stapostpnr -j4 \
    -i $(librelane.state latest ./test/aes256/runs/synth) 
$ python3 -m librelane test/aes256/config.yaml \
    --overwrite --run-tag opt \
    -c RUN_NL_CHAIN=0 -c RUN_PL_CHAIN=1 \
    --from checker.yosysunmappedcells --to openroad.stapostpnr -j4 \
    -i $(librelane.state latest ./test/aes256/runs/synth)
$ python3 -m librelane test/aes256/config.yaml \
    --overwrite --run-tag basic \
    -c RUN_NL_CHAIN=0 -c RUN_PL_CHAIN=1 -c DFT_SCAN_OPT=0\
    --from difetto.chain --to openroad.stapostpnr \
    -i test/aes256/runs/opt/*-difetto-chain/state_in.json
$ python3 -m librelane test/aes256/config.yaml \
    --overwrite --run-tag skip \
    -c RUN_NL_CHAIN=0 -c RUN_PL_CHAIN=0 \
    --from difetto.chain --to openroad.stapostpnr \
    -i test/aes256/runs/opt/*-difetto-chain/state_in.json
```

## Legal

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
