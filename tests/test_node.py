import uuid

import pytest
import typeguard

from aiogossip.address import Address, to_address
from aiogossip.node import Node, to_node


def test_node_id_type_check():
    with pytest.raises(TypeError):
        Node(node_id="not a uuid", addresses=set())


def test_node_id_version_check():
    with pytest.raises(ValueError):
        Node(node_id=uuid.uuid4(), addresses=set())  # uuid4 is not uuid1


def test_addresses_type_check():
    with pytest.raises(TypeError):
        Node(node_id=uuid.uuid1(), addresses="not a set")


def test_addresses_content_type_check():
    with pytest.raises(TypeError):
        Node(node_id=uuid.uuid1(), addresses={1, 2, 3})  # not a set of Address


def test_valid_node():
    address = to_address("127.0.0.1:8000")
    node = Node(node_id=uuid.uuid1(), addresses={address})
    assert isinstance(node.node_id, uuid.UUID)
    assert node.node_id.version == 1
    assert isinstance(node.addresses, set)
    assert all(isinstance(address, Address) for address in node.addresses)


def test_to_node_with_node():
    address = to_address("127.0.0.1:8000")
    original_node = Node(node_id=uuid.uuid1(), addresses={address})
    converted_node = to_node(original_node)
    assert converted_node is original_node


def test_to_node_with_uuid():
    node_id = uuid.uuid1()
    converted_node = to_node(node_id)
    assert isinstance(converted_node, Node)
    assert converted_node.node_id == node_id
    assert converted_node.addresses == set()


def test_to_node_with_uuid_str():
    node_id = uuid.uuid1()
    converted_node = to_node(str(node_id))
    assert isinstance(converted_node, Node)
    assert converted_node.node_id == node_id
    assert converted_node.addresses == set()


def test_to_node_with_uuid_str_and_address():
    node_id = uuid.uuid1()
    address = "127.0.0.1:8000"
    converted_node = to_node(f"{node_id}@{address}")
    assert isinstance(converted_node, Node)
    assert converted_node.node_id == node_id
    assert converted_node.addresses == {to_address(address)}


def test_to_node_with_invalid_type():
    with pytest.raises(typeguard.TypeCheckError):
        to_node(123)  # not a Node, UUID, or str


def test_to_node_with_invalid_uuid_version():
    with pytest.raises(ValueError):
        to_node(str(uuid.uuid4()))  # uuid4 is not uuid1


def test_to_node_with_invalid_uuid_version_in_str():
    with pytest.raises(ValueError):
        to_node(f"{uuid.uuid4()}@127.0.0.1:8000")  # uuid4 is not uuid1


@pytest.mark.parametrize("instances", [2])
def test_node_hash(addresses):
    node1 = Node(node_id=uuid.uuid1(), addresses={addresses[0]})
    node2 = Node(node_id=uuid.uuid1(), addresses={addresses[1]})
    assert hash(node1) != hash(node2)
    assert hash(node1) == hash(node1)
