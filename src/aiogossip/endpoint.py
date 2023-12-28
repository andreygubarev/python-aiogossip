import dataclasses

from .address import Address
from .node import Node


@dataclasses.dataclass(frozen=True, slots=True)
class Endpoint:
    """
    Dataclass that represents a network endpoint consisting of pair of addresses (source and destination).
    """

    node: Node

    src: Address | None = None
    dst: Address | None = None

    def __post_init__(self):
        if not isinstance(self.node, Node):
            raise TypeError("node must be Node")

        if self.src and not isinstance(self.src, Address):
            raise TypeError("src must be Address")

        if self.dst and not isinstance(self.dst, Address):
            raise TypeError("dst must be Address")
