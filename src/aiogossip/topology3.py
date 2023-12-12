import uuid

import networkx as nx

from . import types_pb2


class Topology:
    """
    Represents a network topology.

    The `Topology` class provides methods to add nodes, add routes, and manage endpoints in the network topology.
    """

    def __init__(self):
        self.g = nx.Graph()

    def add_node(self, node: bytes | uuid.UUID | types_pb2.Node):
        """
        Add a node to the topology.

        Args:
            node: The node to be added. It can be of type bytes, uuid.UUID, or types_pb2.Node.

        Raises:
            TypeError: If the node type is unknown.

        """
        if isinstance(node, bytes):
            node = types_pb2.Node(node_id=node)
        elif isinstance(node, uuid.UUID):
            node = types_pb2.Node(node_id=node.bytes)
        elif isinstance(node, types_pb2.Node):
            pass
        else:
            raise TypeError(f"Unknown node type {type(node)}")

        if node.node_id not in self.g:
            self.g.add_node(node.node_id, node=node)

    def get_node(self, node_id: bytes | uuid.UUID) -> types_pb2.Node:
        """
        Get a node from the topology.

        Args:
            node_id: The ID of the node to retrieve. It can be of type bytes or uuid.UUID.

        Returns:
            The node with the specified ID.

        Raises:
            TypeError: If the node ID type is unknown.

        """
        if isinstance(node_id, bytes):
            pass
        elif isinstance(node_id, uuid.UUID):
            node_id = node_id.bytes
        else:
            raise TypeError(f"Unknown node type {type(node_id)}")

        return self.g.nodes[node_id]["node"]

    def add_route(
        self,
        snode: bytes | uuid.UUID | types_pb2.Node,
        saddr: types_pb2.Address,
        dnode: bytes | uuid.UUID | types_pb2.Node,
        daddr: types_pb2.Address,
    ):
        """
        Add a route to the topology.

        Args:
            snode: The source node of the route. It can be of type bytes, uuid.UUID, or types_pb2.Node.
            saddr: The source address of the route.
            dnode: The destination node of the route. It can be of type bytes, uuid.UUID, or types_pb2.Node.
            daddr: The destination address of the route.

        """
        if not isinstance(snode, types_pb2.Node):
            snode = self.get_node(snode)
        if not isinstance(dnode, types_pb2.Node):
            dnode = self.get_node(dnode)

        self.g.add_edge(snode.node_id, dnode.node_id, saddr=saddr, daddr=daddr)

    def get_route(
        self, snode: bytes | uuid.UUID | types_pb2.Node, dnode: bytes | uuid.UUID | types_pb2.Node
    ) -> types_pb2.Address:
        """
        Get the route from the source node to the destination node.

        Args:
            snode: The source node of the route. It can be of type bytes, uuid.UUID, or types_pb2.Node.
            dnode: The destination node of the route. It can be of type bytes, uuid.UUID, or types_pb2.Node.

        Returns:
            The destination address of the route.

        """
        if not isinstance(snode, types_pb2.Node):
            snode = self.get_node(snode)
        if not isinstance(dnode, types_pb2.Node):
            dnode = self.get_node(dnode)

        return self.g.edges[snode.node_id, dnode.node_id]["daddr"]

    def add_route_latency(
        self, snode: bytes | uuid.UUID | types_pb2.Node, dnode: bytes | uuid.UUID | types_pb2.Node, latency: float
    ):
        """
        Add latency to a route in the topology.

        Args:
            snode: The source node of the route. It can be of type bytes, uuid.UUID, or types_pb2.Node.
            dnode: The destination node of the route. It can be of type bytes, uuid.UUID, or types_pb2.Node.
            latency: The latency to be added to the route.

        """
        if not isinstance(snode, types_pb2.Node):
            snode = self.get_node(snode)
        if not isinstance(dnode, types_pb2.Node):
            dnode = self.get_node(dnode)

        self.g.edges[snode, dnode]["latency"] = latency

    def get_route_latency(
        self, snode: bytes | uuid.UUID | types_pb2.Node, dnode: bytes | uuid.UUID | types_pb2.Node
    ) -> float:
        """
        Get the latency of a route in the topology.

        Args:
            snode: The source node of the route. It can be of type bytes, uuid.UUID, or types_pb2.Node.
            dnode: The destination node of the route. It can be of type bytes, uuid.UUID, or types_pb2.Node.

        Returns:
            The latency of the route.

        """
        if not isinstance(snode, types_pb2.Node):
            snode = self.get_node(snode)
        if not isinstance(dnode, types_pb2.Node):
            dnode = self.get_node(dnode)

        return self.g.edges[snode, dnode]["latency"]

    def add_endpoint(self, node: bytes | uuid.UUID | types_pb2.Node, endpoint: types_pb2.Endpoint):
        """
        Add an endpoint to a node in the topology.

        Args:
            node: The node to which the endpoint will be added. It can be of type bytes, uuid.UUID, or types_pb2.Node.
            endpoint: The endpoint to be added.

        """
        if not isinstance(node, types_pb2.Node):
            node = self.get_node(node)

        if endpoint not in node.endpoints:
            node.endpoints.append(endpoint)


# class Routing:
#     def __init__(self, topology):
#         self.topology = topology

#     def update_routes_send(self, message, peer_id, peer_addr):
#         ...

#     def update_routes_recv(self, message, peer_id, peer_addr):
#         ...
