import random
import uuid

import networkx as nx
import typeguard

from .endpoint import Endpoint
from .node import Node
from .route import Route


class Topology:
    def __init__(self):
        self.g = nx.DiGraph()

    @typeguard.typechecked
    def add_node(self, node: Node) -> None:
        """
        Adds a node to the topology.

        Args:
            node (Node): The node to be added.

        """
        if node.node_id in self.g:
            self.get_node(node.node_id).addresses.update(node.addresses)
        else:
            self.g.add_node(node.node_id, node=node)

    @typeguard.typechecked
    def get_node(self, node_id: uuid.UUID) -> Node:
        """
        Retrieve a node from the topology by its ID.

        Args:
            node_id (uuid.UUID): The ID of the node to retrieve.

        Returns:
            Node: The node object.

        """
        return self.g.nodes[node_id]["node"]

    @typeguard.typechecked
    def get_random_successor_nodes(self, snode: Node, n: int, exclude_nodes: set[Node] = None) -> list[Node]:
        """
        Returns a list of randomly selected successor nodes from the given source node.

        Args:
            snode (Node): The source node.
            n (int): The number of successor nodes to select.
            exclude_nodes (set[Node], optional): Set of nodes to exclude from selection. Defaults to None.

        Returns:
            list[Node]: A list of randomly selected successor nodes.
        """
        routes = self.get_successor_routes(snode)
        exclude_nodes = exclude_nodes or set()
        dnodes = [r.dnode for r in routes if r.dnode not in exclude_nodes]
        return random.sample(dnodes, min(n, len(dnodes)))

    @typeguard.typechecked
    def add_route(
        self,
        route: Route,
    ) -> None:
        """
        Adds a route to the topology.

        Args:
            route (Route): The route to be added.

        Returns:
            None
        """
        self.g.add_edge(route.snode.node_id, route.dnode.node_id, saddr=route.saddr, daddr=route.daddr)

    @typeguard.typechecked
    def get_route(self, snode: Node, dnode: Node) -> Route:
        """
        Retrieve a route between two nodes in the topology.

        Args:
            snode (Node): The source node.
            dnode (Node): The destination node.

        Returns:
            Route: The route.

        """
        return Route(
            snode=snode,
            saddr=self.g.edges[snode.node_id, dnode.node_id]["saddr"],
            dnode=dnode,
            daddr=self.g.edges[snode.node_id, dnode.node_id]["daddr"],
        )

    @typeguard.typechecked
    def get_shortest_route(self, snode: Node, dnode: Node) -> Route:
        """
        Get the shortest route between two nodes.

        Args:
            snode (Node): The source node.
            dnode (Node): The destination node.

        Returns:
            Route: The shortest route between the source and destination nodes.
        """
        # IMPORTANT
        path = nx.shortest_path(self.g.to_undirected(), snode.node_id, dnode.node_id)
        return self.get_route(self.get_node(path[0]), self.get_node(path[1]))

    @typeguard.typechecked
    def get_successor_routes(self, snode: Node) -> list[Route]:
        """
        Get all routes originating from a node.

        Args:
            snode (Node): The source node.

        Returns:
            list[Route]: A list of routes originating from the node.
        """
        routes = []
        for dnode in self.g.successors(snode.node_id):
            routes.append(self.get_route(snode, self.get_node(dnode)))
        return routes

    @typeguard.typechecked
    def update_routes(self, endpoints: list[Endpoint]):
        """
        Update the routes in the topology based on the given list of endpoints.

        Args:
            endpoints (list[Endpoint]): A list of endpoints representing the nodes in the topology.

        Raises:
            ValueError: If the number of endpoints is less than 2.

        """
        if len(endpoints) < 2:
            raise ValueError("Endpoints must contain at least two endpoints")

        for endpoint in endpoints:
            endpoint.node.addresses.add(endpoint.src)
            endpoint.node.addresses.add(endpoint.dst)
            self.add_node(endpoint.node)

        # IMPORTANT: discovery
        hops = list(zip(endpoints[:-1], endpoints[1:]))
        for src, dst in hops:
            self.add_route(Route(src.node, src.dst, dst.node, dst.dst))
        self.add_route(Route(dst.node, dst.dst, src.node, src.dst))

    def __len__(self) -> int:
        """
        Returns the number of nodes in the topology.

        Returns:
            int: The number of nodes in the topology.
        """
        return len(self.g)

    def __iter__(self) -> iter:
        """
        Returns an iterator over the nodes in the topology.

        Returns:
            iter: An iterator over the nodes in the topology.
        """
        return iter(self.get_node(node_id) for node_id in self.g)

    def __contains__(self, node: Node) -> bool:
        """
        Returns True if the node is in the topology.

        Args:
            node (Node): The node to check.

        Returns:
            bool: True if the node is in the topology.
        """
        return node.node_id in self.g
