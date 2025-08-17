from typing import List, Literal
from dataclasses import field
from marshmallow import fields
from marshmallow_dataclass import dataclass, class_schema


@dataclass
class Instance:
    clk: str
    edge: Literal["rising", "falling"]
    name: str
    bits: int


class InstanceList(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        deserialized = []
        clk = None
        edge = "rising"
        for inst in value:
            if isinstance(inst, dict):
                clk = inst.get("clk", clk)
                edge = inst.get("edge", edge)
                bits = inst.get("bits", 1)
                deserialized.append(
                    Instance(
                        **{
                            "clk": clk,
                            "edge": edge,
                            "name": inst["name"],
                            "bits": bits,
                        }
                    )
                )
            else:
                deserialized.append(
                    Instance(
                        **{
                            "clk": clk,
                            "edge": edge,
                            "name": inst,
                            "bits": 1,
                        }
                    )
                )

        return super()._deserialize(deserialized, attr, data, **kwargs)


@dataclass
class ScanList:
    insts: List[Instance] = field(
        default_factory=list, metadata={"marshmallow_field": InstanceList()}
    )


@dataclass
class Partition:
    name: str
    scan_lists: List[ScanList]


@dataclass
class Chain:
    name: str
    partitions: List[Partition]

    @property
    def length(self):
        total = 0
        for partition in self.partitions:
            for scan_list in partition.scan_lists:
                for inst in scan_list.insts:
                    total += inst.bits
        return total

    def get_length_of_uniform_chain(self) -> int:
        partitions = self.partitions
        if len(partitions) == 0:
            return 0
        assert len(partitions) == 1, "multiple partitions not supported"
        partition = partitions[0]
        scan_lists = partition.scan_lists
        if len(scan_lists) == 0:
            return 0
        assert len(scan_lists) == 1, "multiple scan lists not supported"
        return self.length


def load_chains(raw) -> List[Chain]:
    city_schema = class_schema(Chain)()
    return [city_schema.load(chain_raw) for chain_raw in raw]
