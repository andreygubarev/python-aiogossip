import asyncio
import math
import random

import pytest

from aiogossip.gossip2 import Gossip
from aiogossip.transport import Transport


@pytest.fixture(params=[1, 2, 3, 5, 10, 25], ids=lambda x: f"n_nodes={x}")
def n_nodes(request):
    return request.param


@pytest.fixture(params=range(5), ids=lambda x: f"seed={x}")
def rnd(request):
    random.seed(request.param)


@pytest.fixture
def nodes(n_nodes, event_loop, rnd):
    def get_node():
        transport = Transport(("localhost", 0), loop=event_loop)
        return Gossip(transport=transport)

    n_connections = math.ceil(math.sqrt(n_nodes))
    nodes = [get_node() for _ in range(n_nodes)]
    seed = nodes[0]
    for node in nodes:
        seed.topology.add(node.transport.addr)

        node.topology.add(seed.transport.addr)
        for n in random.sample(nodes, n_connections):
            node.topology.add(n.transport.addr)

        node.topology.remove(node.transport.addr)
    return nodes


@pytest.mark.asyncio
async def test_gossip(nodes):
    message = {"message": "Hello, world!", "metadata": {}}

    await nodes[0].gossip(message)

    async def listener(peer):
        try:
            async with asyncio.timeout(0.1):
                async for message in peer.recv():
                    pass
        except asyncio.TimeoutError:
            pass

    tasks = [asyncio.create_task(listener(peer)) for peer in nodes]
    await asyncio.gather(*tasks)

    if len(nodes) == 1:
        assert nodes[0].transport.messages_received == 0
    else:
        for peer in nodes:
            if any([peer.transport.addr in p.topology for p in nodes]):
                assert peer.transport.messages_received > 0, peer.topology
        messages_received = sum(p.transport.messages_received for p in nodes)
        assert messages_received <= 2 ** len(nodes)

    for peer in nodes:
        peer.transport.close()


@pytest.mark.asyncio
async def test_send_and_receive():
    nodes = [Gossip(Transport(("localhost", 0)), []) for _ in range(2)]
    message = {"message": "Hello, world!", "metadata": {}}

    await nodes[0].send(message, nodes[1].transport.addr)
    received_message = await anext(nodes[1].recv())
    assert received_message["message"] == message["message"]
