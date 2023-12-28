import pytest

from aiogossip.message import (
    Endpoint,
    Message,
    update_recv_endpoints,
    update_send_endpoints,
)


@pytest.mark.parametrize("instances", [2])
def test_message(gossips):
    message = Message(
        route_snode=gossips[0].node,
        route_dnode=gossips[1].node,
    )
    assert message.route_snode == gossips[0].node
    assert message.route_dnode == gossips[1].node


@pytest.mark.parametrize("instances", [2])
def test_update_send_endpoints(gossips):
    send = Endpoint(node=gossips[0].node, src=list(gossips[0].node.addresses)[0])
    recv = Endpoint(node=gossips[1].node, dst=list(gossips[1].node.addresses)[0])

    message = Message(
        route_snode=gossips[0].node,
        route_dnode=gossips[1].node,
    )
    updated_message = update_send_endpoints(message, send, recv)

    assert updated_message.route_endpoints == [send, recv]
    assert updated_message.route_endpoints[-2].src == send.src
    assert updated_message.route_endpoints[-1].dst == recv.dst


@pytest.mark.parametrize("instances", [2])
def test_update_send_endpoints_prefilled(gossips):
    send = Endpoint(node=gossips[0].node, src=list(gossips[0].node.addresses)[0])
    recv = Endpoint(node=gossips[1].node, dst=list(gossips[1].node.addresses)[0])

    message = Message(
        route_snode=gossips[0].node,
        route_dnode=gossips[1].node,
        route_endpoints=[send],
    )
    updated_message = update_send_endpoints(message, send, recv)

    assert updated_message.route_endpoints == [send, recv]
    assert updated_message.route_endpoints[-2].src == send.src
    assert updated_message.route_endpoints[-1].dst == recv.dst


@pytest.mark.parametrize("instances", [2])
def test_update_recv_endpoints(gossips):
    send = Endpoint(node=gossips[0].node, src=list(gossips[0].node.addresses)[0])
    recv = Endpoint(node=gossips[1].node, dst=list(gossips[1].node.addresses)[0])

    message = Message(
        route_snode=gossips[0].node,
        route_dnode=gossips[1].node,
        route_endpoints=[send, recv],
    )
    updated_message = update_recv_endpoints(message, send, recv)

    assert updated_message.route_endpoints == [send, recv]
    assert updated_message.route_endpoints[-2].dst == send.dst
    assert updated_message.route_endpoints[-1].src == recv.src


@pytest.mark.parametrize("instances", [2])
def test_message_hash(gossips):
    message = Message(route_snode=gossips[0].node, route_dnode=gossips[1].node, message_id="test_id")
    assert hash(message) == hash("test_id")
