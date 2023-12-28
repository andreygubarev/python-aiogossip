import uuid

import networkx as nx
import pytest

from aiogossip.address import to_address
from aiogossip.endpoint import Endpoint
from aiogossip.node import Node
from aiogossip.topology import Route, Topology


def test_topology_initialization():
    topology = Topology()
    assert isinstance(topology.g, nx.DiGraph)


def test_topology_initialization_empty():
    topology = Topology()
    assert len(topology.g.nodes) == 0
    assert len(topology.g.edges) == 0


def test_add_node(node):
    topology = Topology()
    topology.add_node(node)
    assert node.node_id in topology.g
    assert topology.g.nodes[node.node_id]["node"] == node


def test_topology_get_node(node):
    topology = Topology()
    topology.add_node(node)
    assert topology.get_node(node.node_id) == node


@pytest.mark.parametrize("instances", [2])
def test_topology_add_route(nodes, addresses):
    topology = Topology()

    nodes[0].addresses.add(addresses[0])
    topology.add_node(nodes[0])

    nodes[1].addresses.add(addresses[1])
    topology.add_node(nodes[1])

    route = Route(nodes[0], addresses[0], nodes[1], addresses[1])
    topology.add_route(route)

    assert topology.g.has_edge(nodes[0].node_id, nodes[1].node_id)
    assert topology.g.edges[nodes[0].node_id, nodes[1].node_id]["saddr"] == addresses[0]
    assert topology.g.edges[nodes[0].node_id, nodes[1].node_id]["daddr"] == addresses[1]


@pytest.mark.parametrize("instances", [2])
def test_topology_get_route(nodes, addresses):
    topology = Topology()

    nodes[0].addresses.add(addresses[0])
    topology.add_node(nodes[0])

    nodes[1].addresses.add(addresses[1])
    topology.add_node(nodes[1])

    route = Route(nodes[0], addresses[0], nodes[1], addresses[1])
    topology.add_route(route)

    retrieved_route = topology.get_route(nodes[0], nodes[1])

    assert retrieved_route.snode == nodes[0]
    assert retrieved_route.saddr == addresses[0]
    assert retrieved_route.dnode == nodes[1]
    assert retrieved_route.daddr == addresses[1]


@pytest.mark.parametrize("instances", [3])
def test_topology_get_shortest_route(nodes, addresses):
    topology = Topology()

    nodes[0].addresses.add(addresses[0])
    topology.add_node(nodes[0])

    nodes[1].addresses.add(addresses[1])
    topology.add_node(nodes[1])

    nodes[2].addresses.add(addresses[2])
    topology.add_node(nodes[2])

    topology.add_route(Route(nodes[0], addresses[0], nodes[1], addresses[1]))
    topology.add_route(Route(nodes[1], addresses[1], nodes[2], addresses[2]))

    shortest_route = topology.get_shortest_route(nodes[0], nodes[2])

    assert shortest_route.snode == nodes[0]
    assert shortest_route.saddr == addresses[0]
    assert shortest_route.dnode == nodes[1]
    assert shortest_route.daddr == addresses[1]


@pytest.mark.parametrize("instances", [3])
def test_topology_get_shortest_route_reverse(nodes, addresses):
    topology = Topology()

    nodes[0].addresses.add(addresses[0])
    topology.add_node(nodes[0])

    nodes[1].addresses.add(addresses[1])
    topology.add_node(nodes[1])

    nodes[2].addresses.add(addresses[2])
    topology.add_node(nodes[2])

    topology.add_route(Route(nodes[0], addresses[0], nodes[1], addresses[1]))
    # skip adding the reverse route, because node[2] doesn't know about node[0] to node[1] route

    topology.add_route(Route(nodes[1], addresses[1], nodes[2], addresses[2]))
    topology.add_route(Route(nodes[2], addresses[2], nodes[1], addresses[1]))

    shortest_route = topology.get_shortest_route(nodes[2], nodes[0])

    assert shortest_route.snode == nodes[2]
    assert shortest_route.saddr == addresses[2]
    assert shortest_route.dnode == nodes[1]
    assert shortest_route.daddr == addresses[1]


@pytest.mark.parametrize("instances", [3])
def test_topology_len(nodes):
    topology = Topology()
    for node in nodes:
        topology.add_node(node)
    assert len(topology) == len(nodes)


