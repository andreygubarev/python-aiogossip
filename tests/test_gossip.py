import asyncio
import math
import random

import pytest

from aiogossip.gossip import Gossip
from aiogossip.transport import Transport


@pytest.fixture(params=range(5), ids=lambda x: f"seed={x}")
def rnd(request):
    random.seed(request.param)


@pytest.fixture(params=[1, 2, 3, 5, 10, 25], ids=lambda x: f"n_gossips={x}")
def n_gossips(request):
    return request.param


@pytest.fixture
def gossips(event_loop, rnd, n_gossips):
    def get_gossip():
        transport = Transport(("localhost", 0), loop=event_loop)
        return Gossip(transport=transport)

    n_connections = math.ceil(math.sqrt(n_gossips))
    gossips = [get_gossip() for _ in range(n_gossips)]
    seed = gossips[0]
    for gossip in gossips:
        seed.topology.add([gossip.topology.node])

        gossip.topology.add([seed.topology.node])
        for g in random.sample(gossips, n_connections):
            gossip.topology.add([g.topology.node])

        gossip.topology.remove([gossip.topology.node])
    return gossips


@pytest.mark.asyncio
async def test_gossip(gossips):
    message = {"message": "", "metadata": {}}
    await gossips[0].gossip(message)

    async def listener(gossip):
        try:
            async with asyncio.timeout(0.1):
                async for message in gossip.recv():
                    pass
        except asyncio.TimeoutError:
            pass

    listeners = [asyncio.create_task(listener(n)) for n in gossips]
    await asyncio.gather(*listeners)

    for gossip in gossips:
        if any([gossip.topology.node in p.topology for p in gossips]):
            assert gossip.transport.rx_packets > 0, gossip.topology
    rx_packets = sum(p.transport.rx_packets for p in gossips)
    assert rx_packets <= 2 ** len(gossips)

    for gossip in gossips:
        gossip.transport.close()


@pytest.mark.asyncio
async def test_send_and_receive():
    gossips = [Gossip(Transport(("localhost", 0)), []) for _ in range(2)]
    message = {"message": "Hello, world!", "metadata": {}}

    await gossips[0].send(message, gossips[1].topology.node)
    received_message = await anext(gossips[1].recv())
    assert received_message["message"] == message["message"]
