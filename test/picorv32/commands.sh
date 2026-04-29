python3 -m librelane test/picorv32/config.yaml \
    --overwrite --run-tag synth \
    --to difetto.cut
python3 -m librelane test/picorv32/config.yaml \
    --overwrite --run-tag fault \
    -c RUN_NL_CHAIN=1 -c RUN_PL_CHAIN=0 \
    --from difetto.topologicalchain --to openroad.stapostpnr -j4 \
    -i $(librelane.state latest ./test/picorv32/runs/synth) 
python3 -m librelane test/picorv32/config.yaml \
    --overwrite --run-tag opt \
    -c RUN_NL_CHAIN=0 -c RUN_PL_CHAIN=1 \
    --from checker.yosysunmappedcells --to openroad.stapostpnr -j4 \
    -i $(librelane.state latest ./test/picorv32/runs/synth)
python3 -m librelane test/picorv32/config.yaml \
    --overwrite --run-tag basic \
    -c RUN_NL_CHAIN=0 -c RUN_PL_CHAIN=1 -c DFT_SCAN_OPT=0\
    --from difetto.chain --to openroad.stapostpnr \
    -i test/picorv32/runs/opt/*-difetto-chain/state_in.json
python3 -m librelane test/picorv32/config.yaml \
    --overwrite --run-tag skip \
    -c RUN_NL_CHAIN=0 -c RUN_PL_CHAIN=0 \
    --from difetto.chain --to openroad.stapostpnr \
    -i test/picorv32/runs/opt/*-difetto-chain/state_in.json
