import dataclasses
import uuid

import pytest

from aiogossip.address import to_address
from aiogossip.node import Node
from aiogossip.route import Route


@pytest.fixture
def saddr():
    return to_address(("192.168.1.1", 8080))


@pytest.fixture
def snode(saddr):
    return Node(uuid.uuid1(), {saddr})


@pytest.fixture
def daddr():
    return to_address(("192.168.1.2", 8080))


@pytest.fixture
def dnode(daddr):
    return Node(uuid.uuid1(), {daddr})


def test_route_init(snode, saddr, dnode, daddr):
    route = Route(snode, saddr, dnode, daddr)

    assert route.snode == snode
    assert route.saddr == saddr
    assert route.dnode == dnode
    assert route.daddr == daddr


def test_route_init_with_same_node_id(snode, saddr, daddr):
    snode = dataclasses.replace(snode, addresses={saddr, daddr})
    snode = Node(snode.node_id, {saddr, daddr})
    with pytest.raises(ValueError):
        Route(snode, saddr, snode, daddr)


def test_route_init_with_saddr_not_in_snode(snode, dnode, daddr):
    saddr = to_address(("192.168.1.3", 8080))  # This address is not in snode
    with pytest.raises(ValueError):
        Route(snode, saddr, dnode, daddr)


def test_route_init_with_daddr_not_in_dnode(snode, saddr, dnode):
    daddr = to_address(("192.168.1.4", 8080))  # This address is not in dnode
    with pytest.raises(ValueError):
        Route(snode, saddr, dnode, daddr)


def test_route_init_with_invalid_snode_type(saddr, dnode, daddr):
    snode = "invalid_snode"
    with pytest.raises(TypeError):
        Route(snode, saddr, dnode, daddr)


def test_route_init_with_invalid_saddr_type(snode, dnode, daddr):
    saddr = "invalid_saddr"
    with pytest.raises(TypeError):
        Route(snode, saddr, dnode, daddr)


def test_route_init_with_invalid_dnode_type(snode, saddr, daddr):
    dnode = "invalid_dnode"
    with pytest.raises(TypeError):
        Route(snode, saddr, dnode, daddr)


def test_route_init_with_invalid_daddr_type(snode, saddr, dnode):
    daddr = "invalid_daddr"
    with pytest.raises(TypeError):
        Route(snode, saddr, dnode, daddr)
