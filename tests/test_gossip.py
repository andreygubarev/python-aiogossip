import asyncio
import collections
import dataclasses

import pytest

from aiogossip import gossip
from aiogossip.message import Message
from aiogossip.route import Route


async def test_gossip_initialization(node, transport):
    fanout = 5
    g = gossip.Gossip(node, transport, fanout)

    assert g.node == node
    assert g.transport == transport
    assert g._fanout == fanout
    assert len(g.topology) == 1


async def test_gossip_close(node, transport):
    g = gossip.Gossip(node, transport)
    await g.close()
    assert transport.sock._closed


async def test_gossip_fanout(node, transport):
    fanout = 5
    g = gossip.Gossip(node, transport, fanout)
    assert g.fanout == 1


@pytest.mark.parametrize("instances", [50])
async def test_gossip_cycles(node, transport, nodes):
    assert gossip.Gossip(node, transport, 0).cycles == 0
    assert gossip.Gossip(node, transport, 1).cycles == 1

    g = gossip.Gossip(node, transport, 5)
    for node in nodes[:5]:
        g.topology.add_node(node)
    assert g.cycles == 2

    g = gossip.Gossip(node, transport, 5)
    for node in nodes[:15]:
        g.topology.add_node(node)
    assert g.cycles == 2

    g = gossip.Gossip(node, transport, 5)
    for node in nodes[:25]:
        g.topology.add_node(node)
    assert g.cycles == 2

    g = gossip.Gossip(node, transport, 5)
    for node in nodes[:50]:
        g.topology.add_node(node)
    assert g.cycles == 3


@pytest.mark.parametrize("instances", [2])
async def test_send_and_receive(gossips):
    snode = gossips[0].node
    dnode = gossips[1].node
    saddr = gossips[0].transport.addr
    daddr = gossips[1].transport.addr

    gossips[0].topology.add_node(dnode)
    gossips[0].topology.add_route(Route(snode, saddr, dnode, daddr))

    message = Message(snode.node_id, dnode.node_id)
    sent_message = await gossips[0].send(message, dnode)
    assert gossips[0].transport.tx_packets > 0

    assert sent_message.message_id == message.message_id
    assert sent_message.message_type == message.message_type

    assert sent_message.route_endpoints[-2].node == snode
    assert sent_message.route_endpoints[-2].src == saddr
    assert sent_message.route_endpoints[-2].dst is None

    assert sent_message.route_endpoints[-1].node == dnode
    assert sent_message.route_endpoints[-1].src is None
    assert sent_message.route_endpoints[-1].dst == daddr

    async with asyncio.timeout(0.1):
        received_message = await anext(gossips[1].recv())

    assert received_message.message_id == message.message_id
    assert received_message.message_type == message.message_type

    assert received_message.route_endpoints[-2].node == snode
    assert received_message.route_endpoints[-2].src == saddr
    assert received_message.route_endpoints[-2].dst == saddr

    assert received_message.route_endpoints[-1].node == dnode
    assert received_message.route_endpoints[-1].src == daddr
    assert received_message.route_endpoints[-1].dst == daddr


@pytest.mark.parametrize("random_seed", [0])
@pytest.mark.parametrize("instances", [10])
@pytest.mark.asyncio
async def test_gossip(random_seed, gossips, message):
    assert gossips[0].fanout
    message = dataclasses.replace(message, message_type={Message.Type.GOSSIP})
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

    for g in gossips:
        if g.node == gossips[0].node:
            continue
        if any([g.node in g.topology for g in gossips]):
            assert g.transport.rx_packets > 0, g.topology
    rx_packets = sum(g.transport.rx_packets for g in gossips)
    assert rx_packets <= 2 ** len(gossips)

    for g in gossips:
        g.transport.close()


async def test_send_ack_value_error(gossips):
    g = gossips[0]
    message = Message(g.node.node_id, g.node.node_id, message_type={Message.Type.ACK})
    with pytest.raises(ValueError):
        await g.send_ack(message, g.node)

    message = Message(g.node.node_id, g.node.node_id, message_type={})
    with pytest.raises(ValueError):
        await g.send_ack(message, g.node)

    for g in gossips:
        g.transport.close()


@pytest.mark.parametrize("instances", [2])
async def test_send_ack(gossips, message):
    messages = collections.defaultdict(list)

    async def listener(gossip):
        try:
            async with asyncio.timeout(0.1):
                async for message in gossip.recv():
                    messages[gossip.node].append(message)
        except asyncio.TimeoutError:
            pass

    listeners = [asyncio.create_task(listener(n)) for n in gossips]

    message = dataclasses.replace(
        message,
        message_type={Message.Type.SYN},
        route_snode=gossips[0].node.node_id,
        route_dnode=gossips[1].node.node_id,
    )
    await gossips[0].send(message, gossips[1].node)
    await asyncio.gather(*listeners)

    assert len(messages[gossips[0].node]) == 1
    assert messages[gossips[0].node][0].message_type == {Message.Type.ACK}
    assert messages[gossips[0].node][0].route_snode == gossips[1].node.node_id
    assert messages[gossips[0].node][0].route_dnode == gossips[0].node.node_id

    assert len(messages[gossips[1].node]) == 1
    assert messages[gossips[1].node][0].message_type == {Message.Type.SYN}
    assert messages[gossips[1].node][0].route_snode == gossips[0].node.node_id
    assert messages[gossips[1].node][0].route_dnode == gossips[1].node.node_id

    for g in gossips:
        g.transport.close()


@pytest.mark.parametrize("instances", [2])
async def test_send_handshake(gossips):
    messages = collections.defaultdict(list)

    async def listener(gossip):
        try:
            async with asyncio.timeout(0.1):
                async for message in gossip.recv():
                    messages[gossip.node].append(message)
        except asyncio.TimeoutError:
            pass

    listeners = [asyncio.create_task(listener(n)) for n in gossips]

    await gossips[0].send_handshake(gossips[1].node)
    await asyncio.gather(*listeners)

    assert len(messages[gossips[0].node]) == 1
    assert messages[gossips[0].node][0].message_type == {Message.Type.ACK}
    assert messages[gossips[0].node][0].route_snode == gossips[1].node.node_id
    assert messages[gossips[0].node][0].route_dnode == gossips[0].node.node_id

    assert len(messages[gossips[1].node]) == 0

    for g in gossips:
        g.transport.close()


@pytest.mark.parametrize("instances", [3])
async def test_send_forward(gossips_with_topology_star):
    gossips = gossips_with_topology_star
    gossips[1].topology.add_node(gossips[2].node)
    # let node1 know that node2 is connected to node0
    gossips[1].topology.add_route(
        Route(gossips[0].node, list(gossips[0].node.addresses)[0], gossips[2].node, gossips[2].transport.addr)
    )

    messages = collections.defaultdict(list)

    async def listener(gossip):
        try:
            async with asyncio.timeout(0.1):
                async for message in gossip.recv():
                    messages[gossip.node].append(message)
        except asyncio.TimeoutError:
            pass

    listeners = [asyncio.create_task(listener(n)) for n in gossips]

    await gossips[1].send_handshake(gossips[2].node)
    await asyncio.gather(*listeners)

    for g in gossips:
        g.transport.close()
