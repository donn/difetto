python3 -m librelane ./test/spm/config.yaml --run-tag new_pnr --flow DifettoPNR --overwrite
python3 -m librelane ./test/spm/config.yaml --run-tag atpg --flow DifettoATPG --overwrite\
    --with-initial-state test/spm/runs/new_pnr/*-difetto-cut/state_out.json
python3 -m librelane ./test/spm/config.yaml --run-tag test --flow DifettoTest --overwrite\
    --with-initial-state test/spm/runs/atpg/*-difetto-quaighsim/state_out.json\
    --with-initial-state test/spm/runs/new_pnr/*-difetto-chain/state_out.json
