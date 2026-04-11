# Lofty's 8-Core Chess Computer

Adapted from https://github.com/lofty/gf180mcu-chess, but I removed the TAP
controller and JTAG registers.

## Commands

```
$ librelane test/lofty_chess/config.yaml \
    --overwrite --run-tag synth \
    --to difetto.cut
$ librelane test/lofty_chess/config.yaml \
    --overwrite --run-tag fault --flow DifettoPNRTopologicalChain \
    --from difetto.topologicalchain --to openroad.detailedrouting \
    -i $(librelane.state latest ./test/lofty_chess/runs/synth) 
$ librelane test/lofty_chess/config.yaml \
    --overwrite --run-tag opt --flow DifettoPNR \
    --from checker.yosysunmappedcells --to openroad.detailedrouting \
    -i $(librelane.state latest ./test/lofty_chess/runs/synth)
```
