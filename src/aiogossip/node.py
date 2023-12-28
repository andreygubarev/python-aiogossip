import dataclasses
import uuid
from typing import Set

import typeguard

from .address import Address, to_address


@dataclasses.dataclass(frozen=True, slots=True)
class Node:
    node_id: uuid.UUID
    addresses: Set[Address]

    def __post_init__(self):
        if not isinstance(self.node_id, uuid.UUID):
            raise TypeError("node_id must be UUID")

        if not self.node_id.version == 1:
            raise ValueError("node_id must be UUIDv1")

        if not isinstance(self.addresses, set):
            raise TypeError("addresses must be set")

        for address in self.addresses:
            if not isinstance(address, Address):
                raise TypeError("addresses must be set of Address")

    def __hash__(self):
        return hash(self.node_id)


@typeguard.typechecked
def to_node(node: Node | uuid.UUID | str) -> Node:
    """
    Convert the given node representation to an instance of `Node`.

    Args:
        node (Node | uuid.UUID | str): The node representation.

    Returns:
        Node: The converted node.

    Raises:
        TypeError: If the `node` argument is not of type `Node`, `UUID`, or `str`.
    """
    if isinstance(node, uuid.UUID):
        node = Node(node, set())
    elif isinstance(node, str):
        if "@" in node:
            node, addr = node.split("@", 1)
            node = uuid.UUID(node)
            if node.version != 1:
                raise ValueError("node must be UUIDv1")
            addr = to_address(addr)
            node = Node(node, {addr})
        else:
            node = uuid.UUID(node)
            if node.version != 1:
                raise ValueError("node must be UUIDv1")
            node = Node(node, set())

    return node
