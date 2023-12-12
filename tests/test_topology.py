# import ipaddress

# import pytest

# from aiogossip.types_pb2 import Route
# from aiogossip.topology import Node, Topology
# from aiogossip.transport.address import Address, parse_addr


# def test_topology(topology):
#     assert isinstance(topology, Topology)
#     assert isinstance(topology.node, Node)
#     assert isinstance(topology.node_id, bytes)
#     assert isinstance(topology.node_addr, Address)


# def test_topology_add(topology):
#     topology.add([Node(node_id=topology.node_id, node_addr=topology.node_addr)])
#     topology.add([Node(node_id="node2", node_addr="127.0.0.1:8001")])
#     assert len(topology) == 2


# def test_topology_update_route(topology, message):
#     message.routing.routes.append(
#         Route(
#             node_id=b"node1",
#             saddr="127.0.0.1:8000",
#             daddr="127.0.0.1:8000",
#         )
#     )

#     message.routing.routes.append(
#         Route(
#             node_id=b"node1",
#             saddr="127.0.0.1:8001",
#         )
#     )

#     topology.update(message.routing.routes)
#     assert len(topology) == 2


# def test_topology_update_route_invalid(topology, message):
#     with pytest.raises(ValueError):
#         message.routing.routes.append(
#             Route(
#                 node_id=b"node1",
#                 saddr="127.0.0.1:8000",
#                 daddr="127.0.0.1:8000",
#             )
#         )
#         topology.update(message.routing.routes)


# def test_topology_sample(topology):
#     topology.add([Node(node_id="node2", node_addr="127.0.0.1:8002")])
#     topology.add([Node(node_id="node3", node_addr="127.0.0.1:8003")])
#     sample = topology.sample(1, ignore=["node3"])
#     assert len(sample) == 1
#     assert sample[0] in ["node1", "node2"]


# def test_topology_iter(topology):
#     topology.add([Node(node_id="node2", node_addr="127.0.0.1:8002")])
#     assert list(topology) == [topology.node_id, "node2"]


# def test_topology_getitem():
#     topology = Topology("node1", parse_addr("127.0.0.1:8000"))
#     assert topology["node1"]["node_id"] == "node1"


# def test_topology_contains():
#     topology = Topology("node1", parse_addr("127.0.0.1:8000"))
#     assert "node1" in topology


# def test_topology_get_next_peer():
#     topology = Topology(b"node1", parse_addr("127.0.0.1:8000"))
#     topology.add([Node(node_id="node2", node_addr="127.0.0.1:8002")])
#     peer_id, peer_addr = topology.get_next_peer("node2")
#     assert peer_id == "node2"
#     assert peer_addr.ip == ipaddress.ip_address("127.0.0.1")
#     assert peer_addr.port == 8002
