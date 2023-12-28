import dataclasses

from .address import Address
from .node import Node


@dataclasses.dataclass(frozen=True, slots=True)
class Route:
    snode: Node
    saddr: Address

    dnode: Node
    daddr: Address

    def __post_init__(self):
        if not isinstance(self.snode, Node):
            raise TypeError("snode must be Node")

        if not isinstance(self.saddr, Address):
            raise TypeError("saddr must be Address")

        if self.saddr not in self.snode.addresses:
            raise ValueError("saddr must be in snode")

        if not isinstance(self.dnode, Node):
            raise TypeError("dnode must be Node")

        if not isinstance(self.daddr, Address):
            raise TypeError("daddr must be Address")

        if self.daddr not in self.dnode.addresses:
            raise ValueError("daddr must be in dnode")

        if self.snode == self.dnode:
            raise ValueError("snode and dnode must be different")
