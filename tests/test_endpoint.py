import pytest

from aiogossip.endpoint import Endpoint


def test_endpoint_post_init_node_type(address):
    with pytest.raises(TypeError, match="node must be Node"):
        Endpoint("not a Node", address, address)


def test_endpoint_post_init_saddr_type(node, address):
    with pytest.raises(TypeError, match="src must be Address"):
        Endpoint(node, "not an Address", address)


def test_endpoint_post_init_daddr_type(node, address):
    with pytest.raises(TypeError, match="dst must be Address"):
        Endpoint(node, address, "not an Address")


def test_endpoint_post_init_correct_types(node, address):
    try:
        Endpoint(node, address, address)
    except TypeError:
        pytest.fail("TypeError was raised with correct types")
