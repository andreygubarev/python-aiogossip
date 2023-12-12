import uuid

import pytest

from aiogossip.topology3 import Topology
from aiogossip.types_pb2 import Node


@pytest.fixture
def topology():
    return Topology()


# Topology.add_node ###########################################################


def test_add_node_with_bytes(topology):
    node_id = b"some_node_id"
    topology.add_node(node_id)
    assert node_id in topology.g


def test_add_node_with_uuid(topology):
    node_id = uuid.uuid4()
    topology.add_node(node_id)
    assert node_id.bytes in topology.g


def test_add_node_with_node(topology):
    node_id = b"another_node_id"
    node = Node(node_id=node_id)
    topology.add_node(node)
    assert node_id in topology.g


def test_add_node_with_unknown_type(topology):
    with pytest.raises(TypeError):
        topology.add_node(123)  # Integer is not a valid type


# Topology.get_node ###########################################################


def test_get_node_with_bytes(topology):
    node_id = b"some_node_id"
    topology.add_node(node_id)
    retrieved_node = topology.get_node(node_id)
    assert retrieved_node.node_id == node_id


def test_get_node_with_uuid(topology):
    node_id = uuid.uuid4()
    topology.add_node(node_id)
    retrieved_node = topology.get_node(node_id)
    assert retrieved_node.node_id == node_id.bytes


def test_get_node_with_unknown_type(topology):
    with pytest.raises(TypeError):
        topology.get_node(123)  # Integer is not a valid type


def test_get_node_not_exist(topology):
    with pytest.raises(KeyError):
        topology.get_node(b"non_existent_node")  # This node does not exist in the topology
