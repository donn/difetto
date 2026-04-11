## Commands

```
$ librelane test/aes128/config.yaml \
    --overwrite --run-tag synth \
    --to difetto.cut
$ librelane test/aes128/config.yaml \
    --overwrite --run-tag fault --flow DifettoPNRTopologicalChain \
    --from difetto.topologicalchain --to openroad.detailedrouting \
    -i $(librelane.state latest ./test/aes128/runs/synth) 
$ librelane test/aes128/config.yaml \
    --overwrite --run-tag opt --flow DifettoPNR \
    --from checker.yosysunmappedcells --to openroad.detailedrouting \
    -i $(librelane.state latest ./test/aes128/runs/synth)
```
