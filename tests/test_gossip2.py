import asyncio
import random

import pytest

from aiogossip.gossip2 import Gossip
from aiogossip.transport import Transport

random.seed(0)


@pytest.fixture
def peers(event_loop):
    n_peers = 5

    def peer():
        return Gossip(Transport(("localhost", 0), loop=event_loop), [])

    peers = [peer() for _ in range(n_peers)]
    for peer in peers:
        peer.peers = [p.transport.addr for p in random.sample(peers, 3)]
        if peer.transport.addr in peer.peers:
            peer.peers.remove(peer.transport.addr)

    return peers


@pytest.mark.asyncio
async def test_send_and_receive(peers):
    message = {"message": "Hello, world!", "metadata": {}}

    await peers[0].send(message, peers[1].transport.addr)
    received_message = await anext(peers[1].recv())
    assert received_message["message"] == message["message"]


@pytest.mark.asyncio
async def test_gossip(peers):
    message = {"message": "Hello, world!", "metadata": {}}

    await peers[0].gossip(message)

    async def listener(peer):
        try:
            async with asyncio.timeout(0.1):
                async for message in peer.recv():
                    pass
        except asyncio.TimeoutError:
            pass

    tasks = [asyncio.create_task(listener(peer)) for peer in peers]
    await asyncio.gather(*tasks)

    for peer in peers:
        assert peer.transport.messages_received > 0
