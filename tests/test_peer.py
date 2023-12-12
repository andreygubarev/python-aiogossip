import asyncio

import pytest


@pytest.mark.parametrize("random_seed", [0])
@pytest.mark.parametrize("instances", [2])
@pytest.mark.asyncio
async def test_peer(peers, message):
    peer1 = peers[0]
    assert peer1.peer_id is not None
    peer2 = peers[1]
    assert peer2.peer_id is not None
    assert peer1.peer_id != peer2.peer_id

    peer1.connect([peer2.node])
    assert peer2.peer_id in peer1.gossip.topology

    message.payload = b"Hello, world!"
    await peer1.publish("test", message)

    handler_message = None

    @peer2.subscribe("test")
    async def handler(message):
        nonlocal handler_message
        handler_message = message.payload

    await asyncio.sleep(0.1)
    assert handler_message == message.payload

    for peer in peers:
        await peer.disconnect()


@pytest.mark.parametrize("random_seed", [0])
@pytest.mark.parametrize("instances", [2])
@pytest.mark.asyncio
async def test_peer_publish_ack(peers, message):
    peers[0].connect([peers[1].node])
    await asyncio.sleep(0.1)

    response = await peers[0].publish("topic", message, syn=True)

    messages = []
    async for message in response:
        messages.append(message)

    assert len(messages) == 1
    assert messages[0].routing.snode == peers[1].peer_id
    assert messages[0].routing.dnode == peers[0].peer_id

    for peer in peers:
        await peer.disconnect()


@pytest.mark.parametrize("random_seed", [0])
@pytest.mark.parametrize("instances", [3])
@pytest.mark.asyncio
async def test_peer_forwarding(peers, message):
    peers[0].connect([peers[1].node])
    peers[1].connect([peers[2].node])

    handler_message = None
    subscribe = peers[0].subscribe("test")

    @subscribe
    async def handler(message):
        nonlocal handler_message
        handler_message = message.payload

    await asyncio.sleep(0.1)

    message.kind.append(message.Kind.REQ)
    message.routing.snode = peers[2].peer_id
    message.routing.dnode = peers[0].peer_id
    message.payload = b"test_peer_forwarding"
    await peers[2].publish("test", message, peers=[peers[0].peer_id])

    await asyncio.sleep(0.1)
    assert handler_message == message.payload

    for peer in peers:
        await peer.disconnect()


@pytest.mark.parametrize("random_seed", [0])
@pytest.mark.parametrize("instances", [3])
@pytest.mark.asyncio
async def test_peer_reverse_forwarding(peers, message):
    peers[0].connect([peers[1].node])
    peers[1].connect([peers[2].node])
    await asyncio.sleep(0.1)

    handler_message = None
    subscribe = peers[2].subscribe("test")

    @subscribe
    async def handler(message):
        nonlocal handler_message
        handler_message = message.payload

    message.kind.append(message.Kind.REQ)
    message.routing.snode = peers[0].peer_id
    message.routing.dnode = peers[2].peer_id
    message.payload = b"test_peer_reverse_forwarding"
    await peers[0].publish("test", message, peers=[peers[2].peer_id])

    await asyncio.sleep(0.1)
    assert handler_message == message.payload

    for peer in peers:
        await peer.disconnect()