@pytest.mark.parametrize("instances", [3])
def test_topology_get_successor_routes(nodes, addresses):
    topology = Topology()

    nodes[0].addresses.add(addresses[0])
    topology.add_node(nodes[0])
    nodes[1].addresses.add(addresses[1])
    topology.add_node(nodes[1])
    nodes[2].addresses.add(addresses[2])
    topology.add_node(nodes[2])

    topology.add_route(Route(nodes[0], addresses[0], nodes[1], addresses[1]))
    topology.add_route(Route(nodes[0], addresses[0], nodes[2], addresses[2]))

    successor_routes = topology.get_successor_routes(nodes[0])

    assert len(successor_routes) == 2

    assert successor_routes[0].snode == nodes[0]
    assert successor_routes[0].saddr == addresses[0]
    assert successor_routes[0].dnode == nodes[1]
    assert successor_routes[0].daddr == addresses[1]

    assert successor_routes[1].snode == nodes[0]
    assert successor_routes[1].saddr == addresses[0]
    assert successor_routes[1].dnode == nodes[2]
    assert successor_routes[1].daddr == addresses[2]


@pytest.mark.parametrize("instances", [4])
def test_get_random_dnodes(nodes, addresses):
    topology = Topology()

    # Add nodes to topology
    nodes[0].addresses.add(addresses[0])
    topology.add_node(nodes[0])
    nodes[1].addresses.add(addresses[1])
    topology.add_node(nodes[1])
    nodes[2].addresses.add(addresses[2])
    topology.add_node(nodes[2])
    nodes[3].addresses.add(addresses[3])
    topology.add_node(nodes[3])

    # Create routes
    route1 = Route(nodes[0], addresses[0], nodes[1], addresses[1])
    topology.add_route(route1)
    route2 = Route(nodes[0], addresses[0], nodes[2], addresses[2])
    topology.add_route(route2)
    route3 = Route(nodes[0], addresses[0], nodes[3], addresses[3])
    topology.add_route(route3)

    # Exclude node2 and node3
    exclude_nodes = {nodes[2], nodes[3]}

    # Get random destination nodes
    random_dnodes = topology.get_random_successor_nodes(nodes[0], 1, exclude_nodes)

    # Assert the number of random destination nodes
    assert len(random_dnodes) == 1

    # Assert that the random destination node is not in the excluded nodes
    assert random_dnodes[0] not in exclude_nodes

    # Assert that the random destination node is in the list of destination nodes
    assert random_dnodes[0] in [route1.dnode, route2.dnode, route3.dnode]


@pytest.mark.parametrize("instances", [3])
def test_topology_iter(nodes):
    topology = Topology()
    for node in nodes:
        topology.add_node(node)
    assert set(topology) == set(nodes)


@pytest.mark.parametrize("instances", [3])
def test_topology_contains(nodes):
    topology = Topology()
    for node in nodes:
        topology.add_node(node)

    assert nodes[0] in topology
    assert nodes[1] in topology
    assert nodes[2] in topology


def test_topology_update_routes_with_three_endpoints():
    nodes = [
        Node(
            uuid.UUID("aaaaaaaa-9eb9-11ee-9bae-76ec1a7abb6c"),
            {to_address("127.0.0.1:10000"), to_address("192.168.0.1:10000")},
        ),
        Node(
            uuid.UUID("bbbbbbbb-9eb9-11ee-9bae-76ec1a7abb6c"),
            {to_address("127.0.0.1:10001"), to_address("192.168.0.1:10001")},
        ),
        Node(
            uuid.UUID("cccccccc-9eb8-11ee-ad78-76ec1a7abb6c"),
            {to_address("127.0.0.1:10002"), to_address("192.168.0.1:10002")},
        ),
    ]

    topology = Topology()
    topology.add_node(nodes[0])
    with pytest.raises(ValueError):
        topology.update_routes(
            [
                Endpoint(nodes[0], src=to_address("127.0.0.1:10000"), dst=to_address("192.168.0.1:10000")),
            ]
        )

    topology.update_routes(
        [
            Endpoint(nodes[0], src=to_address("127.0.0.1:10000"), dst=to_address("192.168.0.1:10000")),
            Endpoint(nodes[1], src=to_address("127.0.0.1:10001"), dst=to_address("192.168.0.1:10001")),
            Endpoint(nodes[2], src=to_address("127.0.0.1:10002"), dst=to_address("192.168.0.1:10002")),
        ]
    )

    assert topology.g.has_edge(nodes[0].node_id, nodes[1].node_id)
    assert not topology.g.has_edge(nodes[1].node_id, nodes[0].node_id)
    assert topology.g.edges[nodes[0].node_id, nodes[1].node_id]["daddr"] == to_address("192.168.0.1:10001")

    assert topology.g.has_edge(nodes[1].node_id, nodes[2].node_id)
    assert topology.g.edges[nodes[1].node_id, nodes[2].node_id]["daddr"] == to_address("192.168.0.1:10002")

    assert topology.g.has_edge(nodes[2].node_id, nodes[1].node_id)
    assert topology.g.edges[nodes[2].node_id, nodes[1].node_id]["daddr"] == to_address("192.168.0.1:10001")
