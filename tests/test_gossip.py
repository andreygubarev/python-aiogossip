import asyncio

import pytest


@pytest.mark.asyncio
async def test_gossip(gossips, message):
    await gossips[0].send_gossip(message)

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
        if gossip.topology.node == gossips[0].topology.node:
            continue
        if any([gossip.topology.node in p.topology for p in gossips]):
            assert gossip.transport.rx_packets > 0, gossip.topology
    rx_packets = sum(p.transport.rx_packets for p in gossips)
    assert rx_packets <= 2 ** len(gossips)

    for gossip in gossips:
        gossip.transport.close()


@pytest.mark.parametrize("random_seed", [0])
@pytest.mark.parametrize("instances", [2])
@pytest.mark.asyncio
async def test_send_and_receive(gossips, message):
    message.kind.append(message.Kind.REQ)
    message.routing.snode = gossips[0].topology.node_id
    message.routing.dnode = gossips[1].topology.node_id
    message.payload = b"test_send_and_receive"
    await gossips[0].send(message, gossips[1].topology.node_id)

    received_message = await anext(gossips[1].recv())
    assert received_message.payload == message.payload
