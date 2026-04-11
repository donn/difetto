## Commands

```
$ librelane test/picorv32/config.yaml \
    --overwrite --run-tag synth \
    --to difetto.cut
$ librelane test/picorv32/config.yaml \
    --overwrite --run-tag fault --flow DifettoPNRTopologicalChain \
    --from difetto.topologicalchain --to openroad.stapostpnr -j4 \
    -i $(librelane.state latest ./test/picorv32/runs/synth) 
$ librelane test/picorv32/config.yaml \
    --overwrite --run-tag opt --flow DifettoPNR \
    --from checker.yosysunmappedcells --to openroad.stapostpnr -j4 \
    -i $(librelane.state latest ./test/picorv32/runs/synth)
```
