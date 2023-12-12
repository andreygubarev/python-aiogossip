import math
import random
import uuid

import pytest

from aiogossip.broker import Broker
from aiogossip.gossip import Gossip
from aiogossip.peer import Peer
from aiogossip.topology import Topology
from aiogossip.transport import Transport
from aiogossip.types_pb2 import Message

# Generic #####################################################################


@pytest.fixture(params=[0, 1, 2, 3, 4], ids=lambda x: f"random_seed={x}")
def random_seed(request):
    random.seed(request.param)
    return request.param


@pytest.fixture(params=[1, 2, 3, 5, 10], ids=lambda x: f"instances={x}")
def instances(request):
    return request.param


# Message #####################################################################


def get_message():
    message = Message()
    message.id = uuid.uuid4().bytes
    return message


@pytest.fixture
def message():
    return get_message()


# Transport ###################################################################


def get_transport(event_loop):
    return Transport(("localhost", 0), loop=event_loop)


@pytest.fixture
def transport(event_loop):
    return get_transport(event_loop)


@pytest.fixture
def transports(event_loop, instances):
    return [get_transport(event_loop) for _ in range(instances)]


# Topology ####################################################################


def get_topology(transport):
    node_id = uuid.uuid4().bytes
    node_addr = transport.addr
    return Topology(node_id, node_addr)


@pytest.fixture
def topology(transport):
    return get_topology(transport)


# Gossip ######################################################################


def get_gossip(transport):
    return Gossip(transport=transport)


@pytest.fixture
def gossip(transport):
    return get_gossip(transport)


@pytest.fixture
def gossips(transports, random_seed):
    gossips = [get_gossip(transport) for transport in transports]
    gossips_connections = math.ceil(math.sqrt(len(gossips)))
    for gossip in gossips:
        gossips[0].topology.create_node(gossip.topology.node, gossip.topology.node_addr)
        gossips[0].topology.create_node_edge(gossip.topology.node)

        for g in random.sample(gossips, gossips_connections):
            gossip.topology.create_node(g.topology.node, g.topology.node_addr)
            gossip.topology.create_node_edge(g.topology.node)
    return gossips


# Broker ######################################################################


def get_broker(gossip):
    return Broker(gossip)


@pytest.fixture
def broker(gossip):
    return get_broker(gossip)


@pytest.fixture
def brokers(gossips):
    return [get_broker(gossip) for gossip in gossips]


# Peer ########################################################################


def get_peer(event_loop):
    return Peer(loop=event_loop)


@pytest.fixture
def peer(event_loop):
    return get_peer(event_loop)


@pytest.fixture
def peers(event_loop, instances, random_seed):
    return [Peer(loop=event_loop) for _ in range(instances)]
