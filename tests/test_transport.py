import ipaddress

import pytest
import typeguard

from aiogossip.address import Address
from aiogossip.message import Message


@pytest.mark.asyncio
async def test_send_recv(transport, message):
    await transport.send(message, transport.addr)
    received_message, received_addr = await transport.recv()
    assert received_message == message
    assert received_addr == transport.addr
    transport.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("instances", [2])
async def test_send_large_packet(transport, gossips):
    message = Message(
        route_snode=gossips[0].node,
        route_dnode=gossips[1].node,
        payload={"data": "a" * 4096},
    )

    with pytest.raises(ValueError):
        await transport.send(message, transport.addr)


@pytest.mark.asyncio
async def test_send_type_errors(transport, message):
    with pytest.raises(typeguard.TypeCheckError):
        await transport.send(message, ("127.0.0.1", 1337))

    with pytest.raises(TypeError):
        await transport.send(message, Address("127.0.0.1", 1337))

    with pytest.raises(TypeError):
        await transport.send(message, Address(ipaddress.ip_address("127.0.0.1"), 1337.0))
